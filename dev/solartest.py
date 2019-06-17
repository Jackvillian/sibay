from datetime import date
from pytz import timezone
from solartime import SolarTime
today = date(2014, 4, 20)
localtz = timezone('Europe/Moscow')
lat, lon = 38.0, -79.0
sun = SolarTime()
schedule = sun.sun_utc(today, lat, lon)
sunset = schedule['sunset'].astimezone(localtz)
print (sunset)