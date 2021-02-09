import re

# Converts co-ordinates to latitude and longitude
# Degrees, minutes, seconds <-> Decimal Degrees
# Code from
# https://stackoverflow.com/questions/2579535/convert-dd-decimal-degrees-to-dms-degrees-minutes-seconds-in-python


# Converts Degrees, minutes, seconds to Decimal Degrees
def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if direction == 'W' or direction == 'S':
        dd *= -1
    return dd


# Converts Decimal Degrees to Degrees, minutes, seconds
def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]


# Parses Latitude/Longitude
def parse_dms(dms):
    parts = re.split(r'[^\d\w]+', dms)
    lat = dms2dd(parts[0], parts[1], parts[2], parts[3])
    return lat


# Converts co-ordinates from iOS compass application to latitude and longitude
def coordinates(inp):
    try:
        ar = inp
        ar = ar.replace("″ N", "″N")
        ar = ar.replace("″ W", "″W")
        ar = ar.replace("″ S", "″S")
        ar = ar.replace("″ E", "″E")
        ar = ar.replace("  ", ",")
        ar = ar.replace(" ", ",")
        ar = ar.split(",")
        first = ar[0]
        second = ar[1]
        return (parse_dms(first), parse_dms(second))
    except Exception:
        return None
