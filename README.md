# OSENSA Restaurant

# Introduction
OSENSA Restaurant is a tiny event-driven demo: customers place ORDERs from a web UI, the Python backend simulates prep time, and the UI shows FOOD ready events in real time via MQTT over WebSockets.

A 4-table one-page interface: click ORDER, type a food (free text), and it appears under that table when ready. Multiple orders can run concurrently.


---

# Pipeline
1. Frontend publishes ORDER 
2. Broker (MQTT over WebSockets)
3. Backend validates + waits random 0.8–4s 
4. Backend publishes FOOD 
5. Frontend updates the table list.

Note: If error then it shows up below in global errors section.

Note: While food is preparing it is shown below as well.

Component files:
- Frontend
  - src/App.svelte
  - src/lib/mqtt.ts
  - src/lib/store.ts
  - src/lib/types.ts
- Backend
  - src/kitchen/domain.py
  - src/kitchen/service.py
  - src/kitchen/config.py
  - src/kitchen/main.py
- Broker
  - broker/mosquitto.conf (dev)
  - broker/mosquitto.prod.conf (prod)
- Tests
  - backend/tests/*
  - frontend/src/lib/__tests__/*

Be sure to check out the comments in each file for config and detailed notes.

---

# Tech Stack

## Backend
Python 3.11+, asyncio, paho-mqtt.
- Validates orders, simulates prep, publishes FOOD.
- Structured logging, never crashes on bad input (publishes status:error instead).

## Frontend
Svelte 5 + Vite + TypeScript + mqtt.js.
- Sends ORDER, subscribes to FOOD, reactive UI.

## Broker
Eclipse Mosquitto (MQTT over WebSockets).
- Dev: anonymous allowed on ws://localhost:8083/mqtt.
- Prod: WSS + username/password.

## Tests
- Backend: pytest.
- Frontend: Vitest (unit tests for stores and MQTT wiring).

---

# Initial Setup (Local)

Prereqs: Docker Desktop, Python 3.11+, Node.js 20.19+ (or 22.12+).

1) Start the broker (from repo root)
```
docker compose up -d
```

2) Backend
```
cd backend
python -m venv .venv
Windows PowerShell: .\\.venv\\Scripts\\Activate.ps1
Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```
- Set environment (per terminal session):
  - Windows:
    - $env:PYTHONPATH = (Resolve-Path .\\src).Path
    - $env:MQTT_URL = "ws://localhost:8083/mqtt"
  - Linux/macOS:
    - export PYTHONPATH=$(pwd)/src
    - export MQTT_URL=ws://localhost:8083/mqtt
- Run:
```
python -m kitchen.main
```
  - Expect to see a “mqtt_connected” log.


3) Frontend

```
cd frontend
npm install
Optional: create .env.local with VITE_MQTT_URL=ws://localhost:8083/mqtt
npm run dev
Open the printed URL (usually http://localhost:5173).
```

---

# Directory Structure
```
osensa-restaurant/
- broker/
  - mosquitto.conf
  - mosquitto.prod.conf
  - Dockerfile (optional for prod broker)
- backend/
  - Dockerfile
  - requirements.txt
  - pytest.ini
  - src/kitchen/
    - __init__.py
    - config.py
    - domain.py
    - service.py
    - main.py
  - tests/
    - test_domain.py
    - test_service_concurrency.py
- frontend/
  - netlify.toml
  - index.html
  - package.json
  - tsconfig.json
  - vite.config.ts
  - src/
    - app.css
    - main.ts
    - App.svelte
    - lib/
      - mqtt.ts
      - store.ts
      - types.ts
      - __tests__/
        - mqtt.spec.ts
        - store.spec.ts
- docker-compose.yml
- .gitignore
- README.md
```

---

# Running Tests

Backend:
```
- cd backend
- .\\.venv\\Scripts\\Activate.ps1  (or source .venv/bin/activate)
- pytest -q
```

Frontend:
```
- cd frontend
- npm run test
```

---

# Topics & JSON

Topics:
```
- Orders: restaurant/orders/<table>
- Foods:  restaurant/foods/<table> (table 0 used for global/invalid errors)
```

Order:
```
{ "orderId": "uuid", "table": 1, "food": "Pizza", "ts": 1700000000000 }
```
FoodEvent:
```
{ "orderId": "uuid", "table": 1, "food": "Pizza", "status": "ready" | "error", "prepMs": 2970?, "error": "invalid order"? }
```
---

# Deployment (Quick)

Broker:
- Use mosquitto.prod.conf (allow_anonymous false + password_file).
- Serve WSS on 8083 via your platform or a TLS proxy.

Backend (Dockerfile provided):
- Build & run on Fly/Render/Railway.
- Set env MQTT_URL=wss://<your-broker>/mqtt.
- Keep one instance always-on.

Frontend (Netlify):
- Build: npm install && npm run build
- Publish: dist
- Env var: VITE_MQTT_URL=wss://<your-broker>/mqtt

---

# Troubleshooting

- If Vite complains about Node version, then install Node 20.19+ (or 22.12+).
- If Blank UI, then check DevTools console and restart dev server after changing vite.config.ts.
- If Backend "No module named kitchen", then set PYTHONPATH to backend/src.

---

Thank you.
