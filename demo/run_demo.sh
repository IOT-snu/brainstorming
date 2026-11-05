#!/bin/bash
# Everything we can demonstrate before the ESP32 boards arrive, in about two minutes.
# Run from anywhere:  bash demo/run_demo.sh          (add --esp32 to also compile the firmware, about 1 minute)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
line() { printf '\n========== %s ==========\n' "$1"; }

line "1. Unit and property tests of the simulator (16 tests)"
(cd experiments/foa && python3 -m pytest -q tests)

line "2. ESP32 C code checked against the Python reference"
python3 firmware/make_vectors.py
cc -O2 -std=c99 -Wall -Wextra -o firmware/host_test firmware/host_test.c firmware/esp32_foa/foa_core.c firmware/esp32_foa/foa_sha256.c -lm
./firmware/host_test firmware/vectors.bin

line "3. Live simulation on real N-BaIoT traffic"
python3 demo/live_demo.py

if [ "$1" == "--esp32" ]; then
  line "4. Compile the firmware for a real ESP32"
  arduino-cli compile --fqbn esp32:esp32:esp32 firmware/esp32_foa 2>&1 | grep -E "Sketch uses|Global variables"
  arduino-cli compile --fqbn esp32:esp32:esp32 firmware/footprint_baseline 2>&1 | grep -E "Sketch uses|Global variables" | sed 's/^/(without FOA) /'
  arduino-cli compile --fqbn esp32:esp32:esp32 firmware/ina219_monitor 2>&1 | grep -E "Sketch uses" | sed 's/^/(power monitor) /'
fi

line "Done. Open demo/demo_scene1.png and demo/demo_scene2.png"
