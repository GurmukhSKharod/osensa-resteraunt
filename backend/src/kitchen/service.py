"""
Service layer: bridge between MQTT broker and our domain logic.

Design:
- Use paho-mqtt with transport="websockets" so the backend can use WS.
- Run the paho network loop in a background thread.
- Push inbound messages into an asyncio.Queue from paho callbacks.
- An async consumer pulls messages, and for each one:
    validate -> await sleep(prep_ms) -> publish FoodEvent
- bad input: publish an error event
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
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


# Logging setup 
log = logging.getLogger("kitchen.service")
if not log.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt='{"level":"%(levelname)s","t":"%(asctime)s","msg":"%(message)s"}'
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.INFO)


# Small helper to parse ws://host:port/path into host/port/path
@dataclass(frozen=True)
class WsEndpoint:
    host: str
    port: int
    path: str


def parse_ws_url(url: str) -> WsEndpoint:
    """
    Accepts: ws://localhost:8083/mqtt  or  wss://my-broker/mqtt
    Returns: host, port, path (default port 80/443 if missing)
    """
    u = urlparse(url)
    if u.scheme not in ("ws", "wss"):
        raise ValueError("MQTT_URL must start with ws:// or wss://")

    port = u.port or (443 if u.scheme == "wss" else 80)
    path = u.path or "/mqtt"
    return WsEndpoint(host=u.hostname or "localhost", port=port, path=path)


# Core order handler - async, testable without a broker
async def handle_order(
    raw_payload: bytes,
    publish: Callable[[str, bytes], Awaitable[None]],
    min_ms: int = config.MIN_PREP_MS,
    max_ms: int = config.MAX_PREP_MS,
) -> None:
    """
    Process one ORDER message:
    - parse/validate
    - compute prep time
    - await sleep
    - publish ready event

    On validation error, publish an error event.
    """
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


# MQTT runner - uses paho-mqtt websockets and integrates with asyncio via Queue
class MqttService:
    def __init__(self, ws_url: str, loop: asyncio.AbstractEventLoop):
        self.ws = parse_ws_url(ws_url)
        self.loop = loop
        self.client = mqtt.Client(transport="websockets")  # WS transport
        self.client.enable_logger()  # pipe basic logs to stdlib logging

        # Events come in on this queue (populated from paho callbacks)
        self.queue: asyncio.Queue[tuple[str, bytes]] = asyncio.Queue()

        # Wire callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        # Set WS path 
        self.client.ws_set_options(path=self.ws.path)

        # Backoff reconnect in our loop if needed
        self._stop = asyncio.Event()

    # paho callbacks (run in its thread)
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("mqtt_connected")
            client.subscribe(f"{config.ORDER_TOPIC_PREFIX}#")
        else:
            log.error(f"mqtt_connect_failed rc={rc}")

    def _on_message(self, client, userdata, msg):
        # asyncio loop 
        try:
            asyncio.run_coroutine_threadsafe(self.queue.put((msg.topic, msg.payload)), self.loop)
        except RuntimeError:
            pass

    async def publish(self, topic: str, payload: bytes) -> None:
        # paho publish is sync, run in executor
        def _pub():
            self.client.publish(topic, payload=payload, qos=1)

        await self.loop.run_in_executor(None, _pub)

    async def run(self) -> None:
        """
        Connect to broker and process messages until stop() is called.
        Uses paho's background thread for network I/O.
        """
        while not self._stop.is_set():
            try:
                # Connect - will raise on DNS/socket errors
                self.client.connect(self.ws.host, self.ws.port, keepalive=30)
                self.client.loop_start()  # start background network loop

                # Main consumer loop
                while not self._stop.is_set():
                    topic, payload = await self.queue.get()
                    if not topic.startswith(config.ORDER_TOPIC_PREFIX):
                        continue
                    # Fire-and-forget task for concurrency
                    asyncio.create_task(handle_order(payload, self.publish))
            except (socket.gaierror, OSError) as e:
                log.error(f"mqtt_connect_error: {e}; retrying in 2s")
                await asyncio.sleep(2)
            finally:
                self.client.loop_stop()
                try:
                    self.client.disconnect()
                except Exception:
                    pass

    def stop(self) -> None:
        self._stop.set()
