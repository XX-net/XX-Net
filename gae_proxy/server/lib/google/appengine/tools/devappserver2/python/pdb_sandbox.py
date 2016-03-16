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
"""Modify pdb to work with the devappserver2 sandbox."""

import sys
import threading

def install(config):
  """Install the necessary changes to pdb.

  Monkeypatch pdb so that it can be used in the devappserver sandbox. Must
  be called after the sandbox has been installed but before stdin/stdout
  objects have been reassigned.

  Args:
    config: The runtime_config_pb2.Config to use to configure the sandbox.
  """
  # Import here (i.e. after sandbox installed) to get the post sandbox pdb.
  # Extremely important so that we monkeypatch the same pdb the apps can
  # import.
  import pdb as pdb_postsandbox

  # Save stdin/stdout as the references will not be available when user
  # code runs.
  real_stdin = sys.stdin
  real_stdout = sys.stdout

  # Capture the original Pdb so we can forward the __init__ call after
  # monkeypatching (if not captured, forwarding the call results in infinite
  # recursion).
  pdb_premonkeypatch = pdb_postsandbox.Pdb

  if config.threadsafe or config.max_instances != 1:
    warning = """
********************************************************************************
* WARNING: please read before using PDB:
* https://developers.google.com/appengine/docs/python/tools/devserver#Python_Debugging_with_PDB
********************************************************************************

"""
    lock = threading.Lock()
  else:
    warning = ''

  class _Pdb(pdb_postsandbox.Pdb):
    _warning_written = False

    # TODO: improve argument handling so if new arguments are added
    # in the future or the defaults change, this does not need to be updated.
    def __init__(self, completekey='tab', stdin=None, stdout=None, skip=None):
      if stdin is None:
        stdin = real_stdin
      if stdout is None:
        stdout = real_stdout
      # Pdb is old style class so no super().
      pdb_premonkeypatch.__init__(self, completekey, stdin, stdout, skip)

      if warning:
        with lock:
          # Note: while the goal is to write the warning only one time, it
          # may be written multiple times (once each per instance).
          if not _Pdb._warning_written:
            stdout.write(warning)
            _Pdb._warning_written = True

  pdb_postsandbox.Pdb = _Pdb
