# PicoWeather
Raspberry Pi Pico program which uses the BME280 sensor to send temperature and humidity data to a server every 10 minutes.
PicoWeatherServer is the Python server which receives the data from the Pi Pico. It can run on any system with Python and the relevant network modules.

To install:
1. Modify the pico_wifi_config.py file to include the relevant details for your wifi network (change the 'ssid' and 'ssid_password' strings)
2. Modify the 'host' and 'port' details within pico_wifi_config.py to match the details of the server where you will run PicoWeatherServer.py
3. Upload all files to / on your Pico W
4. Start PicoWeatherServer on the server that will be gathering the data (see the README in the PicoWeatherServer repository)
5. Reboot your Pico

