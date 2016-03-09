#
# Copyright 2008 The ndb Authors. All Rights Reserved.
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

"""A tasklet decorator.

Tasklets are a way to write concurrently running functions without
threads; tasklets are executed by an event loop and can suspend
themselves blocking for I/O or some other operation using a yield
statement.  The notion of a blocking operation is abstracted into the
Future class, but a tasklet may also yield an RPC in order to wait for
that RPC to complete.

The @tasklet decorator wraps generator function so that when it is
called, a Future is returned while the generator is executed by the
event loop.  Within the tasklet, any yield of a Future waits for and
returns the Future's result.  For example:

  @tasklet
  def foo():
    a = yield <some Future>
    b = yield <another Future>
    raise Return(a + b)

  def main():
    f = foo()
    x = f.get_result()
    print x

Note that blocking until the Future's result is available using
get_result() is somewhat inefficient (though not vastly -- it is not
busy-waiting).  In most cases such code should be rewritten as a tasklet
instead:

  @tasklet
  def main_tasklet():
    f = foo()
    x = yield f
    print x

Calling a tasklet automatically schedules it with the event loop:

  def main():
    f = main_tasklet()
    eventloop.run()  # Run until no tasklets left to do
    f.done()  # Returns True

As a special feature, if the wrapped function is not a generator
function, its return value is returned via the Future.  This makes the
following two equivalent:

  @tasklet
  def foo():
    return 42

  @tasklet
  def foo():
    if False: yield  # The presence of 'yield' makes foo a generator
    raise Return(42)  # Or, after PEP 380, return 42

This feature (inspired by Monocle) is handy in case you are
implementing an interface that expects tasklets but you have no need to
suspend -- there's no need to insert a dummy yield in order to make
the tasklet into a generator.
"""

import collections
import logging
import os
import sys
import types

from .google_imports import apiproxy_stub_map
from .google_imports import apiproxy_rpc
from .google_imports import datastore
from .google_imports import datastore_errors
from .google_imports import datastore_pbs
from .google_imports import datastore_rpc
from .google_imports import namespace_manager

from . import eventloop
from . import utils

__all__ = ['Return', 'tasklet', 'synctasklet', 'toplevel', 'sleep',
           'add_flow_exception', 'get_return_value',
           'get_context', 'set_context',
           'make_default_context', 'make_context',
           'Future', 'MultiFuture', 'QueueFuture', 'SerialQueueFuture',
           'ReducingFuture',
          ]

_logging_debug = utils.logging_debug


def _is_generator(obj):
  """Helper to test for a generator object.

  NOTE: This tests for the (iterable) object returned by calling a
  generator function, not for a generator function.
  """
  return isinstance(obj, types.GeneratorType)


class _State(utils.threading_local):
  """Hold thread-local state."""

  current_context = None

  def __init__(self):
    super(_State, self).__init__()
    self.all_pending = set()

  def add_pending(self, fut):
    _logging_debug('all_pending: add %s', fut)
    self.all_pending.add(fut)

  def remove_pending(self, fut, status='success'):
    if fut in self.all_pending:
      _logging_debug('all_pending: %s: remove %s', status, fut)
      self.all_pending.remove(fut)
    else:
      _logging_debug('all_pending: %s: not found %s', status, fut)

  def clear_all_pending(self):
    if self.all_pending:
      logging.info('all_pending: clear %s', self.all_pending)
      self.all_pending.clear()
    else:
      _logging_debug('all_pending: clear no-op')

  def dump_all_pending(self, verbose=False):
    pending = []
    for fut in self.all_pending:
      if verbose:
        line = fut.dump() + ('\n' + '-' * 40)
      else:
        line = fut.dump_stack()
      pending.append(line)
    return '\n'.join(pending)


_state = _State()


# Tuple of exceptions that should not be logged (except in debug mode).
_flow_exceptions = ()


def add_flow_exception(exc):
  """Add an exception that should not be logged.

  The argument must be a subclass of Exception.
  """
  global _flow_exceptions
  if not isinstance(exc, type) or not issubclass(exc, Exception):
    raise TypeError('Expected an Exception subclass, got %r' % (exc,))
  as_set = set(_flow_exceptions)
  as_set.add(exc)
  _flow_exceptions = tuple(as_set)


def _init_flow_exceptions():
  """Internal helper to initialize _flow_exceptions.

  This automatically adds webob.exc.HTTPException, if it can be imported.
  """
  global _flow_exceptions
  _flow_exceptions = ()
  add_flow_exception(datastore_errors.Rollback)
  try:
    from webob import exc
  except ImportError:
    pass
  else:
    add_flow_exception(exc.HTTPException)


_init_flow_exceptions()


