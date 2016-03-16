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
"""Exceptions common to the entire package."""




class Error(Exception):
  """Base class for exceptions in this package."""


class InvalidAppConfigError(Error):
  """The supplied application configuration (app.yaml) file is invalid."""


class AppConfigNotFoundError(Error):
  """Application configuration file not found i.e. no app.yaml in directory."""


class DockerfileError(Error):
  """Raised if a Dockerfile was found along with a non-custom runtime."""

