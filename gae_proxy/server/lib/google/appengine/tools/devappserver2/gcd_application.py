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
"""Cloud datastore Web Application handling."""



import getpass
import os
import shutil
import sys
import tempfile

from google.appengine.tools import sdk_update_checker
from google.appengine.tools.devappserver2 import runtime_factories


def generate_gcd_app(app_id):
  """Generates an app in tmp for a cloud datastore implementation."""
  if sys.platform == 'win32':
    # The temp directory is per-user on Windows so there is no reason to add
    # the username to the generated directory name.
    user_format = ''
  else:
    try:
      user_name = getpass.getuser()
    except Exception:  # The possible set of exceptions is not documented.
      user_format = ''
    else:
      user_format = '.%s' % user_name

  tempdir = tempfile.gettempdir()
  version = sdk_update_checker.GetVersionObject()
  sdk_version = version['release'] if version else 'unknown'
  gcd_path = os.path.join(tempdir,
                          'appengine-gcd-war.%s%s%s' % (sdk_version,
                                                        app_id, user_format))

  if not os.path.exists(gcd_path):
    os.mkdir(gcd_path)
    webinf_path = os.path.join(gcd_path, 'WEB-INF')
    os.mkdir(webinf_path)
    filter_path = os.path.join(webinf_path, 'lib')
    os.mkdir(filter_path)
    if runtime_factories.java_runtime:
      filter_jar = _get_filter_jar()
      shutil.copy(filter_jar, filter_path)

  with open(os.path.join(gcd_path, 'WEB-INF', 'web.xml'), 'w') as f:
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
<web-app version="2.5" xmlns="http://java.sun.com/xml/ns/javaee"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://java.sun.com/xml/ns/javaee
         http://java.sun.com/xml/ns/javaee/web-app_2_5.xsd">

  <security-constraint>
    <web-resource-collection>
      <web-resource-name>datastore_constraint</web-resource-name>
      <url-pattern>/datastore/*</url-pattern>
    </web-resource-collection>
    <user-data-constraint>
      <transport-guarantee>CONFIDENTIAL</transport-guarantee>
    </user-data-constraint>
  </security-constraint>

  <filter>
    <filter-name>ProtoJsonFilter</filter-name>
    <filter-class>
      com.google.apphosting.client.datastoreservice.app.filter.ProtoJsonFilter
    </filter-class>
  </filter>

  <filter-mapping>
    <filter-name>ProtoJsonFilter</filter-name>
    <url-pattern>/datastore/*</url-pattern>
  </filter-mapping>

  <servlet>
    <servlet-name>DatastoreApiServlet</servlet-name>
    <servlet-class>
      com.google.apphosting.client.datastoreservice.app.DatastoreApiServlet
    </servlet-class>
    <load-on-startup>1</load-on-startup>
  </servlet>

  <servlet-mapping>
    <servlet-name>DatastoreApiServlet</servlet-name>
    <url-pattern>/datastore/*</url-pattern>
  </servlet-mapping>

</web-app>""")

  gcd_app_xml = os.path.join(gcd_path, 'WEB-INF', 'appengine-web.xml')
  with open(gcd_app_xml, 'w') as f:
    f.write("""<?xml version="1.0" encoding="utf-8"?>
<appengine-web-app xmlns="http://appengine.google.com/ns/1.0">
  <application>%s</application>
  <version>1</version>
  <module>google-cloud-datastore</module>

  <precompilation-enabled>true</precompilation-enabled>
  <threadsafe>true</threadsafe>

</appengine-web-app>""" % app_id)

  return gcd_app_xml


def _get_filter_jar():
  """Returns the appengine-datastore-filter.jar jar location.

  Returns:
      the appengine-datastore-filter.jar jar absolute location.
  """

  java_dir = os.environ.get('APP_ENGINE_JAVA_PATH', None)
  if not java_dir:
    tools_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    java_dir = os.path.join(tools_dir, 'java')
  filter_dir = os.path.join(java_dir,
                            'lib', 'opt', 'tools', 'appengine-datastore', 'v1')
  filter_jar = os.path.join(filter_dir, 'appengine-datastore-filter.jar')
  return filter_jar