class Future(object):
  """A Future has 0 or more callbacks.

  The callbacks will be called when the result is ready.

  NOTE: This is somewhat inspired but not conformant to the Future interface
  defined by PEP 3148.  It is also inspired (and tries to be somewhat
  compatible with) the App Engine specific UserRPC and MultiRpc classes.
  """
  # TODO: Trim the API; there are too many ways to do the same thing.
  # TODO: Compare to Monocle's much simpler Callback class.

  # Constants for state property.
  IDLE = apiproxy_rpc.RPC.IDLE  # Not yet running (unused)
  RUNNING = apiproxy_rpc.RPC.RUNNING  # Not yet completed.
  FINISHING = apiproxy_rpc.RPC.FINISHING  # Completed.

  # XXX Add docstrings to all methods.  Separate PEP 3148 API from RPC API.

  _geninfo = None  # Extra info about suspended generator.

  def __init__(self, info=None):
    # TODO: Make done a method, to match PEP 3148?
    # pylint: disable=invalid-name
    __ndb_debug__ = 'SKIP'  # Hide this frame from self._where
    self._info = info  # Info from the caller about this Future's purpose.
    self._where = utils.get_stack()
    self._context = None
    self._reset()

  def _reset(self):
    self._done = False
    self._result = None
    self._exception = None
    self._traceback = None
    self._callbacks = []
    self._immediate_callbacks = []
    _state.add_pending(self)
    self._next = None  # Links suspended Futures together in a stack.

  # TODO: Add a __del__ that complains if neither get_exception() nor
  # check_success() was ever called?  What if it's not even done?

  def __repr__(self):
    if self._done:
      if self._exception is not None:
        state = 'exception %s: %s' % (self._exception.__class__.__name__,
                                      self._exception)
      else:
        state = 'result %r' % (self._result,)
    else:
      state = 'pending'
    line = '?'
    for line in self._where:
      if 'tasklets.py' not in line:
        break
    if self._info:
      line += ' for %s' % self._info
    if self._geninfo:
      line += ' %s' % self._geninfo
    return '<%s %x created by %s; %s>' % (
        self.__class__.__name__, id(self), line, state)

  def dump(self):
    return '%s\nCreated by %s' % (self.dump_stack(),
                                  '\n called by '.join(self._where))

  def dump_stack(self):
    lines = []
    fut = self
    while fut is not None:
      lines.append(str(fut))
      fut = fut._next
    return '\n waiting for '.join(lines)

  def add_callback(self, callback, *args, **kwds):
    if self._done:
      eventloop.queue_call(None, callback, *args, **kwds)
    else:
      self._callbacks.append((callback, args, kwds))

  def add_immediate_callback(self, callback, *args, **kwds):
    if self._done:
      callback(*args, **kwds)
    else:
      self._immediate_callbacks.append((callback, args, kwds))

  def set_result(self, result):
    if self._done:
      raise RuntimeError('Result cannot be set twice.')
    self._result = result
    self._done = True
    _state.remove_pending(self)
    for callback, args, kwds in self._immediate_callbacks:
      callback(*args, **kwds)
    for callback, args, kwds in self._callbacks:
      eventloop.queue_call(None, callback, *args, **kwds)

  def set_exception(self, exc, tb=None):
    if not isinstance(exc, BaseException):
      raise TypeError('exc must be an Exception; received %r' % exc)
    if self._done:
      raise RuntimeError('Exception cannot be set twice.')
    self._exception = exc
    self._traceback = tb
    self._done = True
    _state.remove_pending(self, status='fail')
    for callback, args, kwds in self._immediate_callbacks:
      callback(*args, **kwds)
    for callback, args, kwds in self._callbacks:
      eventloop.queue_call(None, callback, *args, **kwds)

  def done(self):
    return self._done

  @property
  def state(self):
    # This is just for compatibility with UserRPC and MultiRpc.
    # A Future is considered running as soon as it is created.
    if self._done:
      return self.FINISHING
    else:
      return self.RUNNING

  def wait(self):
    if self._done:
      return
    ev = eventloop.get_event_loop()
    while not self._done:
      if not ev.run1():
        logging.info('Deadlock in %s', self)
        logging.info('All pending Futures:\n%s', _state.dump_all_pending())
        _logging_debug('All pending Futures (verbose):\n%s',
                       _state.dump_all_pending(verbose=True))
        self.set_exception(RuntimeError('Deadlock waiting for %s' % self))

  def get_exception(self):
    self.wait()
    return self._exception

  def get_traceback(self):
    self.wait()
    return self._traceback

  def check_success(self):
    self.wait()
    if self._exception is not None:
      raise self._exception.__class__, self._exception, self._traceback

  def get_result(self):
    self.check_success()
    return self._result

  # TODO: Have a tasklet that does this
  @classmethod
  def wait_any(cls, futures):
    # TODO: Flatten MultiRpcs.
    waiting_on = set(futures)
    ev = eventloop.get_event_loop()
    while waiting_on:
      for f in waiting_on:
        if f.state == cls.FINISHING:
          return f
      ev.run1()
    return None

  # TODO: Have a tasklet that does this
  @classmethod
  def wait_all(cls, futures):
    # TODO: Flatten MultiRpcs.
    waiting_on = set(futures)
    ev = eventloop.get_event_loop()
    while waiting_on:
      waiting_on = set(f for f in waiting_on if f.state == cls.RUNNING)
      ev.run1()

  def _help_tasklet_along(self, ns, ds_conn, gen, val=None, exc=None, tb=None):
    # XXX Docstring
    info = utils.gen_info(gen)
    # pylint: disable=invalid-name
    __ndb_debug__ = info
    try:
      save_context = get_context()
      save_namespace = namespace_manager.get_namespace()
      save_ds_connection = datastore._GetConnection()
      try:
        set_context(self._context)
        if ns != save_namespace:
          namespace_manager.set_namespace(ns)
        if ds_conn is not save_ds_connection:
          datastore._SetConnection(ds_conn)
        if exc is not None:
          _logging_debug('Throwing %s(%s) into %s',
                         exc.__class__.__name__, exc, info)
          value = gen.throw(exc.__class__, exc, tb)
        else:
          _logging_debug('Sending %r to %s', val, info)
          value = gen.send(val)
          self._context = get_context()
      finally:
        ns = namespace_manager.get_namespace()
        ds_conn = datastore._GetConnection()
        set_context(save_context)
        if save_namespace != ns:
          namespace_manager.set_namespace(save_namespace)
        if save_ds_connection is not ds_conn:
          datastore._SetConnection(save_ds_connection)

    except StopIteration, err:
      result = get_return_value(err)
      _logging_debug('%s returned %r', info, result)
      self.set_result(result)
      return

    except GeneratorExit:
      # In Python 2.5, this derives from Exception, but we don't want
      # to handle it like other Exception instances.  So we catch and
      # re-raise it immediately.  See issue 127.  http://goo.gl/2p5Pn
      # TODO: Remove when Python 2.5 is no longer supported.
      raise

    except Exception, err:
      _, _, tb = sys.exc_info()
      if isinstance(err, _flow_exceptions):
        # Flow exceptions aren't logged except in "heavy debug" mode,
        # and then only at DEBUG level, without a traceback.
        _logging_debug('%s raised %s(%s)',
                       info, err.__class__.__name__, err)
      elif utils.DEBUG and logging.getLogger().level < logging.DEBUG:
        # In "heavy debug" mode, log a warning with traceback.
        # (This is the same condition as used in utils.logging_debug().)
        logging.warning('%s raised %s(%s)',
                        info, err.__class__.__name__, err, exc_info=True)
      else:
        # Otherwise, log a warning without a traceback.
        logging.warning('%s raised %s(%s)', info, err.__class__.__name__, err)
      self.set_exception(err, tb)
      return

    else:
      _logging_debug('%s yielded %r', info, value)
      if isinstance(value, (apiproxy_stub_map.UserRPC,
                            datastore_rpc.MultiRpc)):
        # TODO: Tail recursion if the RPC is already complete.
        eventloop.queue_rpc(value, self._on_rpc_completion,
                            value, ns, ds_conn, gen)
        return
      if isinstance(value, Future):
        # TODO: Tail recursion if the Future is already done.
        if self._next:
          raise RuntimeError('Future has already completed yet next is %r' %
                             self._next)
        self._next = value
        self._geninfo = utils.gen_info(gen)
        _logging_debug('%s is now blocked waiting for %s', self, value)
        value.add_callback(self._on_future_completion, value, ns, ds_conn, gen)
        return
      if isinstance(value, (tuple, list)):
        # Arrange for yield to return a list of results (not Futures).
        info = 'multi-yield from %s' % utils.gen_info(gen)
        mfut = MultiFuture(info)
        try:
          for subfuture in value:
            mfut.add_dependent(subfuture)
          mfut.complete()
        except GeneratorExit:
          raise
        except Exception, err:
          _, _, tb = sys.exc_info()
          mfut.set_exception(err, tb)
        mfut.add_callback(self._on_future_completion, mfut, ns, ds_conn, gen)
        return
      if _is_generator(value):
        # TODO: emulate PEP 380 here?
        raise NotImplementedError('Cannot defer to another generator.')
      raise RuntimeError('A tasklet should not yield a plain value: '
                         '%.200s yielded %.200r' % (info, value))

  def _on_rpc_completion(self, rpc, ns, ds_conn, gen):
    try:
      result = rpc.get_result()
    except GeneratorExit:
      raise
    except Exception, err:
      _, _, tb = sys.exc_info()
      self._help_tasklet_along(ns, ds_conn, gen, exc=err, tb=tb)
    else:
      self._help_tasklet_along(ns, ds_conn, gen, result)

  def _on_future_completion(self, future, ns, ds_conn, gen):
    if self._next is future:
      self._next = None
      self._geninfo = None
      _logging_debug('%s is no longer blocked waiting for %s', self, future)
    exc = future.get_exception()
    if exc is not None:
      self._help_tasklet_along(ns, ds_conn, gen,
                               exc=exc, tb=future.get_traceback())
    else:
      val = future.get_result()  # This won't raise an exception.
      self._help_tasklet_along(ns, ds_conn, gen, val)


