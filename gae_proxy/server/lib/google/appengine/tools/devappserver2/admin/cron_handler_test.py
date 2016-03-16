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
"""Tests for devappserver2.admin.cron_handler."""

import datetime
import traceback
import unittest

import google

import mox
import webapp2

from google.appengine.api import croninfo
from google.appengine.api import yaml_errors
from google.appengine.tools.devappserver2 import dispatcher
from google.appengine.tools.devappserver2.admin import cron_handler

CRON_INFO_EXTERNAL = croninfo.CronInfoExternal(cron=[
    croninfo.CronEntry(
        url='/foo',
        schedule='every day 00:00',
        timezone='UTC',
        description='description',
        target='version'),
    croninfo.CronEntry(
        url='/bar',
        schedule='every day 00:00',
        description='description'),
    ])


class CronHandlerTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self._pytz = cron_handler.pytz

  def tearDown(self):
    cron_handler.pytz = self._pytz
    self.mox.UnsetStubs()

  def test_post(self):
    self.mox.StubOutWithMock(cron_handler.CronHandler, 'dispatcher')
    request = webapp2.Request.blank('/cron', POST={'url': '/url'})
    response = webapp2.Response()
    handler = cron_handler.CronHandler(request, response)
    handler.dispatcher = self.mox.CreateMock(dispatcher.Dispatcher)
    handler.dispatcher.add_request(
        method='GET',
        relative_url='/url',
        headers=[('X-AppEngine-Cron', 'true')],
        body='',
        source_ip='0.1.0.1').AndReturn(
            dispatcher.ResponseTuple('500 Internal Server Error', [], ''))
    self.mox.ReplayAll()
    handler.post()
    self.mox.VerifyAll()
    self.assertEqual(500, response.status_int)

  def test_get_with_pytz(self, pytz=object()):
    cron_handler.pytz = pytz
    jobs = object()
    request = webapp2.Request.blank('/cron')
    response = webapp2.Response()
    handler = cron_handler.CronHandler(request, response)
    self.mox.StubOutWithMock(handler, '_get_cron_jobs')
    self.mox.StubOutWithMock(handler, 'render')
    handler._get_cron_jobs().AndReturn(jobs)
    handler.render('cron.html',
                   {'has_pytz': bool(pytz), 'cronjobs': jobs}).AndReturn(
                       'template')
    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()
    self.assertEqual('template', response.body)

  def test_get_without_pytz(self):
    self.test_get_with_pytz(pytz=None)

  def test_get_with_invalid_cron_yaml(self):
    cron_handler.pytz = None
    request = webapp2.Request.blank('/cron')
    response = webapp2.Response()
    handler = cron_handler.CronHandler(request, response)
    self.mox.StubOutWithMock(handler, '_get_cron_jobs')
    self.mox.StubOutWithMock(handler, 'render')
    self.mox.StubOutWithMock(traceback, 'format_exc')
    handler._get_cron_jobs().AndRaise(yaml_errors.Error)
    traceback.format_exc().AndReturn('traceback')
    handler.render(
        'cron.html',
        {'has_pytz': False, 'cron_error': 'traceback'}).AndReturn('template')
    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()
    self.assertEqual('template', response.body)

  @unittest.skipIf(cron_handler.pytz is None, 'requires pytz')
  def test_get_cron_jobs_with_pytz(self):
    handler = cron_handler.CronHandler(None, None)
    self.mox.StubOutWithMock(handler, '_parse_cron_yaml')
    handler._parse_cron_yaml().AndReturn(CRON_INFO_EXTERNAL)
    self.mox.ReplayAll()
    cron_jobs = handler._get_cron_jobs()
    self.mox.VerifyAll()
    self.assertEqual(2, len(cron_jobs))
    next_runs = [cron_jobs[0].pop('times'), cron_jobs[1].pop('times')]
    self.assertEqual(CRON_INFO_EXTERNAL.cron[0].ToDict(), cron_jobs[0])
    self.assertEqual(CRON_INFO_EXTERNAL.cron[1].ToDict(), cron_jobs[1])
    for next_run in next_runs:
      self.assertEqual(3, len(next_run))
      for run in next_run:
        datetime.datetime.strptime(run['runtime'], '%Y-%m-%d %H:%M:%SZ')

  def test_get_cron_jobs_without_pytz(self):
    cron_handler.pytz = None
    handler = cron_handler.CronHandler(None, None)
    self.mox.StubOutWithMock(handler, '_parse_cron_yaml')
    handler._parse_cron_yaml().AndReturn(CRON_INFO_EXTERNAL)
    self.mox.ReplayAll()
    cron_jobs = handler._get_cron_jobs()
    self.mox.VerifyAll()
    self.assertEqual(2, len(cron_jobs))
    self.assertEqual(CRON_INFO_EXTERNAL.cron[0].ToDict(), cron_jobs[0])
    next_run = cron_jobs[1].pop('times')
    self.assertEqual(CRON_INFO_EXTERNAL.cron[1].ToDict(), cron_jobs[1])
    self.assertEqual(3, len(next_run))
    for run in next_run:
      datetime.datetime.strptime(run['runtime'], '%Y-%m-%d %H:%M:%SZ')

  def test_get_cron_jobs_no_cron_yaml(self):
    cron_handler.pytz = None
    handler = cron_handler.CronHandler(None, None)
    self.mox.StubOutWithMock(handler, '_parse_cron_yaml')
    handler._parse_cron_yaml().AndReturn(None)
    self.mox.ReplayAll()
    self.assertEqual([], handler._get_cron_jobs())
    self.mox.VerifyAll()

if __name__ == '__main__':
  unittest.main()
