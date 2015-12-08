# -*- coding: ascii -*-

import sys, os, os.path
import unittest, doctest
try:
    import cPickle as pickle
except ImportError:
    import pickle
from datetime import datetime, time, timedelta, tzinfo
import warnings

if __name__ == '__main__':
    # Only munge path if invoked as a script. Testrunners should have setup
    # the paths already
    sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, os.pardir)))

import pytz
from pytz import reference
from pytz.tzfile import _byte_string
from pytz.tzinfo import DstTzInfo, StaticTzInfo

# I test for expected version to ensure the correct version of pytz is
# actually being tested.
EXPECTED_VERSION='2015.7'
EXPECTED_OLSON_VERSION='2015g'

fmt = '%Y-%m-%d %H:%M:%S %Z%z'

NOTIME = timedelta(0)

# GMT is a tzinfo.StaticTzInfo--the class we primarily want to test--while
# UTC is reference implementation.  They both have the same timezone meaning.
UTC = pytz.timezone('UTC')
GMT = pytz.timezone('GMT')
assert isinstance(GMT, StaticTzInfo), 'GMT is no longer a StaticTzInfo'

def prettydt(dt):
    """datetime as a string using a known format.

    We don't use strftime as it doesn't handle years earlier than 1900
    per http://bugs.python.org/issue1777412
    """
    if dt.utcoffset() >= timedelta(0):
        offset = '+%s' % (dt.utcoffset(),)
    else:
        offset = '-%s' % (-1 * dt.utcoffset(),)
    return '%04d-%02d-%02d %02d:%02d:%02d %s %s' % (
        dt.year, dt.month, dt.day,
        dt.hour, dt.minute, dt.second,
        dt.tzname(), offset)


try:
    unicode
except NameError:
    # Python 3.x doesn't have unicode(), making writing code
    # for Python 2.3 and Python 3.x a pain.
    unicode = str


class BasicTest(unittest.TestCase):

    def testVersion(self):
        # Ensuring the correct version of pytz has been loaded
        self.assertEqual(EXPECTED_VERSION, pytz.__version__,
                'Incorrect pytz version loaded. Import path is stuffed '
                'or this test needs updating. (Wanted %s, got %s)'
                % (EXPECTED_VERSION, pytz.__version__))

        self.assertEqual(EXPECTED_OLSON_VERSION, pytz.OLSON_VERSION,
                'Incorrect pytz version loaded. Import path is stuffed '
                'or this test needs updating. (Wanted %s, got %s)'
                % (EXPECTED_OLSON_VERSION, pytz.OLSON_VERSION))

    def testGMT(self):
        now = datetime.now(tz=GMT)
        self.assertTrue(now.utcoffset() == NOTIME)
        self.assertTrue(now.dst() == NOTIME)
        self.assertTrue(now.timetuple() == now.utctimetuple())
        self.assertTrue(now==now.replace(tzinfo=UTC))

    def testReferenceUTC(self):
        now = datetime.now(tz=UTC)
        self.assertTrue(now.utcoffset() == NOTIME)
        self.assertTrue(now.dst() == NOTIME)
        self.assertTrue(now.timetuple() == now.utctimetuple())

    def testUnknownOffsets(self):
        # This tzinfo behavior is required to make
        # datetime.time.{utcoffset, dst, tzname} work as documented.

        dst_tz = pytz.timezone('US/Eastern')

        # This information is not known when we don't have a date,
        # so return None per API.
        self.assertTrue(dst_tz.utcoffset(None) is None)
        self.assertTrue(dst_tz.dst(None) is None)
        # We don't know the abbreviation, but this is still a valid
        # tzname per the Python documentation.
        self.assertEqual(dst_tz.tzname(None), 'US/Eastern')

    def clearCache(self):
        pytz._tzinfo_cache.clear()

    def testUnicodeTimezone(self):
        # We need to ensure that cold lookups work for both Unicode
        # and traditional strings, and that the desired singleton is
        # returned.
        self.clearCache()
        eastern = pytz.timezone(unicode('US/Eastern'))
        self.assertTrue(eastern is pytz.timezone('US/Eastern'))

        self.clearCache()
        eastern = pytz.timezone('US/Eastern')
        self.assertTrue(eastern is pytz.timezone(unicode('US/Eastern')))