def sleep(dt):
  """Public function to sleep some time.

  Example:
    yield tasklets.sleep(0.5)  # Sleep for half a sec.
  """
  fut = Future('sleep(%.3f)' % dt)
  eventloop.queue_call(dt, fut.set_result, None)
  return fut


class MultiFuture(Future):
  """A Future that depends on multiple other Futures.

  This is used internally by 'v1, v2, ... = yield f1, f2, ...'; the
  semantics (e.g. error handling) are constrained by that use case.

  The protocol from the caller's POV is:

    mf = MultiFuture()
    mf.add_dependent(<some other Future>)  -OR- mf.putq(<some value>)
    mf.add_dependent(<some other Future>)  -OR- mf.putq(<some value>)
      .
      . (More mf.add_dependent() and/or mf.putq() calls)
      .
    mf.complete()  # No more dependents will be added.
      .
      . (Time passes)
      .
    results = mf.get_result()

  Now, results is a list of results from all dependent Futures in
  the order in which they were added.

  It is legal to add the same dependent multiple times.

  Callbacks can be added at any point.

  From a dependent Future POV, there's nothing to be done: a callback
  is automatically added to each dependent Future which will signal
  its completion to the MultiFuture.

  Error handling: if any dependent future raises an error, it is
  propagated to mf.  To force an early error, you can call
  mf.set_exception() instead of mf.complete().  After this you can't
  call mf.add_dependent() or mf.putq() any more.
  """

  def __init__(self, info=None):
    # pylint: disable=invalid-name
    __ndb_debug__ = 'SKIP'  # Hide this frame from self._where
    self._full = False
    self._dependents = set()
    self._results = []
    super(MultiFuture, self).__init__(info=info)

  def __repr__(self):
    # TODO: This may be invoked before __init__() returns,
    # from Future.__init__().  Beware.
    line = super(MultiFuture, self).__repr__()
    lines = [line]
    for fut in self._results:
      lines.append(fut.dump_stack().replace('\n', '\n  '))
    return '\n waiting for '.join(lines)

  # TODO: Maybe rename this method, since completion of a Future/RPC
  # already means something else.  But to what?
  def complete(self):
    if self._full:
      raise RuntimeError('MultiFuture cannot complete twice.')
    self._full = True
    if not self._dependents:
      self._finish()

  # TODO: Maybe don't overload set_exception() with this?
  def set_exception(self, exc, tb=None):
    self._full = True
    super(MultiFuture, self).set_exception(exc, tb)

  def _finish(self):
    if not self._full:
      raise RuntimeError('MultiFuture cannot finish until completed.')
    if self._dependents:
      raise RuntimeError('MultiFuture cannot finish whilst waiting for '
                         'dependents %r' % self._dependents)
    if self._done:
      raise RuntimeError('MultiFuture done before finishing.')
    try:
      result = [r.get_result() for r in self._results]
    except GeneratorExit:
      raise
    except Exception, err:
      _, _, tb = sys.exc_info()
      self.set_exception(err, tb)
    else:
      self.set_result(result)

  def putq(self, value):
    if isinstance(value, Future):
      fut = value
    else:
      fut = Future()
      fut.set_result(value)
    self.add_dependent(fut)

  def add_dependent(self, fut):
    if isinstance(fut, list):
      mfut = MultiFuture()
      map(mfut.add_dependent, fut)
      mfut.complete()
      fut = mfut
    elif not isinstance(fut, Future):
      raise TypeError('Expected Future, received %s: %r' % (type(fut), fut))
    if self._full:
      raise RuntimeError('MultiFuture cannot add a dependent once complete.')
    self._results.append(fut)
    if fut not in self._dependents:
      self._dependents.add(fut)
      fut.add_callback(self._signal_dependent_done, fut)

  def _signal_dependent_done(self, fut):
    self._dependents.remove(fut)
    if self._full and not self._dependents and not self._done:
      self._finish()


