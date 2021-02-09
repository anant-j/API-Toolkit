from urllib.request import urlopen
from dateutil import tz
from datetime import datetime
import sys


# This is required because not sure where deployment servers are located
# Cannot rely on system's date & time values
def current_time():
    return datetime.now()


# This is required because not sure where deployment servers are located
# Cannot rely on system's date & time values
def current_time_from_api():
    res = urlopen('http://just-the-time.appspot.com/')
    result = res.read().strip()
    result_str = result.decode('utf-8')
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')
    utc = datetime.strptime(result_str, '%Y-%m-%d %H:%M:%S')
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return central


# Calculates seconds between two datetime values
def seconds_between(left, right):
    return (left-right).total_seconds()


# Logs Error Message in PythonAnywhere
def log_error(message):
    time = (datetime.now())
    error_code = shift(str(time.timestamp()), 5)
    print(error_code + " : " + message, file=sys.stderr)
    return error_code


# https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password#:~:text=To%20encrypt%20or%20decrypt%20messages,encrypted%20token%20are%20bytes%20objects.
def shift(text, s):
    result = ""
    # transverse the plain text
    for i in range(len(text)):
        char = text[i]
        # Encrypt uppercase characters in plain text

        if (char.isupper()):
            result += chr((ord(char) + s-65) % 26 + 65)
        # Encrypt lowercase characters in plain text
        else:
            result += chr((ord(char) + s - 97) % 26 + 97)
    return result


def handle_exception(caller, error):
    err_code = log_error("( " + caller + " ) : " + error)
    return "An Error occurred while processing your request. " + \
        "Error code : " + err_code, 500