class PicklingTest(unittest.TestCase):

    def _roundtrip_tzinfo(self, tz):
        p = pickle.dumps(tz)
        unpickled_tz = pickle.loads(p)
        self.assertTrue(tz is unpickled_tz, '%s did not roundtrip' % tz.zone)

    def _roundtrip_datetime(self, dt):
        # Ensure that the tzinfo attached to a datetime instance
        # is identical to the one returned. This is important for
        # DST timezones, as some state is stored in the tzinfo.
        tz = dt.tzinfo
        p = pickle.dumps(dt)
        unpickled_dt = pickle.loads(p)
        unpickled_tz = unpickled_dt.tzinfo
        self.assertTrue(tz is unpickled_tz, '%s did not roundtrip' % tz.zone)

    def testDst(self):
        tz = pytz.timezone('Europe/Amsterdam')
        dt = datetime(2004, 2, 1, 0, 0, 0)

        for localized_tz in tz._tzinfos.values():
            self._roundtrip_tzinfo(localized_tz)
            self._roundtrip_datetime(dt.replace(tzinfo=localized_tz))

    def testRoundtrip(self):
        dt = datetime(2004, 2, 1, 0, 0, 0)
        for zone in pytz.all_timezones:
            tz = pytz.timezone(zone)
            self._roundtrip_tzinfo(tz)

    def testDatabaseFixes(self):
        # Hack the pickle to make it refer to a timezone abbreviation
        # that does not match anything. The unpickler should be able
        # to repair this case
        tz = pytz.timezone('Australia/Melbourne')
        p = pickle.dumps(tz)
        tzname = tz._tzname
        hacked_p = p.replace(_byte_string(tzname),
                             _byte_string('?'*len(tzname)))
        self.assertNotEqual(p, hacked_p)
        unpickled_tz = pickle.loads(hacked_p)
        self.assertTrue(tz is unpickled_tz)

        # Simulate a database correction. In this case, the incorrect
        # data will continue to be used.
        p = pickle.dumps(tz)
        new_utcoffset = tz._utcoffset.seconds + 42

        # Python 3 introduced a new pickle protocol where numbers are stored in
        # hexadecimal representation. Here we extract the pickle
        # representation of the number for the current Python version.
        old_pickle_pattern = pickle.dumps(tz._utcoffset.seconds)[3:-1]
        new_pickle_pattern = pickle.dumps(new_utcoffset)[3:-1]
        hacked_p = p.replace(old_pickle_pattern, new_pickle_pattern)

        self.assertNotEqual(p, hacked_p)
        unpickled_tz = pickle.loads(hacked_p)
        self.assertEqual(unpickled_tz._utcoffset.seconds, new_utcoffset)
        self.assertTrue(tz is not unpickled_tz)

    def testOldPickles(self):
        # Ensure that applications serializing pytz instances as pickles
        # have no troubles upgrading to a new pytz release. These pickles
        # where created with pytz2006j
        east1 = pickle.loads(_byte_string(
            "cpytz\n_p\np1\n(S'US/Eastern'\np2\nI-18000\n"
            "I0\nS'EST'\np3\ntRp4\n."
            ))
        east2 = pytz.timezone('US/Eastern').localize(
            datetime(2006, 1, 1)).tzinfo
        self.assertTrue(east1 is east2)

        # Confirm changes in name munging between 2006j and 2007c cause
        # no problems.
        pap1 = pickle.loads(_byte_string(
            "cpytz\n_p\np1\n(S'America/Port_minus_au_minus_Prince'"
            "\np2\nI-17340\nI0\nS'PPMT'\np3\ntRp4\n."))
        pap2 = pytz.timezone('America/Port-au-Prince').localize(
            datetime(1910, 1, 1)).tzinfo
        self.assertTrue(pap1 is pap2)

        gmt1 = pickle.loads(_byte_string(
            "cpytz\n_p\np1\n(S'Etc/GMT_plus_10'\np2\ntRp3\n."))
        gmt2 = pytz.timezone('Etc/GMT+10')
        self.assertTrue(gmt1 is gmt2)


