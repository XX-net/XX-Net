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




"""CGI server interface to Python runtime.

CGI-compliant interface between the Python runtime and user-provided Python
code.
"""

from __future__ import with_statement



import cStringIO
from email import feedparser
import imp
import logging
import marshal
import os
import sys
import traceback
import types


def HandleRequest(unused_environ, handler_name, unused_url, post_data,
                  unused_error, application_root, python_lib,
                  import_hook=None):
  """Handle a single CGI request.

  Handles a request for handler_name in the form 'path/to/handler.py' with the
  environment contained in environ.

  Args:
    handler_name: A str containing the user-specified handler file to use for
        this request as specified in the script field of a handler in app.yaml.
    post_data: A stream containing the post data for this request.
    application_root: A str containing the root path of the application.
    python_lib: A str containing the root the Python App Engine library.
    import_hook: Optional import hook (PEP 302 style loader).

  Returns:
    A dict containing zero or more of the following:
      error: App Engine error code. 0 for OK, 1 for error. Defaults to OK if not
          set. If set, then the other fields may be missing.
      response_code: HTTP response code.
      headers: A list of tuples (key, value) of HTTP headers.
      body: A str of the body of the response.
  """
  body = cStringIO.StringIO()
  module_name = _FileToModuleName(handler_name)
  parent_module, _, submodule_name = module_name.rpartition('.')
  parent_module = _GetModuleOrNone(parent_module)
  main = None



  if module_name in sys.modules:
    module = sys.modules[module_name]
    main = _GetValidMain(module)
  if not main:
    module = imp.new_module('__main__')
    if import_hook is not None:
      module.__loader__ = import_hook
  saved_streams = sys.stdin, sys.stdout
  try:
    sys.modules['__main__'] = module
    module.__dict__['__name__'] = '__main__'
    sys.stdin = post_data
    sys.stdout = body
    if main:
      os.environ['PATH_TRANSLATED'] = module.__file__
      main()
    else:
      filename = _AbsolutePath(handler_name, application_root, python_lib)
      if filename.endswith(os.sep + '__init__.py'):
        module.__path__ = [os.path.dirname(filename)]
      if import_hook is None:
        code, filename = _LoadModuleCode(filename)
      else:
        code = import_hook.get_code(module_name)
      if not code:
        return {'error': 2}
      os.environ['PATH_TRANSLATED'] = filename
      module.__file__ = filename
      try:
        sys.modules[module_name] = module
        eval(code, module.__dict__)
      except:


        del sys.modules[module_name]
        if parent_module and submodule_name in parent_module.__dict__:
          del parent_module.__dict__[submodule_name]
        raise
      else:
        if parent_module:
          parent_module.__dict__[submodule_name] = module
    return _ParseResponse(body)
  except:
    exception = sys.exc_info()


    message = ''.join(traceback.format_exception(exception[0], exception[1],
                                                 exception[2].tb_next))
    logging.error(message)
    return {'error': 1}
  finally:
    sys.stdin, sys.stdout = saved_streams
    module.__name__ = module_name
    if '__main__' in sys.modules:
      del sys.modules['__main__']


def _ParseResponse(response):
  """Parses an HTTP response into a dict.

  Args:
    response: A cStringIO.StringIO (StringO) containing the HTTP response.

  Returns:
    A dict with fields:
      body: A str containing the body.
      headers: A list containing tuples (key, value) of key and value pairs.
      response_code: An int containing the HTTP response code.
  """

  response.reset()
  parser = feedparser.FeedParser()

  parser._set_headersonly()


  while True:
    line = response.readline()
    if not feedparser.headerRE.match(line):
      if not feedparser.NLCRE.match(line):
        parser.feed(line)
      break
    parser.feed(line)
  parsed_response = parser.close()

  if 'Status' in parsed_response:
    status = int(parsed_response['Status'].split(' ', 1)[0])
    del parsed_response['Status']
  else:
    status = 200
  return {'body': parsed_response.get_payload() + response.read(),
          'headers': parsed_response.items(),
          'response_code': status}


