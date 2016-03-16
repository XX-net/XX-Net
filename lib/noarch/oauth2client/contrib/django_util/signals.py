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

""" Signals for Google OAuth2 Helper

This module contains signals for Google OAuth2 Helper. Currently it only
contains one, which fires when an OAuth2 authorization flow has completed.
"""

import django.dispatch

"""Signal that fires when  OAuth2 Flow has completed.
It passes the Django request object and the OAuth2 credentials object to the
 receiver.
"""
oauth2_authorized = django.dispatch.Signal(
    providing_args=["request", "credentials"])