class USEasternDSTStartTestCase(unittest.TestCase):
    tzinfo = pytz.timezone('US/Eastern')

    # 24 hours before DST changeover
    transition_time = datetime(2002, 4, 7, 7, 0, 0, tzinfo=UTC)

    # Increase for 'flexible' DST transitions due to 1 minute granularity
    # of Python's datetime library
    instant = timedelta(seconds=1)

    # before transition
    before = {
        'tzname': 'EST',
        'utcoffset': timedelta(hours = -5),
        'dst': timedelta(hours = 0),
        }

    # after transition
    after = {
        'tzname': 'EDT',
        'utcoffset': timedelta(hours = -4),
        'dst': timedelta(hours = 1),
        }

    def _test_tzname(self, utc_dt, wanted):
        tzname = wanted['tzname']
        dt = utc_dt.astimezone(self.tzinfo)
        self.assertEqual(dt.tzname(), tzname,
            'Expected %s as tzname for %s. Got %s' % (
                tzname, str(utc_dt), dt.tzname()
                )
            )

    def _test_utcoffset(self, utc_dt, wanted):
        utcoffset = wanted['utcoffset']
        dt = utc_dt.astimezone(self.tzinfo)
        self.assertEqual(
                dt.utcoffset(), wanted['utcoffset'],
                'Expected %s as utcoffset for %s. Got %s' % (
                    utcoffset, utc_dt, dt.utcoffset()
                    )
                )

    def _test_dst(self, utc_dt, wanted):
        dst = wanted['dst']
        dt = utc_dt.astimezone(self.tzinfo)
        self.assertEqual(dt.dst(),dst,
            'Expected %s as dst for %s. Got %s' % (
                dst, utc_dt, dt.dst()
                )
            )

    def test_arithmetic(self):
        utc_dt = self.transition_time

        for days in range(-420, 720, 20):
            delta = timedelta(days=days)

            # Make sure we can get back where we started
            dt = utc_dt.astimezone(self.tzinfo)
            dt2 = dt + delta
            dt2 = dt2 - delta
            self.assertEqual(dt, dt2)

            # Make sure arithmetic crossing DST boundaries ends
            # up in the correct timezone after normalization
            utc_plus_delta = (utc_dt + delta).astimezone(self.tzinfo)
            local_plus_delta = self.tzinfo.normalize(dt + delta)
            self.assertEqual(
                    prettydt(utc_plus_delta),
                    prettydt(local_plus_delta),
                    'Incorrect result for delta==%d days.  Wanted %r. Got %r'%(
                        days,
                        prettydt(utc_plus_delta),
                        prettydt(local_plus_delta),
                        )
                    )

    def _test_all(self, utc_dt, wanted):
        self._test_utcoffset(utc_dt, wanted)
        self._test_tzname(utc_dt, wanted)
        self._test_dst(utc_dt, wanted)

    def testDayBefore(self):
        self._test_all(
                self.transition_time - timedelta(days=1), self.before
                )

    def testTwoHoursBefore(self):
        self._test_all(
                self.transition_time - timedelta(hours=2), self.before
                )

    def testHourBefore(self):
        self._test_all(
                self.transition_time - timedelta(hours=1), self.before
                )

    def testInstantBefore(self):
        self._test_all(
                self.transition_time - self.instant, self.before
                )

    def testTransition(self):
        self._test_all(
                self.transition_time, self.after
                )

    def testInstantAfter(self):
        self._test_all(
                self.transition_time + self.instant, self.after
                )

    def testHourAfter(self):
        self._test_all(
                self.transition_time + timedelta(hours=1), self.after
                )

    def testTwoHoursAfter(self):
        self._test_all(
                self.transition_time + timedelta(hours=1), self.after
                )

    def testDayAfter(self):
        self._test_all(
                self.transition_time + timedelta(days=1), self.after
                )


