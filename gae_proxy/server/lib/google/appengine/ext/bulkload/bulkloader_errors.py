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





"""Exceptions raised by bulkloader methods."""









class Error(Exception):
  """Base bulkloader error type."""


class ErrorOnTransform(Error):
  """An exception was raised during this transform."""



class InvalidConfiguration(Error):
  """The configuration is invalid."""


class InvalidCodeInConfiguration(Error):
  """A code or lambda statement in the configuration could not be evaulated."""


class InvalidExportData(Error):
  """The export data cannot be written using this connector object."""


class InvalidImportData(Error):
  """The import data is inconsistent with the configuration."""
