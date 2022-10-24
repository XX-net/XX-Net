# Author: Milan Lysonek
#
# See the LICENSE file for legal information regarding use of this file.

"""Helper functions for output formatting"""


def none_as_unknown(text, number):
    """
    Return text if text isn't None or empty, otherwise return 'unknown(number)'

    :type text: str
    :param text: string, that we want format
    :type number: int
    :param number: number used in text
    """
    if not text:
        text = "unknown({0})".format(number)
    return text