class USEasternDSTEndTestCase(USEasternDSTStartTestCase):
    tzinfo = pytz.timezone('US/Eastern')
    transition_time = datetime(2002, 10, 27, 6, 0, 0, tzinfo=UTC)
    before = {
        'tzname': 'EDT',
        'utcoffset': timedelta(hours = -4),
        'dst': timedelta(hours = 1),
        }
    after = {
        'tzname': 'EST',
        'utcoffset': timedelta(hours = -5),
        'dst': timedelta(hours = 0),
        }


class USEasternEPTStartTestCase(USEasternDSTStartTestCase):
    transition_time = datetime(1945, 8, 14, 23, 0, 0, tzinfo=UTC)
    before = {
        'tzname': 'EWT',
        'utcoffset': timedelta(hours = -4),
        'dst': timedelta(hours = 1),
        }
    after = {
        'tzname': 'EPT',
        'utcoffset': timedelta(hours = -4),
        'dst': timedelta(hours = 1),
        }


class USEasternEPTEndTestCase(USEasternDSTStartTestCase):
    transition_time = datetime(1945, 9, 30, 6, 0, 0, tzinfo=UTC)
    before = {
        'tzname': 'EPT',
        'utcoffset': timedelta(hours = -4),
        'dst': timedelta(hours = 1),
        }
    after = {
        'tzname': 'EST',
        'utcoffset': timedelta(hours = -5),
        'dst': timedelta(hours = 0),
        }


class WarsawWMTEndTestCase(USEasternDSTStartTestCase):
    # In 1915, Warsaw changed from Warsaw to Central European time.
    # This involved the clocks being set backwards, causing a end-of-DST
    # like situation without DST being involved.
    tzinfo = pytz.timezone('Europe/Warsaw')
    transition_time = datetime(1915, 8, 4, 22, 36, 0, tzinfo=UTC)
    before = {
        'tzname': 'WMT',
        'utcoffset': timedelta(hours=1, minutes=24),
        'dst': timedelta(0),
        }
    after = {
        'tzname': 'CET',
        'utcoffset': timedelta(hours=1),
        'dst': timedelta(0),
        }


class VilniusWMTEndTestCase(USEasternDSTStartTestCase):
    # At the end of 1916, Vilnius changed timezones putting its clock
    # forward by 11 minutes 35 seconds. Neither timezone was in DST mode.
    tzinfo = pytz.timezone('Europe/Vilnius')
    instant = timedelta(seconds=31)
    transition_time = datetime(1916, 12, 31, 22, 36, 00, tzinfo=UTC)
    before = {
        'tzname': 'WMT',
        'utcoffset': timedelta(hours=1, minutes=24),
        'dst': timedelta(0),
        }
    after = {
        'tzname': 'KMT',
        'utcoffset': timedelta(hours=1, minutes=36), # Really 1:35:36
        'dst': timedelta(0),
        }


class VilniusCESTStartTestCase(USEasternDSTStartTestCase):
    # In 1941, Vilnius changed from MSG to CEST, switching to summer
    # time while simultaneously reducing its UTC offset by two hours,
    # causing the clocks to go backwards for this summer time
    # switchover.
    tzinfo = pytz.timezone('Europe/Vilnius')
    transition_time = datetime(1941, 6, 23, 21, 00, 00, tzinfo=UTC)
    before = {
        'tzname': 'MSK',
        'utcoffset': timedelta(hours=3),
        'dst': timedelta(0),
        }
    after = {
        'tzname': 'CEST',
        'utcoffset': timedelta(hours=2),
        'dst': timedelta(hours=1),
        }


