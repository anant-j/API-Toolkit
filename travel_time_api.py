import requests
import time
import json
import os
from datetime import datetime,timedelta
from dateutil import tz
from urllib.request import urlopen

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory+'/secrets/distance_matrix_keys.json') as f:
    api_keys = json.load(f)

class TravelTime:
    def __init__(self, start,end):
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        apikey = api_keys["API_key"]
        self.origin=start
        self.destination=end
        querystring = {"units":"metric","departure_time":str(int(time.time())),"traffic_model":"best_guess","origins":self.origin,"destinations":self.destination,"key":apikey}
        headers = {
            'cache-control': "no-cache",
            'postman-token': "something"
            }
        response = requests.request("GET", url, headers=headers, params=querystring)
        result = json.loads(response.text)
        self.current_time=time.strftime("%I:%M:%S")
        self.distance = result['rows'][0]['elements'][0]['distance']['text']
        self.traffic_time= result['rows'][0]['elements'][0]['duration_in_traffic']['text']
        self.traffic_time_sec= result['rows'][0]['elements'][0]['duration_in_traffic']['value']
   
    def get_distance(self): 
        return self.distance

    def get_traffictime(self):
        return self.traffic_time

    def get_traffictime_sec(self):
        return self.traffic_time_sec

def bus_home():
    Travel=TravelTime("33 Yonge Street,Toronto, Ontario","Main St. W. @ Paisley Ave. S., HAMILTON, Onatrio")
    leg1=Travel.get_traffictime_sec()
    total_time=(int(leg1)//60)+25
    if (total_time>59):
        total_time=str(timedelta(minutes=total_time))
        hour=total_time[:-6]
        if int(hour) > 1:
            res_hour = hour + " hours"
        else:
            res_hour = hour + " hour"
        minute=total_time[2:-3]
        res_eta=eta(int(str(hour)),int(str(minute)))
        if int(minute) > 1:
            res_minute = minute +" minutes"
        else:
            res_minute = minute + " minute"
        return (res_hour+" "+res_minute+"\nThe estimated ETA is: "+res_eta)
    else:
        return (str(total_time)+" minutes.\nThe estimated ETA is: " + res_eta)

def gowork():
    Travel=TravelTime("King St. W. @ Dundurn St. N","Union Station Bus Terminal Toronto")
    leg1=Travel.get_traffictime_sec()
    total_time=(int(leg1)//60)+22
    if (total_time>59):
        total_time=str(timedelta(minutes=total_time))
        hour=total_time[:-6]
        if int(hour) > 1:
            res_hour = hour + " hours"
        else:
            res_hour = hour + " hour"
        minute=total_time[2:-3]
        res_eta=eta(int(str(hour)),int(str(minute)))
        print(res_eta)        
        if int(minute) > 1:
            res_minute = minute +" minutes"
        else:
            res_minute = minute + " minute"
        return (res_hour+" "+res_minute+"\nThe estimated ETA is: "+res_eta)
    else:
        return (str(total_time)+" minutes.\nThe estimated ETA is: "+res_eta)


def eta(h,m):
    res = urlopen('http://just-the-time.appspot.com/')
    result = res.read().strip()
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')
    utc = datetime.strptime(result_str, '%Y-%m-%d %H:%M:%S')
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return (str(central + timedelta(hours=h,minutes=m))[11:19])
