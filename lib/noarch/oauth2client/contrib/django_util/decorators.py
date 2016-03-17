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

from django import shortcuts
from oauth2client.contrib import django_util
from six import wraps


def oauth_required(decorated_function=None, scopes=None, **decorator_kwargs):
    """ Decorator to require OAuth2 credentials for a view


    .. code-block:: python
       :caption: views.py
       :name: views_required_2


       from oauth2client.django_util.decorators import oauth_required

       @oauth_required
       def requires_default_scopes(request):
          email = request.credentials.id_token['email']
          service = build(serviceName='calendar', version='v3',
                       http=request.oauth.http,
                       developerKey=API_KEY)
          events = service.events().list(
                                    calendarId='primary').execute()['items']
          return HttpResponse("email: %s , calendar: %s" % (email, str(events)))

    :param decorated_function: View function to decorate, must have the Django
           request object as the first argument
    :param scopes: Scopes to require, will default
    :param decorator_kwargs: Can include ``return_url`` to specify the URL to
           return to after OAuth2 authorization is complete
    :return: An OAuth2 Authorize view if credentials are not found or if the
             credentials are missing the required scopes. Otherwise,
             the decorated view.
    """

    def curry_wrapper(wrapped_function):
        @wraps(wrapped_function)
        def required_wrapper(request, *args, **kwargs):
            return_url = decorator_kwargs.pop('return_url',
                                              request.get_full_path())
            user_oauth = django_util.UserOAuth2(request, scopes, return_url)
            if not user_oauth.has_credentials():
                return shortcuts.redirect(user_oauth.get_authorize_redirect())
            setattr(request, django_util.oauth2_settings.request_prefix,
                    user_oauth)
            return wrapped_function(request, *args, **kwargs)

        return required_wrapper

    if decorated_function:
        return curry_wrapper(decorated_function)
    else:
        return curry_wrapper


def oauth_enabled(decorated_function=None, scopes=None, **decorator_kwargs):
    """ Decorator to enable OAuth Credentials if authorized, and setup
    the oauth object on the request object to provide helper functions
    to start the flow otherwise.

    .. code-block:: python
       :caption: views.py
       :name: views_enabled3

       from oauth2client.django_util.decorators import oauth_enabled

       @oauth_enabled
       def optional_oauth2(request):
           if request.oauth.has_credentials():
               # this could be passed into a view
               # request.oauth.http is also initialized
               return HttpResponse("User email: %s" %
                                   request.oauth.credentials.id_token['email'])
           else:
               return HttpResponse('Here is an OAuth Authorize link:
               <a href="%s">Authorize</a>' %
               request.oauth.get_authorize_redirect())


    :param decorated_function: View function to decorate
    :param scopes: Scopes to require, will default
    :param decorator_kwargs: Can include ``return_url`` to specify the URL to
           return to after OAuth2 authorization is complete
    :return: The decorated view function
    """

    def curry_wrapper(wrapped_function):
        @wraps(wrapped_function)
        def enabled_wrapper(request, *args, **kwargs):
            return_url = decorator_kwargs.pop('return_url',
                                              request.get_full_path())
            user_oauth = django_util.UserOAuth2(request, scopes, return_url)
            setattr(request, django_util.oauth2_settings.request_prefix,
                    user_oauth)
            return wrapped_function(request, *args, **kwargs)

        return enabled_wrapper

    if decorated_function:
        return curry_wrapper(decorated_function)
    else:
        return curry_wrapper