class LondonHistoryStartTestCase(USEasternDSTStartTestCase):
    # The first known timezone transition in London was in 1847 when
    # clocks where synchronized to GMT. However, we currently only
    # understand v1 format tzfile(5) files which does handle years
    # this far in the past, so our earliest known transition is in
    # 1916.
    tzinfo = pytz.timezone('Europe/London')
    # transition_time = datetime(1847, 12, 1, 1, 15, 00, tzinfo=UTC)
    # before = {
    #     'tzname': 'LMT',
    #     'utcoffset': timedelta(minutes=-75),
    #     'dst': timedelta(0),
    #     }
    # after = {
    #     'tzname': 'GMT',
    #     'utcoffset': timedelta(0),
    #     'dst': timedelta(0),
    #     }
    transition_time = datetime(1916, 5, 21, 2, 00, 00, tzinfo=UTC)
    before = {
        'tzname': 'GMT',
        'utcoffset': timedelta(0),
        'dst': timedelta(0),
        }
    after = {
        'tzname': 'BST',
        'utcoffset': timedelta(hours=1),
        'dst': timedelta(hours=1),
        }


class LondonHistoryEndTestCase(USEasternDSTStartTestCase):
    # Timezone switchovers are projected into the future, even
    # though no official statements exist or could be believed even
    # if they did exist. We currently only check the last known
    # transition in 2037, as we are still using v1 format tzfile(5)
    # files.
    tzinfo = pytz.timezone('Europe/London')
    # transition_time = datetime(2499, 10, 25, 1, 0, 0, tzinfo=UTC)
    transition_time = datetime(2037, 10, 25, 1, 0, 0, tzinfo=UTC)
    before = {
        'tzname': 'BST',
        'utcoffset': timedelta(hours=1),
        'dst': timedelta(hours=1),
        }
    after = {
        'tzname': 'GMT',
        'utcoffset': timedelta(0),
        'dst': timedelta(0),
        }


class NoumeaHistoryStartTestCase(USEasternDSTStartTestCase):
    # Noumea adopted a whole hour offset in 1912. Previously
    # it was 11 hours, 5 minutes and 48 seconds off UTC. However,
    # due to limitations of the Python datetime library, we need
    # to round that to 11 hours 6 minutes.
    tzinfo = pytz.timezone('Pacific/Noumea')
    transition_time = datetime(1912, 1, 12, 12, 54, 12, tzinfo=UTC)
    before = {
        'tzname': 'LMT',
        'utcoffset': timedelta(hours=11, minutes=6),
        'dst': timedelta(0),
        }
    after = {
        'tzname': 'NCT',
        'utcoffset': timedelta(hours=11),
        'dst': timedelta(0),
        }


class NoumeaDSTEndTestCase(USEasternDSTStartTestCase):
    # Noumea dropped DST in 1997.
    tzinfo = pytz.timezone('Pacific/Noumea')
    transition_time = datetime(1997, 3, 1, 15, 00, 00, tzinfo=UTC)
    before = {
        'tzname': 'NCST',
        'utcoffset': timedelta(hours=12),
        'dst': timedelta(hours=1),
        }
    after = {
        'tzname': 'NCT',
        'utcoffset': timedelta(hours=11),
        'dst': timedelta(0),
        }


class NoumeaNoMoreDSTTestCase(NoumeaDSTEndTestCase):
    # Noumea dropped DST in 1997. Here we test that it stops occuring.
    transition_time = (
        NoumeaDSTEndTestCase.transition_time + timedelta(days=365*10))
    before = NoumeaDSTEndTestCase.after
    after = NoumeaDSTEndTestCase.after


class TahitiTestCase(USEasternDSTStartTestCase):
    # Tahiti has had a single transition in its history.
    tzinfo = pytz.timezone('Pacific/Tahiti')
    transition_time = datetime(1912, 10, 1, 9, 58, 16, tzinfo=UTC)
    before = {
        'tzname': 'LMT',
        'utcoffset': timedelta(hours=-9, minutes=-58),
        'dst': timedelta(0),
        }
    after = {
        'tzname': 'TAHT',
        'utcoffset': timedelta(hours=-10),
        'dst': timedelta(0),
        }