class QueueFuture(Future):
  """A Queue following the same protocol as MultiFuture.

  However, instead of returning results as a list, it lets you
  retrieve results as soon as they are ready, one at a time, using
  getq().  The Future itself finishes with a result of None when the
  last result is ready (regardless of whether it was retrieved).

  The getq() method returns a Future which blocks until the next
  result is ready, and then returns that result.  Each getq() call
  retrieves one unique result.  Extra getq() calls after the last
  result is already returned return EOFError as their Future's
  exception.  (I.e., q.getq() returns a Future as always, but yieding
  that Future raises EOFError.)

  NOTE: Values can also be pushed directly via .putq(value).  However
  there is no flow control -- if the producer is faster than the
  consumer, the queue will grow unbounded.
  """
  # TODO: Refactor to share code with MultiFuture.

  def __init__(self, info=None):
    self._full = False
    self._dependents = set()
    self._completed = collections.deque()
    self._waiting = collections.deque()
    # Invariant: at least one of _completed and _waiting is empty.
    # Also: _full and not _dependents <==> _done.
    super(QueueFuture, self).__init__(info=info)

  # TODO: __repr__

  def complete(self):
    if self._full:
      raise RuntimeError('MultiFuture cannot complete twice.')
    self._full = True
    if not self._dependents:
      self.set_result(None)
      self._mark_finished()

  def set_exception(self, exc, tb=None):
    self._full = True
    super(QueueFuture, self).set_exception(exc, tb)
    if not self._dependents:
      self._mark_finished()

  def putq(self, value):
    if isinstance(value, Future):
      fut = value
    else:
      fut = Future()
      fut.set_result(value)
    self.add_dependent(fut)

  def add_dependent(self, fut):
    if not isinstance(fut, Future):
      raise TypeError('fut must be a Future instance; received %r' % fut)
    if self._full:
      raise RuntimeError('QueueFuture add dependent once complete.')
    if fut not in self._dependents:
      self._dependents.add(fut)
      fut.add_callback(self._signal_dependent_done, fut)

  def _signal_dependent_done(self, fut):
    if not fut.done():
      raise RuntimeError('Future not done before signalling dependant done.')
    self._dependents.remove(fut)
    exc = fut.get_exception()
    tb = fut.get_traceback()
    val = None
    if exc is None:
      val = fut.get_result()
    if self._waiting:
      waiter = self._waiting.popleft()
      self._pass_result(waiter, exc, tb, val)
    else:
      self._completed.append((exc, tb, val))
    if self._full and not self._dependents and not self._done:
      self.set_result(None)
      self._mark_finished()

  def _mark_finished(self):
    if not self.done():
      raise RuntimeError('Future not done before marking as finished.')
    while self._waiting:
      waiter = self._waiting.popleft()
      self._pass_eof(waiter)

  def getq(self):
    fut = Future()
    if self._completed:
      exc, tb, val = self._completed.popleft()
      self._pass_result(fut, exc, tb, val)
    elif self._full and not self._dependents:
      self._pass_eof(fut)
    else:
      self._waiting.append(fut)
    return fut

  def _pass_eof(self, fut):
    if not self._done:
      raise RuntimeError('QueueFuture cannot pass EOF until done.')
    exc = self.get_exception()
    if exc is not None:
      tb = self.get_traceback()
    else:
      exc = EOFError('Queue is empty')
      tb = None
    self._pass_result(fut, exc, tb, None)

  def _pass_result(self, fut, exc, tb, val):
    if exc is not None:
      fut.set_exception(exc, tb)
    else:
      fut.set_result(val)


