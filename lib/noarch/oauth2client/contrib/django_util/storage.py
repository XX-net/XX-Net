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

from oauth2client.contrib.dictionary_storage import DictionaryStorage

_CREDENTIALS_KEY = 'google_oauth2_credentials'


def get_storage(request):
    # TODO(issue 319): Make this pluggable with different storage providers
    # https://github.com/google/oauth2client/issues/319
    """ Gets a Credentials storage object for the Django OAuth2 Helper object
    :param request: Reference to the current request object
    :return: A OAuth2Client Storage implementation based on sessions
    """
    return DictionaryStorage(request.session, key=_CREDENTIALS_KEY)
