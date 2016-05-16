#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#









"""Implementation of scheduling for Groc format schedules.

A Groc schedule looks like '1st,2nd monday 9:00', or 'every 20 mins'. This
module takes a parsed schedule (produced by Antlr) and creates objects that
can produce times that match this schedule.

A parsed schedule is one of two types - an Interval or a Specific Time.
See the class docstrings for more.

Extensions to be considered:

  allowing a comma separated list of times to run
"""



import calendar
import datetime






try:
  import pytz
except ImportError:
  pytz = None

import groc

HOURS = 'hours'
MINUTES = 'minutes'

try:
  from pytz import NonExistentTimeError
  from pytz import AmbiguousTimeError
except ImportError:

  class NonExistentTimeError(Exception):
    pass

  class AmbiguousTimeError(Exception):
    pass


def GrocTimeSpecification(schedule, timezone=None):
  """Factory function.

  Turns a schedule specification into a TimeSpecification.

  Arguments:
    schedule: the schedule specification, as a string
    timezone: the optional timezone as a string for this specification.
        Defaults to 'UTC' - valid entries are things like 'Australia/Victoria'
        or 'PST8PDT'.
  Returns:
    a TimeSpecification instance
  """
  parser = groc.CreateParser(schedule)
  parser.timespec()

  if parser.period_string:
    return IntervalTimeSpecification(parser.interval_mins,
                                     parser.period_string,
                                     parser.synchronized,
                                     parser.start_time_string,
                                     parser.end_time_string,
                                     timezone)
  else:
    return SpecificTimeSpecification(parser.ordinal_set, parser.weekday_set,
                                     parser.month_set,
                                     parser.monthday_set,
                                     parser.time_string,
                                     timezone)


class TimeSpecification(object):
  """Base class for time specifications."""

  def GetMatches(self, start, n):
    """Returns the next n times that match the schedule, starting at time start.

    Arguments:
      start: a datetime to start from. Matches will start from after this time.
      n:     the number of matching times to return

    Returns:
      a list of n datetime objects
    """
    out = []
    for _ in range(n):
      start = self.GetMatch(start)
      out.append(start)
    return out

  def GetMatch(self, start):
    """Returns the next match after time start.

    Must be implemented in subclasses.

    Arguments:
      start: a datetime to start from. Matches will start from after this time.
          This may be in any pytz time zone, or it may be timezone-naive
          (interpreted as UTC).

    Returns:
      a datetime object in the timezone of the input 'start'
    """
    raise NotImplementedError


def _GetTimezone(timezone_string):
  """Converts a timezone string to a pytz timezone object.

  Arguments:
    timezone_string: a string representing a timezone, or None

  Returns:
    a pytz timezone object, or None

  Raises:
    ValueError: if timezone_string is specified, but pytz module could not be
        loaded
  """
  if pytz is None:
    if timezone_string:
      raise ValueError('need pytz in order to specify a timezone')
    return None

  if timezone_string:
    return pytz.timezone(timezone_string)
  else:
    return pytz.utc


def _ToTimeZone(t, tzinfo):
  """Converts 't' to the time zone 'tzinfo'.

  Arguments:
    t: a datetime object.  It may be in any pytz time zone, or it may be
        timezone-naive (interpreted as UTC).
    tzinfo: a pytz timezone object, or None.

  Returns:
    a datetime object in the time zone 'tzinfo'
  """
  if pytz is None:

    return t.replace(tzinfo=None)
  elif tzinfo:

    if not t.tzinfo:
      t = pytz.utc.localize(t)
    return tzinfo.normalize(t.astimezone(tzinfo))
  elif t.tzinfo:

    return pytz.utc.normalize(t.astimezone(pytz.utc)).replace(tzinfo=None)
  else:

    return t


def _GetTime(time_string):
  """Converts a string to a datetime.time object.

  Arguments:
    time_string: a string representing a time ('hours:minutes')

  Returns:
    a datetime.time object
  """
  hourstr, minutestr = time_string.split(':')
  return datetime.time(int(hourstr), int(minutestr))


