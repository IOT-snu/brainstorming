@echo off
set /p PORT=COM port of the board (for example COM5):
set /p ID=Node number (0, 1, 2 or 3):
echo Flashing node %ID% on %PORT% ...
arduino-cli compile --fqbn esp8266:esp8266:nodemcuv2 --build-property "build.extra_flags=-DNODE_ID=%ID%" --upload -p %PORT% firmware\esp8266_foa
echo.
echo If it says "Hard resetting via RTS pin" it worked. Run 5_watch_node.bat to check it.
pause
