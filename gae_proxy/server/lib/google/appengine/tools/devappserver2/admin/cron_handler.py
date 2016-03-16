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
"""A handler that allows the user to see and test cron tasks."""

import datetime
import os.path
import traceback

from google.appengine.cron import groctimespecification
from google.appengine.api import croninfo
from google.appengine.api import yaml_errors
from google.appengine.tools.devappserver2.admin import admin_request_handler

try:
  import pytz
except ImportError:
  pytz = None

REMOTE_IP = '0.1.0.1'


class CronHandler(admin_request_handler.AdminRequestHandler):

  def get(self):
    values = {}
    values['has_pytz'] = bool(pytz)
    try:
      values['cronjobs'] = self._get_cron_jobs()
    except (StandardError, yaml_errors.Error):
      values['cron_error'] = traceback.format_exc()
    self.response.write(self.render('cron.html', values))

  def _get_cron_jobs(self):
    cron_info = self._parse_cron_yaml()
    if not cron_info or not cron_info.cron:
      return []
    jobs = []
    for entry in cron_info.cron:
      job = entry.ToDict()
      if not entry.timezone or pytz:
        now = datetime.datetime.utcnow()
        schedule = groctimespecification.GrocTimeSpecification(
            entry.schedule, entry.timezone)
        matches = schedule.GetMatches(now, 3)
        job['times'] = []
        for match in matches:
          job['times'].append(
              {'runtime': match.strftime('%Y-%m-%d %H:%M:%SZ'),
               'difference': str(match - now)})
      jobs.append(job)
    return jobs

  def _parse_cron_yaml(self):
    """Loads the cron.yaml file and parses it.

    Returns:
      A croninfo.CronInfoExternal containing cron jobs.

    Raises:
      yaml_errors.Error, StandardError: The cron.yaml was invalid.
    """
    for cron_yaml in ('cron.yaml', 'cron.yml'):
      try:
        with open(os.path.join(self.configuration.modules[0].application_root,
                               cron_yaml)) as f:
          cron_info = croninfo.LoadSingleCron(f)
          return cron_info
      except IOError:
        continue
    return None

  def post(self):
    self.response.status = self.dispatcher.add_request(
        method='GET',
        relative_url=self.request.get('url'),
        headers=[('X-AppEngine-Cron', 'true')],
        body='',
        source_ip=REMOTE_IP).status
