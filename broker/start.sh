#!/usr/bin/env sh
set -eu

PORT="${PORT:-8083}"

cat >/mosquitto/config/mosquitto.conf <<EOF
persistence true
persistence_location /mosquitto/data/

listener ${PORT}
protocol websockets
http_dir /mosquitto/www

allow_anonymous true
EOF

exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf -v