def _ParseHeader(header):
  """Parses a str header into a (key, value) pair."""
  key, _, value = header.partition(':')
  return key.strip(), value.strip()


def _GetValidMain(module):
  """Returns a main function in module if it exists and is valid or None.

  A main function is valid if it can be called with no arguments, i.e. calling
  module.main() would be valid.

  Args:
    module: The module in which to search for a main function.

  Returns:
    A function that takes no arguments if found or None otherwise.
  """
  if not hasattr(module, 'main'):
    return None
  main = module.main
  if not hasattr(main, '__call__'):
    return None
  defaults = main.__defaults__
  if defaults:
    default_argcount = len(defaults)
  else:
    default_argcount = 0
  if (main.__code__.co_argcount - default_argcount) == 0:
    return main
  else:
    return None


def _FileToModuleName(filename):
  """Returns the module name corresponding to a filename."""
  _, lib, suffix = filename.partition('$PYTHON_LIB/')
  if lib:
    module = suffix
  else:
    module = filename
  module = os.path.normpath(module)
  if '.py' in module:
    module = module.rpartition('.py')[0]
  module = module.replace(os.sep, '.')
  module = module.strip('.')
  if module.endswith('.__init__'):
    module = module.rpartition('.__init__')[0]
  return module


def _AbsolutePath(filename, application_root, python_lib):
  """Returns the absolute path of a Python script file.

  Args:
    filename: A str containing the handler script path.
    application_root: The absolute path of the root of the application.
    python_lib: The absolute path of the Python library.

  Returns:
    The absolute path of the handler script.
  """
  _, lib, suffix = filename.partition('$PYTHON_LIB/')
  if lib:
    filename = os.path.join(python_lib, suffix)
  else:
    filename = os.path.join(application_root, filename)
  if filename.endswith(os.sep) or os.path.isdir(filename):
    filename = os.path.join(filename, '__init__.py')
  return filename


def _LoadModuleCode(filename):
  """Loads the code of a module, using compiled bytecode if available.

  Args:
    filename: The Python script filename.

  Returns:
    A 2-tuple (code, filename) where:
      code: A code object contained in the file or None if it does not exist.
      filename: The name of the file loaded, either the same as the arg
          filename, or the corresponding .pyc file.
  """
  compiled_filename = filename + 'c'
  if os.path.exists(compiled_filename):
    with open(compiled_filename, 'r') as f:
      magic_numbers = f.read(8)
      if len(magic_numbers) == 8 and magic_numbers[:4] == imp.get_magic():
        try:
          return _FixCodeFilename(marshal.load(f), filename), compiled_filename
        except (EOFError, ValueError):
          pass

  if os.path.exists(filename):
    with open(filename, 'r') as f:
      code = compile(f.read(), filename, 'exec', 0, True)
    return code, filename
  else:
    return None, filename


def _FixCodeFilename(code, filename):
  """Creates a CodeType with co_filename replaced with filename.

  Also affects nested code objects in co_consts.

  Args:
    code: The code object to be replaced.
    filename: The replacement filename.

  Returns:
    A new code object with its co_filename set to the provided filename.
  """
  if isinstance(code, types.CodeType):
    code = types.CodeType(
        code.co_argcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        code.co_code,
        tuple([_FixCodeFilename(c, filename) for c in code.co_consts]),
        code.co_names,
        code.co_varnames,
        filename,
        code.co_name,
        code.co_firstlineno,
        code.co_lnotab,
        code.co_freevars,
        code.co_cellvars)
  return code


def _GetModuleOrNone(module_name):
  """Returns a module if it exists or None."""
  module = None
  if module_name:
    try:
      module = __import__(module_name)
    except ImportError:
      pass
    else:
      for name in module_name.split('.')[1:]:
        module = getattr(module, name)
  return module
