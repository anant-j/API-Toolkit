import json
import os
from datetime import datetime, timedelta
from urllib.request import urlopen

import requests
from dateutil import tz

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory + '/secrets/keys.json') as f:
    api_keys = json.load(f)


class TravelTime:
    def __init__(self, start, end):
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        apikey = api_keys["Google_Distance_Matrix"]
        self.origin = start
        self.destination = end
        querystring = {"units": "metric",
                       "departure_time": str(int(current_time().timestamp())),
                       "traffic_model": "best_guess",
                       "origins": self.origin,
                       "destinations": self.destination,
                       "key": apikey}
        headers = {
            'cache-control': "no-cache",
        }
        response = requests.request(
            "GET", url, headers=headers, params=querystring)
        result = json.loads(response.text)
        self.current_time = current_time().strftime("%I:%M:%S")
        self.distance = result['rows'][0]['elements'][0]['distance']['text']
        self.traffic_time = result['rows'][0]['elements'][0]['duration_in_traffic']['text']
        self.traffic_time_sec = result['rows'][0]['elements'][0]['duration_in_traffic']['value']


# This is required because not sure where deployment servers are located
# Cannot rely on system's date & time values
def current_time():
    res = urlopen('http://just-the-time.appspot.com/')
    result = res.read().strip()
    result_str = result.decode('utf-8')
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')
    utc = datetime.strptime(result_str, '%Y-%m-%d %H:%M:%S')
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return (central)
    # print(int(central.timestamp()))


# Computes estimated time of arrival
def eta(time):
    central = current_time()
    return (str(central + timedelta(seconds=time))[0:19])
