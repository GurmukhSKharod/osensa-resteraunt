"""
Main for running the backend locally + deployed demo.
"""

import asyncio
import logging
import os
from .health import run_health_server

from .service import MqttService

# Basic logging (stderr)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main() -> None:

    ws_url = os.getenv("MQTT_URL", "ws://localhost:8083/mqtt")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # start HTTP health server for Render
    asyncio.create_task(run_health_server())

    svc = MqttService(ws_url, loop=loop)

    try:
        loop.run_until_complete(svc.run())
    except KeyboardInterrupt:
        pass
    finally:
        svc.stop()
        # give tasks a moment to cancel cleanly
        loop.run_until_complete(asyncio.sleep(0.1))
        loop.stop()
        loop.close()


if __name__ == "__main__":
    main()
