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

"""Application Config For Django OAuth2 Helper

Django 1.7+ provides an
[applications](https://docs.djangoproject.com/en/1.8/ref/applications/)
API so that Django projects can introspect on installed applications using a
stable API. This module exists to follow that convention.
"""

import sys

# Django 1.7+ only supports Python 2.7+
if sys.hexversion >= 0x02070000:  # pragma: NO COVER
    from django.apps import AppConfig

    class GoogleOAuth2HelperConfig(AppConfig):
        """ App Config for Django Helper"""
        name = 'oauth2client.django_util'
        verbose_name = "Google OAuth2 Django Helper"
