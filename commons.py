import os
import sys
import time
from datetime import datetime
from urllib.request import urlopen

from dateutil import tz

my_directory = os.path.dirname(os.path.abspath(__file__))


def write(path, content):
    """ Writes current branch and sha to a file
    that is displayed by the /git endpoint """
    file = f'{my_directory}/{path}'
    with open(file, 'w') as filetowrite:
        filetowrite.write(content)


def read(path):
    """ Reads the contents of the file for
    the deployed git branch status """
    file = f'{my_directory}/{path}'
    # tests/gitstats.txt
    with open(file, 'r') as filetoread:
        return filetoread.read()


def current_time():
    """ Returns Current System Time """
    return datetime.now()


def current_time_from_api():
    """ Get's current time from API.
    This is required because not sure where deployment servers are located
    Cannot rely on system's date & time values """
    res = urlopen('http://just-the-time.appspot.com/')
    result = res.read().strip()
    result_str = result.decode('utf-8')
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')
    utc = datetime.strptime(result_str, '%Y-%m-%d %H:%M:%S')
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return central


def seconds_between(left, right):
    """ Calculates seconds between two datetime values """
    return (left - right).total_seconds()


def handle_exception(caller, error_message):
    """ Handles Exceptions by logging them and returning error code """
    try:
        err_code = log_error(f'({caller}) : {error_message})')
        return f'An unexpected error occurred while processing your request. Error code : {err_code}', 500
    except Exception:
        return 'An unexpected error occurred while processing your request.'


def log_error(message):
    """ Logs Error Message in PythonAnywhere """
    time = (datetime.now())
    error_code = shift(str(time.timestamp()), 5)
    print(f'{error_code} : ' + str(message), file=sys.stderr)
    return str(error_code)


def log_request(message, request_time):
    """ Logs request message with request time by printing to log """
    print(f'{message} request took {request_time}')


# https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password#:~:text=To%20encrypt%20or%20decrypt%20messages,encrypted%20token%20are%20bytes%20objects.
def shift(text, s):
    """ Caesar-Cipher Encryption
    Shifts Characters by given key """
    result = ""
    # transverse the plain text
    for i in range(len(text)):
        char = text[i]
        # Shift uppercase characters in plain text
        if char.isupper():
            result += chr((ord(char) + s - 65) % 26 + 65)
        # Shift lowercase characters in plain text
        else:
            result += chr((ord(char) + s - 97) % 26 + 97)
    return result


class Timer:
    """ Timer Class
    Used for calculating the run time of a program
    """

    def __init__(self):
        """ Assigns the current time value to start attribute """
        self.start = time.time()

    def end(self):
        """ Deducts current time value from the start attribute """
        current_time = time.time()
        difference = current_time - self.start
        return difference
