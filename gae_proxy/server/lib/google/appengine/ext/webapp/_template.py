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




"""A simple django-based templating framework for use by internal components.

This module should NOT be used by components outside of the google.appengine
package.
"""





import warnings
warnings.filterwarnings('ignore',
                        '',
                        DeprecationWarning,
                        r'ext\.webapp\._template')

import google.appengine._internal.django.template as django_template
from google.appengine.ext.webapp import template


def render(template_path, template_dict, debug=False):
  """Renders the template at the given path with the given dict of values.

  Example usage:
    render("templates/index.html", {"name": "Bret", "values": [1, 2, 3]})

  Args:
    template_path: path to a Django template
    template_dict: dictionary of values to apply to the template

  Returns:
    The rendered template as a string.
  """
  t = template._load_internal_django(template_path, debug)
  return t.render(django_template.Context(template_dict))