class SamoaInternationalDateLineChange(USEasternDSTStartTestCase):
    # At the end of 2011, Samoa will switch from being east of the
    # international dateline to the west. There will be no Dec 30th
    # 2011 and it will switch from UTC-10 to UTC+14.
    tzinfo = pytz.timezone('Pacific/Apia')
    transition_time = datetime(2011, 12, 30, 10, 0, 0, tzinfo=UTC)
    before = {
        'tzname': 'SDT',
        'utcoffset': timedelta(hours=-10),
        'dst': timedelta(hours=1),
        }
    after = {
        'tzname': 'WSDT',
        'utcoffset': timedelta(hours=14),
        'dst': timedelta(hours=1),
        }


class ReferenceUSEasternDSTStartTestCase(USEasternDSTStartTestCase):
    tzinfo = reference.Eastern
    def test_arithmetic(self):
        # Reference implementation cannot handle this
        pass


class ReferenceUSEasternDSTEndTestCase(USEasternDSTEndTestCase):
    tzinfo = reference.Eastern

    def testHourBefore(self):
        # Python's datetime library has a bug, where the hour before
        # a daylight saving transition is one hour out. For example,
        # at the end of US/Eastern daylight saving time, 01:00 EST
        # occurs twice (once at 05:00 UTC and once at 06:00 UTC),
        # whereas the first should actually be 01:00 EDT.
        # Note that this bug is by design - by accepting this ambiguity
        # for one hour one hour per year, an is_dst flag on datetime.time
        # became unnecessary.
        self._test_all(
                self.transition_time - timedelta(hours=1), self.after
                )

    def testInstantBefore(self):
        self._test_all(
                self.transition_time - timedelta(seconds=1), self.after
                )

    def test_arithmetic(self):
        # Reference implementation cannot handle this
        pass


