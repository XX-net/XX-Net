# Authors: 
#   Trevor Perrin
#   Martin von Loewis - python 3 port
#
# See the LICENSE file for legal information regarding use of this file.

"""Base class for SharedKeyDB and VerifierDB."""

try:
    import anydbm
except ImportError:
    # Python 3
    import dbm as anydbm
import threading
import time
import logging

class BaseDB(object):
    def __init__(self, filename, type):
        self.type = type
        self.filename = filename
        if self.filename:
            self.db = None
        else:
            self.db = {}
        self.lock = threading.Lock()

    def create(self):
        """
        Create a new on-disk database.

        :raises anydbm.error: If there's a problem creating the database.
        """
        logger = logging.getLogger(__name__)

        if self.filename:
            logger.debug('server %s - create - will open db', time.time())
            self.db = anydbm.open(self.filename, "n") #raises anydbm.error
            logger.debug('server %s - create - setting type', time.time())
            self.db["--Reserved--type"] = self.type
            logger.debug('server %s - create - syncing', time.time())
            self.db.sync()
            logger.debug('server %s - create - fun exit', time.time())
        else:
            logger.debug('server %s - create - using dict() as DB',
                         time.time())
            self.db = {}

    def open(self):
        """
        Open a pre-existing on-disk database.

        :raises anydbm.error: If there's a problem opening the database.
        :raises ValueError: If the database is not of the right type.
        """
        if not self.filename:
            raise ValueError("Can only open on-disk databases")
        self.db = anydbm.open(self.filename, "w") #raises anydbm.error
        try:
            if self.db["--Reserved--type"] != self.type:
                raise ValueError("Not a %s database" % self.type)
        except KeyError:
            raise ValueError("Not a recognized database")

    def __getitem__(self, username):
        if self.db == None:
            raise AssertionError("DB not open")

        self.lock.acquire()
        try:
            valueStr = self.db[username]
        finally:
            self.lock.release()

        return self._getItem(username, valueStr)

    def __setitem__(self, username, value):
        if self.db == None:
            raise AssertionError("DB not open")

        valueStr = self._setItem(username, value)

        self.lock.acquire()
        try:
            self.db[username] = valueStr
            if self.filename:
                self.db.sync()
        finally:
            self.lock.release()

    def __delitem__(self, username):
        if self.db == None:
            raise AssertionError("DB not open")

        self.lock.acquire()
        try:
            del(self.db[username])
            if self.filename:
                self.db.sync()
        finally:
            self.lock.release()

    def __contains__(self, username):
        """
        Check if the database contains the specified username.

        :param str username: The username to check for.

        :rtype: bool
        :returns: True if the database contains the username, False
            otherwise.
        """
        if self.db == None:
            raise AssertionError("DB not open")

        self.lock.acquire()
        try:
            return username in self.db
        finally:
            self.lock.release()

    def check(self, username, param):
        value = self.__getitem__(username)
        return self._checkItem(value, username, param)

    def keys(self):
        """
        Return a list of usernames in the database.

        :rtype: list
        :returns: The usernames in the database.
        """
        if self.db == None:
            raise AssertionError("DB not open")

        self.lock.acquire()
        try:
            usernames = self.db.keys()
        finally:
            self.lock.release()
        usernames = [u for u in usernames if not u.startswith("--Reserved--")]
        return usernames
