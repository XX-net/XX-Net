# Authors: 
#   Trevor Perrin
#   Martin von Loewis - python 3 port
#   Mirko Dziadzka - bugfix
#
# See the LICENSE file for legal information regarding use of this file.

"""Class for caching TLS sessions."""

import threading
import time

class SessionCache(object):
    """This class is used by the server to cache TLS sessions.

    Caching sessions allows the client to use TLS session resumption
    and avoid the expense of a full handshake.  To use this class,
    simply pass a SessionCache instance into the server handshake
    function.

    This class is thread-safe.
    """

    #References to these instances
    #are also held by the caller, who may change the 'resumable'
    #flag, so the SessionCache must return the same instances
    #it was passed in.

    def __init__(self, maxEntries=10000, maxAge=14400):
        """Create a new SessionCache.

        :type maxEntries: int
        :param maxEntries: The maximum size of the cache.  When this
            limit is reached, the oldest sessions will be deleted as
            necessary to make room for new ones.  The default is 10000.

        :type maxAge: int
        :param maxAge:  The number of seconds before a session expires
            from the cache.  The default is 14400 (i.e. 4 hours)."""

        self.lock = threading.Lock()

        # Maps sessionIDs to sessions
        self.entriesDict = {}

        #Circular list of (sessionID, timestamp) pairs
        self.entriesList = [(None,None)] * maxEntries

        self.firstIndex = 0
        self.lastIndex = 0
        self.maxAge = maxAge

    def __getitem__(self, sessionID):
        self.lock.acquire()
        try:
            self._purge() #Delete old items, so we're assured of a new one
            session = self.entriesDict[bytes(sessionID)]

            #When we add sessions they're resumable, but it's possible
            #for the session to be invalidated later on (if a fatal alert
            #is returned), so we have to check for resumability before
            #returning the session.

            if session.valid():
                return session
            else:
                raise KeyError()
        finally:
            self.lock.release()


    def __setitem__(self, sessionID, session):
        self.lock.acquire()
        try:
            #Add the new element
            self.entriesDict[bytes(sessionID)] = session
            self.entriesList[self.lastIndex] = (bytes(sessionID), time.time())
            self.lastIndex = (self.lastIndex+1) % len(self.entriesList)

            #If the cache is full, we delete the oldest element to make an
            #empty space
            if self.lastIndex == self.firstIndex:
                del(self.entriesDict[self.entriesList[self.firstIndex][0]])
                self.firstIndex = (self.firstIndex+1) % len(self.entriesList)
        finally:
            self.lock.release()

    #Delete expired items
    def _purge(self):
        currentTime = time.time()

        #Search through the circular list, deleting expired elements until
        #we reach a non-expired element.  Since elements in list are
        #ordered in time, we can break once we reach the first non-expired
        #element
        index = self.firstIndex
        while index != self.lastIndex:
            if currentTime - self.entriesList[index][1] > self.maxAge:
                del(self.entriesDict[self.entriesList[index][0]])
                index = (index+1) % len(self.entriesList)
            else:
                break
        self.firstIndex = index
