@echo off
echo Installing Arduino CLI and Python (needs internet)...
winget install -e --id ArduinoSA.CLI --accept-source-agreements --accept-package-agreements
winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
echo.
echo DONE. Now CLOSE this window and double-click 2_setup_arduino.bat
pause
