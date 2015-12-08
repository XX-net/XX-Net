# -*- coding: utf-8 -*-
"""
    babel.dates
    ~~~~~~~~~~~

    Locale dependent formatting and parsing of dates and times.

    The default locale for the functions in this module is determined by the
    following environment variables, in that order:

     * ``LC_TIME``,
     * ``LC_ALL``, and
     * ``LANG``

    :copyright: (c) 2013 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import division

import re
import warnings
import pytz as _pytz

from datetime import date, datetime, time, timedelta
from bisect import bisect_right

from babel.core import default_locale, get_global, Locale
from babel.util import UTC, LOCALTZ
from babel._compat import string_types, integer_types, number_types


LC_TIME = default_locale('LC_TIME')

# Aliases for use in scopes where the modules are shadowed by local variables
date_ = date
datetime_ = datetime
time_ = time


def get_timezone(zone=None):
    """Looks up a timezone by name and returns it.  The timezone object
    returned comes from ``pytz`` and corresponds to the `tzinfo` interface and
    can be used with all of the functions of Babel that operate with dates.

    If a timezone is not known a :exc:`LookupError` is raised.  If `zone`
    is ``None`` a local zone object is returned.

    :param zone: the name of the timezone to look up.  If a timezone object
                 itself is passed in, mit's returned unchanged.
    """
    if zone is None:
        return LOCALTZ
    if not isinstance(zone, string_types):
        return zone
    try:
        return _pytz.timezone(zone)
    except _pytz.UnknownTimeZoneError:
        raise LookupError('Unknown timezone %s' % zone)


def get_next_timezone_transition(zone=None, dt=None):
    """Given a timezone it will return a :class:`TimezoneTransition` object
    that holds the information about the next timezone transition that's going
    to happen.  For instance this can be used to detect when the next DST
    change is going to happen and how it looks like.

    The transition is calculated relative to the given datetime object.  The
    next transition that follows the date is used.  If a transition cannot
    be found the return value will be `None`.

    Transition information can only be provided for timezones returned by
    the :func:`get_timezone` function.

    :param zone: the timezone for which the transition should be looked up.
                 If not provided the local timezone is used.
    :param dt: the date after which the next transition should be found.
               If not given the current time is assumed.
    """
    zone = get_timezone(zone)
    if dt is None:
        dt = datetime.utcnow()
    else:
        dt = dt.replace(tzinfo=None)

    if not hasattr(zone, '_utc_transition_times'):
        raise TypeError('Given timezone does not have UTC transition '
                        'times.  This can happen because the operating '
                        'system fallback local timezone is used or a '
                        'custom timezone object')

    try:
        idx = max(0, bisect_right(zone._utc_transition_times, dt))
        old_trans = zone._transition_info[idx - 1]
        new_trans = zone._transition_info[idx]
        old_tz = zone._tzinfos[old_trans]
        new_tz = zone._tzinfos[new_trans]
    except (LookupError, ValueError):
        return None

    return TimezoneTransition(
        activates=zone._utc_transition_times[idx],
        from_tzinfo=old_tz,
        to_tzinfo=new_tz,
        reference_date=dt
    )


class TimezoneTransition(object):
    """A helper object that represents the return value from
    :func:`get_next_timezone_transition`.
    """

    def __init__(self, activates, from_tzinfo, to_tzinfo, reference_date=None):
        #: the time of the activation of the timezone transition in UTC.
        self.activates = activates
        #: the timezone from where the transition starts.
        self.from_tzinfo = from_tzinfo
        #: the timezone for after the transition.
        self.to_tzinfo = to_tzinfo
        #: the reference date that was provided.  This is the `dt` parameter
        #: to the :func:`get_next_timezone_transition`.
        self.reference_date = reference_date

    @property
    def from_tz(self):
        """The name of the timezone before the transition."""
        return self.from_tzinfo._tzname

    @property
    def to_tz(self):
        """The name of the timezone after the transition."""
        return self.to_tzinfo._tzname

    @property
    def from_offset(self):
        """The UTC offset in seconds before the transition."""
        return int(self.from_tzinfo._utcoffset.total_seconds())

    @property
    def to_offset(self):
        """The UTC offset in seconds after the transition."""
        return int(self.to_tzinfo._utcoffset.total_seconds())

    def __repr__(self):
        return '<TimezoneTransition %s -> %s (%s)>' % (
            self.from_tz,
            self.to_tz,
            self.activates,
        )


def get_period_names(locale=LC_TIME):
    """Return the names for day periods (AM/PM) used by the locale.

    >>> get_period_names(locale='en_US')['am']
    u'AM'

    :param locale: the `Locale` object, or a locale string
    """
    return Locale.parse(locale).periods


def get_day_names(width='wide', context='format', locale=LC_TIME):
    """Return the day names used by the locale for the specified format.

    >>> get_day_names('wide', locale='en_US')[1]
    u'Tuesday'
    >>> get_day_names('abbreviated', locale='es')[1]
    u'mar.'
    >>> get_day_names('narrow', context='stand-alone', locale='de_DE')[1]
    u'D'

    :param width: the width to use, one of "wide", "abbreviated", or "narrow"
    :param context: the context, either "format" or "stand-alone"
    :param locale: the `Locale` object, or a locale string
    """
    return Locale.parse(locale).days[context][width]


def get_month_names(width='wide', context='format', locale=LC_TIME):
    """Return the month names used by the locale for the specified format.

    >>> get_month_names('wide', locale='en_US')[1]
    u'January'
    >>> get_month_names('abbreviated', locale='es')[1]
    u'ene.'
    >>> get_month_names('narrow', context='stand-alone', locale='de_DE')[1]
    u'J'

    :param width: the width to use, one of "wide", "abbreviated", or "narrow"
    :param context: the context, either "format" or "stand-alone"
    :param locale: the `Locale` object, or a locale string
    """
    return Locale.parse(locale).months[context][width]


def get_quarter_names(width='wide', context='format', locale=LC_TIME):
    """Return the quarter names used by the locale for the specified format.

    >>> get_quarter_names('wide', locale='en_US')[1]
    u'1st quarter'
    >>> get_quarter_names('abbreviated', locale='de_DE')[1]
    u'Q1'

    :param width: the width to use, one of "wide", "abbreviated", or "narrow"
    :param context: the context, either "format" or "stand-alone"
    :param locale: the `Locale` object, or a locale string
    """
    return Locale.parse(locale).quarters[context][width]


def get_era_names(width='wide', locale=LC_TIME):
    """Return the era names used by the locale for the specified format.

    >>> get_era_names('wide', locale='en_US')[1]
    u'Anno Domini'
    >>> get_era_names('abbreviated', locale='de_DE')[1]
    u'n. Chr.'

    :param width: the width to use, either "wide", "abbreviated", or "narrow"
    :param locale: the `Locale` object, or a locale string
    """
    return Locale.parse(locale).eras[width]


def get_date_format(format='medium', locale=LC_TIME):
    """Return the date formatting patterns used by the locale for the specified
    format.

    >>> get_date_format(locale='en_US')
    <DateTimePattern u'MMM d, y'>
    >>> get_date_format('full', locale='de_DE')
    <DateTimePattern u'EEEE, d. MMMM y'>

    :param format: the format to use, one of "full", "long", "medium", or
                   "short"
    :param locale: the `Locale` object, or a locale string
    """
    return Locale.parse(locale).date_formats[format]


def get_datetime_format(format='medium', locale=LC_TIME):
    """Return the datetime formatting patterns used by the locale for the
    specified format.

    >>> get_datetime_format(locale='en_US')
    u'{1}, {0}'

    :param format: the format to use, one of "full", "long", "medium", or
                   "short"
    :param locale: the `Locale` object, or a locale string
    """
    patterns = Locale.parse(locale).datetime_formats
    if format not in patterns:
        format = None
    return patterns[format]


def get_time_format(format='medium', locale=LC_TIME):
    """Return the time formatting patterns used by the locale for the specified
    format.

    >>> get_time_format(locale='en_US')
    <DateTimePattern u'h:mm:ss a'>
    >>> get_time_format('full', locale='de_DE')
    <DateTimePattern u'HH:mm:ss zzzz'>

    :param format: the format to use, one of "full", "long", "medium", or
                   "short"
    :param locale: the `Locale` object, or a locale string
    """
    return Locale.parse(locale).time_formats[format]


def get_timezone_gmt(datetime=None, width='long', locale=LC_TIME):
    """Return the timezone associated with the given `datetime` object formatted
    as string indicating the offset from GMT.

    >>> dt = datetime(2007, 4, 1, 15, 30)
    >>> get_timezone_gmt(dt, locale='en')
    u'GMT+00:00'

    >>> tz = get_timezone('America/Los_Angeles')
    >>> dt = tz.localize(datetime(2007, 4, 1, 15, 30))
    >>> get_timezone_gmt(dt, locale='en')
    u'GMT-07:00'
    >>> get_timezone_gmt(dt, 'short', locale='en')
    u'-0700'

    The long format depends on the locale, for example in France the acronym
    UTC string is used instead of GMT:

    >>> get_timezone_gmt(dt, 'long', locale='fr_FR')
    u'UTC-07:00'

    .. versionadded:: 0.9

    :param datetime: the ``datetime`` object; if `None`, the current date and
                     time in UTC is used
    :param width: either "long" or "short"
    :param locale: the `Locale` object, or a locale string
    """
    if datetime is None:
        datetime = datetime_.utcnow()
    elif isinstance(datetime, integer_types):
        datetime = datetime_.utcfromtimestamp(datetime).time()
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=UTC)
    locale = Locale.parse(locale)

    offset = datetime.tzinfo.utcoffset(datetime)
    seconds = offset.days * 24 * 60 * 60 + offset.seconds
    hours, seconds = divmod(seconds, 3600)
    if width == 'short':
        pattern = u'%+03d%02d'
    else:
        pattern = locale.zone_formats['gmt'] % '%+03d:%02d'
    return pattern % (hours, seconds // 60)


def get_timezone_location(dt_or_tzinfo=None, locale=LC_TIME):
    u"""Return a representation of the given timezone using "location format".

    The result depends on both the local display name of the country and the
    city associated with the time zone:

    >>> tz = get_timezone('America/St_Johns')
    >>> print(get_timezone_location(tz, locale='de_DE'))
    Kanada (St. John’s) Zeit
    >>> tz = get_timezone('America/Mexico_City')
    >>> get_timezone_location(tz, locale='de_DE')
    u'Mexiko (Mexiko-Stadt) Zeit'

    If the timezone is associated with a country that uses only a single
    timezone, just the localized country name is returned:

    >>> tz = get_timezone('Europe/Berlin')
    >>> get_timezone_name(tz, locale='de_DE')
    u'Mitteleurop\\xe4ische Zeit'

    .. versionadded:: 0.9

    :param dt_or_tzinfo: the ``datetime`` or ``tzinfo`` object that determines
                         the timezone; if `None`, the current date and time in
                         UTC is assumed
    :param locale: the `Locale` object, or a locale string
    :return: the localized timezone name using location format
    """
    if dt_or_tzinfo is None:
        dt = datetime.now()
        tzinfo = LOCALTZ
    elif isinstance(dt_or_tzinfo, string_types):
        dt = None
        tzinfo = get_timezone(dt_or_tzinfo)
    elif isinstance(dt_or_tzinfo, integer_types):
        dt = None
        tzinfo = UTC
    elif isinstance(dt_or_tzinfo, (datetime, time)):
        dt = dt_or_tzinfo
        if dt.tzinfo is not None:
            tzinfo = dt.tzinfo
        else:
            tzinfo = UTC
    else:
        dt = None
        tzinfo = dt_or_tzinfo
    locale = Locale.parse(locale)

    if hasattr(tzinfo, 'zone'):
        zone = tzinfo.zone
    else:
        zone = tzinfo.tzname(dt or datetime.utcnow())

    # Get the canonical time-zone code
    zone = get_global('zone_aliases').get(zone, zone)

    info = locale.time_zones.get(zone, {})

    # Otherwise, if there is only one timezone for the country, return the
    # localized country name
    region_format = locale.zone_formats['region']
    territory = get_global('zone_territories').get(zone)
    if territory not in locale.territories:
        territory = 'ZZ' # invalid/unknown
    territory_name = locale.territories[territory]
    if territory and len(get_global('territory_zones').get(territory, [])) == 1:
        return region_format % (territory_name)

    # Otherwise, include the city in the output
    fallback_format = locale.zone_formats['fallback']
    if 'city' in info:
        city_name = info['city']
    else:
        metazone = get_global('meta_zones').get(zone)
        metazone_info = locale.meta_zones.get(metazone, {})
        if 'city' in metazone_info:
            city_name = metazone_info['city']
        elif '/' in zone:
            city_name = zone.split('/', 1)[1].replace('_', ' ')
        else:
            city_name = zone.replace('_', ' ')

    return region_format % (fallback_format % {
        '0': city_name,
        '1': territory_name
    })


def get_timezone_name(dt_or_tzinfo=None, width='long', uncommon=False,
                      locale=LC_TIME, zone_variant=None):
    r"""Return the localized display name for the given timezone. The timezone
    may be specified using a ``datetime`` or `tzinfo` object.

    >>> dt = time(15, 30, tzinfo=get_timezone('America/Los_Angeles'))
    >>> get_timezone_name(dt, locale='en_US')
    u'Pacific Standard Time'
    >>> get_timezone_name(dt, width='short', locale='en_US')
    u'PST'

    If this function gets passed only a `tzinfo` object and no concrete
    `datetime`,  the returned display name is indenpendent of daylight savings
    time. This can be used for example for selecting timezones, or to set the
    time of events that recur across DST changes:

    >>> tz = get_timezone('America/Los_Angeles')
    >>> get_timezone_name(tz, locale='en_US')
    u'Pacific Time'
    >>> get_timezone_name(tz, 'short', locale='en_US')
    u'PT'

    If no localized display name for the timezone is available, and the timezone
    is associated with a country that uses only a single timezone, the name of
    that country is returned, formatted according to the locale:

    >>> tz = get_timezone('Europe/Berlin')
    >>> get_timezone_name(tz, locale='de_DE')
    u'Mitteleurop\xe4ische Zeit'
    >>> get_timezone_name(tz, locale='pt_BR')
    u'Hor\xe1rio da Europa Central'

    On the other hand, if the country uses multiple timezones, the city is also
    included in the representation:

    >>> tz = get_timezone('America/St_Johns')
    >>> get_timezone_name(tz, locale='de_DE')
    u'Neufundland-Zeit'

    Note that short format is currently not supported for all timezones and
    all locales.  This is partially because not every timezone has a short
    code in every locale.  In that case it currently falls back to the long
    format.

    For more information see `LDML Appendix J: Time Zone Display Names
    <http://www.unicode.org/reports/tr35/#Time_Zone_Fallback>`_

    .. versionadded:: 0.9

    .. versionchanged:: 1.0
       Added `zone_variant` support.

    :param dt_or_tzinfo: the ``datetime`` or ``tzinfo`` object that determines
                         the timezone; if a ``tzinfo`` object is used, the
                         resulting display name will be generic, i.e.
                         independent of daylight savings time; if `None`, the
                         current date in UTC is assumed
    :param width: either "long" or "short"
    :param uncommon: deprecated and ignored
    :param zone_variant: defines the zone variation to return.  By default the
                           variation is defined from the datetime object
                           passed in.  If no datetime object is passed in, the
                           ``'generic'`` variation is assumed.  The following
                           values are valid: ``'generic'``, ``'daylight'`` and
                           ``'standard'``.
    :param locale: the `Locale` object, or a locale string
    """
    if dt_or_tzinfo is None:
        dt = datetime.now()
        tzinfo = LOCALTZ
    elif isinstance(dt_or_tzinfo, string_types):
        dt = None
        tzinfo = get_timezone(dt_or_tzinfo)
    elif isinstance(dt_or_tzinfo, integer_types):
        dt = None
        tzinfo = UTC
    elif isinstance(dt_or_tzinfo, (datetime, time)):
        dt = dt_or_tzinfo
        if dt.tzinfo is not None:
            tzinfo = dt.tzinfo
        else:
            tzinfo = UTC
    else:
        dt = None
        tzinfo = dt_or_tzinfo
    locale = Locale.parse(locale)

    if hasattr(tzinfo, 'zone'):
        zone = tzinfo.zone
    else:
        zone = tzinfo.tzname(dt)

    if zone_variant is None:
        if dt is None:
            zone_variant = 'generic'
        else:
            dst = tzinfo.dst(dt)
            if dst:
                zone_variant = 'daylight'
            else:
                zone_variant = 'standard'
    else:
        if zone_variant not in ('generic', 'standard', 'daylight'):
            raise ValueError('Invalid zone variation')

    # Get the canonical time-zone code
    zone = get_global('zone_aliases').get(zone, zone)

    info = locale.time_zones.get(zone, {})
    # Try explicitly translated zone names first
    if width in info:
        if zone_variant in info[width]:
            return info[width][zone_variant]

    metazone = get_global('meta_zones').get(zone)
    if metazone:
        metazone_info = locale.meta_zones.get(metazone, {})
        if width in metazone_info:
            if zone_variant in metazone_info[width]:
                return metazone_info[width][zone_variant]

    # If we have a concrete datetime, we assume that the result can't be
    # independent of daylight savings time, so we return the GMT offset
    if dt is not None:
        return get_timezone_gmt(dt, width=width, locale=locale)

    return get_timezone_location(dt_or_tzinfo, locale=locale)


def format_date(date=None, format='medium', locale=LC_TIME):
    """Return a date formatted according to the given pattern.

    >>> d = date(2007, 04, 01)
    >>> format_date(d, locale='en_US')
    u'Apr 1, 2007'
    >>> format_date(d, format='full', locale='de_DE')
    u'Sonntag, 1. April 2007'

    If you don't want to use the locale default formats, you can specify a
    custom date pattern:

    >>> format_date(d, "EEE, MMM d, ''yy", locale='en')
    u"Sun, Apr 1, '07"

    :param date: the ``date`` or ``datetime`` object; if `None`, the current
                 date is used
    :param format: one of "full", "long", "medium", or "short", or a custom
                   date/time pattern
    :param locale: a `Locale` object or a locale identifier
    """
    if date is None:
        date = date_.today()
    elif isinstance(date, datetime):
        date = date.date()

    locale = Locale.parse(locale)
    if format in ('full', 'long', 'medium', 'short'):
        format = get_date_format(format, locale=locale)
    pattern = parse_pattern(format)
    return pattern.apply(date, locale)


def format_datetime(datetime=None, format='medium', tzinfo=None,
                    locale=LC_TIME):
    r"""Return a date formatted according to the given pattern.

    >>> dt = datetime(2007, 04, 01, 15, 30)
    >>> format_datetime(dt, locale='en_US')
    u'Apr 1, 2007, 3:30:00 PM'

    For any pattern requiring the display of the time-zone, the third-party
    ``pytz`` package is needed to explicitly specify the time-zone:

    >>> format_datetime(dt, 'full', tzinfo=get_timezone('Europe/Paris'),
    ...                 locale='fr_FR')
    u'dimanche 1 avril 2007 17:30:00 heure d\u2019\xe9t\xe9 d\u2019Europe centrale'
    >>> format_datetime(dt, "yyyy.MM.dd G 'at' HH:mm:ss zzz",
    ...                 tzinfo=get_timezone('US/Eastern'), locale='en')
    u'2007.04.01 AD at 11:30:00 EDT'

    :param datetime: the `datetime` object; if `None`, the current date and
                     time is used
    :param format: one of "full", "long", "medium", or "short", or a custom
                   date/time pattern
    :param tzinfo: the timezone to apply to the time for display
    :param locale: a `Locale` object or a locale identifier
    """
    if datetime is None:
        datetime = datetime_.utcnow()
    elif isinstance(datetime, number_types):
        datetime = datetime_.utcfromtimestamp(datetime)
    elif isinstance(datetime, time):
        datetime = datetime_.combine(date.today(), datetime)
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=UTC)
    if tzinfo is not None:
        datetime = datetime.astimezone(get_timezone(tzinfo))
        if hasattr(tzinfo, 'normalize'): # pytz
            datetime = tzinfo.normalize(datetime)

    locale = Locale.parse(locale)
    if format in ('full', 'long', 'medium', 'short'):
        return get_datetime_format(format, locale=locale) \
            .replace("'", "") \
            .replace('{0}', format_time(datetime, format, tzinfo=None,
                                        locale=locale)) \
            .replace('{1}', format_date(datetime, format, locale=locale))
    else:
        return parse_pattern(format).apply(datetime, locale)


def format_time(time=None, format='medium', tzinfo=None, locale=LC_TIME):
    r"""Return a time formatted according to the given pattern.

    >>> t = time(15, 30)
    >>> format_time(t, locale='en_US')
    u'3:30:00 PM'
    >>> format_time(t, format='short', locale='de_DE')
    u'15:30'

    If you don't want to use the locale default formats, you can specify a
    custom time pattern:

    >>> format_time(t, "hh 'o''clock' a", locale='en')
    u"03 o'clock PM"

    For any pattern requiring the display of the time-zone a
    timezone has to be specified explicitly:

    >>> t = datetime(2007, 4, 1, 15, 30)
    >>> tzinfo = get_timezone('Europe/Paris')
    >>> t = tzinfo.localize(t)
    >>> format_time(t, format='full', tzinfo=tzinfo, locale='fr_FR')
    u'15:30:00 heure d\u2019\xe9t\xe9 d\u2019Europe centrale'
    >>> format_time(t, "hh 'o''clock' a, zzzz", tzinfo=get_timezone('US/Eastern'),
    ...             locale='en')
    u"09 o'clock AM, Eastern Daylight Time"

    As that example shows, when this function gets passed a
    ``datetime.datetime`` value, the actual time in the formatted string is
    adjusted to the timezone specified by the `tzinfo` parameter. If the
    ``datetime`` is "naive" (i.e. it has no associated timezone information),
    it is assumed to be in UTC.

    These timezone calculations are **not** performed if the value is of type
    ``datetime.time``, as without date information there's no way to determine
    what a given time would translate to in a different timezone without
    information about whether daylight savings time is in effect or not. This
    means that time values are left as-is, and the value of the `tzinfo`
    parameter is only used to display the timezone name if needed:

    >>> t = time(15, 30)
    >>> format_time(t, format='full', tzinfo=get_timezone('Europe/Paris'),
    ...             locale='fr_FR')
    u'15:30:00 heure normale d\u2019Europe centrale'
    >>> format_time(t, format='full', tzinfo=get_timezone('US/Eastern'),
    ...             locale='en_US')
    u'3:30:00 PM Eastern Standard Time'

    :param time: the ``time`` or ``datetime`` object; if `None`, the current
                 time in UTC is used
    :param format: one of "full", "long", "medium", or "short", or a custom
                   date/time pattern
    :param tzinfo: the time-zone to apply to the time for display
    :param locale: a `Locale` object or a locale identifier
    """
    if time is None:
        time = datetime.utcnow()
    elif isinstance(time, number_types):
        time = datetime.utcfromtimestamp(time)
    if time.tzinfo is None:
        time = time.replace(tzinfo=UTC)
    if isinstance(time, datetime):
        if tzinfo is not None:
            time = time.astimezone(tzinfo)
            if hasattr(tzinfo, 'normalize'): # pytz
                time = tzinfo.normalize(time)
        time = time.timetz()
    elif tzinfo is not None:
        time = time.replace(tzinfo=tzinfo)

    locale = Locale.parse(locale)
    if format in ('full', 'long', 'medium', 'short'):
        format = get_time_format(format, locale=locale)
    return parse_pattern(format).apply(time, locale)


TIMEDELTA_UNITS = (
    ('year',   3600 * 24 * 365),
    ('month',  3600 * 24 * 30),
    ('week',   3600 * 24 * 7),
    ('day',    3600 * 24),
    ('hour',   3600),
    ('minute', 60),
    ('second', 1)
)


def format_timedelta(delta, granularity='second', threshold=.85,
                     add_direction=False, format='long',
                     locale=LC_TIME):
    """Return a time delta according to the rules of the given locale.

    >>> format_timedelta(timedelta(weeks=12), locale='en_US')
    u'3 months'
    >>> format_timedelta(timedelta(seconds=1), locale='es')
    u'1 segundo'

    The granularity parameter can be provided to alter the lowest unit
    presented, which defaults to a second.

    >>> format_timedelta(timedelta(hours=3), granularity='day',
    ...                  locale='en_US')
    u'1 day'

    The threshold parameter can be used to determine at which value the
    presentation switches to the next higher unit. A higher threshold factor
    means the presentation will switch later. For example:

    >>> format_timedelta(timedelta(hours=23), threshold=0.9, locale='en_US')
    u'1 day'
    >>> format_timedelta(timedelta(hours=23), threshold=1.1, locale='en_US')
    u'23 hours'

    In addition directional information can be provided that informs
    the user if the date is in the past or in the future:

    >>> format_timedelta(timedelta(hours=1), add_direction=True, locale='en')
    u'in 1 hour'
    >>> format_timedelta(timedelta(hours=-1), add_direction=True, locale='en')
    u'1 hour ago'

    The format parameter controls how compact or wide the presentation is:

    >>> format_timedelta(timedelta(hours=3), format='short', locale='en')
    u'3 hrs'
    >>> format_timedelta(timedelta(hours=3), format='narrow', locale='en')
    u'3h'

    :param delta: a ``timedelta`` object representing the time difference to
                  format, or the delta in seconds as an `int` value
    :param granularity: determines the smallest unit that should be displayed,
                        the value can be one of "year", "month", "week", "day",
                        "hour", "minute" or "second"
    :param threshold: factor that determines at which point the presentation
                      switches to the next higher unit
    :param add_direction: if this flag is set to `True` the return value will
                          include directional information.  For instance a
                          positive timedelta will include the information about
                          it being in the future, a negative will be information
                          about the value being in the past.
    :param format: the format, can be "narrow", "short" or "long". (
                   "medium" is deprecated, currently converted to "long" to
                   maintain compatibility)
    :param locale: a `Locale` object or a locale identifier
    """
    if format not in ('narrow', 'short', 'medium', 'long'):
        raise TypeError('Format must be one of "narrow", "short" or "long"')
    if format == 'medium':
        warnings.warn('"medium" value for format param of format_timedelta'
                      ' is deprecated. Use "long" instead',
                      category=DeprecationWarning)
        format = 'long'
    if isinstance(delta, timedelta):
        seconds = int((delta.days * 86400) + delta.seconds)
    else:
        seconds = delta
    locale = Locale.parse(locale)

    def _iter_patterns(a_unit):
        if add_direction:
            unit_rel_patterns = locale._data['date_fields'][a_unit]
            if seconds >= 0:
                yield unit_rel_patterns['future']
            else:
                yield unit_rel_patterns['past']
        a_unit = 'duration-' + a_unit
        yield locale._data['unit_patterns'].get(a_unit + ':' + format)
        yield locale._data['unit_patterns'].get(a_unit)

    for unit, secs_per_unit in TIMEDELTA_UNITS:
        value = abs(seconds) / secs_per_unit
        if value >= threshold or unit == granularity:
            if unit == granularity and value > 0:
                value = max(1, value)
            value = int(round(value))
            plural_form = locale.plural_form(value)
            pattern = None
            for patterns in _iter_patterns(unit):
                if patterns is not None:
                    pattern = patterns[plural_form]
                    break
            # This really should not happen
            if pattern is None:
                return u''
            return pattern.replace('{0}', str(value))

    return u''


def parse_date(string, locale=LC_TIME):
    """Parse a date from a string.

    This function uses the date format for the locale as a hint to determine
    the order in which the date fields appear in the string.

    >>> parse_date('4/1/04', locale='en_US')
    datetime.date(2004, 4, 1)
    >>> parse_date('01.04.2004', locale='de_DE')
    datetime.date(2004, 4, 1)

    :param string: the string containing the date
    :param locale: a `Locale` object or a locale identifier
    """
    # TODO: try ISO format first?
    format = get_date_format(locale=locale).pattern.lower()
    year_idx = format.index('y')
    month_idx = format.index('m')
    if month_idx < 0:
        month_idx = format.index('l')
    day_idx = format.index('d')

    indexes = [(year_idx, 'Y'), (month_idx, 'M'), (day_idx, 'D')]
    indexes.sort()
    indexes = dict([(item[1], idx) for idx, item in enumerate(indexes)])

    # FIXME: this currently only supports numbers, but should also support month
    #        names, both in the requested locale, and english

    numbers = re.findall('(\d+)', string)
    year = numbers[indexes['Y']]
    if len(year) == 2:
        year = 2000 + int(year)
    else:
        year = int(year)
    month = int(numbers[indexes['M']])
    day = int(numbers[indexes['D']])
    if month > 12:
        month, day = day, month
    return date(year, month, day)


def parse_time(string, locale=LC_TIME):
    """Parse a time from a string.

    This function uses the time format for the locale as a hint to determine
    the order in which the time fields appear in the string.

    >>> parse_time('15:30:00', locale='en_US')
    datetime.time(15, 30)

    :param string: the string containing the time
    :param locale: a `Locale` object or a locale identifier
    :return: the parsed time
    :rtype: `time`
    """
    # TODO: try ISO format first?
    format = get_time_format(locale=locale).pattern.lower()
    hour_idx = format.index('h')
    if hour_idx < 0:
        hour_idx = format.index('k')
    min_idx = format.index('m')
    sec_idx = format.index('s')

    indexes = [(hour_idx, 'H'), (min_idx, 'M'), (sec_idx, 'S')]
    indexes.sort()
    indexes = dict([(item[1], idx) for idx, item in enumerate(indexes)])

    # FIXME: support 12 hour clock, and 0-based hour specification
    #        and seconds should be optional, maybe minutes too
    #        oh, and time-zones, of course

    numbers = re.findall('(\d+)', string)
    hour = int(numbers[indexes['H']])
    minute = int(numbers[indexes['M']])
    second = int(numbers[indexes['S']])
    return time(hour, minute, second)


class DateTimePattern(object):

    def __init__(self, pattern, format):
        self.pattern = pattern
        self.format = format

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.pattern)

    def __unicode__(self):
        return self.pattern

    def __mod__(self, other):
        if type(other) is not DateTimeFormat:
            return NotImplemented
        return self.format % other

    def apply(self, datetime, locale):
        return self % DateTimeFormat(datetime, locale)


class DateTimeFormat(object):

    def __init__(self, value, locale):
        assert isinstance(value, (date, datetime, time))
        if isinstance(value, (datetime, time)) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        self.value = value
        self.locale = Locale.parse(locale)

    def __getitem__(self, name):
        char = name[0]
        num = len(name)
        if char == 'G':
            return self.format_era(char, num)
        elif char in ('y', 'Y', 'u'):
            return self.format_year(char, num)
        elif char in ('Q', 'q'):
            return self.format_quarter(char, num)
        elif char in ('M', 'L'):
            return self.format_month(char, num)
        elif char in ('w', 'W'):
            return self.format_week(char, num)
        elif char == 'd':
            return self.format(self.value.day, num)
        elif char == 'D':
            return self.format_day_of_year(num)
        elif char == 'F':
            return self.format_day_of_week_in_month()
        elif char in ('E', 'e', 'c'):
            return self.format_weekday(char, num)
        elif char == 'a':
            return self.format_period(char)
        elif char == 'h':
            if self.value.hour % 12 == 0:
                return self.format(12, num)
            else:
                return self.format(self.value.hour % 12, num)
        elif char == 'H':
            return self.format(self.value.hour, num)
        elif char == 'K':
            return self.format(self.value.hour % 12, num)
        elif char == 'k':
            if self.value.hour == 0:
                return self.format(24, num)
            else:
                return self.format(self.value.hour, num)
        elif char == 'm':
            return self.format(self.value.minute, num)
        elif char == 's':
            return self.format(self.value.second, num)
        elif char == 'S':
            return self.format_frac_seconds(num)
        elif char == 'A':
            return self.format_milliseconds_in_day(num)
        elif char in ('z', 'Z', 'v', 'V'):
            return self.format_timezone(char, num)
        else:
            raise KeyError('Unsupported date/time field %r' % char)

    def format_era(self, char, num):
        width = {3: 'abbreviated', 4: 'wide', 5: 'narrow'}[max(3, num)]
        era = int(self.value.year >= 0)
        return get_era_names(width, self.locale)[era]

    def format_year(self, char, num):
        value = self.value.year
        if char.isupper():
            week = self.get_week_number(self.get_day_of_year())
            if week == 0:
                value -= 1
        year = self.format(value, num)
        if num == 2:
            year = year[-2:]
        return year

    def format_quarter(self, char, num):
        quarter = (self.value.month - 1) // 3 + 1
        if num <= 2:
            return ('%%0%dd' % num) % quarter
        width = {3: 'abbreviated', 4: 'wide', 5: 'narrow'}[num]
        context = {'Q': 'format', 'q': 'stand-alone'}[char]
        return get_quarter_names(width, context, self.locale)[quarter]

    def format_month(self, char, num):
        if num <= 2:
            return ('%%0%dd' % num) % self.value.month
        width = {3: 'abbreviated', 4: 'wide', 5: 'narrow'}[num]
        context = {'M': 'format', 'L': 'stand-alone'}[char]
        return get_month_names(width, context, self.locale)[self.value.month]

    def format_week(self, char, num):
        if char.islower(): # week of year
            day_of_year = self.get_day_of_year()
            week = self.get_week_number(day_of_year)
            if week == 0:
                date = self.value - timedelta(days=day_of_year)
                week = self.get_week_number(self.get_day_of_year(date),
                                            date.weekday())
            return self.format(week, num)
        else: # week of month
            week = self.get_week_number(self.value.day)
            if week == 0:
                date = self.value - timedelta(days=self.value.day)
                week = self.get_week_number(date.day, date.weekday())
                pass
            return '%d' % week

    def format_weekday(self, char, num):
        if num < 3:
            if char.islower():
                value = 7 - self.locale.first_week_day + self.value.weekday()
                return self.format(value % 7 + 1, num)
            num = 3
        weekday = self.value.weekday()
        width = {3: 'abbreviated', 4: 'wide', 5: 'narrow'}[num]
        context = {3: 'format', 4: 'format', 5: 'stand-alone'}[num]
        return get_day_names(width, context, self.locale)[weekday]

    def format_day_of_year(self, num):
        return self.format(self.get_day_of_year(), num)

    def format_day_of_week_in_month(self):
        return '%d' % ((self.value.day - 1) // 7 + 1)

    def format_period(self, char):
        period = {0: 'am', 1: 'pm'}[int(self.value.hour >= 12)]
        return get_period_names(locale=self.locale)[period]

    def format_frac_seconds(self, num):
        value = str(self.value.microsecond)
        return self.format(round(float('.%s' % value), num) * 10**num, num)

    def format_milliseconds_in_day(self, num):
        msecs = self.value.microsecond // 1000 + self.value.second * 1000 + \
                self.value.minute * 60000 + self.value.hour * 3600000
        return self.format(msecs, num)

    def format_timezone(self, char, num):
        width = {3: 'short', 4: 'long'}[max(3, num)]
        if char == 'z':
            return get_timezone_name(self.value, width, locale=self.locale)
        elif char == 'Z':
            return get_timezone_gmt(self.value, width, locale=self.locale)
        elif char == 'v':
            return get_timezone_name(self.value.tzinfo, width,
                                     locale=self.locale)
        elif char == 'V':
            if num == 1:
                return get_timezone_name(self.value.tzinfo, width,
                                         uncommon=True, locale=self.locale)
            return get_timezone_location(self.value.tzinfo, locale=self.locale)

    def format(self, value, length):
        return ('%%0%dd' % length) % value

    def get_day_of_year(self, date=None):
        if date is None:
            date = self.value
        return (date - date.replace(month=1, day=1)).days + 1

    def get_week_number(self, day_of_period, day_of_week=None):
        """Return the number of the week of a day within a period. This may be
        the week number in a year or the week number in a month.

        Usually this will return a value equal to or greater than 1, but if the
        first week of the period is so short that it actually counts as the last
        week of the previous period, this function will return 0.

        >>> format = DateTimeFormat(date(2006, 1, 8), Locale.parse('de_DE'))
        >>> format.get_week_number(6)
        1

        >>> format = DateTimeFormat(date(2006, 1, 8), Locale.parse('en_US'))
        >>> format.get_week_number(6)
        2

        :param day_of_period: the number of the day in the period (usually
                              either the day of month or the day of year)
        :param day_of_week: the week day; if ommitted, the week day of the
                            current date is assumed
        """
        if day_of_week is None:
            day_of_week = self.value.weekday()
        first_day = (day_of_week - self.locale.first_week_day -
                     day_of_period + 1) % 7
        if first_day < 0:
            first_day += 7
        week_number = (day_of_period + first_day - 1) // 7
        if 7 - first_day >= self.locale.min_week_days:
            week_number += 1
        return week_number


PATTERN_CHARS = {
    'G': [1, 2, 3, 4, 5],                                           # era
    'y': None, 'Y': None, 'u': None,                                # year
    'Q': [1, 2, 3, 4], 'q': [1, 2, 3, 4],                           # quarter
    'M': [1, 2, 3, 4, 5], 'L': [1, 2, 3, 4, 5],                     # month
    'w': [1, 2], 'W': [1],                                          # week
    'd': [1, 2], 'D': [1, 2, 3], 'F': [1], 'g': None,               # day
    'E': [1, 2, 3, 4, 5], 'e': [1, 2, 3, 4, 5], 'c': [1, 3, 4, 5],  # week day
    'a': [1],                                                       # period
    'h': [1, 2], 'H': [1, 2], 'K': [1, 2], 'k': [1, 2],             # hour
    'm': [1, 2],                                                    # minute
    's': [1, 2], 'S': None, 'A': None,                              # second
    'z': [1, 2, 3, 4], 'Z': [1, 2, 3, 4], 'v': [1, 4], 'V': [1, 4]  # zone
}


def parse_pattern(pattern):
    """Parse date, time, and datetime format patterns.

    >>> parse_pattern("MMMMd").format
    u'%(MMMM)s%(d)s'
    >>> parse_pattern("MMM d, yyyy").format
    u'%(MMM)s %(d)s, %(yyyy)s'

    Pattern can contain literal strings in single quotes:

    >>> parse_pattern("H:mm' Uhr 'z").format
    u'%(H)s:%(mm)s Uhr %(z)s'

    An actual single quote can be used by using two adjacent single quote
    characters:

    >>> parse_pattern("hh' o''clock'").format
    u"%(hh)s o'clock"

    :param pattern: the formatting pattern to parse
    """
    if type(pattern) is DateTimePattern:
        return pattern

    result = []
    quotebuf = None
    charbuf = []
    fieldchar = ['']
    fieldnum = [0]

    def append_chars():
        result.append(''.join(charbuf).replace('%', '%%'))
        del charbuf[:]

    def append_field():
        limit = PATTERN_CHARS[fieldchar[0]]
        if limit and fieldnum[0] not in limit:
            raise ValueError('Invalid length for field: %r'
                             % (fieldchar[0] * fieldnum[0]))
        result.append('%%(%s)s' % (fieldchar[0] * fieldnum[0]))
        fieldchar[0] = ''
        fieldnum[0] = 0

    for idx, char in enumerate(pattern.replace("''", '\0')):
        if quotebuf is None:
            if char == "'": # quote started
                if fieldchar[0]:
                    append_field()
                elif charbuf:
                    append_chars()
                quotebuf = []
            elif char in PATTERN_CHARS:
                if charbuf:
                    append_chars()
                if char == fieldchar[0]:
                    fieldnum[0] += 1
                else:
                    if fieldchar[0]:
                        append_field()
                    fieldchar[0] = char
                    fieldnum[0] = 1
            else:
                if fieldchar[0]:
                    append_field()
                charbuf.append(char)

        elif quotebuf is not None:
            if char == "'": # end of quote
                charbuf.extend(quotebuf)
                quotebuf = None
            else: # inside quote
                quotebuf.append(char)

    if fieldchar[0]:
        append_field()
    elif charbuf:
        append_chars()

    return DateTimePattern(pattern, u''.join(result).replace('\0', "'"))
