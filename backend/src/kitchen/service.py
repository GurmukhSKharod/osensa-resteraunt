"""
Service layer: bridge between MQTT broker and our domain logic.

- Uses paho-mqtt with WebSockets so the backend can talk to the broker at wss://.../mqtt
- Paho's network loop runs in a background thread.
- Inbound messages are pushed into an asyncio.Queue from paho callbacks.
- An async consumer validates orders, sleeps for a random "prep time",
  then publishes FOOD events (or an error event on invalid input).
"""

from __future__ import annotations
import asyncio
import json
import logging
import socket
from dataclasses import dataclass
from typing import Callable, Awaitable, Optional
from urllib.parse import urlparse

import paho.mqtt.client as mqtt

from . import config
from .domain import (
    validate_order,
    make_food_event_ok,
    make_food_event_err,
    prep_time,
    ValidationError,
)

log = logging.getLogger("kitchen.service")
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(
        logging.Formatter(fmt='{"level":"%(levelname)s","t":"%(asctime)s","msg":"%(message)s"}')
    )
    log.addHandler(_h)
    log.setLevel(logging.INFO)


@dataclass(frozen=True)
class WsEndpoint:
    host: str
    port: int
    path: str
    secure: bool


def parse_ws_url(url: str) -> WsEndpoint:
    u = urlparse(url)
    if u.scheme not in ("ws", "wss"):
        raise ValueError("MQTT_URL must start with ws:// or wss://")
    port = u.port or (443 if u.scheme == "wss" else 80)
    path = u.path or "/mqtt"
    return WsEndpoint(host=u.hostname or "localhost", port=port, path=path, secure=(u.scheme == "wss"))


async def handle_order(
    raw_payload: bytes,
    publish: Callable[[str, bytes], Awaitable[None]],
    min_ms: int = config.MIN_PREP_MS,
    max_ms: int = config.MAX_PREP_MS,
) -> None:
    data: Optional[dict] = None
    try:
        data = json.loads(raw_payload.decode("utf-8"))
        order = validate_order(data)
    except (ValidationError, json.JSONDecodeError) as e:
        log.warning(f"invalid_order: {e}")
        evt = make_food_event_err(data if isinstance(data, dict) else {}, "invalid order")
        topic = f"{config.FOOD_TOPIC_PREFIX}{evt.table or 0}"
        await publish(topic, json.dumps(evt.__dict__).encode("utf-8"))
        return

    ms = prep_time(min_ms, max_ms)
    log.info(f"order_received table={order.table} food={order.food} orderId={order.orderId} prepMs={ms}")
    await asyncio.sleep(ms / 1000.0)
    evt = make_food_event_ok(order, ms)
    topic = f"{config.FOOD_TOPIC_PREFIX}{order.table}"
    await publish(topic, json.dumps(evt.__dict__).encode("utf-8"))
    log.info(f"food_published table={order.table} orderId={order.orderId} prepMs={ms}")


class MqttService:
    def __init__(self, ws_url: str, loop: asyncio.AbstractEventLoop):
        self.ws = parse_ws_url(ws_url)
        self.loop = loop
        self.client = mqtt.Client(client_id="backend-kitchen", transport="websockets")

        def _on_log(client, userdata, level, buf):
            print("PAHO:", level, buf)
        self.client.on_log = _on_log

        self.client.ws_set_options(path=self.ws.path)

        if self.ws.secure:
            self.client.tls_set()
            self.client.tls_insecure_set(False)

        self.queue: asyncio.Queue[tuple[str, bytes]] = asyncio.Queue()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self._stop = asyncio.Event()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("mqtt_connected")
            client.subscribe(f"{config.ORDER_TOPIC_PREFIX}#")
        else:
            log.error(f"mqtt_connect_failed rc={rc}")

    def _on_message(self, client, userdata, msg):
        try:
            asyncio.run_coroutine_threadsafe(self.queue.put((msg.topic, msg.payload)), self.loop)
        except RuntimeError:
            pass

    async def publish(self, topic: str, payload: bytes) -> None:
        def _pub():
            self.client.publish(topic, payload=payload, qos=1)
        await self.loop.run_in_executor(None, _pub)

    async def run(self) -> None:
        while not self._stop.is_set():
            try:
                self.client.connect(self.ws.host, self.ws.port, keepalive=30)
                self.client.loop_start()
                while not self._stop.is_set():
                    topic, payload = await self.queue.get()
                    if topic.startswith(config.ORDER_TOPIC_PREFIX):
                        asyncio.create_task(handle_order(payload, self.publish))
            except (socket.gaierror, OSError) as e:
                log.error(f"mqtt_connect_error: {e}; retrying in 2s")
                await asyncio.sleep(2)
            finally:
                try:
                    self.client.loop_stop()
                    self.client.disconnect()
                except Exception:
                    pass

    def stop(self) -> None:
        self._stop.set()