class IntervalTimeSpecification(TimeSpecification):
  """A time specification for a given interval.

  An Interval type spec runs at the given fixed interval. It has the following
  attributes:
  period - the type of interval, either 'hours' or 'minutes'
  interval - the number of units of type period.
  synchronized - whether to synchronize the times to be locked to a fixed
      period (midnight in the specified timezone).
  start_time, end_time - restrict matches to a given range of times every day.
      If these are None, there is no restriction.  Otherwise, they are
      datetime.time objects.
  timezone - the time zone in which start_time and end_time should be
      interpreted, or None (defaults to UTC).  This is a pytz timezone object.
  """

  def __init__(self, interval, period, synchronized=False,
               start_time_string='', end_time_string='', timezone=None):
    super(IntervalTimeSpecification, self).__init__()
    if interval < 1:
      raise groc.GrocException('interval must be greater than zero')
    self.interval = interval
    self.period = period
    self.synchronized = synchronized
    if self.period == HOURS:
      self.seconds = self.interval * 3600
    else:
      self.seconds = self.interval * 60
    self.timezone = _GetTimezone(timezone)


    if self.synchronized:
      if start_time_string:
        raise ValueError(
            'start_time_string may not be specified if synchronized is true')
      if end_time_string:
        raise ValueError(
            'end_time_string may not be specified if synchronized is true')
      if (self.seconds > 86400) or ((86400 % self.seconds) != 0):
        raise groc.GrocException('can only use synchronized for periods that'
                                 ' divide evenly into 24 hours')


      self.start_time = datetime.time(0, 0)
      self.end_time = datetime.time(23, 59)
    elif start_time_string:
      if not end_time_string:
        raise ValueError(
            'end_time_string must be specified if start_time_string is')
      self.start_time = _GetTime(start_time_string)
      self.end_time = _GetTime(end_time_string)
    else:
      if end_time_string:
        raise ValueError(
            'start_time_string must be specified if end_time_string is')
      self.start_time = None
      self.end_time = None

  def GetMatch(self, start):
    """Returns the next match after 'start'.

    Arguments:
      start: a datetime to start from. Matches will start from after this time.
          This may be in any pytz time zone, or it may be timezone-naive
          (interpreted as UTC).

    Returns:
      a datetime object in the timezone of the input 'start'
    """
    if self.start_time is None:



      result = start + datetime.timedelta(seconds=self.seconds)
      return result - datetime.timedelta(seconds=result.second)


    t = _ToTimeZone(start, self.timezone)


    start_time = self._GetPreviousDateTime(t, self.start_time, self.timezone)



    t_delta = t - start_time
    t_delta_seconds = (t_delta.days * 60 * 24 + t_delta.seconds)
    num_intervals = (t_delta_seconds + self.seconds) / self.seconds
    interval_time = (
        start_time + datetime.timedelta(seconds=(num_intervals * self.seconds)))
    if self.timezone:
      interval_time = self.timezone.normalize(interval_time)



    next_start_time = self._GetNextDateTime(t, self.start_time, self.timezone)
    if (self._TimeIsInRange(t) and
        self._TimeIsInRange(interval_time) and
        interval_time < next_start_time):
      result = interval_time
    else:
      result = next_start_time


    return _ToTimeZone(result, start.tzinfo)

  def _TimeIsInRange(self, t):
    """Returns true if 't' falls between start_time and end_time, inclusive.

    Arguments:
      t: a datetime object, in self.timezone

    Returns:
      a boolean
    """


    previous_start_time = self._GetPreviousDateTime(
        t, self.start_time, self.timezone)
    previous_end_time = self._GetPreviousDateTime(
        t, self.end_time, self.timezone)
    if previous_start_time > previous_end_time:
      return True
    else:
      return t == previous_end_time

  @staticmethod
  def _GetPreviousDateTime(t, target_time, tzinfo):
    """Returns the latest datetime <= 't' that has the time target_time.

    Arguments:
      t: a datetime.datetime object, in any timezone
      target_time: a datetime.time object, in any timezone
      tzinfo: a pytz timezone object, or None

    Returns:
      a datetime.datetime object, in the timezone 'tzinfo'
    """

    date = t.date()
    while True:
      result = IntervalTimeSpecification._CombineDateAndTime(
          date, target_time, tzinfo)
      if result <= t:
        return result
      date -= datetime.timedelta(days=1)

  @staticmethod
  def _GetNextDateTime(t, target_time, tzinfo):
    """Returns the earliest datetime > 't' that has the time target_time.

    Arguments:
      t: a datetime.datetime object, in any timezone
      target_time: a datetime.time object, in any timezone
      tzinfo: a pytz timezone object, or None

    Returns:
      a datetime.datetime object, in the timezone 'tzinfo'
    """

    date = t.date()
    while True:
      result = IntervalTimeSpecification._CombineDateAndTime(
          date, target_time, tzinfo)
      if result > t:
        return result
      date += datetime.timedelta(days=1)

  @staticmethod
  def _CombineDateAndTime(date, time, tzinfo):
    """Creates a datetime object from date and time objects.

    This is similar to the datetime.combine method, but its timezone
    calculations are designed to work with pytz.

    Arguments:
      date: a datetime.date object, in any timezone
      time: a datetime.time object, in any timezone
      tzinfo: a pytz timezone object, or None

    Returns:
      a datetime.datetime object, in the timezone 'tzinfo'
    """
    naive_result = datetime.datetime(
        date.year, date.month, date.day, time.hour, time.minute, time.second)
    if tzinfo is None:
      return naive_result

    try:
      return tzinfo.localize(naive_result, is_dst=None)
    except AmbiguousTimeError:


      return min(tzinfo.localize(naive_result, is_dst=True),
                 tzinfo.localize(naive_result, is_dst=False))
    except NonExistentTimeError:




      while True:
        naive_result += datetime.timedelta(minutes=1)
        try:
          return tzinfo.localize(naive_result, is_dst=None)
        except NonExistentTimeError:
          pass


