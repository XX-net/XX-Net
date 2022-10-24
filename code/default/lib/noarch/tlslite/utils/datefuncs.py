# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

import os

#Functions for manipulating datetime objects
#CCYY-MM-DDThh:mm:ssZ
def parseDateClass(s):
    year, month, day = s.split("-")
    day, tail = day[:2], day[2:]
    hour, minute, second = tail[1:].split(":")
    second = second[:2]
    year, month, day = int(year), int(month), int(day)
    hour, minute, second = int(hour), int(minute), int(second)
    return createDateClass(year, month, day, hour, minute, second)


if os.name != "java":
    from datetime import datetime, timedelta

    #Helper functions for working with a date/time class
    def createDateClass(year, month, day, hour, minute, second):
        return datetime(year, month, day, hour, minute, second)

    def printDateClass(d):
        #Split off fractional seconds, append 'Z'
        return d.isoformat().split(".")[0]+"Z"

    def getNow():
        return datetime.utcnow()

    def getHoursFromNow(hours):
        return datetime.utcnow() + timedelta(hours=hours)

    def getMinutesFromNow(minutes):
        return datetime.utcnow() + timedelta(minutes=minutes)

    def isDateClassExpired(d):
        return d < datetime.utcnow()

    def isDateClassBefore(d1, d2):
        return d1 < d2

else:
    #Jython 2.1 is missing lots of python 2.3 stuff,
    #which we have to emulate here:
    import java
    import jarray

    def createDateClass(year, month, day, hour, minute, second):
        c = java.util.Calendar.getInstance()
        c.setTimeZone(java.util.TimeZone.getTimeZone("UTC"))
        c.set(year, month-1, day, hour, minute, second)
        return c

    def printDateClass(d):
        return "%04d-%02d-%02dT%02d:%02d:%02dZ" % \
        (d.get(d.YEAR), d.get(d.MONTH)+1, d.get(d.DATE), \
        d.get(d.HOUR_OF_DAY), d.get(d.MINUTE), d.get(d.SECOND))

    def getNow():
        c = java.util.Calendar.getInstance()
        c.setTimeZone(java.util.TimeZone.getTimeZone("UTC"))
        c.get(c.HOUR) #force refresh?
        return c

    def getHoursFromNow(hours):
        d = getNow()
        d.add(d.HOUR, hours)
        return d

    def isDateClassExpired(d):
        n = getNow()
        return d.before(n)

    def isDateClassBefore(d1, d2):
        return d1.before(d2)
