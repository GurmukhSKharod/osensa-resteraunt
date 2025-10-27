#!/usr/bin/env sh
set -eu

PORT="${PORT:-8083}"

cat >/mosquitto/config/mosquitto.conf <<EOF
persistence true
persistence_location /mosquitto/data/

listener ${PORT}
protocol websockets
http_dir /mosquitto/www

# Demo-friendly; tighten for prod with auth (see notes later)
allow_anonymous true
EOF

exec /docker-entrypoint.sh mosquitto -c /mosquitto/config/mosquitto.conf
