from six import PY2


if PY2:
  class BlockingIOError(Exception):
      pass


  class BrokenPipeError(Exception):
      pass


  class ConnectionError(Exception):
      pass


  class ConnectionResetError(Exception):
      pass


  class ConnectionAbortedError(Exception):
      pass
else:
    BlockingIOError = BlockingIOError
    BrokenPipeError = BrokenPipeError
    ConnectionError = ConnectionError
    ConnectionResetError = ConnectionResetError
    ConnectionAbortedError = ConnectionAbortedError
