# Copyright 2015 Google Inc.  All rights reserved.
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

"""Utilities for the Flask web framework

Provides a Flask extension that makes using OAuth2 web server flow easier.
The extension includes views that handle the entire auth flow and a
``@required`` decorator to automatically ensure that user credentials are
available.


Configuration
=============

To configure, you'll need a set of OAuth2 web application credentials from the
`Google Developer's Console <https://console.developers.google.com/project/_/\
apiui/credential>`__.

.. code-block:: python

    from oauth2client.contrib.flask_util import UserOAuth2

    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'your-secret-key'

    app.config['GOOGLE_OAUTH2_CLIENT_SECRETS_JSON'] = 'client_secrets.json'

    # or, specify the client id and secret separately
    app.config['GOOGLE_OAUTH2_CLIENT_ID'] = 'your-client-id'
    app.config['GOOGLE_OAUTH2_CLIENT_SECRET'] = 'your-client-secret'

    oauth2 = UserOAuth2(app)


Usage
=====

Once configured, you can use the :meth:`UserOAuth2.required` decorator to
ensure that credentials are available within a view.

.. code-block:: python
   :emphasize-lines: 3,7,10

    # Note that app.route should be the outermost decorator.
    @app.route('/needs_credentials')
    @oauth2.required
    def example():
        # http is authorized with the user's credentials and can be used
        # to make http calls.
        http = oauth2.http()

        # Or, you can access the credentials directly
        credentials = oauth2.credentials

If you want credentials to be optional for a view, you can leave the decorator
off and use :meth:`UserOAuth2.has_credentials` to check.

.. code-block:: python
   :emphasize-lines: 3

    @app.route('/optional')
    def optional():
        if oauth2.has_credentials():
            return 'Credentials found!'
        else:
            return 'No credentials!'


When credentials are available, you can use :attr:`UserOAuth2.email` and
:attr:`UserOAuth2.user_id` to access information from the `ID Token
<https://developers.google.com/identity/protocols/OpenIDConnect?hl=en>`__, if
available.

.. code-block:: python
   :emphasize-lines: 4

    @app.route('/info')
    @oauth2.required
    def info():
        return "Hello, {} ({})".format(oauth2.email, oauth2.user_id)


URLs & Trigging Authorization
=============================

The extension will add two new routes to your application:

    * ``"oauth2.authorize"`` -> ``/oauth2authorize``
    * ``"oauth2.callback"`` -> ``/oauth2callback``

When configuring your OAuth2 credentials on the Google Developer's Console, be
sure to add ``http[s]://[your-app-url]/oauth2callback`` as an authorized
callback url.

Typically you don't not need to use these routes directly, just be sure to
decorate any views that require credentials with ``@oauth2.required``. If
needed, you can trigger authorization at any time by redirecting the user
to the URL returned by :meth:`UserOAuth2.authorize_url`.

.. code-block:: python
   :emphasize-lines: 3

    @app.route('/login')
    def login():
        return oauth2.authorize_url("/")


Incremental Auth
================

This extension also supports `Incremental Auth <https://developers.google.com\
/identity/protocols/OAuth2WebServer?hl=en#incrementalAuth>`__. To enable it,
configure the extension with ``include_granted_scopes``.

.. code-block:: python

    oauth2 = UserOAuth2(app, include_granted_scopes=True)

Then specify any additional scopes needed on the decorator, for example:

.. code-block:: python
   :emphasize-lines: 2,7

    @app.route('/drive')
    @oauth2.required(scopes=["https://www.googleapis.com/auth/drive"])
    def requires_drive():
        ...

    @app.route('/calendar')
    @oauth2.required(scopes=["https://www.googleapis.com/auth/calendar"])
    def requires_calendar():
        ...

The decorator will ensure that the the user has authorized all specified scopes
before allowing them to access the view, and will also ensure that credentials
do not lose any previously authorized scopes.


Storage
=======

By default, the extension uses a Flask session-based storage solution. This
means that credentials are only available for the duration of a session. It
also means that with Flask's default configuration, the credentials will be
visible in the session cookie. It's highly recommended to use database-backed
session and to use https whenever handling user credentials.

If you need the credentials to be available longer than a user session or
available outside of a request context, you will need to implement your own
:class:`oauth2client.Storage`.
"""

