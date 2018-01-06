# Hydro Berry Pi

This script is part of a hydroponics garden monitoring system. Details of the system are 
here: http://blog.francoismaillet.com/indoor-nft-hydroponics/

The script currently fetches readings from sensors connected to a Pi as well as weather information 
from the OpenWeatherMap API and serves an endpoint that a Prometheus server can get the data from.

The sensors used are:

- Ambiant light sensor: KY-018
- Ambiant temperature sensor: DHT11
- Water temperature sensor: DS18B20


## Usage

Create a file named `openweather_api_url.txt` and put the OpenWeatherMap API URL that contains your key
and the location for which you want to fetch the weather data.

Start the script and configure a Promethus server to fetch data from the route it serves.
