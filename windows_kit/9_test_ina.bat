@echo off
set /p PORT=COM port of Node 0 (for example COM10):
set PORT=%PORT:COM=%
set PORT=COM%PORT:com=%
arduino-cli compile --fqbn esp8266:esp8266:nodemcuv2 --upload -p %PORT% i2c_scan
echo Showing the test output. Press Ctrl+C to stop.
arduino-cli monitor -p %PORT% -c baudrate=115200
pause
