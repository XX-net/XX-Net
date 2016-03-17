import re

__all__ = ['Range', 'ContentRange']

_rx_range = re.compile('bytes *= *(\d*) *- *(\d*)', flags=re.I)
_rx_content_range = re.compile(r'bytes (?:(\d+)-(\d+)|[*])/(?:(\d+)|[*])')

class Range(object):
    """
        Represents the Range header.
    """

    def __init__(self, start, end):
        assert end is None or end >= 0, "Bad range end: %r" % end
        self.start = start
        self.end = end # non-inclusive

    def range_for_length(self, length):
        """
            *If* there is only one range, and *if* it is satisfiable by
            the given length, then return a (start, end) non-inclusive range
            of bytes to serve.  Otherwise return None
        """
        if length is None:
            return None
        start, end = self.start, self.end
        if end is None:
            end = length
            if start < 0:
                start += length
        if _is_content_range_valid(start, end, length):
            stop = min(end, length)
            return (start, stop)
        else:
            return None

    def content_range(self, length):
        """
            Works like range_for_length; returns None or a ContentRange object

            You can use it like::

                response.content_range = req.range.content_range(response.content_length)

            Though it's still up to you to actually serve that content range!
        """
        range = self.range_for_length(length)
        if range is None:
            return None
        return ContentRange(range[0], range[1], length)

    def __str__(self):
        s,e = self.start, self.end
        if e is None:
            r = 'bytes=%s' % s
            if s >= 0:
                r += '-'
            return r
        return 'bytes=%s-%s' % (s, e-1)

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__,
            self.start, self.end)

    def __iter__(self):
        return iter((self.start, self.end))

    @classmethod
    def parse(cls, header):
        """
            Parse the header; may return None if header is invalid
        """
        m = _rx_range.match(header or '')
        if not m:
            return None
        start, end = m.groups()
        if not start:
            return cls(-int(end), None)
        start = int(start)
        if not end:
            return cls(start, None)
        end = int(end) + 1 # return val is non-inclusive
        if start >= end:
            return None
        return cls(start, end)


class ContentRange(object):

    """
    Represents the Content-Range header

    This header is ``start-stop/length``, where start-stop and length
    can be ``*`` (represented as None in the attributes).
    """

    def __init__(self, start, stop, length):
        if not _is_content_range_valid(start, stop, length):
            raise ValueError(
                "Bad start:stop/length: %r-%r/%r" % (start, stop, length))
        self.start = start
        self.stop = stop # this is python-style range end (non-inclusive)
        self.length = length

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self)

    def __str__(self):
        if self.length is None:
            length = '*'
        else:
            length = self.length
        if self.start is None:
            assert self.stop is None
            return 'bytes */%s' % length
        stop = self.stop - 1 # from non-inclusive to HTTP-style
        return 'bytes %s-%s/%s' % (self.start, stop, length)

    def __iter__(self):
        """
            Mostly so you can unpack this, like:

                start, stop, length = res.content_range
        """
        return iter([self.start, self.stop, self.length])

    @classmethod
    def parse(cls, value):
        """
            Parse the header.  May return None if it cannot parse.
        """
        m = _rx_content_range.match(value or '')
        if not m:
            return None
        s, e, l = m.groups()
        if s:
            s = int(s)
            e = int(e) + 1
        l = l and int(l)
        if not _is_content_range_valid(s, e, l, response=True):
            return None
        return cls(s, e, l)


def _is_content_range_valid(start, stop, length, response=False):
    if (start is None) != (stop is None):
        return False
    elif start is None:
        return length is None or length >= 0
    elif length is None:
        return 0 <= start < stop
    elif start >= stop:
        return False
    elif response and stop > length:
        # "content-range: bytes 0-50/10" is invalid for a response
        # "range: bytes 0-50" is valid for a request to a 10-bytes entity
        return False
    else:
        return 0 <= start < length
