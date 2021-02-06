from urllib.request import urlopen
from dateutil import tz
from datetime import datetime


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


def seconds_between(left, right):
    return ((left-right).total_seconds())
