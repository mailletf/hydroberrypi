
from prometheus_client import start_http_server, Gauge
import argparse
import urllib.request
import json
import time
import os
import logging

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

# setup logging
logger = logging.getLogger('hydroberrypi')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)
formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)


# Software SPI configuration for analog sensors
CLK = 18
MISO = 23
MOSI = 24
CS = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

# which input channels on the MCP3008 are the sensors connected to
ANALOG_CHANNEL_LIGHT = 0


# setup filepath to read 1-wire device readings
base_dir = '/sys/bus/w1/devices/'
ambiant_temp_path = os.path.join(base_dir, "28-03168be0d1ff", "w1_slave")
reservoir_temp_path = os.path.join(base_dir, "28-0416a192e5ff", "w1_slave")

# setup openweather api url
OPENWEATHER_API = -1
if os.path.exists("openweather_api_url.txt"):
    # if the file exists, naivly load it without checking anything
    OPENWEATHER_API = open("openweather_api_url.txt").read().strip()
    print("OpenweatherMap URL: ", OPENWEATHER_API)


def read_1wire(path):
    # 5d 01 4b 46 7f ff 0c 10 94 : crc=94 YES
    # 5d 01 4b 46 7f ff 0c 10 94 t=21812
    lines = open(path).readlines()
    if lines[0].strip()[-3:] != 'YES':
        return NaN

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        return float(temp_string)


# setup prometeus metrics
RESERVOIR_TEMP = Gauge('reservoir_temp', 'Reservoir temperature')
AMBIANT_TEMP = Gauge('ambiant_temp', 'Ambiant temperature')
LIGHT_INTENSITY = Gauge('light_intensity', 'Light intensity')

WEATHER_TEMPERATURE = Gauge('weather_temp', 'Weather - Temperature in celcius')
WEATHER_PRESSURE = Gauge('weather_pressure',
                         'Weather - Atmospheric pressure (on the sea level, ' +
                         'if there is no sea_level or grnd_level data), hPa')
WEATHER_HUMIDITY = Gauge('weather_humidity', 'Weather - Humidity %')
WEATHER_WIND_SPEED = Gauge('weather_wind_speed',
                           'Weather - Wind speed meter/sec')
WEATHER_CLOUDS = Gauge('weather_cloud', 'Weather - Cloudiness %')
WEATHER_SUNRISE = Gauge('weather_sunrise', 'Weather - Sunrise time, unix, UTC')
WEATHER_SUNSET = Gauge('weather_sunset', 'Weather - Sunset time, unix, UTC')


def update_light_intensity():
    val = mcp.read_adc(ANALOG_CHANNEL_LIGHT)
    LIGHT_INTENSITY.set(val)
    logger.debug("Light intensity: "+str(val))


def update_reservoir_temp():
    val = read_1wire(reservoir_temp_path) / 1000.0
    logger.debug("Reservoir temp: "+str(val)+" Celcius")
    RESERVOIR_TEMP.set(val)


def update_ambiant_temp():
    val = read_1wire(ambiant_temp_path) / 1000.0
    logger.debug("Ambiant temp: "+str(val)+" Celcius")
    AMBIANT_TEMP.set(val)


last_weather_update = -1
def update_current_weather():
    DEMO_URL = "https://openweathermap.org/data/2.5/weather?q=Verdun,ca&appid=b1b15e88fa797225412429c1c50c122a1"
    global last_weather_update
    time_diff = time.time() - last_weather_update
    if time_diff > 60*15:
        last_weather_update = time.time()
        try:
            with urllib.request.urlopen(OPENWEATHER_API) as url:
                data = json.loads(url.read().decode())
                logger.info(data)

                WEATHER_TEMPERATURE.set(data["main"]["temp"])
                WEATHER_PRESSURE.set(data["main"]["pressure"])
                WEATHER_HUMIDITY.set(data["main"]["humidity"])
                WEATHER_WIND_SPEED.set(data["wind"]["speed"])
                WEATHER_CLOUDS.set(data["clouds"]["all"])
                WEATHER_SUNRISE.set(data["sys"]["sunrise"])
                WEATHER_SUNSET.set(data["sys"]["sunset"])

        except Exception as e:
            logger.warning("Error updating weather: " + str(e))

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--port", help="Port to use for web server",
                            type=int, default=8000)
    parser.add_argument("--disable-light-sensor", help="Disable reading from the light sensor", action="store_true")
    parser.add_argument("--disable-reservoir-sensor", help="Disable reading from the reservoir temperature sensor", action="store_true")
    parser.add_argument("--disable-ambiant-sensor", help="Disable reading from the ambiant temperature sensor", action="store_true")
    parser.add_argument("--disable-weather", help="Disable fetching current weather", action="store_true")
    args = parser.parse_args()

    # Start up the server to expose the metrics.
    logger.info("Starting up HTTP server on port %d..." % args.port)
    start_http_server(args.port)

    logger.info("Starting main loop...")
    while True:
        logger.debug("Polling sensors")
        if not args.disable_light_sensor: update_light_intensity()
        if not args.disable_reservoir_sensor: update_reservoir_temp()
        if not args.disable_ambiant_sensor: update_ambiant_temp()
        if not args.disable_weather: update_current_weather()
        time.sleep(5)
