# Copyright 2015 Google Inc.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for the Django web framework

Provides Django views and helpers the make using the OAuth2 web server
flow easier. It includes an ``oauth_required`` decorator to automatically ensure
that user credentials are available, and an ``oauth_enabled`` decorator to check
if the user has authorized, and helper shortcuts to create the authorization
URL otherwise.


Configuration
=============

To configure, you'll need a set of OAuth2 web application credentials from
`Google Developer's Console <https://console.developers.google.com/project/_/apiui/credential>`.

Add the helper to your INSTALLED_APPS:

.. code-block:: python
   :caption: settings.py
   :name: installed_apps

    INSTALLED_APPS = (
        # other apps
        "oauth2client.contrib.django_util"
    )

Add the client secrets created earlier to the settings. You can either
specify the path to the credentials file in JSON format

.. code-block:: python
   :caption:  settings.py
   :name: secrets_file

   GOOGLE_OAUTH2_CLIENT_SECRETS_JSON=/path/to/client-secret.json

Or, directly configure the client Id and client secret.


.. code-block:: python
   :caption: settings.py
   :name: secrets_config

   GOOGLE_OAUTH2_CLIENT_ID=client-id-field
   GOOGLE_OAUTH2_CLIENT_SECRET=client-secret-field

By default, the default scopes for the required decorator only contains the
``email`` scopes. You can change that default in the settings.

.. code-block:: python
   :caption: settings.py
   :name: scopes

   GOOGLE_OAUTH2_SCOPES = ('email', 'https://www.googleapis.com/auth/calendar',)

By default, the decorators will add an `oauth` object to the Django request
object, and include all of its state and helpers inside that object. If the
`oauth` name conflicts with another usage, it can be changed

.. code-block:: python
   :caption: settings.py
   :name: request_prefix

   # changes request.oauth to request.google_oauth
   GOOGLE_OAUTH2_REQUEST_ATTRIBUTE = 'google_oauth'

Add the oauth2 routes to your application's urls.py urlpatterns.

.. code-block:: python
   :caption: urls.py
   :name: urls

   from oauth2client.contrib.django_util.site import urls as oauth2_urls

   urlpatterns += [url(r'^oauth2/', include(oauth2_urls))]

To require OAuth2 credentials for a view, use the `oauth2_required` decorator.
This creates a credentials object with an id_token, and allows you to create an
`http` object to build service clients with. These are all attached to the
request.oauth

.. code-block:: python
   :caption: views.py
   :name: views_required

   from oauth2client.contrib.django_util.decorators import oauth_required

   @oauth_required
   def requires_default_scopes(request):
      email = request.oauth.credentials.id_token['email']
      service = build(serviceName='calendar', version='v3',
                    http=request.oauth.http,
                   developerKey=API_KEY)
      events = service.events().list(calendarId='primary').execute()['items']
      return HttpResponse("email: %s , calendar: %s" % (email, str(events)))

To make OAuth2 optional and provide an authorization link in your own views.