class SerialQueueFuture(Future):
  """Like QueueFuture but maintains the order of insertion.

  This class is used by Query operations.

  Invariants:

  - At least one of _queue and _waiting is empty.
  - The Futures in _waiting are always pending.

  (The Futures in _queue may be pending or completed.)

  In the discussion below, add_dependent() is treated the same way as
  putq().

  If putq() is ahead of getq(), the situation is like this:

                         putq()
                         v
    _queue: [f1, f2, ...]; _waiting: []
    ^
    getq()

  Here, putq() appends a Future to the right of _queue, and getq()
  removes one from the left.

  If getq() is ahead of putq(), it's like this:

              putq()
              v
    _queue: []; _waiting: [f1, f2, ...]
                                       ^
                                       getq()

  Here, putq() removes a Future from the left of _waiting, and getq()
  appends one to the right.

  When both are empty, putq() appends a Future to the right of _queue,
  while getq() appends one to the right of _waiting.

  The _full flag means that no more calls to putq() will be made; it
  is set by calling either complete() or set_exception().

  Calling complete() signals that no more putq() calls will be made.
  If getq() is behind, subsequent getq() calls will eat up _queue
  until it is empty, and after that will return a Future that passes
  EOFError (note that getq() itself never raises EOFError).  If getq()
  is ahead when complete() is called, the Futures in _waiting are all
  passed an EOFError exception (thereby eating up _waiting).

  If, instead of complete(), set_exception() is called, the exception
  and traceback set there will be used instead of EOFError.
  """

  def __init__(self, info=None):
    self._queue = collections.deque()
    self._waiting = collections.deque()
    super(SerialQueueFuture, self).__init__(info=info)

  # TODO: __repr__

  def complete(self):
    while self._waiting:
      waiter = self._waiting.popleft()
      waiter.set_exception(EOFError('Queue is empty'))
    # When the writer is complete the future will also complete. If there are
    # still pending queued futures, these futures are themselves in the pending
    # list, so they will eventually be executed.
    self.set_result(None)

  def set_exception(self, exc, tb=None):
    super(SerialQueueFuture, self).set_exception(exc, tb)
    while self._waiting:
      waiter = self._waiting.popleft()
      waiter.set_exception(exc, tb)

  def putq(self, value):
    if isinstance(value, Future):
      fut = value
    else:
      if self._waiting:
        waiter = self._waiting.popleft()
        waiter.set_result(value)
        return
      fut = Future()
      fut.set_result(value)
    self.add_dependent(fut)

  def add_dependent(self, fut):
    if not isinstance(fut, Future):
      raise TypeError('fut must be a Future instance; received %r' % fut)
    if self._done:
      raise RuntimeError('SerialQueueFuture cannot add dependent '
                         'once complete.')
    if self._waiting:
      waiter = self._waiting.popleft()
      fut.add_callback(_transfer_result, fut, waiter)
    else:
      self._queue.append(fut)

  def getq(self):
    if self._queue:
      fut = self._queue.popleft()
    else:
      fut = Future()
      if self._done:
        err = self.get_exception()
        if err is not None:
          tb = self.get_traceback()
        else:
          err = EOFError('Queue is empty')
          tb = None
        fut.set_exception(err, tb)
      else:
        self._waiting.append(fut)
    return fut