class LocalTestCase(unittest.TestCase):
    def testLocalize(self):
        loc_tz = pytz.timezone('Europe/Amsterdam')

        loc_time = loc_tz.localize(datetime(1930, 5, 10, 0, 0, 0))
        # Actually +00:19:32, but Python datetime rounds this
        self.assertEqual(loc_time.strftime('%Z%z'), 'AMT+0020')

        loc_time = loc_tz.localize(datetime(1930, 5, 20, 0, 0, 0))
        # Actually +00:19:32, but Python datetime rounds this
        self.assertEqual(loc_time.strftime('%Z%z'), 'NST+0120')

        loc_time = loc_tz.localize(datetime(1940, 5, 10, 0, 0, 0))
        self.assertEqual(loc_time.strftime('%Z%z'), 'NET+0020')

        loc_time = loc_tz.localize(datetime(1940, 5, 20, 0, 0, 0))
        self.assertEqual(loc_time.strftime('%Z%z'), 'CEST+0200')

        loc_time = loc_tz.localize(datetime(2004, 2, 1, 0, 0, 0))
        self.assertEqual(loc_time.strftime('%Z%z'), 'CET+0100')

        loc_time = loc_tz.localize(datetime(2004, 4, 1, 0, 0, 0))
        self.assertEqual(loc_time.strftime('%Z%z'), 'CEST+0200')

        tz = pytz.timezone('Europe/Amsterdam')
        loc_time = loc_tz.localize(datetime(1943, 3, 29, 1, 59, 59))
        self.assertEqual(loc_time.strftime('%Z%z'), 'CET+0100')


        # Switch to US
        loc_tz = pytz.timezone('US/Eastern')

        # End of DST ambiguity check
        loc_time = loc_tz.localize(datetime(1918, 10, 27, 1, 59, 59), is_dst=1)
        self.assertEqual(loc_time.strftime('%Z%z'), 'EDT-0400')

        loc_time = loc_tz.localize(datetime(1918, 10, 27, 1, 59, 59), is_dst=0)
        self.assertEqual(loc_time.strftime('%Z%z'), 'EST-0500')

        self.assertRaises(pytz.AmbiguousTimeError,
            loc_tz.localize, datetime(1918, 10, 27, 1, 59, 59), is_dst=None
            )

        # Start of DST non-existent times
        loc_time = loc_tz.localize(datetime(1918, 3, 31, 2, 0, 0), is_dst=0)
        self.assertEqual(loc_time.strftime('%Z%z'), 'EST-0500')

        loc_time = loc_tz.localize(datetime(1918, 3, 31, 2, 0, 0), is_dst=1)
        self.assertEqual(loc_time.strftime('%Z%z'), 'EDT-0400')

        self.assertRaises(pytz.NonExistentTimeError,
            loc_tz.localize, datetime(1918, 3, 31, 2, 0, 0), is_dst=None
            )

        # Weird changes - war time and peace time both is_dst==True

        loc_time = loc_tz.localize(datetime(1942, 2, 9, 3, 0, 0))
        self.assertEqual(loc_time.strftime('%Z%z'), 'EWT-0400')

        loc_time = loc_tz.localize(datetime(1945, 8, 14, 19, 0, 0))
        self.assertEqual(loc_time.strftime('%Z%z'), 'EPT-0400')

        loc_time = loc_tz.localize(datetime(1945, 9, 30, 1, 0, 0), is_dst=1)
        self.assertEqual(loc_time.strftime('%Z%z'), 'EPT-0400')

        loc_time = loc_tz.localize(datetime(1945, 9, 30, 1, 0, 0), is_dst=0)
        self.assertEqual(loc_time.strftime('%Z%z'), 'EST-0500')

        # Weird changes - ambiguous time (end-of-DST like) but is_dst==False
        for zonename, ambiguous_naive, expected in [
                ('Europe/Warsaw', datetime(1915, 8, 4, 23, 59, 59),
                 ['1915-08-04 23:59:59 WMT+0124',
                  '1915-08-04 23:59:59 CET+0100']),
                ('Europe/Moscow', datetime(2014, 10, 26, 1, 30),
                 ['2014-10-26 01:30:00 MSK+0400',
                  '2014-10-26 01:30:00 MSK+0300'])]:
            loc_tz = pytz.timezone(zonename)
            self.assertRaises(pytz.AmbiguousTimeError,
                loc_tz.localize, ambiguous_naive, is_dst=None
                )
            # Also test non-boolean is_dst in the weird case
            for dst in [True, timedelta(1), False, timedelta(0)]:
                loc_time = loc_tz.localize(ambiguous_naive, is_dst=dst)
                self.assertEqual(loc_time.strftime(fmt), expected[not dst])

    def testNormalize(self):
        tz = pytz.timezone('US/Eastern')
        dt = datetime(2004, 4, 4, 7, 0, 0, tzinfo=UTC).astimezone(tz)
        dt2 = dt - timedelta(minutes=10)
        self.assertEqual(
                dt2.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                '2004-04-04 02:50:00 EDT-0400'
                )

        dt2 = tz.normalize(dt2)
        self.assertEqual(
                dt2.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                '2004-04-04 01:50:00 EST-0500'
                )

    def testPartialMinuteOffsets(self):
        # utcoffset in Amsterdam was not a whole minute until 1937
        # However, we fudge this by rounding them, as the Python
        # datetime library
        tz = pytz.timezone('Europe/Amsterdam')
        utc_dt = datetime(1914, 1, 1, 13, 40, 28, tzinfo=UTC) # correct
        utc_dt = utc_dt.replace(second=0) # But we need to fudge it
        loc_dt = utc_dt.astimezone(tz)
        self.assertEqual(
                loc_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                '1914-01-01 14:00:00 AMT+0020'
                )

        # And get back...
        utc_dt = loc_dt.astimezone(UTC)
        self.assertEqual(
                utc_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                '1914-01-01 13:40:00 UTC+0000'
                )

    def no_testCreateLocaltime(self):
        # It would be nice if this worked, but it doesn't.
        tz = pytz.timezone('Europe/Amsterdam')
        dt = datetime(2004, 10, 31, 2, 0, 0, tzinfo=tz)
        self.assertEqual(
                dt.strftime(fmt),
                '2004-10-31 02:00:00 CET+0100'
                )


