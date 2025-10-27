# backend/src/kitchen/main.py
"""
Main entry for the kitchen worker: connects to MQTT broker and processes orders.
"""

import asyncio
import logging
import os

from .service import MqttService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def main() -> None:
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
