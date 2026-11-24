#!/bin/bash
# Flash the FOA firmware to one ESP8266 (NodeMCU).   Usage: bash firmware/flash_esp8266.sh <port> <node id 0-3> [calib]
# Example: bash firmware/flash_esp8266.sh /dev/cu.usbserial-0001 1
set -e
PORT="$1"; ID="$2"; EXTRA=""
[ -z "$PORT" ] || [ -z "$ID" ] && { echo "usage: $0 <port> <node id> [calib]"; exit 1; }
[ "$3" == "calib" ] && EXTRA="-DCALIB_LOG"
SKETCH="$(cd "$(dirname "$0")" && pwd)/esp8266_foa"
arduino-cli compile --fqbn esp8266:esp8266:nodemcuv2 --build-property "build.extra_flags=-DNODE_ID=$ID $EXTRA" --upload -p "$PORT" "$SKETCH"
echo "Flashed node $ID on $PORT. Watch it with: arduino-cli monitor -p $PORT -c baudrate=115200"