class SpecificTimeSpecification(TimeSpecification):
  """Specific time specification.

  A Specific interval is more complex, but defines a certain time to run and
  the days that it should run. It has the following attributes:
  time     - the time of day to run, as 'HH:MM'
  ordinals - first, second, third &c, as a set of integers in 1..5
  months   - the months that this should run, as a set of integers in 1..12
  weekdays - the days of the week that this should run, as a set of integers,
             0=Sunday, 6=Saturday
  timezone - the optional timezone as a string for this specification.
             Defaults to UTC - valid entries are things like Australia/Victoria
             or PST8PDT.

  A specific time schedule can be quite complex. A schedule could look like
  this:
  '1st,third sat,sun of jan,feb,mar 09:15'

  In this case, ordinals would be {1,3}, weekdays {0,6}, months {1,2,3} and
  time would be '09:15'.
  """

  def __init__(self, ordinals=None, weekdays=None, months=None, monthdays=None,
               timestr='00:00', timezone=None):
    super(SpecificTimeSpecification, self).__init__()
    if weekdays and monthdays:
      raise ValueError('cannot supply both monthdays and weekdays')
    if ordinals is None:

      self.ordinals = set(range(1, 6))
    else:
      self.ordinals = set(ordinals)
      if self.ordinals and (min(self.ordinals) < 1 or max(self.ordinals) > 5):
        raise ValueError('ordinals must be between 1 and 5 inclusive, '
                         'got %r' % ordinals)

    if weekdays is None:

      self.weekdays = set(range(7))
    else:
      self.weekdays = set(weekdays)
      if self.weekdays and (min(self.weekdays) < 0 or max(self.weekdays) > 6):
        raise ValueError('weekdays must be between '
                         '0 (sun) and 6 (sat) inclusive, '
                         'got %r' % weekdays)

    if months is None:

      self.months = set(range(1, 13))
    else:
      self.months = set(months)
      if self.months and (min(self.months) < 1 or max(self.months) > 12):
        raise ValueError('months must be between '
                         '1 (jan) and 12 (dec) inclusive, '
                         'got %r' % months)

    if not monthdays:
      self.monthdays = set()
    else:
      if min(monthdays) < 1:
        raise ValueError('day of month must be greater than 0')
      if max(monthdays) > 31:
        raise ValueError('day of month must be less than 32')
      if self.months:
        for month in self.months:
          _, ndays = calendar.monthrange(4, month)
          if min(monthdays) <= ndays:
            break
        else:
          raise ValueError('invalid day of month, '
                           'got day %r of month %r' % (max(monthdays), month))
      self.monthdays = set(monthdays)
    self.time = _GetTime(timestr)
    self.timezone = _GetTimezone(timezone)

  def _MatchingDays(self, year, month):
    """Returns matching days for the given year and month.

    For the given year and month, return the days that match this instance's
    day specification, based on either (a) the ordinals and weekdays, or
    (b) the explicitly specified monthdays.  If monthdays are specified,
    dates that fall outside the range of the month will not be returned.

    Arguments:
      year: the year as an integer
      month: the month as an integer, in range 1-12

    Returns:
      a list of matching days, as ints in range 1-31
    """
    start_day, last_day = calendar.monthrange(year, month)
    if self.monthdays:
      return sorted([day for day in self.monthdays if day <= last_day])


    out_days = []
    start_day = (start_day + 1) % 7
    for ordinal in self.ordinals:
      for weekday in self.weekdays:
        day = ((weekday - start_day) % 7) + 1
        day += 7 * (ordinal - 1)
        if day <= last_day:
          out_days.append(day)
    return sorted(out_days)

  def _NextMonthGenerator(self, start, matches):
    """Creates a generator that produces results from the set 'matches'.

    Matches must be >= 'start'. If none match, the wrap counter is incremented,
    and the result set is reset to the full set. Yields a 2-tuple of (match,
    wrapcount).

    Arguments:
      start: first set of matches will be >= this value (an int)
      matches: the set of potential matches (a sequence of ints)

    Yields:
      a two-tuple of (match, wrap counter). match is an int in range (1-12),
      wrapcount is a int indicating how many times we've wrapped around.
    """
    potential = matches = sorted(matches)

    after = start - 1
    wrapcount = 0
    while True:
      potential = [x for x in potential if x > after]
      if not potential:


        wrapcount += 1
        potential = matches
      after = potential[0]
      yield (after, wrapcount)

  def GetMatch(self, start):
    """Returns the next match after time start.

    Must be implemented in subclasses.

    Arguments:
      start: a datetime to start from. Matches will start from after this time.
          This may be in any pytz time zone, or it may be timezone-naive
          (interpreted as UTC).

    Returns:
      a datetime object in the timezone of the input 'start'
    """





    start_time = _ToTimeZone(start, self.timezone).replace(tzinfo=None)
    if self.months:

      months = self._NextMonthGenerator(start_time.month, self.months)
    while True:

      month, yearwraps = months.next()
      candidate_month = start_time.replace(day=1, month=month,
                                           year=start_time.year + yearwraps)


      day_matches = self._MatchingDays(candidate_month.year, month)

      if ((candidate_month.year, candidate_month.month)
          == (start_time.year, start_time.month)):

        day_matches = [x for x in day_matches if x >= start_time.day]
      while day_matches:

        out = candidate_month.replace(day=day_matches[0], hour=self.time.hour,
                                      minute=self.time.minute, second=0,
                                      microsecond=0)

        if self.timezone and pytz is not None:




          try:
            out = self.timezone.localize(out, is_dst=None)
          except AmbiguousTimeError:




            start_utc = _ToTimeZone(start, pytz.utc)
            dst_doubled_time_first_match_utc = _ToTimeZone(
                self.timezone.localize(out, is_dst=True), pytz.utc)
            if start_utc < dst_doubled_time_first_match_utc:
              out = self.timezone.localize(out, is_dst=True)
            else:
              out = self.timezone.localize(out, is_dst=False)
          except NonExistentTimeError:
            day_matches.pop(0)
            continue


        if start < _ToTimeZone(out, start.tzinfo):
          return _ToTimeZone(out, start.tzinfo)
        else:
          day_matches.pop(0)
