@echo off
echo Setting up ESP8266 support and libraries (5-10 minutes)...
arduino-cli config init
arduino-cli config add board_manager.additional_urls https://arduino.esp8266.com/stable/package_esp8266com_index.json
arduino-cli core update-index
arduino-cli core install esp8266:esp8266
arduino-cli lib install "Adafruit SSD1306" "Adafruit GFX Library" "DHT sensor library" "Adafruit Unified Sensor"
python -m pip install pyserial
echo.
echo DONE. Next: edit firmware\esp8266_foa\foa_config.h (see START_HERE.txt step 4)
pause
