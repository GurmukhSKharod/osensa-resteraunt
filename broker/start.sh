#!/usr/bin/env sh
set -eu

PORT="${PORT:-8083}"

# Ensure paths exist
mkdir -p /mosquitto/config
mkdir -p /mosquitto/data
mkdir -p /mosquitto/www    

echo "<h1>Mosquitto WebSockets</h1>" > /mosquitto/www/index.html

cat >/mosquitto/config/mosquitto.conf <<EOF
persistence true
persistence_location /mosquitto/data/

listener ${PORT}
protocol websockets
http_dir /mosquitto/www

allow_anonymous true
EOF

exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf -v
