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

import hashlib
import json
import os
import pickle
from django import http
from django.core import urlresolvers
from django import shortcuts
from oauth2client import client
from oauth2client.contrib import django_util
from oauth2client.contrib.django_util import signals
from oauth2client.contrib.django_util import storage

_CSRF_KEY = 'google_oauth2_csrf_token'
_FLOW_KEY = 'google_oauth2_flow_{0}'


def _make_flow(request, scopes, return_url=None):
    """Creates a Web Server Flow"""
    # Generate a CSRF token to prevent malicious requests.
    csrf_token = hashlib.sha256(os.urandom(1024)).hexdigest()

    request.session[_CSRF_KEY] = csrf_token

    state = json.dumps({
        'csrf_token': csrf_token,
        'return_url': return_url,
    })

    flow = client.OAuth2WebServerFlow(
        client_id=django_util.oauth2_settings.client_id,
        client_secret=django_util.oauth2_settings.client_secret,
        scope=scopes,
        state=state,
        redirect_uri=request.build_absolute_uri(
            urlresolvers.reverse("google_oauth:callback")))

    flow_key = _FLOW_KEY.format(csrf_token)
    request.session[flow_key] = pickle.dumps(flow)
    return flow


def _get_flow_for_token(csrf_token, request):
    """ Looks up the flow in session to recover information about requested
    scopes."""
    flow_pickle = request.session.get(_FLOW_KEY.format(csrf_token), None)
    return None if flow_pickle is None else pickle.loads(flow_pickle)


def oauth2_callback(request):
    """ View that handles the user's return from OAuth2 provider.

    This view verifies the CSRF state and OAuth authorization code, and on
    success stores the credentials obtained in the storage provider,
    and redirects to the return_url specified in the authorize view and
    stored in the session.

    :param request: Django request
    :return: A redirect response back to the return_url
    """
    if 'error' in request.GET:
        reason = request.GET.get(
            'error_description', request.GET.get('error', ''))
        return http.HttpResponseBadRequest(
            'Authorization failed %s' % reason)

    try:
        encoded_state = request.GET['state']
        code = request.GET['code']
    except KeyError:
        return http.HttpResponseBadRequest(
            "Request missing state or authorization code")

    try:
        server_csrf = request.session[_CSRF_KEY]
    except KeyError:
        return http.HttpResponseBadRequest("No existing session for this flow.")

    try:
        state = json.loads(encoded_state)
        client_csrf = state['csrf_token']
        return_url = state['return_url']
    except (ValueError, KeyError):
        return http.HttpResponseBadRequest('Invalid state parameter.')

    if client_csrf != server_csrf:
        return http.HttpResponseBadRequest('Invalid CSRF token.')

    flow = _get_flow_for_token(client_csrf, request)

    if not flow:
        return http.HttpResponseBadRequest("Missing Oauth2 flow.")

    try:
        credentials = flow.step2_exchange(code)
    except client.FlowExchangeError as exchange_error:
        return http.HttpResponseBadRequest(
            "An error has occurred: {0}".format(exchange_error))

    storage.get_storage(request).put(credentials)

    signals.oauth2_authorized.send(sender=signals.oauth2_authorized,
                                   request=request, credentials=credentials)
    return shortcuts.redirect(return_url)


def oauth2_authorize(request):
    """ View to start the OAuth2 Authorization flow

     This view starts the OAuth2 authorization flow. If scopes is passed in
     as a  GET URL parameter, it will authorize those scopes, otherwise the
     default scopes specified in settings. The return_url can also be
     specified as a GET parameter, otherwise the referer header will be
     checked, and if that isn't found it will return to the root path.

    :param request: The Django request object
    :return: A redirect to Google OAuth2 Authorization
    """
    scopes = request.GET.getlist('scopes', django_util.oauth2_settings.scopes)
    return_url = request.GET.get('return_url', None)

    if not return_url:
        return_url = request.META.get('HTTP_REFERER', '/')
    flow = _make_flow(request=request, scopes=scopes, return_url=return_url)
    auth_url = flow.step1_get_authorize_url()
    return shortcuts.redirect(auth_url)