def _transfer_result(fut1, fut2):
  """Helper to transfer result or errors from one Future to another."""
  exc = fut1.get_exception()
  if exc is not None:
    tb = fut1.get_traceback()
    fut2.set_exception(exc, tb)
  else:
    val = fut1.get_result()
    fut2.set_result(val)


class ReducingFuture(Future):
  """A Queue following the same protocol as MultiFuture.

  However the result, instead of being a list of results of dependent
  Futures, is computed by calling a 'reducer' tasklet.  The reducer tasklet
  takes a list of values and returns a single value.  It may be called
  multiple times on sublists of values and should behave like
  e.g. sum().

  NOTE: The reducer input values may be reordered compared to the
  order in which they were added to the queue.
  """
  # TODO: Refactor to reuse some code with MultiFuture.

  def __init__(self, reducer, info=None, batch_size=20):
    self._reducer = reducer
    self._batch_size = batch_size
    self._full = False
    self._dependents = set()
    self._completed = collections.deque()
    self._queue = collections.deque()
    super(ReducingFuture, self).__init__(info=info)

  # TODO: __repr__

  def complete(self):
    if self._full:
      raise RuntimeError('ReducingFuture cannot complete twice.')
    self._full = True
    if not self._dependents:
      self._mark_finished()

  def set_exception(self, exc, tb=None):
    self._full = True
    self._queue.clear()
    super(ReducingFuture, self).set_exception(exc, tb)

  def putq(self, value):
    if isinstance(value, Future):
      fut = value
    else:
      fut = Future()
      fut.set_result(value)
    self.add_dependent(fut)

  def add_dependent(self, fut):
    if self._full:
      raise RuntimeError('ReducingFuture cannot add dependent once complete.')
    self._internal_add_dependent(fut)

  def _internal_add_dependent(self, fut):
    if not isinstance(fut, Future):
      raise TypeError('fut must be a Future; received %r' % fut)
    if fut not in self._dependents:
      self._dependents.add(fut)
      fut.add_callback(self._signal_dependent_done, fut)

  def _signal_dependent_done(self, fut):
    if not fut.done():
      raise RuntimeError('Future not done before signalling dependant done.')
    self._dependents.remove(fut)
    if self._done:
      return  # Already done.
    try:
      val = fut.get_result()
    except GeneratorExit:
      raise
    except Exception, err:
      _, _, tb = sys.exc_info()
      self.set_exception(err, tb)
      return
    self._queue.append(val)
    if len(self._queue) >= self._batch_size:
      todo = list(self._queue)
      self._queue.clear()
      try:
        nval = self._reducer(todo)
      except GeneratorExit:
        raise
      except Exception, err:
        _, _, tb = sys.exc_info()
        self.set_exception(err, tb)
        return
      if isinstance(nval, Future):
        self._internal_add_dependent(nval)
      else:
        self._queue.append(nval)
    if self._full and not self._dependents:
      self._mark_finished()

  def _mark_finished(self):
    if not self._queue:
      self.set_result(None)
    elif len(self._queue) == 1:
      self.set_result(self._queue.pop())
    else:
      todo = list(self._queue)
      self._queue.clear()
      try:
        nval = self._reducer(todo)
      except GeneratorExit:
        raise
      except Exception, err:
        _, _, tb = sys.exc_info()
        self.set_exception(err, tb)
        return
      if isinstance(nval, Future):
        self._internal_add_dependent(nval)
      else:
        self.set_result(nval)


# Alias for StopIteration used to mark return values.
# To use this, raise Return(<your return value>).  The semantics
# are exactly the same as raise StopIteration(<your return value>)
# but using Return clarifies that you are intending this to be the
# return value of a tasklet.
# TODO: According to Monocle authors Steve and Greg Hazel, Twisted
# used an exception to signal a return value from a generator early
# on, and they found out it was error-prone.  Should I worry?
Return = StopIteration


def get_return_value(err):
  # XXX Docstring
  if not err.args:
    result = None
  elif len(err.args) == 1:
    result = err.args[0]
  else:
    result = err.args
  return result


