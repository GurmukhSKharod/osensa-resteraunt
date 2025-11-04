# backend/app.py
import asyncio
import os
import threading
import logging

from src.kitchen.health import run_health_server
from src.kitchen.service import MqttService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def _health_thread():
    asyncio.run(run_health_server())

def main() -> None:
    threading.Thread(target=_health_thread, daemon=True).start()

    ws_url = os.getenv("MQTT_URL", "ws://localhost:8083/mqtt")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    svc = MqttService(ws_url, loop=loop)
    try:
        loop.run_until_complete(svc.run())
    except KeyboardInterrupt:
        pass
    finally:
        svc.stop()
        loop.run_until_complete(asyncio.sleep(0.1))
        loop.stop()
        loop.close()

if __name__ == "__main__":
    main()