import hashlib
import json
import os
import pickle
from functools import wraps

import six.moves.http_client as httplib
import httplib2

try:
    from flask import Blueprint
    from flask import _app_ctx_stack
    from flask import current_app
    from flask import redirect
    from flask import request
    from flask import session
    from flask import url_for
except ImportError:  # pragma: NO COVER
    raise ImportError('The flask utilities require flask 0.9 or newer.')

from oauth2client.client import FlowExchangeError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.contrib.dictionary_storage import DictionaryStorage
from oauth2client import clientsecrets


__author__ = 'jonwayne@google.com (Jon Wayne Parrott)'

_DEFAULT_SCOPES = ('email',)
_CREDENTIALS_KEY = 'google_oauth2_credentials'
_FLOW_KEY = 'google_oauth2_flow_{0}'
_CSRF_KEY = 'google_oauth2_csrf_token'


def _get_flow_for_token(csrf_token):
    """Retrieves the flow instance associated with a given CSRF token from
    the Flask session."""
    flow_pickle = session.get(
        _FLOW_KEY.format(csrf_token), None)

    if flow_pickle is None:
        return None
    else:
        return pickle.loads(flow_pickle)


class UserOAuth2(object):
    """Flask extension for making OAuth 2.0 easier.

    Configuration values:

        * ``GOOGLE_OAUTH2_CLIENT_SECRETS_JSON`` path to a client secrets json
          file, obtained from the credentials screen in the Google Developers
          console.
        * ``GOOGLE_OAUTH2_CLIENT_ID`` the oauth2 credentials' client ID. This
          is only needed if ``GOOGLE_OAUTH2_CLIENT_SECRETS_JSON`` is not
          specified.
        * ``GOOGLE_OAUTH2_CLIENT_SECRET`` the oauth2 credentials' client
          secret. This is only needed if ``GOOGLE_OAUTH2_CLIENT_SECRETS_JSON``
          is not specified.

    If app is specified, all arguments will be passed along to init_app.

    If no app is specified, then you should call init_app in your application
    factory to finish initialization.
    """

    def __init__(self, app=None, *args, **kwargs):
        self.app = app
        if app is not None:
            self.init_app(app, *args, **kwargs)

    def init_app(self, app, scopes=None, client_secrets_file=None,
                 client_id=None, client_secret=None, authorize_callback=None,
                 storage=None, **kwargs):
        """Initialize this extension for the given app.

        Arguments:
            app: A Flask application.
            scopes: Optional list of scopes to authorize.
            client_secrets_file: Path to a file containing client secrets. You
                can also specify the GOOGLE_OAUTH2_CLIENT_SECRETS_JSON config
                value.
            client_id: If not specifying a client secrets file, specify the
                OAuth2 client id. You can also specify the
                GOOGLE_OAUTH2_CLIENT_ID config value. You must also provide a
                client secret.
            client_secret: The OAuth2 client secret. You can also specify the
                GOOGLE_OAUTH2_CLIENT_SECRET config value.
            authorize_callback: A function that is executed after successful
                user authorization.
            storage: A oauth2client.client.Storage subclass for storing the
                credentials. By default, this is a Flask session based storage.
            kwargs: Any additional args are passed along to the Flow
                constructor.
        """
        self.app = app
        self.authorize_callback = authorize_callback
        self.flow_kwargs = kwargs

        if storage is None:
            storage = DictionaryStorage(session, key=_CREDENTIALS_KEY)
        self.storage = storage

        if scopes is None:
            scopes = app.config.get('GOOGLE_OAUTH2_SCOPES', _DEFAULT_SCOPES)
        self.scopes = scopes

        self._load_config(client_secrets_file, client_id, client_secret)

        app.register_blueprint(self._create_blueprint())

    def _load_config(self, client_secrets_file, client_id, client_secret):
        """Loads oauth2 configuration in order of priority.

        Priority:
            1. Config passed to the constructor or init_app.
            2. Config passed via the GOOGLE_OAUTH2_CLIENT_SECRETS_FILE app
               config.
            3. Config passed via the GOOGLE_OAUTH2_CLIENT_ID and
               GOOGLE_OAUTH2_CLIENT_SECRET app config.

        Raises:
            ValueError if no config could be found.
        """
        if client_id and client_secret:
            self.client_id, self.client_secret = client_id, client_secret
            return

        if client_secrets_file:
            self._load_client_secrets(client_secrets_file)
            return

        if 'GOOGLE_OAUTH2_CLIENT_SECRETS_FILE' in self.app.config:
            self._load_client_secrets(
                self.app.config['GOOGLE_OAUTH2_CLIENT_SECRETS_FILE'])
            return

        try:
            self.client_id, self.client_secret = (
                self.app.config['GOOGLE_OAUTH2_CLIENT_ID'],
                self.app.config['GOOGLE_OAUTH2_CLIENT_SECRET'])
        except KeyError:
            raise ValueError(
                'OAuth2 configuration could not be found. Either specify the '
                'client_secrets_file or client_id and client_secret or set the'
                'app configuration variables '
                'GOOGLE_OAUTH2_CLIENT_SECRETS_FILE or '
                'GOOGLE_OAUTH2_CLIENT_ID and GOOGLE_OAUTH2_CLIENT_SECRET.')

    def _load_client_secrets(self, filename):
        """Loads client secrets from the given filename."""
        client_type, client_info = clientsecrets.loadfile(filename)
        if client_type != clientsecrets.TYPE_WEB:
            raise ValueError(
                'The flow specified in {0} is not supported.'.format(
                    client_type))

        self.client_id = client_info['client_id']
        self.client_secret = client_info['client_secret']

    def _make_flow(self, return_url=None, **kwargs):
        """Creates a Web Server Flow"""
        # Generate a CSRF token to prevent malicious requests.
        csrf_token = hashlib.sha256(os.urandom(1024)).hexdigest()

        session[_CSRF_KEY] = csrf_token

        state = json.dumps({
            'csrf_token': csrf_token,
            'return_url': return_url
        })

        kw = self.flow_kwargs.copy()
        kw.update(kwargs)

        extra_scopes = kw.pop('scopes', [])
        scopes = set(self.scopes).union(set(extra_scopes))

        flow = OAuth2WebServerFlow(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=scopes,
            state=state,
            redirect_uri=url_for('oauth2.callback', _external=True),
            **kw)

        flow_key = _FLOW_KEY.format(csrf_token)
        session[flow_key] = pickle.dumps(flow)

        return flow

    def _create_blueprint(self):
        bp = Blueprint('oauth2', __name__)
        bp.add_url_rule('/oauth2authorize', 'authorize', self.authorize_view)
        bp.add_url_rule('/oauth2callback', 'callback', self.callback_view)

        return bp

    def authorize_view(self):
        """Flask view that starts the authorization flow.

        Starts flow by redirecting the user to the OAuth2 provider.
        """
        args = request.args.to_dict()

        # Scopes will be passed as mutliple args, and to_dict() will only
        # return one. So, we use getlist() to get all of the scopes.
        args['scopes'] = request.args.getlist('scopes')

        return_url = args.pop('return_url', None)
        if return_url is None:
            return_url = request.referrer or '/'

        flow = self._make_flow(return_url=return_url, **args)
        auth_url = flow.step1_get_authorize_url()

        return redirect(auth_url)

    def callback_view(self):
        """Flask view that handles the user's return from OAuth2 provider.

        On return, exchanges the authorization code for credentials and stores
        the credentials.
        """
        if 'error' in request.args:
            reason = request.args.get(
                'error_description', request.args.get('error', ''))
            return ('Authorization failed: {0}'.format(reason),
                    httplib.BAD_REQUEST)

        try:
            encoded_state = request.args['state']
            server_csrf = session[_CSRF_KEY]
            code = request.args['code']
        except KeyError:
            return 'Invalid request', httplib.BAD_REQUEST

        try:
            state = json.loads(encoded_state)
            client_csrf = state['csrf_token']
            return_url = state['return_url']
        except (ValueError, KeyError):
            return 'Invalid request state', httplib.BAD_REQUEST

        if client_csrf != server_csrf:
            return 'Invalid request state', httplib.BAD_REQUEST

        flow = _get_flow_for_token(server_csrf)

        if flow is None:
            return 'Invalid request state', httplib.BAD_REQUEST

        # Exchange the auth code for credentials.
        try:
            credentials = flow.step2_exchange(code)
        except FlowExchangeError as exchange_error:
            current_app.logger.exception(exchange_error)
            content = 'An error occurred: {0}'.format(exchange_error)
            return content, httplib.BAD_REQUEST

        # Save the credentials to the storage.
        self.storage.put(credentials)

        if self.authorize_callback:
            self.authorize_callback(credentials)

        return redirect(return_url)

    @property
    def credentials(self):
        """The credentials for the current user or None if unavailable."""
        ctx = _app_ctx_stack.top

        if not hasattr(ctx, _CREDENTIALS_KEY):
            ctx.google_oauth2_credentials = self.storage.get()

        return ctx.google_oauth2_credentials

    def has_credentials(self):
        """Returns True if there are valid credentials for the current user."""
        return self.credentials and not self.credentials.invalid

    @property
    def email(self):
        """Returns the user's email address or None if there are no credentials.

        The email address is provided by the current credentials' id_token.
        This should not be used as unique identifier as the user can change
        their email. If you need a unique identifier, use user_id.
        """
        if not self.credentials:
            return None
        try:
            return self.credentials.id_token['email']
        except KeyError:
            current_app.logger.error(
                'Invalid id_token {0}'.format(self.credentials.id_token))

    @property
    def user_id(self):
        """Returns the a unique identifier for the user

        Returns None if there are no credentials.

        The id is provided by the current credentials' id_token.
        """
        if not self.credentials:
            return None
        try:
            return self.credentials.id_token['sub']
        except KeyError:
            current_app.logger.error(
                'Invalid id_token {0}'.format(self.credentials.id_token))

    def authorize_url(self, return_url, **kwargs):
        """Creates a URL that can be used to start the authorization flow.

        When the user is directed to the URL, the authorization flow will
        begin. Once complete, the user will be redirected to the specified
        return URL.

        Any kwargs are passed into the flow constructor.
        """
        return url_for('oauth2.authorize', return_url=return_url, **kwargs)

    def required(self, decorated_function=None, scopes=None,
                 **decorator_kwargs):
        """Decorator to require OAuth2 credentials for a view.

        If credentials are not available for the current user, then they will
        be redirected to the authorization flow. Once complete, the user will
        be redirected back to the original page.
        """

        def curry_wrapper(wrapped_function):
            @wraps(wrapped_function)
            def required_wrapper(*args, **kwargs):
                return_url = decorator_kwargs.pop('return_url', request.url)

                requested_scopes = set(self.scopes)
                if scopes is not None:
                    requested_scopes |= set(scopes)
                if self.has_credentials():
                    requested_scopes |= self.credentials.scopes

                requested_scopes = list(requested_scopes)

                # Does the user have credentials and does the credentials have
                # all of the needed scopes?
                if (self.has_credentials() and
                        self.credentials.has_scopes(requested_scopes)):
                    return wrapped_function(*args, **kwargs)
                # Otherwise, redirect to authorization
                else:
                    auth_url = self.authorize_url(
                        return_url,
                        scopes=requested_scopes,
                        **decorator_kwargs)

                    return redirect(auth_url)

            return required_wrapper

        if decorated_function:
            return curry_wrapper(decorated_function)
        else:
            return curry_wrapper

    def http(self, *args, **kwargs):
        """Returns an authorized http instance.

        Can only be called if there are valid credentials for the user, such
        as inside of a view that is decorated with @required.

        Args:
            *args: Positional arguments passed to httplib2.Http constructor.
            **kwargs: Positional arguments passed to httplib2.Http constructor.

        Raises:
            ValueError if no credentials are available.
        """
        if not self.credentials:
            raise ValueError('No credentials available.')
        return self.credentials.authorize(httplib2.Http(*args, **kwargs))