def tasklet(func):
  # XXX Docstring

  @utils.wrapping(func)
  def tasklet_wrapper(*args, **kwds):
    # XXX Docstring

    # TODO: make most of this a public function so you can take a bare
    # generator and turn it into a tasklet dynamically.  (Monocle has
    # this I believe.)
    # pylint: disable=invalid-name
    __ndb_debug__ = utils.func_info(func)
    fut = Future('tasklet %s' % utils.func_info(func))
    fut._context = get_context()
    try:
      result = func(*args, **kwds)
    except StopIteration, err:
      # Just in case the function is not a generator but still uses
      # the "raise Return(...)" idiom, we'll extract the return value.
      result = get_return_value(err)
    if _is_generator(result):
      ns = namespace_manager.get_namespace()
      ds_conn = datastore._GetConnection()
      eventloop.queue_call(None, fut._help_tasklet_along, ns, ds_conn, result)
    else:
      fut.set_result(result)
    return fut

  return tasklet_wrapper


def synctasklet(func):
  """Decorator to run a function as a tasklet when called.

  Use this to wrap a request handler function that will be called by
  some web application framework (e.g. a Django view function or a
  webapp.RequestHandler.get method).
  """
  taskletfunc = tasklet(func)  # wrap at declaration time.

  @utils.wrapping(func)
  def synctasklet_wrapper(*args, **kwds):
    # pylint: disable=invalid-name
    __ndb_debug__ = utils.func_info(func)
    return taskletfunc(*args, **kwds).get_result()
  return synctasklet_wrapper


def toplevel(func):
  """A sync tasklet that sets a fresh default Context.

  Use this for toplevel view functions such as
  webapp.RequestHandler.get() or Django view functions.
  """
  synctaskletfunc = synctasklet(func)  # wrap at declaration time.

  @utils.wrapping(func)
  def add_context_wrapper(*args, **kwds):
    # pylint: disable=invalid-name
    __ndb_debug__ = utils.func_info(func)
    _state.clear_all_pending()
    # Create and install a new context.
    ctx = make_default_context()
    try:
      set_context(ctx)
      return synctaskletfunc(*args, **kwds)
    finally:
      set_context(None)
      ctx.flush().check_success()
      eventloop.run()  # Ensure writes are flushed, etc.
  return add_context_wrapper


_CONTEXT_KEY = '__CONTEXT__'

_DATASTORE_APP_ID_ENV = 'DATASTORE_APP_ID'
_DATASTORE_PROJECT_ID_ENV = 'DATASTORE_PROJECT_ID'
_DATASTORE_ADDITIONAL_APP_IDS_ENV = 'DATASTORE_ADDITIONAL_APP_IDS'
_DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV = 'DATASTORE_USE_PROJECT_ID_AS_APP_ID'


def get_context():
  # XXX Docstring
  ctx = None
  if os.getenv(_CONTEXT_KEY):
    ctx = _state.current_context
  if ctx is None:
    ctx = make_default_context()
    set_context(ctx)
  return ctx


def make_default_context():
  # XXX Docstring
  datastore_app_id = os.environ.get(_DATASTORE_APP_ID_ENV, None)
  datastore_project_id = os.environ.get(_DATASTORE_PROJECT_ID_ENV, None)
  if datastore_app_id or datastore_project_id:
    # We will create a Cloud Datastore context.
    app_id_override = bool(os.environ.get(
        _DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV, False))
    if not datastore_app_id and not app_id_override:
      raise ValueError('Could not determine app id. To use project id (%s) '
                       'instead, set %s=true. This will affect the '
                       'serialized form of entities and should not be used '
                       'if serialized entities will be shared between '
                       'code running on App Engine and code running off '
                       'App Engine. Alternatively, set %s=<app id>.'
                       % (datastore_project_id,
                          _DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV,
                          _DATASTORE_APP_ID_ENV))
    elif datastore_app_id:
      if app_id_override:
        raise ValueError('App id was provided (%s) but %s was set to true. '
                         'Please unset either %s or %s.' %
                         (datastore_app_id,
                          _DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV,
                          _DATASTORE_APP_ID_ENV,
                          _DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV))
      elif datastore_project_id:
        # Project id and app id provided, make sure they are the same.
        id_resolver = datastore_pbs.IdResolver([datastore_app_id])
        if (datastore_project_id !=
            id_resolver.resolve_project_id(datastore_app_id)):
          raise ValueError('App id "%s" does not match project id "%s".'
                           % (datastore_app_id, datastore_project_id))

    datastore_app_id = datastore_project_id or datastore_app_id
    additional_app_str = os.environ.get(_DATASTORE_ADDITIONAL_APP_IDS_ENV, '')
    additional_apps = (app.strip() for app in additional_app_str.split(','))
    return _make_cloud_datastore_context(datastore_app_id, additional_apps)
  return make_context()


@utils.positional(0)
def make_context(conn=None, config=None):
  # XXX Docstring
  from . import context  # Late import to deal with circular imports.
  return context.Context(conn=conn, config=config)