.. code-block:: python
   :caption: views.py
   :name: views_enabled2

   from oauth2client.contrib.django_util.decorators import oauth_enabled

   @oauth_enabled
   def optional_oauth2(request):
       if request.oauth.has_credentials():
           # this could be passed into a view
           # request.oauth.http is also initialized
           return HttpResponse("User email: %s"
            % request.oauth.credentials.id_token['email'])
       else:
           return HttpResponse('Here is an OAuth Authorize link:
           <a href="%s">Authorize</a>' % request.oauth.get_authorize_redirect())

If a view needs a scope not included in the default scopes specified in
the settings, you can use [incremental auth](https://developers.google.com/identity/sign-in/web/incremental-auth)
and specify additional scopes in the decorator arguments.

.. code-block:: python
   :caption: views.py
   :name: views_required_additional_scopes

   @oauth_enabled(scopes=['https://www.googleapis.com/auth/drive'])
   def drive_required(request):
       if request.oauth.has_credentials():
           service = build(serviceName='drive', version='v2',
                http=request.oauth.http,
                developerKey=API_KEY)
           events = service.files().list().execute()['items']
           return HttpResponse(str(events))
       else:
           return HttpResponse('Here is an OAuth Authorize link:
           <a href="%s">Authorize</a>' % request.oauth.get_authorize_redirect())


To provide a callback on authorization being completed, use the
oauth2_authorized signal:

.. code-block:: python
   :caption: views.py
   :name: signals

   from oauth2client.contrib.django_util.signals import oauth2_authorized

   def test_callback(sender, request, credentials, **kwargs):
       print "Authorization Signal Received %s" % credentials.id_token['email']

   oauth2_authorized.connect(test_callback)

"""

import django.conf
from django.core import exceptions
from django.core import urlresolvers
import httplib2
from oauth2client import clientsecrets
from oauth2client.contrib.django_util import storage
from six.moves.urllib import parse

GOOGLE_OAUTH2_DEFAULT_SCOPES = ('email',)
GOOGLE_OAUTH2_REQUEST_ATTRIBUTE = 'oauth'


def _load_client_secrets(filename):
    """Loads client secrets from the given filename."""
    client_type, client_info = clientsecrets.loadfile(filename)

    if client_type != clientsecrets.TYPE_WEB:
        raise ValueError(
            'The flow specified in {} is not supported, only the WEB flow '
            'type  is supported.'.format(client_type))
    return client_info['client_id'], client_info['client_secret']


def _get_oauth2_client_id_and_secret(settings_instance):
    """Initializes client id and client secret based on the settings"""
    secret_json = getattr(django.conf.settings,
                          'GOOGLE_OAUTH2_CLIENT_SECRETS_JSON', None)
    if secret_json is not None:
        return _load_client_secrets(secret_json)
    else:
        client_id = getattr(settings_instance, "GOOGLE_OAUTH2_CLIENT_ID",
                            None)
        client_secret = getattr(settings_instance,
                                "GOOGLE_OAUTH2_CLIENT_SECRET", None)
        if client_id is not None and client_secret is not None:
            return client_id, client_secret
        else:
            raise exceptions.ImproperlyConfigured(
                "Must specify either GOOGLE_OAUTH2_CLIENT_SECRETS_JSON, or  "
                " both GOOGLE_OAUTH2_CLIENT_ID and GOOGLE_OAUTH2_CLIENT_SECRET "
                "in settings.py")


class OAuth2Settings(object):
    """Initializes Django OAuth2 Helper Settings

    This class loads the OAuth2 Settings from the Django settings, and then
    provides those settings as attributes to the rest of the views and
    decorators in the module.

    Attributes:
      scopes: A list of OAuth2 scopes that the decorators and views will use
              as defaults
      request_prefix: The name of the attribute that the decorators use to
                    attach the UserOAuth2 object to the Django request object.
      client_id: The OAuth2 Client ID
      client_secret: The OAuth2 Client Secret
    """

    def __init__(self, settings_instance):
        self.scopes = getattr(settings_instance, 'GOOGLE_OAUTH2_SCOPES',
                              GOOGLE_OAUTH2_DEFAULT_SCOPES)
        self.request_prefix = getattr(settings_instance,
                                      'GOOGLE_OAUTH2_REQUEST_ATTRIBUTE',
                                      GOOGLE_OAUTH2_REQUEST_ATTRIBUTE)
        self.client_id, self.client_secret = \
            _get_oauth2_client_id_and_secret(settings_instance)

        if ('django.contrib.sessions.middleware.SessionMiddleware'
                not in settings_instance.MIDDLEWARE_CLASSES):
            raise exceptions.ImproperlyConfigured(
                "The Google OAuth2 Helper requires session middleware to "
                "be installed. Edit your MIDDLEWARE_CLASSES setting"
                " to include 'django.contrib.sessions.middleware."
                "SessionMiddleware'.")


oauth2_settings = OAuth2Settings(django.conf.settings)


def _redirect_with_params(url_name, *args, **kwargs):
    """Helper method to create a redirect response that uses GET URL
    parameters."""

    url = urlresolvers.reverse(url_name, args=args)
    params = parse.urlencode(kwargs, True)
    return "{0}?{1}".format(url, params)


class UserOAuth2(object):
    """Class to create oauth2 objects on Django request objects containing
    credentials and helper methods.
    """

    def __init__(self, request, scopes=None, return_url=None):
        """Initialize the Oauth2 Object
        :param request: Django request object
        :param scopes: Scopes desired for this OAuth2 flow
        :param return_url: URL to return to after authorization is complete
        :return:
        """
        self.request = request
        self.return_url = return_url or request.get_full_path()
        self.scopes = set(oauth2_settings.scopes)
        if scopes:
            self.scopes |= set(scopes)

        # make sure previously requested custom scopes are maintained
        # in future authorizations
        credentials = storage.get_storage(self.request).get()
        if credentials:
            self.scopes |= credentials.scopes

    def get_authorize_redirect(self):
        """Creates a URl to start the OAuth2 authorization flow"""
        get_params = {
            'return_url': self.return_url,
            'scopes': self.scopes
        }

        return _redirect_with_params('google_oauth:authorize',
                                     **get_params)

    def has_credentials(self):
        """Returns True if there are valid credentials for the current user
        and required scopes."""
        return (self.credentials and not self.credentials.invalid
                and self.credentials.has_scopes(self.scopes))

    @property
    def credentials(self):
        """Gets the authorized credentials for this flow, if they exist"""
        return storage.get_storage(self.request).get()

    @property
    def http(self):
        """Helper method to create an HTTP client authorized with OAuth2
        credentials"""
        if self.has_credentials():
            return self.credentials.authorize(httplib2.Http())
        return None
