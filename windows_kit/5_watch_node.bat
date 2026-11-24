@echo off
set /p PORT=COM port of the board (for example COM5):
echo Showing the board's output. Look for BOOT,...,wifi=1. Press Ctrl+C to stop.
arduino-cli monitor -p %PORT% -c baudrate=115200
pause
