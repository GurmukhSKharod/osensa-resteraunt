# aiohttp health server so deploy can probe the service.
import os
from aiohttp import web

async def _ok(_):
    return web.Response(text="ok")

async def run_health_server():
    app = web.Application()
    app.router.add_get("/health", _ok)
    port = int(os.environ.get("PORT", "8080"))  
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()