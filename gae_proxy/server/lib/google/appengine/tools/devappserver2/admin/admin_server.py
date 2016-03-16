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
"""Run a server displaying the administrative UI for the application."""



import logging

import google
import webapp2

from google.appengine.tools.devappserver2 import wsgi_server
from google.appengine.tools.devappserver2.admin import admin_request_handler
from google.appengine.tools.devappserver2.admin import blobstore_viewer
from google.appengine.tools.devappserver2.admin import console
from google.appengine.tools.devappserver2.admin import cron_handler
from google.appengine.tools.devappserver2.admin import datastore_indexes_viewer
from google.appengine.tools.devappserver2.admin import datastore_stats_handler
from google.appengine.tools.devappserver2.admin import datastore_viewer
from google.appengine.tools.devappserver2.admin import mail_request_handler
from google.appengine.tools.devappserver2.admin import memcache_viewer
from google.appengine.tools.devappserver2.admin import modules_handler
from google.appengine.tools.devappserver2.admin import quit_handler
from google.appengine.tools.devappserver2.admin import search_handler
from google.appengine.tools.devappserver2.admin import static_file_handler
from google.appengine.tools.devappserver2.admin import taskqueue_queues_handler
from google.appengine.tools.devappserver2.admin import taskqueue_tasks_handler
from google.appengine.tools.devappserver2.admin import xmpp_request_handler


class AdminApplication(webapp2.WSGIApplication):
  """A WSGI application that serves an administrative UI for the application."""

  def __init__(self, dispatch, configuration):
    """Initializer for AdminApplication.

    Args:
      dispatch: A dispatcher.Dispatcher instance used to route requests and
          provide state about running servers.
      configuration: An application_configuration.ApplicationConfiguration
          instance containing the configuration for the application.
    """
    super(AdminApplication, self).__init__(
        [('/datastore', datastore_viewer.DatastoreRequestHandler),
         ('/datastore/edit/(.*)', datastore_viewer.DatastoreEditRequestHandler),
         ('/datastore/edit', datastore_viewer.DatastoreEditRequestHandler),
         ('/datastore-indexes',
          datastore_indexes_viewer.DatastoreIndexesViewer),
         ('/datastore-stats', datastore_stats_handler.DatastoreStatsHandler),
         ('/console', console.ConsoleRequestHandler),
         ('/console/restart/(.+)', console.ConsoleRequestHandler.restart),
         ('/memcache', memcache_viewer.MemcacheViewerRequestHandler),
         ('/blobstore', blobstore_viewer.BlobstoreRequestHandler),
         ('/blobstore/blob/(.+)', blobstore_viewer.BlobRequestHandler),
         ('/taskqueue', taskqueue_queues_handler.TaskQueueQueuesHandler),
         ('/taskqueue/queue/(.+)',
          taskqueue_tasks_handler.TaskQueueTasksHandler),
         ('/cron', cron_handler.CronHandler),
         ('/xmpp', xmpp_request_handler.XmppRequestHandler),
         ('/mail', mail_request_handler.MailRequestHandler),
         ('/quit', quit_handler.QuitHandler),
         ('/search', search_handler.SearchIndexesListHandler),
         ('/search/document', search_handler.SearchDocumentHandler),
         ('/search/index', search_handler.SearchIndexHandler),
         ('/assets/(.+)', static_file_handler.StaticFileHandler),
         ('/instances', modules_handler.ModulesHandler),
         webapp2.Route('/',
                       webapp2.RedirectHandler,
                       defaults={'_uri': '/instances'})],
        debug=True)
    self.dispatcher = dispatch
    self.configuration = configuration


class AdminServer(wsgi_server.WsgiServer):
  """Serves an administrative UI for the application over HTTP."""

  def __init__(self, host, port, dispatch, configuration, xsrf_token_path):
    """Initializer for AdminServer.

    Args:
      host: A string containing the name of the host that the server should bind
          to e.g. "localhost".
      port: An int containing the port that the server should bind to e.g. 80.
      dispatch: A dispatcher.Dispatcher instance used to route requests and
          provide state about running servers.
      configuration: An application_configuration.ApplicationConfiguration
          instance containing the configuration for the application.
      xsrf_token_path: A string containing the path to a file that contains the
          XSRF configuration for the admin UI.
    """
    self._host = host
    self._xsrf_token_path = xsrf_token_path
    super(AdminServer, self).__init__((host, port),
                                      AdminApplication(dispatch, configuration))

  def start(self):
    """Start the AdminServer."""
    admin_request_handler.AdminRequestHandler.init_xsrf(self._xsrf_token_path)
    super(AdminServer, self).start()
    logging.info('Starting admin server at: http://%s:%d', self._host,
                 self.port)

  def quit(self):
    """Quits the AdminServer."""
    super(AdminServer, self).quit()
    console.ConsoleRequestHandler.quit()