def _make_cloud_datastore_context(app_id, external_app_ids=()):
  """Creates a new context to connect to a remote Cloud Datastore instance.

  This should only be used outside of Google App Engine.

  Args:
    app_id: The application id to connect to. This differs from the project
      id as it may have an additional prefix, e.g. "s~" or "e~".
    external_app_ids: A list of apps that may be referenced by data in your
      application. For example, if you are connected to s~my-app and store keys
      for s~my-other-app, you should include s~my-other-app in the external_apps
      list.
  Returns:
    An ndb.Context that can connect to a Remote Cloud Datastore. You can use
    this context by passing it to ndb.set_context.
  """
  from . import model  # Late import to deal with circular imports.
  # Late import since it might not exist.
  if not datastore_pbs._CLOUD_DATASTORE_ENABLED:
    raise datastore_errors.BadArgumentError(
        datastore_pbs.MISSING_CLOUD_DATASTORE_MESSAGE)
  import googledatastore
  try:
    from google.appengine.datastore import cloud_datastore_v1_remote_stub
  except ImportError:
    from google3.apphosting.datastore import cloud_datastore_v1_remote_stub

  current_app_id = os.environ.get('APPLICATION_ID', None)
  if current_app_id and current_app_id != app_id:
    # TODO(pcostello): We should support this so users can connect to different
    # applications.
    raise ValueError('Cannot create a Cloud Datastore context that connects '
                     'to an application (%s) that differs from the application '
                     'already connected to (%s).' % (app_id, current_app_id))
  os.environ['APPLICATION_ID'] = app_id

  id_resolver = datastore_pbs.IdResolver((app_id,) + tuple(external_app_ids))
  project_id = id_resolver.resolve_project_id(app_id)
  endpoint = googledatastore.helper.get_project_endpoint_from_env(project_id)
  datastore = googledatastore.Datastore(
      project_endpoint=endpoint,
      credentials=googledatastore.helper.get_credentials_from_env())

  conn = model.make_connection(_api_version=datastore_rpc._CLOUD_DATASTORE_V1,
                               _id_resolver=id_resolver)

  # If necessary, install the stubs
  try:
    stub = cloud_datastore_v1_remote_stub.CloudDatastoreV1RemoteStub(datastore)
    apiproxy_stub_map.apiproxy.RegisterStub(datastore_rpc._CLOUD_DATASTORE_V1,
                                            stub)
  except:
    pass  # The stub is already installed.
  # TODO(pcostello): Ensure the current stub is connected to the right project.
  return make_context(conn=conn)


def set_context(new_context):
  # XXX Docstring
  os.environ[_CONTEXT_KEY] = '1'
  _state.current_context = new_context


# TODO: Rework the following into documentation.

# A tasklet/coroutine/generator can yield the following things:
# - Another tasklet/coroutine/generator; this is entirely equivalent to
#   "for x in g: yield x"; this is handled entirely by the @tasklet wrapper.
#   (Actually, not.  @tasklet returns a function that when called returns
#   a Future.  You can use the pep380 module's @gwrap decorator to support
#   yielding bare generators though.)
# - An RPC (or MultiRpc); the tasklet will be resumed when this completes.
#   This does not use the RPC's callback mechanism.
# - A Future; the tasklet will be resumed when the Future is done.
#   This uses the Future's callback mechanism.

# A Future can be used in several ways:
# - Yield it from a tasklet; see above.
# - Check (poll) its status via f.done.
# - Call its wait() method, perhaps indirectly via check_success()
#   or get_result().  This invokes the event loop.
# - Call the Future.wait_any() or Future.wait_all() method.
#   This is waits for any or all Futures and RPCs in the argument list.

# XXX HIRO XXX

# - A tasklet is a (generator) function decorated with @tasklet.

# - Calling a tasklet schedules the function for execution and returns a Future.

# - A function implementing a tasklet may:
#   = yield a Future; this waits for the Future which returns f.get_result();
#   = yield an RPC; this waits for the RPC and then returns rpc.get_result();
#   = raise Return(result); this sets the outer Future's result;
#   = raise StopIteration or return; this sets the outer Future's result;
#   = raise another exception: this sets the outer Future's exception.

# - If a function implementing a tasklet is not a generator it will be
#   immediately executed to completion and the tasklet wrapper will
#   return a Future that is already done.  (XXX Alternative behavior:
#   it schedules the call to be run by the event loop.)

# - Code not running in a tasklet can call f.get_result() or f.wait() on
#   a future.  This is implemented by a simple loop like the following:

#     while not self._done:
#       eventloop.run1()

# - Here eventloop.run1() runs one "atomic" part of the event loop:
#   = either it calls one immediately ready callback;
#   = or it waits for the first RPC to complete;
#   = or it sleeps until the first callback should be ready;
#   = or it raises an exception indicating all queues are empty.

# - It is possible but suboptimal to call rpc.get_result() or
#   rpc.wait() directly on an RPC object since this will not allow
#   other callbacks to run as they become ready.  Wrapping an RPC in a
#   Future will take care of this issue.

# - The important insight is that when a generator function
#   implementing a tasklet yields, raises or returns, there is always a
#   wrapper that catches this event and either turns it into a
#   callback sent to the event loop, or sets the result or exception
#   for the tasklet's Future.