class CommonTimezonesTestCase(unittest.TestCase):
    def test_bratislava(self):
        # Bratislava is the default timezone for Slovakia, but our
        # heuristics where not adding it to common_timezones. Ideally,
        # common_timezones should be populated from zone.tab at runtime,
        # but I'm hesitant to pay the startup cost as loading the list
        # on demand whilst remaining backwards compatible seems
        # difficult.
        self.assertTrue('Europe/Bratislava' in pytz.common_timezones)
        self.assertTrue('Europe/Bratislava' in pytz.common_timezones_set)

    def test_us_eastern(self):
        self.assertTrue('US/Eastern' in pytz.common_timezones)
        self.assertTrue('US/Eastern' in pytz.common_timezones_set)

    def test_belfast(self):
        # Belfast uses London time.
        self.assertTrue('Europe/Belfast' in pytz.all_timezones_set)
        self.assertFalse('Europe/Belfast' in pytz.common_timezones)
        self.assertFalse('Europe/Belfast' in pytz.common_timezones_set)


class BaseTzInfoTestCase:
    '''Ensure UTC, StaticTzInfo and DstTzInfo work consistently.

    These tests are run for each type of tzinfo.
    '''
    tz = None  # override
    tz_class = None  # override

    def test_expectedclass(self):
        self.assertTrue(isinstance(self.tz, self.tz_class))

    def test_fromutc(self):
        # naive datetime.
        dt1 = datetime(2011, 10, 31)

        # localized datetime, same timezone.
        dt2 = self.tz.localize(dt1)

        # Both should give the same results. Note that the standard
        # Python tzinfo.fromutc() only supports the second.
        for dt in [dt1, dt2]:
            loc_dt = self.tz.fromutc(dt)
            loc_dt2 = pytz.utc.localize(dt1).astimezone(self.tz)
            self.assertEqual(loc_dt, loc_dt2)

        # localized datetime, different timezone.
        new_tz = pytz.timezone('Europe/Paris')
        self.assertTrue(self.tz is not new_tz)
        dt3 = new_tz.localize(dt1)
        self.assertRaises(ValueError, self.tz.fromutc, dt3)

    def test_normalize(self):
        other_tz = pytz.timezone('Europe/Paris')
        self.assertTrue(self.tz is not other_tz)

        dt = datetime(2012, 3, 26, 12, 0)
        other_dt = other_tz.localize(dt)

        local_dt = self.tz.normalize(other_dt)

        self.assertTrue(local_dt.tzinfo is not other_dt.tzinfo)
        self.assertNotEqual(
            local_dt.replace(tzinfo=None), other_dt.replace(tzinfo=None))

    def test_astimezone(self):
        other_tz = pytz.timezone('Europe/Paris')
        self.assertTrue(self.tz is not other_tz)

        dt = datetime(2012, 3, 26, 12, 0)
        other_dt = other_tz.localize(dt)

        local_dt = other_dt.astimezone(self.tz)

        self.assertTrue(local_dt.tzinfo is not other_dt.tzinfo)
        self.assertNotEqual(
            local_dt.replace(tzinfo=None), other_dt.replace(tzinfo=None))


class OptimizedUTCTestCase(unittest.TestCase, BaseTzInfoTestCase):
    tz = pytz.utc
    tz_class = tz.__class__


class LegacyUTCTestCase(unittest.TestCase, BaseTzInfoTestCase):
    # Deprecated timezone, but useful for comparison tests.
    tz = pytz.timezone('Etc/UTC')
    tz_class = StaticTzInfo


class StaticTzInfoTestCase(unittest.TestCase, BaseTzInfoTestCase):
    tz = pytz.timezone('GMT')
    tz_class = StaticTzInfo


class DstTzInfoTestCase(unittest.TestCase, BaseTzInfoTestCase):
    tz = pytz.timezone('Australia/Melbourne')
    tz_class = DstTzInfo


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite('pytz'))
    suite.addTest(doctest.DocTestSuite('pytz.tzinfo'))
    import test_tzinfo
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(test_tzinfo))
    return suite


if __name__ == '__main__':
    warnings.simplefilter("error") # Warnings should be fatal in tests.
    unittest.main(defaultTest='test_suite')
