#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
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
#
"""Tests for google.appengine.tools.devappserver2.wsgi_server."""



import errno
import json
import select
import socket
import time
import unittest
import urllib2

import google

from cherrypy import wsgiserver
import mox

from google.appengine.tools.devappserver2 import wsgi_server


class TestError(Exception):
  pass


class _SingleAddressWsgiServerTest(unittest.TestCase):
  def setUp(self):
    super(_SingleAddressWsgiServerTest, self).setUp()
    self.server = wsgi_server._SingleAddressWsgiServer(('localhost', 0),
                                                       self.wsgi_application)
    self.server.start()

  def tearDown(self):
    super(_SingleAddressWsgiServerTest, self).tearDown()
    self.server.quit()

  def test_serve(self):
    result = urllib2.urlopen('http://localhost:%d/foo?bar=baz' %
                             self.server.port)
    body = result.read()
    environ = json.loads(body)
    self.assertEqual(200, result.code)
    self.assertEqual('/foo', environ['PATH_INFO'])
    self.assertEqual('bar=baz', environ['QUERY_STRING'])

  def wsgi_application(self, environ, start_response):
    start_response('200 OK', [('Content-Type', 'application/json')])
    serializable_environ = environ.copy()
    del serializable_environ['wsgi.input']
    del serializable_environ['wsgi.errors']
    return [json.dumps(serializable_environ)]

  def other_wsgi_application(self, environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ['Hello World']

  def test_set_app(self):
    self.server.set_app(self.other_wsgi_application)
    result = urllib2.urlopen('http://localhost:%d/foo?bar=baz' %
                             self.server.port)
    body = result.read()
    self.assertEqual(200, result.code)
    self.assertEqual('Hello World', body)

  def test_set_error(self):
    self.server.set_error(204)
    result = urllib2.urlopen('http://localhost:%d/foo?bar=baz' %
                             self.server.port)
    self.assertEqual(204, result.code)


class SharedCherryPyThreadPoolTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(wsgi_server._THREAD_POOL, 'submit')
    self.thread_pool = wsgi_server._SharedCherryPyThreadPool()

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_put(self):
    connection = object()
    wsgi_server._THREAD_POOL.submit(self.thread_pool._handle, connection)
    self.mox.ReplayAll()
    self.thread_pool.put(connection)
    self.mox.VerifyAll()
    self.assertEqual(set([connection]), self.thread_pool._connections)

  def test_handle(self):
    connection = self.mox.CreateMock(wsgiserver.HTTPConnection)
    self.mox.StubOutWithMock(self.thread_pool._condition, 'notify')
    self.thread_pool._connections.add(connection)
    connection.communicate()
    connection.close()
    self.thread_pool._condition.notify()
    self.mox.ReplayAll()
    self.thread_pool._handle(connection)
    self.mox.VerifyAll()
    self.assertEqual(set(), self.thread_pool._connections)

  def test_handle_with_exception(self):
    connection = self.mox.CreateMock(wsgiserver.HTTPConnection)
    self.mox.StubOutWithMock(self.thread_pool._condition, 'notify')
    self.thread_pool._connections.add(connection)
    connection.communicate().AndRaise(TestError)
    connection.close()
    self.thread_pool._condition.notify()
    self.mox.ReplayAll()
    self.assertRaises(TestError, self.thread_pool._handle, connection)
    self.mox.VerifyAll()
    self.assertEqual(set(), self.thread_pool._connections)

  def test_stop(self):
    self.mox.ReplayAll()
    self.thread_pool.stop(3)
    self.mox.VerifyAll()

  def test_stop_no_connections(self):
    self.mox.ReplayAll()
    self.thread_pool.stop(0.1)
    self.mox.VerifyAll()

  def test_stop_with_connections(self):
    connection = self.mox.CreateMock(wsgiserver.HTTPConnection)
    self.thread_pool._connections.add(connection)
    self.mox.StubOutWithMock(self.thread_pool, '_shutdown_connection')
    self.thread_pool._shutdown_connection(connection)

    self.mox.ReplayAll()
    self.thread_pool.stop(1)
    self.mox.VerifyAll()

  def test_shutdown_connection(self):

    class DummyObect(object):
      pass

    connection = DummyObect()
    connection.rfile = DummyObect()
    connection.rfile.closed = False
    connection.socket = self.mox.CreateMockAnything()
    connection.socket.shutdown(socket.SHUT_RD)

    self.mox.ReplayAll()
    self.thread_pool._shutdown_connection(connection)
    self.mox.VerifyAll()

  def test_shutdown_connection_rfile_already_close(self):

    class DummyObect(object):
      pass

    connection = DummyObect()
    connection.rfile = DummyObect()
    connection.rfile.closed = True
    connection.socket = self.mox.CreateMockAnything()

    self.mox.ReplayAll()
    self.thread_pool._shutdown_connection(connection)
    self.mox.VerifyAll()


class SelectThreadTest(unittest.TestCase):

  class _MockSocket(object):
    def fileno(self):
      return id(self)

  def setUp(self):
    self.select_thread = wsgi_server.SelectThread()
    self.original_has_poll = wsgi_server._HAS_POLL
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(select, 'select')
    if hasattr(select, 'poll'):
      self.mox.StubOutWithMock(select, 'poll')
    self.mox.StubOutWithMock(time, 'sleep')

  def tearDown(self):
    self.mox.UnsetStubs()
    wsgi_server._HAS_POLL = self.original_has_poll

  def test_add_socket(self):
    file_descriptors = self.select_thread._file_descriptors
    file_descriptor_to_callback = (
        self.select_thread._file_descriptor_to_callback)
    file_descriptors_copy = frozenset(self.select_thread._file_descriptors)
    file_descriptor_to_callback_copy = (
        self.select_thread._file_descriptor_to_callback.copy())
    s = self._MockSocket()
    callback = object()
    self.select_thread.add_socket(s, callback)
    self.assertEqual(file_descriptors_copy, file_descriptors)
    self.assertEqual(file_descriptor_to_callback_copy,
                     file_descriptor_to_callback)
    self.assertEqual(frozenset([s.fileno()]),
                     self.select_thread._file_descriptors)
    self.assertEqual({s.fileno(): callback},
                     self.select_thread._file_descriptor_to_callback)

  def test_remove_socket(self):
    s1 = self._MockSocket()
    callback1 = object()
    s2 = self._MockSocket()
    callback2 = object()
    self.select_thread._file_descriptors = frozenset([s1.fileno(), s2.fileno()])
    self.select_thread._file_descriptor_to_callback = {
        s1.fileno(): callback1, s2.fileno(): callback2}
    file_descriptors = self.select_thread._file_descriptors
    file_descriptor_to_callback = (
        self.select_thread._file_descriptor_to_callback)
    file_descriptors_copy = frozenset(self.select_thread._file_descriptors)
    file_descriptor_to_callback_copy = (
        self.select_thread._file_descriptor_to_callback.copy())
    self.select_thread.remove_socket(s1)
    self.assertEqual(file_descriptors_copy, file_descriptors)
    self.assertEqual(file_descriptor_to_callback_copy,
                     file_descriptor_to_callback)
    self.assertEqual(frozenset([s2.fileno()]),
                     self.select_thread._file_descriptors)
    self.assertEqual({s2.fileno(): callback2},
                     self.select_thread._file_descriptor_to_callback)

  def test_select_no_sockets(self):
    time.sleep(1)
    self.mox.ReplayAll()
    self.select_thread._select()
    self.mox.VerifyAll()

  def test_select_no_poll(self):
    wsgi_server._HAS_POLL = False
    s = self._MockSocket()
    callback = self.mox.CreateMockAnything()
    select.select(frozenset([s.fileno()]), [], [], 1).AndReturn(
        ([s.fileno()], [], []))
    callback()
    self.mox.ReplayAll()
    self.select_thread.add_socket(s, callback)
    self.select_thread._select()
    self.mox.VerifyAll()

  @unittest.skipUnless(wsgi_server._HAS_POLL, 'requires select.poll')
  def test_select_with_poll(self):
    s = self._MockSocket()
    callback = self.mox.CreateMockAnything()
    poll = self.mox.CreateMockAnything()

    select.poll().AndReturn(poll)
    poll.register(s.fileno(), select.POLLIN)
    poll.poll(1000).AndReturn([(s.fileno(), select.POLLIN)])

    callback()
    self.mox.ReplayAll()
    self.select_thread.add_socket(s, callback)
    self.select_thread._select()
    self.mox.VerifyAll()

  def test_select_not_ready_no_poll(self):
    wsgi_server._HAS_POLL = False
    s = self._MockSocket()
    callback = self.mox.CreateMockAnything()
    select.select(frozenset([s.fileno()]), [], [], 1).AndReturn(([], [], []))
    self.mox.ReplayAll()
    self.select_thread.add_socket(s, callback)
    self.select_thread._select()
    self.mox.VerifyAll()

  @unittest.skipUnless(wsgi_server._HAS_POLL, 'requires select.poll')
  def test_select_not_ready_with_poll(self):
    s = self._MockSocket()
    callback = self.mox.CreateMockAnything()
    poll = self.mox.CreateMockAnything()

    select.poll().AndReturn(poll)
    poll.register(s.fileno(), select.POLLIN)
    poll.poll(1000).AndReturn([])

    self.mox.ReplayAll()
    self.select_thread.add_socket(s, callback)
    self.select_thread._select()
    self.mox.VerifyAll()


class WsgiServerStartupTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.server = wsgi_server.WsgiServer(('localhost', 123), None)

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_start_some_fail_to_bind(self):
    failing_server = self.mox.CreateMock(
        wsgi_server._SingleAddressWsgiServer)
    starting_server = self.mox.CreateMock(
        wsgi_server._SingleAddressWsgiServer)
    another_starting_server = self.mox.CreateMock(
        wsgi_server._SingleAddressWsgiServer)
    self.mox.StubOutWithMock(wsgi_server, '_SingleAddressWsgiServer')
    self.mox.StubOutWithMock(socket, 'getaddrinfo')
    socket.getaddrinfo('localhost', 123, socket.AF_UNSPEC, socket.SOCK_STREAM,
                       0, socket.AI_PASSIVE).AndReturn(
                           [(None, None, None, None, ('foo', 'bar', 'baz')),
                            (None, None, None, None, (1, 2, 3, 4, 5)),
                            (None, None, None, None, (3, 4))])
    wsgi_server._SingleAddressWsgiServer(('foo', 'bar'), None).AndReturn(
        failing_server)
    wsgi_server._SingleAddressWsgiServer((1, 2), None).AndReturn(
        starting_server)
    wsgi_server._SingleAddressWsgiServer((3, 4), None).AndReturn(
        another_starting_server)
    starting_server.start()
    failing_server.start().AndRaise(wsgi_server.BindError)
    another_starting_server.start()

    self.mox.ReplayAll()
    self.server.start()
    self.mox.VerifyAll()
    self.assertItemsEqual([starting_server, another_starting_server],
                          self.server._servers)

  def test_start_all_fail_to_bind(self):
    failing_server = self.mox.CreateMock(
        wsgi_server._SingleAddressWsgiServer)
    self.mox.StubOutWithMock(wsgi_server, '_SingleAddressWsgiServer')
    self.mox.StubOutWithMock(socket, 'getaddrinfo')
    socket.getaddrinfo('localhost', 123, socket.AF_UNSPEC, socket.SOCK_STREAM,
                       0, socket.AI_PASSIVE).AndReturn(
                           [(None, None, None, None, ('foo', 'bar', 'baz'))])
    wsgi_server._SingleAddressWsgiServer(('foo', 'bar'), None).AndReturn(
        failing_server)
    failing_server.start().AndRaise(wsgi_server.BindError)

    self.mox.ReplayAll()
    self.assertRaises(wsgi_server.BindError, self.server.start)
    self.mox.VerifyAll()

  def test_remove_duplicates(self):
    foo_server = self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
    foo2_server = self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
    self.mox.StubOutWithMock(wsgi_server, '_SingleAddressWsgiServer')
    self.mox.StubOutWithMock(socket, 'getaddrinfo')
    socket.getaddrinfo('localhost', 123, socket.AF_UNSPEC, socket.SOCK_STREAM,
                       0, socket.AI_PASSIVE).AndReturn(
                           [(0, 0, 0, '', ('127.0.0.1', 123)),
                            (0, 0, 0, '', ('::1', 123, 0, 0)),
                            (0, 0, 0, '', ('127.0.0.1', 123))])
    wsgi_server._SingleAddressWsgiServer(('127.0.0.1', 123), None).AndReturn(
        foo_server)
    foo_server.start()
    wsgi_server._SingleAddressWsgiServer(('::1', 123), None).AndReturn(
        foo2_server)
    foo2_server.start()

    self.mox.ReplayAll()
    self.server.start()
    self.mox.VerifyAll()

  def test_quit(self):
    running_server = self.mox.CreateMock(
        wsgi_server._SingleAddressWsgiServer)
    self.server._servers = [running_server]
    running_server.quit()
    self.mox.ReplayAll()
    self.server.quit()
    self.mox.VerifyAll()


class WsgiServerPort0StartupTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.server = wsgi_server.WsgiServer(('localhost', 0), None)

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_basic_behavior(self):
    inet4_server = self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
    inet6_server = self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
    self.mox.StubOutWithMock(wsgi_server, '_SingleAddressWsgiServer')
    self.mox.StubOutWithMock(socket, 'getaddrinfo')
    socket.getaddrinfo('localhost', 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
                       socket.AI_PASSIVE).AndReturn(
                           [(None, None, None, None, ('127.0.0.1', 0, 'baz')),
                            (None, None, None, None, ('::1', 0, 'baz'))])
    wsgi_server._SingleAddressWsgiServer(('127.0.0.1', 0), None).AndReturn(
        inet4_server)
    inet4_server.start()
    inet4_server.port = 123
    wsgi_server._SingleAddressWsgiServer(('::1', 123), None).AndReturn(
        inet6_server)
    inet6_server.start()
    self.mox.ReplayAll()
    self.server.start()
    self.mox.VerifyAll()
    self.assertItemsEqual([inet4_server, inet6_server],
                          self.server._servers)

  def test_retry_eaddrinuse(self):
    inet4_server = self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
    inet6_server = self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
    inet4_server_retry = self.mox.CreateMock(
        wsgi_server._SingleAddressWsgiServer)
    inet6_server_retry = self.mox.CreateMock(
        wsgi_server._SingleAddressWsgiServer)
    self.mox.StubOutWithMock(wsgi_server, '_SingleAddressWsgiServer')
    self.mox.StubOutWithMock(socket, 'getaddrinfo')
    socket.getaddrinfo('localhost', 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
                       socket.AI_PASSIVE).AndReturn(
                           [(None, None, None, None, ('127.0.0.1', 0, 'baz')),
                            (None, None, None, None, ('::1', 0, 'baz'))])
    # First try
    wsgi_server._SingleAddressWsgiServer(('127.0.0.1', 0), None).AndReturn(
        inet4_server)
    inet4_server.start()
    inet4_server.port = 123
    wsgi_server._SingleAddressWsgiServer(('::1', 123), None).AndReturn(
        inet6_server)
    inet6_server.start().AndRaise(
        wsgi_server.BindError('message', (errno.EADDRINUSE, 'in use')))
    inet4_server.quit()
    # Retry
    wsgi_server._SingleAddressWsgiServer(('127.0.0.1', 0), None).AndReturn(
        inet4_server_retry)
    inet4_server_retry.start()
    inet4_server_retry.port = 456
    wsgi_server._SingleAddressWsgiServer(('::1', 456), None).AndReturn(
        inet6_server_retry)
    inet6_server_retry.start()
    self.mox.ReplayAll()
    self.server.start()
    self.mox.VerifyAll()
    self.assertItemsEqual([inet4_server_retry, inet6_server_retry],
                          self.server._servers)

  def test_retry_limited(self):
    inet4_servers = [self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
                     for _ in range(wsgi_server._PORT_0_RETRIES)]
    inet6_servers = [self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
                     for _ in range(wsgi_server._PORT_0_RETRIES)]
    self.mox.StubOutWithMock(wsgi_server, '_SingleAddressWsgiServer')
    self.mox.StubOutWithMock(socket, 'getaddrinfo')
    socket.getaddrinfo('localhost', 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
                       socket.AI_PASSIVE).AndReturn(
                           [(None, None, None, None, ('127.0.0.1', 0, 'baz')),
                            (None, None, None, None, ('::1', 0, 'baz'))])
    for offset, (inet4_server, inet6_server) in enumerate(zip(
        inet4_servers, inet6_servers)):
      wsgi_server._SingleAddressWsgiServer(('127.0.0.1', 0), None).AndReturn(
          inet4_server)
      inet4_server.start()
      inet4_server.port = offset + 1
      wsgi_server._SingleAddressWsgiServer(('::1', offset + 1), None).AndReturn(
          inet6_server)
      inet6_server.start().AndRaise(
          wsgi_server.BindError('message', (errno.EADDRINUSE, 'in use')))
      inet4_server.quit()
    self.mox.ReplayAll()
    self.assertRaises(wsgi_server.BindError, self.server.start)
    self.mox.VerifyAll()

  def test_ignore_other_errors(self):
    inet4_server = self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
    inet6_server = self.mox.CreateMock(wsgi_server._SingleAddressWsgiServer)
    self.mox.StubOutWithMock(wsgi_server, '_SingleAddressWsgiServer')
    self.mox.StubOutWithMock(socket, 'getaddrinfo')
    socket.getaddrinfo('localhost', 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
                       socket.AI_PASSIVE).AndReturn(
                           [(None, None, None, None, ('127.0.0.1', 0, 'baz')),
                            (None, None, None, None, ('::1', 0, 'baz'))])
    wsgi_server._SingleAddressWsgiServer(('127.0.0.1', 0), None).AndReturn(
        inet4_server)
    inet4_server.start()
    inet4_server.port = 123
    wsgi_server._SingleAddressWsgiServer(('::1', 123), None).AndReturn(
        inet6_server)
    inet6_server.start().AndRaise(
        wsgi_server.BindError('message', (errno.ENOPROTOOPT, 'no protocol')))
    self.mox.ReplayAll()
    self.server.start()
    self.mox.VerifyAll()
    self.assertItemsEqual([inet4_server],
                          self.server._servers)


class _SingleAddressWsgiServerStartupTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.server = wsgi_server._SingleAddressWsgiServer(('localhost', 0), None)

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_start_port_in_use(self):
    self.mox.StubOutWithMock(socket, 'getaddrinfo')
    self.mox.StubOutWithMock(self.server, 'bind')
    af = object()
    socktype = object()
    proto = object()
    socket.getaddrinfo('localhost', 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
                       socket.AI_PASSIVE).AndReturn(
                           [(af, socktype, proto, None, None)])
    self.server.bind(af, socktype, proto).AndRaise(socket.error)
    self.mox.ReplayAll()
    self.assertRaises(wsgi_server.BindError, self.server.start)
    self.mox.VerifyAll()

  def test_start(self):
    # Ensure no CherryPy thread pools are started.
    self.mox.StubOutWithMock(wsgiserver.ThreadPool, 'start')
    self.mox.StubOutWithMock(wsgi_server._SELECT_THREAD, 'add_socket')
    wsgi_server._SELECT_THREAD.add_socket(mox.IsA(socket.socket),
                                          self.server.tick)
    self.mox.ReplayAll()
    self.server.start()
    self.mox.VerifyAll()

  def test_quit(self):
    self.mox.StubOutWithMock(wsgi_server._SELECT_THREAD, 'remove_socket')
    self.server.socket = object()
    self.server.requests = self.mox.CreateMock(
        wsgi_server._SharedCherryPyThreadPool)
    wsgi_server._SELECT_THREAD.remove_socket(self.server.socket)
    self.server.requests.stop(timeout=1)
    self.mox.ReplayAll()
    self.server.quit()
    self.mox.VerifyAll()

if __name__ == '__main__':
  unittest.main()
