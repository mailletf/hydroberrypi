
from prometheus_client import start_http_server, Gauge
import time, os
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
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)


# Software SPI configuration for analog sensors
CLK  = 18
MISO = 23
MOSI = 24
CS   = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

# which input channels on the MCP3008 are the sensors connected to
ANALOG_CHANNEL_LIGHT = 0


# setup filepath to read 1-wire device readings
base_dir = '/sys/bus/w1/devices/'
ambiant_temp_path = os.path.join(base_dir, "28-03168be0d1ff", "w1_slave")
reservoir_temp_path = os.path.join(base_dir, "28-0416a192e5ff", "w1_slave")

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

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    logger.info("Starting up HTTP server...")
    start_http_server(8000)

    logger.info("Starting main loop...")
    while True:
        logger.debug("Polling sensors")
        update_light_intensity()
        update_reservoir_temp()
        update_ambiant_temp()
        time.sleep(5)


