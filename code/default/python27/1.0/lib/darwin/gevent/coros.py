# This module definitely remains in 1.0.x, probably in versions after that too.
import warnings
warnings.warn('gevent.coros has been renamed to gevent.lock', DeprecationWarning, stacklevel=2)

from gevent.lock import *
from gevent.lock import __all__
