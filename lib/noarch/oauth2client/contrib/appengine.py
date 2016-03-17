# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for Google App Engine

Utilities for making it easier to use OAuth 2.0 on Google App Engine.
"""

import cgi
import json
import logging
import os
import pickle
import threading

import httplib2
import webapp2 as webapp

from google.appengine.api import app_identity
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp.util import login_required

from oauth2client import GOOGLE_AUTH_URI
from oauth2client import GOOGLE_REVOKE_URI
from oauth2client import GOOGLE_TOKEN_URI
from oauth2client import clientsecrets
from oauth2client import util
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import AssertionCredentials
from oauth2client.client import Credentials
from oauth2client.client import Flow
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import Storage
from oauth2client.contrib import xsrfutil

# This is a temporary fix for a Google internal issue.
try:
    from oauth2client.contrib import _appengine_ndb
except ImportError:  # pragma: NO COVER
    _appengine_ndb = None


__author__ = 'jcgregorio@google.com (Joe Gregorio)'

logger = logging.getLogger(__name__)

OAUTH2CLIENT_NAMESPACE = 'oauth2client#ns'

XSRF_MEMCACHE_ID = 'xsrf_secret_key'

if _appengine_ndb is None:
    CredentialsNDBModel = None
    CredentialsNDBProperty = None
    FlowNDBProperty = None
    _NDB_KEY = None
    _NDB_MODEL = None
    SiteXsrfSecretKeyNDB = None
else:
    CredentialsNDBModel = _appengine_ndb.CredentialsNDBModel
    CredentialsNDBProperty = _appengine_ndb.CredentialsNDBProperty
    FlowNDBProperty = _appengine_ndb.FlowNDBProperty
    _NDB_KEY = _appengine_ndb.NDB_KEY
    _NDB_MODEL = _appengine_ndb.NDB_MODEL
    SiteXsrfSecretKeyNDB = _appengine_ndb.SiteXsrfSecretKeyNDB


def _safe_html(s):
    """Escape text to make it safe to display.

    Args:
        s: string, The text to escape.

    Returns:
        The escaped text as a string.
    """
    return cgi.escape(s, quote=1).replace("'", '&#39;')


class InvalidClientSecretsError(Exception):
    """The client_secrets.json file is malformed or missing required fields."""


class InvalidXsrfTokenError(Exception):
    """The XSRF token is invalid or expired."""


class SiteXsrfSecretKey(db.Model):
    """Storage for the sites XSRF secret key.

    There will only be one instance stored of this model, the one used for the
    site.
    """
    secret = db.StringProperty()


def _generate_new_xsrf_secret_key():
    """Returns a random XSRF secret key."""
    return os.urandom(16).encode("hex")


def xsrf_secret_key():
    """Return the secret key for use for XSRF protection.

    If the Site entity does not have a secret key, this method will also create
    one and persist it.

    Returns:
        The secret key.
    """
    secret = memcache.get(XSRF_MEMCACHE_ID, namespace=OAUTH2CLIENT_NAMESPACE)
    if not secret:
        # Load the one and only instance of SiteXsrfSecretKey.
        model = SiteXsrfSecretKey.get_or_insert(key_name='site')
        if not model.secret:
            model.secret = _generate_new_xsrf_secret_key()
            model.put()
        secret = model.secret
        memcache.add(XSRF_MEMCACHE_ID, secret,
                     namespace=OAUTH2CLIENT_NAMESPACE)

    return str(secret)


class AppAssertionCredentials(AssertionCredentials):
    """Credentials object for App Engine Assertion Grants

    This object will allow an App Engine application to identify itself to
    Google and other OAuth 2.0 servers that can verify assertions. It can be
    used for the purpose of accessing data stored under an account assigned to
    the App Engine application itself.

    This credential does not require a flow to instantiate because it
    represents a two legged flow, and therefore has all of the required
    information to generate and refresh its own access tokens.
    """

    @util.positional(2)
    def __init__(self, scope, **kwargs):
        """Constructor for AppAssertionCredentials

        Args:
            scope: string or iterable of strings, scope(s) of the credentials
                   being requested.
            **kwargs: optional keyword args, including:
            service_account_id: service account id of the application. If None
                                or unspecified, the default service account for
                                the app is used.
        """
        self.scope = util.scopes_to_string(scope)
        self._kwargs = kwargs
        self.service_account_id = kwargs.get('service_account_id', None)
        self._service_account_email = None

        # Assertion type is no longer used, but still in the
        # parent class signature.
        super(AppAssertionCredentials, self).__init__(None)

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)
        return AppAssertionCredentials(data['scope'])

    def _refresh(self, http_request):
        """Refreshes the access_token.

        Since the underlying App Engine app_identity implementation does its
        own caching we can skip all the storage hoops and just to a refresh
        using the API.

        Args:
            http_request: callable, a callable that matches the method
                          signature of httplib2.Http.request, used to make the
                          refresh request.

        Raises:
            AccessTokenRefreshError: When the refresh fails.
        """
        try:
            scopes = self.scope.split()
            (token, _) = app_identity.get_access_token(
                scopes, service_account_id=self.service_account_id)
        except app_identity.Error as e:
            raise AccessTokenRefreshError(str(e))
        self.access_token = token

    @property
    def serialization_data(self):
        raise NotImplementedError('Cannot serialize credentials '
                                  'for Google App Engine.')

    def create_scoped_required(self):
        return not self.scope

    def create_scoped(self, scopes):
        return AppAssertionCredentials(scopes, **self._kwargs)

    def sign_blob(self, blob):
        """Cryptographically sign a blob (of bytes).

        Implements abstract method
        :meth:`oauth2client.client.AssertionCredentials.sign_blob`.

        Args:
            blob: bytes, Message to be signed.

        Returns:
            tuple, A pair of the private key ID used to sign the blob and
            the signed contents.
        """
        return app_identity.sign_blob(blob)

    @property
    def service_account_email(self):
        """Get the email for the current service account.

        Returns:
            string, The email associated with the Google App Engine
            service account.
        """
        if self._service_account_email is None:
            self._service_account_email = (
                app_identity.get_service_account_name())
        return self._service_account_email


class FlowProperty(db.Property):
    """App Engine datastore Property for Flow.

    Utility property that allows easy storage and retrieval of an
    oauth2client.Flow
    """

    # Tell what the user type is.
    data_type = Flow

    # For writing to datastore.
    def get_value_for_datastore(self, model_instance):
        flow = super(FlowProperty, self).get_value_for_datastore(
            model_instance)
        return db.Blob(pickle.dumps(flow))

    # For reading from datastore.
    def make_value_from_datastore(self, value):
        if value is None:
            return None
        return pickle.loads(value)

    def validate(self, value):
        if value is not None and not isinstance(value, Flow):
            raise db.BadValueError('Property %s must be convertible '
                                   'to a FlowThreeLegged instance (%s)' %
                                   (self.name, value))
        return super(FlowProperty, self).validate(value)

    def empty(self, value):
        return not value


class CredentialsProperty(db.Property):
    """App Engine datastore Property for Credentials.

    Utility property that allows easy storage and retrieval of
    oath2client.Credentials
    """

    # Tell what the user type is.
    data_type = Credentials

    # For writing to datastore.
    def get_value_for_datastore(self, model_instance):
        logger.info("get: Got type " + str(type(model_instance)))
        cred = super(CredentialsProperty, self).get_value_for_datastore(
            model_instance)
        if cred is None:
            cred = ''
        else:
            cred = cred.to_json()
        return db.Blob(cred)

    # For reading from datastore.
    def make_value_from_datastore(self, value):
        logger.info("make: Got type " + str(type(value)))
        if value is None:
            return None
        if len(value) == 0:
            return None
        try:
            credentials = Credentials.new_from_json(value)
        except ValueError:
            credentials = None
        return credentials

    def validate(self, value):
        value = super(CredentialsProperty, self).validate(value)
        logger.info("validate: Got type " + str(type(value)))
        if value is not None and not isinstance(value, Credentials):
            raise db.BadValueError('Property %s must be convertible '
                                   'to a Credentials instance (%s)' %
                                   (self.name, value))
        return value


class StorageByKeyName(Storage):
    """Store and retrieve a credential to and from the App Engine datastore.

    This Storage helper presumes the Credentials have been stored as a
    CredentialsProperty or CredentialsNDBProperty on a datastore model class,
    and that entities are stored by key_name.
    """

    @util.positional(4)
    def __init__(self, model, key_name, property_name, cache=None, user=None):
        """Constructor for Storage.

        Args:
            model: db.Model or ndb.Model, model class
            key_name: string, key name for the entity that has the credentials
            property_name: string, name of the property that is a
                           CredentialsProperty or CredentialsNDBProperty.
            cache: memcache, a write-through cache to put in front of the
                   datastore. If the model you are using is an NDB model, using
                   a cache will be redundant since the model uses an instance
                   cache and memcache for you.
            user: users.User object, optional. Can be used to grab user ID as a
                  key_name if no key name is specified.
        """
        super(StorageByKeyName, self).__init__()

        if key_name is None:
            if user is None:
                raise ValueError('StorageByKeyName called with no '
                                 'key name or user.')
            key_name = user.user_id()

        self._model = model
        self._key_name = key_name
        self._property_name = property_name
        self._cache = cache

    def _is_ndb(self):
        """Determine whether the model of the instance is an NDB model.

        Returns:
            Boolean indicating whether or not the model is an NDB or DB model.
        """
        # issubclass will fail if one of the arguments is not a class, only
        # need worry about new-style classes since ndb and db models are
        # new-style
        if isinstance(self._model, type):
            if _NDB_MODEL is not None and issubclass(self._model, _NDB_MODEL):
                return True
            elif issubclass(self._model, db.Model):
                return False

        raise TypeError('Model class not an NDB or DB model: %s.' %
                        (self._model,))

    def _get_entity(self):
        """Retrieve entity from datastore.

        Uses a different model method for db or ndb models.

        Returns:
            Instance of the model corresponding to the current storage object
            and stored using the key name of the storage object.
        """
        if self._is_ndb():
            return self._model.get_by_id(self._key_name)
        else:
            return self._model.get_by_key_name(self._key_name)

    def _delete_entity(self):
        """Delete entity from datastore.

        Attempts to delete using the key_name stored on the object, whether or
        not the given key is in the datastore.
        """
        if self._is_ndb():
            _NDB_KEY(self._model, self._key_name).delete()
        else:
            entity_key = db.Key.from_path(self._model.kind(), self._key_name)
            db.delete(entity_key)

    @db.non_transactional(allow_existing=True)
    def locked_get(self):
        """Retrieve Credential from datastore.

        Returns:
            oauth2client.Credentials
        """
        credentials = None
        if self._cache:
            json = self._cache.get(self._key_name)
            if json:
                credentials = Credentials.new_from_json(json)
        if credentials is None:
            entity = self._get_entity()
            if entity is not None:
                credentials = getattr(entity, self._property_name)
                if self._cache:
                    self._cache.set(self._key_name, credentials.to_json())

        if credentials and hasattr(credentials, 'set_store'):
            credentials.set_store(self)
        return credentials

    @db.non_transactional(allow_existing=True)
    def locked_put(self, credentials):
        """Write a Credentials to the datastore.

        Args:
            credentials: Credentials, the credentials to store.
        """
        entity = self._model.get_or_insert(self._key_name)
        setattr(entity, self._property_name, credentials)
        entity.put()
        if self._cache:
            self._cache.set(self._key_name, credentials.to_json())

    @db.non_transactional(allow_existing=True)
    def locked_delete(self):
        """Delete Credential from datastore."""

        if self._cache:
            self._cache.delete(self._key_name)

        self._delete_entity()


class CredentialsModel(db.Model):
    """Storage for OAuth 2.0 Credentials

    Storage of the model is keyed by the user.user_id().
    """
    credentials = CredentialsProperty()


def _build_state_value(request_handler, user):
    """Composes the value for the 'state' parameter.

    Packs the current request URI and an XSRF token into an opaque string that
    can be passed to the authentication server via the 'state' parameter.

    Args:
        request_handler: webapp.RequestHandler, The request.
        user: google.appengine.api.users.User, The current user.

    Returns:
        The state value as a string.
    """
    uri = request_handler.request.url
    token = xsrfutil.generate_token(xsrf_secret_key(), user.user_id(),
                                    action_id=str(uri))
    return uri + ':' + token


def _parse_state_value(state, user):
    """Parse the value of the 'state' parameter.

    Parses the value and validates the XSRF token in the state parameter.

    Args:
        state: string, The value of the state parameter.
        user: google.appengine.api.users.User, The current user.

    Raises:
        InvalidXsrfTokenError: if the XSRF token is invalid.

    Returns:
        The redirect URI.
    """
    uri, token = state.rsplit(':', 1)
    if not xsrfutil.validate_token(xsrf_secret_key(), token, user.user_id(),
                                   action_id=uri):
        raise InvalidXsrfTokenError()

    return uri


class OAuth2Decorator(object):
    """Utility for making OAuth 2.0 easier.

    Instantiate and then use with oauth_required or oauth_aware
    as decorators on webapp.RequestHandler methods.

    ::

        decorator = OAuth2Decorator(
            client_id='837...ent.com',
            client_secret='Qh...wwI',
            scope='https://www.googleapis.com/auth/plus')

        class MainHandler(webapp.RequestHandler):
            @decorator.oauth_required
            def get(self):
                http = decorator.http()
                # http is authorized with the user's Credentials and can be
                # used in API calls

    """

    def set_credentials(self, credentials):
        self._tls.credentials = credentials

    def get_credentials(self):
        """A thread local Credentials object.

        Returns:
            A client.Credentials object, or None if credentials hasn't been set
            in this thread yet, which may happen when calling has_credentials
            inside oauth_aware.
        """
        return getattr(self._tls, 'credentials', None)

    credentials = property(get_credentials, set_credentials)

    def set_flow(self, flow):
        self._tls.flow = flow

    def get_flow(self):
        """A thread local Flow object.

        Returns:
            A credentials.Flow object, or None if the flow hasn't been set in
            this thread yet, which happens in _create_flow() since Flows are
            created lazily.
        """
        return getattr(self._tls, 'flow', None)

    flow = property(get_flow, set_flow)

    @util.positional(4)
    def __init__(self, client_id, client_secret, scope,
                 auth_uri=GOOGLE_AUTH_URI,
                 token_uri=GOOGLE_TOKEN_URI,
                 revoke_uri=GOOGLE_REVOKE_URI,
                 user_agent=None,
                 message=None,
                 callback_path='/oauth2callback',
                 token_response_param=None,
                 _storage_class=StorageByKeyName,
                 _credentials_class=CredentialsModel,
                 _credentials_property_name='credentials',
                 **kwargs):
        """Constructor for OAuth2Decorator

        Args:
            client_id: string, client identifier.
            client_secret: string client secret.
            scope: string or iterable of strings, scope(s) of the credentials
                   being requested.
            auth_uri: string, URI for authorization endpoint. For convenience
                      defaults to Google's endpoints but any OAuth 2.0 provider
                      can be used.
            token_uri: string, URI for token endpoint. For convenience defaults
                       to Google's endpoints but any OAuth 2.0 provider can be
                       used.
            revoke_uri: string, URI for revoke endpoint. For convenience
                        defaults to Google's endpoints but any OAuth 2.0
                        provider can be used.
            user_agent: string, User agent of your application, default to
                        None.
            message: Message to display if there are problems with the
                     OAuth 2.0 configuration. The message may contain HTML and
                     will be presented on the web interface for any method that
                     uses the decorator.
            callback_path: string, The absolute path to use as the callback
                           URI. Note that this must match up with the URI given
                           when registering the application in the APIs
                           Console.
            token_response_param: string. If provided, the full JSON response
                                  to the access token request will be encoded
                                  and included in this query parameter in the
                                  callback URI. This is useful with providers
                                  (e.g. wordpress.com) that include extra
                                  fields that the client may want.
            _storage_class: "Protected" keyword argument not typically provided
                            to this constructor. A storage class to aid in
                            storing a Credentials object for a user in the
                            datastore. Defaults to StorageByKeyName.
            _credentials_class: "Protected" keyword argument not typically
                                provided to this constructor. A db or ndb Model
                                class to hold credentials. Defaults to
                                CredentialsModel.
            _credentials_property_name: "Protected" keyword argument not
                                        typically provided to this constructor.
                                        A string indicating the name of the
                                        field on the _credentials_class where a
                                        Credentials object will be stored.
                                        Defaults to 'credentials'.
            **kwargs: dict, Keyword arguments are passed along as kwargs to
                      the OAuth2WebServerFlow constructor.
        """
        self._tls = threading.local()
        self.flow = None
        self.credentials = None
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = util.scopes_to_string(scope)
        self._auth_uri = auth_uri
        self._token_uri = token_uri
        self._revoke_uri = revoke_uri
        self._user_agent = user_agent
        self._kwargs = kwargs
        self._message = message
        self._in_error = False
        self._callback_path = callback_path
        self._token_response_param = token_response_param
        self._storage_class = _storage_class
        self._credentials_class = _credentials_class
        self._credentials_property_name = _credentials_property_name

    def _display_error_message(self, request_handler):
        request_handler.response.out.write('<html><body>')
        request_handler.response.out.write(_safe_html(self._message))
        request_handler.response.out.write('</body></html>')

    def oauth_required(self, method):
        """Decorator that starts the OAuth 2.0 dance.

        Starts the OAuth dance for the logged in user if they haven't already
        granted access for this application.

        Args:
            method: callable, to be decorated method of a webapp.RequestHandler
                    instance.
        """

        def check_oauth(request_handler, *args, **kwargs):
            if self._in_error:
                self._display_error_message(request_handler)
                return

            user = users.get_current_user()
            # Don't use @login_decorator as this could be used in a
            # POST request.
            if not user:
                request_handler.redirect(users.create_login_url(
                    request_handler.request.uri))
                return

            self._create_flow(request_handler)

            # Store the request URI in 'state' so we can use it later
            self.flow.params['state'] = _build_state_value(
                request_handler, user)
            self.credentials = self._storage_class(
                self._credentials_class, None,
                self._credentials_property_name, user=user).get()

            if not self.has_credentials():
                return request_handler.redirect(self.authorize_url())
            try:
                resp = method(request_handler, *args, **kwargs)
            except AccessTokenRefreshError:
                return request_handler.redirect(self.authorize_url())
            finally:
                self.credentials = None
            return resp

        return check_oauth

    def _create_flow(self, request_handler):
        """Create the Flow object.

        The Flow is calculated lazily since we don't know where this app is
        running until it receives a request, at which point redirect_uri can be
        calculated and then the Flow object can be constructed.

        Args:
            request_handler: webapp.RequestHandler, the request handler.
        """
        if self.flow is None:
            redirect_uri = request_handler.request.relative_url(
                self._callback_path)  # Usually /oauth2callback
            self.flow = OAuth2WebServerFlow(
                self._client_id, self._client_secret, self._scope,
                redirect_uri=redirect_uri, user_agent=self._user_agent,
                auth_uri=self._auth_uri, token_uri=self._token_uri,
                revoke_uri=self._revoke_uri, **self._kwargs)

    def oauth_aware(self, method):
        """Decorator that sets up for OAuth 2.0 dance, but doesn't do it.

        Does all the setup for the OAuth dance, but doesn't initiate it.
        This decorator is useful if you want to create a page that knows
        whether or not the user has granted access to this application.
        From within a method decorated with @oauth_aware the has_credentials()
        and authorize_url() methods can be called.

        Args:
            method: callable, to be decorated method of a webapp.RequestHandler
                    instance.
        """

        def setup_oauth(request_handler, *args, **kwargs):
            if self._in_error:
                self._display_error_message(request_handler)
                return

            user = users.get_current_user()
            # Don't use @login_decorator as this could be used in a
            # POST request.
            if not user:
                request_handler.redirect(users.create_login_url(
                    request_handler.request.uri))
                return

            self._create_flow(request_handler)

            self.flow.params['state'] = _build_state_value(request_handler,
                                                           user)
            self.credentials = self._storage_class(
                self._credentials_class, None,
                self._credentials_property_name, user=user).get()
            try:
                resp = method(request_handler, *args, **kwargs)
            finally:
                self.credentials = None
            return resp
        return setup_oauth

    def has_credentials(self):
        """True if for the logged in user there are valid access Credentials.

        Must only be called from with a webapp.RequestHandler subclassed method
        that had been decorated with either @oauth_required or @oauth_aware.
        """
        return self.credentials is not None and not self.credentials.invalid

    def authorize_url(self):
        """Returns the URL to start the OAuth dance.

        Must only be called from with a webapp.RequestHandler subclassed method
        that had been decorated with either @oauth_required or @oauth_aware.
        """
        url = self.flow.step1_get_authorize_url()
        return str(url)

    def http(self, *args, **kwargs):
        """Returns an authorized http instance.

        Must only be called from within an @oauth_required decorated method, or
        from within an @oauth_aware decorated method where has_credentials()
        returns True.

        Args:
            *args: Positional arguments passed to httplib2.Http constructor.
            **kwargs: Positional arguments passed to httplib2.Http constructor.
        """
        return self.credentials.authorize(httplib2.Http(*args, **kwargs))

    @property
    def callback_path(self):
        """The absolute path where the callback will occur.

        Note this is the absolute path, not the absolute URI, that will be
        calculated by the decorator at runtime. See callback_handler() for how
        this should be used.

        Returns:
            The callback path as a string.
        """
        return self._callback_path

    def callback_handler(self):
        """RequestHandler for the OAuth 2.0 redirect callback.

        Usage::

            app = webapp.WSGIApplication([
                ('/index', MyIndexHandler),
                ...,
                (decorator.callback_path, decorator.callback_handler())
            ])

        Returns:
            A webapp.RequestHandler that handles the redirect back from the
            server during the OAuth 2.0 dance.
        """
        decorator = self

        class OAuth2Handler(webapp.RequestHandler):
            """Handler for the redirect_uri of the OAuth 2.0 dance."""

            @login_required
            def get(self):
                error = self.request.get('error')
                if error:
                    errormsg = self.request.get('error_description', error)
                    self.response.out.write(
                        'The authorization request failed: %s' %
                        _safe_html(errormsg))
                else:
                    user = users.get_current_user()
                    decorator._create_flow(self)
                    credentials = decorator.flow.step2_exchange(
                        self.request.params)
                    decorator._storage_class(
                        decorator._credentials_class, None,
                        decorator._credentials_property_name,
                        user=user).put(credentials)
                    redirect_uri = _parse_state_value(
                        str(self.request.get('state')), user)

                    if (decorator._token_response_param and
                            credentials.token_response):
                        resp_json = json.dumps(credentials.token_response)
                        redirect_uri = util._add_query_parameter(
                            redirect_uri, decorator._token_response_param,
                            resp_json)

                    self.redirect(redirect_uri)

        return OAuth2Handler

    def callback_application(self):
        """WSGI application for handling the OAuth 2.0 redirect callback.

        If you need finer grained control use `callback_handler` which returns
        just the webapp.RequestHandler.

        Returns:
            A webapp.WSGIApplication that handles the redirect back from the
            server during the OAuth 2.0 dance.
        """
        return webapp.WSGIApplication([
            (self.callback_path, self.callback_handler())
        ])


class OAuth2DecoratorFromClientSecrets(OAuth2Decorator):
    """An OAuth2Decorator that builds from a clientsecrets file.

    Uses a clientsecrets file as the source for all the information when
    constructing an OAuth2Decorator.

    ::

        decorator = OAuth2DecoratorFromClientSecrets(
            os.path.join(os.path.dirname(__file__), 'client_secrets.json')
            scope='https://www.googleapis.com/auth/plus')

        class MainHandler(webapp.RequestHandler):
            @decorator.oauth_required
            def get(self):
                http = decorator.http()
                # http is authorized with the user's Credentials and can be
                # used in API calls

    """

    @util.positional(3)
    def __init__(self, filename, scope, message=None, cache=None, **kwargs):
        """Constructor

        Args:
            filename: string, File name of client secrets.
            scope: string or iterable of strings, scope(s) of the credentials
                   being requested.
            message: string, A friendly string to display to the user if the
                     clientsecrets file is missing or invalid. The message may
                     contain HTML and will be presented on the web interface
                     for any method that uses the decorator.
            cache: An optional cache service client that implements get() and
                   set()
            methods. See clientsecrets.loadfile() for details.
            **kwargs: dict, Keyword arguments are passed along as kwargs to
                      the OAuth2WebServerFlow constructor.
        """
        client_type, client_info = clientsecrets.loadfile(filename,
                                                          cache=cache)
        if client_type not in (clientsecrets.TYPE_WEB,
                               clientsecrets.TYPE_INSTALLED):
            raise InvalidClientSecretsError(
                "OAuth2Decorator doesn't support this OAuth 2.0 flow.")

        constructor_kwargs = dict(kwargs)
        constructor_kwargs.update({
            'auth_uri': client_info['auth_uri'],
            'token_uri': client_info['token_uri'],
            'message': message,
        })
        revoke_uri = client_info.get('revoke_uri')
        if revoke_uri is not None:
            constructor_kwargs['revoke_uri'] = revoke_uri
        super(OAuth2DecoratorFromClientSecrets, self).__init__(
            client_info['client_id'], client_info['client_secret'],
            scope, **constructor_kwargs)
        if message is not None:
            self._message = message
        else:
            self._message = 'Please configure your application for OAuth 2.0.'


@util.positional(2)
def oauth2decorator_from_clientsecrets(filename, scope,
                                       message=None, cache=None):
    """Creates an OAuth2Decorator populated from a clientsecrets file.

    Args:
        filename: string, File name of client secrets.
        scope: string or list of strings, scope(s) of the credentials being
               requested.
        message: string, A friendly string to display to the user if the
                 clientsecrets file is missing or invalid. The message may
                 contain HTML and will be presented on the web interface for
                 any method that uses the decorator.
        cache: An optional cache service client that implements get() and set()
               methods. See clientsecrets.loadfile() for details.

    Returns: An OAuth2Decorator
    """
    return OAuth2DecoratorFromClientSecrets(filename, scope,
                                            message=message, cache=cache)
