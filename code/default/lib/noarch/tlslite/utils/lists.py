# Authors:
#   Hubert Kario (2016)
#
# See the LICENSE file for legal information regarding use of this file.

"""Helper functions for handling lists"""

from itertools import chain


def getFirstMatching(values, matches):
    """
    Return the first element in :py:obj:`values` that is also in
    :py:obj:`matches`.

    Return None if values is None, empty or no element in values is also in
    matches.

    :type values: collections.abc.Iterable
    :param values: list of items to look through, can be None
    :type matches: collections.abc.Container
    :param matches: list of items to check against
    """
    assert matches is not None
    if not values:
        return None
    return next((i for i in values if i in matches), None)


def to_str_delimiter(values, delim=", ", last_delim=" or "):
    """
    Format the list as a human readable string.

    Will format the list as a human readable enumeration, separated by commas
    (changable with `delim`) with last value separated with "or" (changable
    with `last_delim`).

    :type values: collections.abc.Iterable
    :param values: list of items to concatenate
    :type delim: str
    :param delim: primary delimiter for objects, comma by default
    :type last_delim: str
    :param last_delim: delimiter for last object in list
    :rtype: str
    """
    # we need to slice the iterator, so we need a copy
    values = list(values)
    return delim.join(chain((str(i) for i in values[:-2]),
                            [last_delim.join(str(i) for i in values[-2:])]))
