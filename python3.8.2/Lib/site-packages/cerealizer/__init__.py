# -*- coding: utf-8 -*-
# Cerealizer
# Copyright (C) 2005-2010 Jean-Baptiste LAMY
# Copyright (C) 2008 Peter Eckersley
#
# This program is free software.
# It is available under the Python licence.

"""Cerealizer -- A secure Pickle-like module

The interface of the Cerealizer module is similar to Pickle, and it supports
__getstate__, __setstate__, __getinitargs__ and __getnewargs__.

Cerealizer supports int, float, bool, complex, string, unicode, tuple, list, set, frozenset,
dict, old-style and new-style class instances. C-defined types are supported but saving the C-side
data may require to write e.g. a specific Handler or a __getstate__ and __setstate__ pair.
Objects with __slots__ are supported too.

You have to register the class you want to serialize, by calling cerealizer.register(YourClass).
Cerealizer can be considered as secure AS LONG AS the following methods of 'YourClass' are secure:
  - __new__
  - __del__
  - __getstate__
  - __setstate__
  - __init__ (ONLY if __getinitargs__ is used for the class)

These methods are the only one Cerealizer may call. For a higher security, Cerealizer maintains
its own reference to these method (exepted __del__ that can only be called indirectly).

Cerealizer doesn't aim at producing Human-readable files. About performances, Cerealizer is
really fast and, when powered by Psyco, it may even beat cPickle! Although Cerealizer is
implemented in less than 500 lines of pure-Python code (which is another reason for Cerealizer
to be secure, since less code means less bugs :-).

Compared to Pickle (cPickle):
 - Cerealizer is secure
 - Cerealizer achieves similar performances (using Psyco)
 - Cerealizer requires you to declare the serializable classes

Compared to Jelly (from TwistedMatrix):
 - Cerealizer is faster
 - Cerealizer does a better job with object cycles, C-defined types and tuples (*)
 - Cerealizer files are not Human readable

(*) Jelly handles them, but tuples and objects in a cycle are first created as _Tuple or
_Dereference objects; this works for Python classes, but not with C-defined types which
expects a precise type (e.g. tuple and not _Tuple).



IMPLEMENTATION DETAILS

GENERAL FILE FORMAT STRUCTURE

Cerealizer format is simple but quite surprising. It uses a "double flat list" format.
It looks like that :

  <magic code (currently cereal1)>\\n
  <number of objects>\\n
  <classname of object #0>\\n
  <optional data for creating object #0 (currently nothing except for tuples)>
  <classname of object #1>\\n
  <optional data for creating object #1 (currently nothing except for tuples)>
  [...]
  <data of object #0 (format depend of the type of object #0)>
  <data of object #1 (format depend of the type of object #1)>
  [...]
  <reference to the 'root' object>

As you can see, the information for a given object is splitted in two parts, the first one
for object's class, and the second one for the object's data.

To avoid problems, the order of the objects is the following:

  <list, dict, set>
  <object, instance>
  <tuple, sorted by depth (=max number of folded tuples)>

Objects are put after basic types (list,...), since object's __setstate__ might rely on
a list, and thus the list must be fully loaded BEFORE calling the object's __setstate__.


DATA (<data of object #n> above)

The part <data of object #n> saves the data of object #n. It may contains reference to other data
(see below, in Cerealizer references include reference to other objects but also raw data like int).

 - an object           is saved by :  <reference to the object state (the value returned by object.__getstate__() or object.__dict__)>
                                      e.g. 'r7\\n' (object #7 being e.g. the __dict__).

 - a  list or a set    is saved by :  <number of item>\\n
                                      <reference to item #0>
                                      <reference to item #1>
                                      [...]
                                      e.g. '3\\ni0\\ni1\\ni2\\n' for [0, 1, 2]

 - a  dict             is saved by :  <number of item>\\n
                                      <reference to value #0>
                                      <reference to key #0>
                                      <reference to value #1>
                                      <reference to key #1>
                                      [...]


REFERENCES (<reference to XXX> above)

In Cerealizer a reference can be either a reference to another object being serialized in the
same file, or a raw value (e.g. an integer).
 - an int              is saved by e.g. 'i187\\n'
 - a  float            is saved by e.g. 'f1.07\\n'
 - a  bool             is saved by      'b0' or 'b1'
 - a  string           is saved by e.g. 's5\\nascii' (where 5 is the number of characters)
 - an unicode          is saved by e.g. 'u4\\nutf8'  (where 4 is the number of characters)
 - an object reference is saved by e.g. 'r3\\n'      (where 3 means reference to object #3)
 -    None             is saved by      'n'
"""

__all__ = ["load", "dump", "loads", "dumps", "freeze_configuration", "register", "register_class", "register_alias", "unregister"]
VERSION = "0.8.3"

import logging
logger = logging.getLogger("cerealizer")

from io  import BytesIO

class EndOfFile                 (Exception): pass
class NotCerealizerFileError    (Exception): pass
class NonCerealizableObjectError(Exception): pass

def _priority_sorter_key(a): return a[0]

class Dumper(object):
  def __init__(self): self.init()
  def init(self):
    self.objs            = []
    self.objs_id         = set()
    self.priorities_objs = [] # [(priority1, obj1), (priority2, obj2),...]
    self.obj2state       = {}
    self.obj2newargs     = {}
    self.id2id           = {}
    self.id2obj          = None
    
  def dump(self, root_obj, s):
    self.collect(root_obj)
    self.priorities_objs.sort(key = _priority_sorter_key)
    self.objs.extend([o for (priority, o) in self.priorities_objs])
    
    s.write(("cereal1\n%s\n" % len(self.objs)).encode("ascii"))
    
    i = 0
    for obj in self.objs:
      self.id2id[id(obj)] = i
      i += 1
    for obj in self.objs: _HANDLERS_[obj.__class__].dump_obj (obj, self, s)
    for obj in self.objs: _HANDLERS_[obj.__class__].dump_data(obj, self, s)
    
    _HANDLERS_[root_obj.__class__].dump_ref(root_obj, self, s)
    self.init()
    
  def undump(self, s):
    txt = s.read(8)
    if txt != b"cereal1\n": 
      if txt == b"":
        raise EndOfFile("")
      raise NotCerealizerFileError('Not a cerealizer file:\n"%s"' % txt)
    
    nb = int(s.readline())
    self.id2obj = [ None ] * nb  # DO NOT DO  self.id2obj = [comprehension list], since undump_ref may access id2obj during its construction
    for i in range(nb):
      classname = s.readline().decode("utf8")
      handler = _HANDLERS.get(classname)
      if not handler: raise NonCerealizableObjectError("Object of class/type '%s' cannot be de-cerealized! Use cerealizer.register to extend Cerealizer support to other classes." % classname[:-1])
      self.id2obj[i] = handler.undump_obj(self, s)
    for obj in self.id2obj: _HANDLERS_[obj.__class__].undump_data(obj, self, s)
    
    r = self.undump_ref(s)
    self.init()
    return r
  
  def collect(self, obj):
    """Dumper.collect(OBJ) -> bool

Collects OBJ for serialization. Returns false is OBJ is already collected; else returns true."""
    handler = _HANDLERS_.get(obj.__class__)
    if not handler: raise NonCerealizableObjectError("Object of class/type '%s' cannot be cerealized! Use cerealizer.register to extend Cerealizer support to other classes." % obj.__class__)
    handler.collect(obj, self)
  
  def dump_ref (self, obj, s):
    """Dumper.dump_ref(OBJ, S)

Writes a reference to OBJ in file S."""
    _HANDLERS_[obj.__class__].dump_ref(obj, self, s)
    
  def undump_ref(self, s):
    """Dumper.undump_ref(S) -> obj

Reads a reference from file S."""
    c = s.read(1)
    if   c == b"i": return int  (s.readline())
    elif c == b"f": return float(s.readline())
    elif c == b"s": return s.read(int(s.readline())).decode("latin") # str in Python 2 => str in Python 3
    elif c == b"u": return s.read(int(s.readline())).decode("utf8") # str in Python 3 or unicode in Python2
    elif c == b"y": return s.read(int(s.readline())) # bytes in Python 3
    elif c == b"r": return self.id2obj[int(s.readline())]
    elif c == b"n": return None
    elif c == b"b": return bool(int(s.read(1)))
    elif c == b"l": return int(s.readline())
    elif c == b"c": return complex(s.readline().decode("ascii"))
    raise ValueError("Unknown ref code '%s'!" % c)
  
  def immutable_depth(self, t):
    depth = 0
    for i in t:
      i2 = self.obj2newargs.get(id(i))
      if not i2 is None: i = i2
      if isinstance(i, tuple) or isinstance(i, frozenset):
        x = self.immutable_depth(i)
        if x > depth: depth = x
    return depth + 1
  
class Handler(object):
  """Handler

A customized handler for serialization and deserialization.
You can subclass it to extend cerealization support to new object.
See also ObjHandler."""
  
  def collect(self, obj, dumper):
    """Handler.collect(obj, dumper) -> bool

Collects all the objects referenced by OBJ.
For each objects ROBJ referenced by OBJ, calls collect method of the Handler for ROBJ's class,
i.e._HANDLERS_[ROBJ.__class__].collect(ROBJ, dumper).
Returns false if OBJ is already referenced (and thus no collection should occur); else returns true.
"""
    i = id(obj)
    if not i in dumper.objs_id:
      dumper.objs.append(obj)
      dumper.objs_id.add(i)
      return 1
    
  def dump_obj (self, obj, dumper, s):
    """Handler.dump_obj(obj, dumper, s)

Dumps OBJ classname in file S."""
    s.write(self.classname.encode("utf8"))
    
  def dump_data(self, obj, dumper, s):
    """Handler.dump_data(obj, dumper, s)

Dumps OBJ data in file S."""
    
  def dump_ref (self, obj, dumper, s):
    """Handler.dump_ref(obj, dumper, s)

Write a reference to OBJ in file S.
You should not override dump_ref, since they is no corresponding 'undump_ref' that you
can override."""
    s.write(("r%s\n" % dumper.id2id[id(obj)]).encode("ascii"))
  
  def undump_obj(self, dumper, s):
    """Handler.undump_obj(dumper, s)

Returns a new uninitialized (=no __init__'ed) instance of the class.
If you override undump_obj, DUMPER and file S can be used to read additional data
saved by Handler.dump_obj()."""
    
  def undump_data(self, obj, dumper, s):
    """Handler.undump_data(obj, dumper, s)

Reads the data for OBJ, from DUMPER and file S.
If you override undump_data, you should use DUMPER.undump_ref(S) to
read a reference or a basic type (=a string, an int,...)."""
    
    
class RefHandler(object):
  def collect  (self, obj, dumper)   : pass
  def dump_obj (self, obj, dumper, s): pass
  def dump_data(self, obj, dumper, s): pass
  
class NoneHandler(RefHandler):
  def dump_ref (self, obj, dumper, s): s.write(b"n")
  
class BytesHandler(RefHandler):
  def dump_ref (self, obj, dumper, s):
    s.write(("y%s\n" % len(obj)).encode("ascii"))
    s.write(obj)
    
class StrHandler(RefHandler):
  def dump_ref (self, obj, dumper, s):
    obj = obj.encode("utf8")
    s.write(("u%s\n" % len(obj)).encode("ascii"))
    s.write(obj)
    
class BoolHandler(RefHandler):
  def dump_ref (self, obj, dumper, s):
    if obj: s.write(b"b1")
    else:   s.write(b"b0")
    
class IntHandler(RefHandler):
  def dump_ref (self, obj, dumper, s): s.write(("i%r\n" % obj).encode("ascii"))
  
class FloatHandler(RefHandler):
  def dump_ref (self, obj, dumper, s): s.write(("f%r\n" % obj).encode("ascii"))
  
class ComplexHandler(RefHandler):
  def dump_ref (self, obj, dumper, s): s.write(("c%s\n" % obj).encode("ascii"))

class TupleHandler(Handler):
  classname = "tuple\n"
  def collect(self, obj, dumper):
    if not id(obj) in dumper.objs_id:
      dumper.priorities_objs.append((dumper.immutable_depth(obj), obj))
      dumper.objs_id.add(id(obj))
      
      for i in obj: dumper.collect(i)
      return 1
    
  def dump_obj(self, obj, dumper, s):
    s.write(("%s%s\n" % (self.classname, len(obj))).encode("ascii"))
    for i in obj: _HANDLERS_[i.__class__].dump_ref(i, dumper, s)
    
  def undump_obj(self, dumper, s): return tuple([dumper.undump_ref(s) for i in range(int(s.readline()))])
  
class FrozensetHandler(TupleHandler):
  classname = "frozenset\n"
  def undump_obj(self, dumper, s): return frozenset([dumper.undump_ref(s) for i in range(int(s.readline()))])
  
  
class ListHandler(Handler):
  classname = "list\n"
  def collect(self, obj, dumper):
    if Handler.collect(self, obj, dumper):
      for i in obj: dumper.collect(i)
      return 1
    
  def dump_data(self, obj, dumper, s):
    s.write(("%s\n" % len(obj)).encode("ascii"))
    for i in obj: _HANDLERS_[i.__class__].dump_ref(i, dumper, s)
    
  def undump_obj(self, dumper, s): return []
  
  def undump_data(self, obj, dumper, s):
    for i in range(int(s.readline())): obj.append(dumper.undump_ref(s))
    
class SetHandler(ListHandler):
  classname = "set\n"
  def undump_obj(self, dumper, s): return set()
  def undump_data(self, obj, dumper, s):
    for i in range(int(s.readline())): obj.add(dumper.undump_ref(s))
    
class DictHandler(Handler):
  classname = "dict\n"
  def collect(self, obj, dumper):
    if Handler.collect(self, obj, dumper):
      for i in obj.keys  (): dumper.collect(i) # Collect is not ordered
      for i in obj.values(): dumper.collect(i)
      return 1
    
  def dump_data(self, obj, dumper, s):
    s.write(("%s\n" % len(obj)).encode("ascii"))
    for k, v in obj.items():
      _HANDLERS_[v.__class__].dump_ref(v, dumper, s) # Value is saved fist
      _HANDLERS_[k.__class__].dump_ref(k, dumper, s)
      
  def undump_obj(self, dumper, s): return {}
  
  def undump_data(self, obj, dumper, s):
    for i in range(int(s.readline())):
      obj[dumper.undump_ref(s)] = dumper.undump_ref(s) # Value is read fist
      

class ObjHandler(Handler):
  """ObjHandler

A Cerealizer Handler that can support any new-style class instances, old-style class instances
as well as C-defined types (although it may not save the C-side data)."""
  def __init__(self, Class, classname = ""):
    self.Class          = Class
    self.Class_new      = getattr(Class, "__new__")
    self.Class_getstate = getattr(Class, "__getstate__", None)  # Check for and store __getstate__ and __setstate__ now
    self.Class_setstate = getattr(Class, "__setstate__", None)  # so we are are they are not modified in the class or the object
    if classname: self.classname = "%s\n"    % classname
    else:         self.classname = "%s.%s\n" % (Class.__module__, Class.__name__)
    
  def collect(self, obj, dumper):
    i = id(obj)
    if not i in dumper.objs_id:
      dumper.priorities_objs.append((-1, obj))
      dumper.objs_id.add(i)
      
      if self.Class_getstate: state = self.Class_getstate(obj)
      else:                   state = obj.__dict__
      dumper.obj2state[i] = state
      dumper.collect(state)
      return 1
    
  def dump_data(self, obj, dumper, s):
    i = dumper.obj2state[id(obj)]
    _HANDLERS_[i.__class__].dump_ref(i, dumper, s)
    
  def undump_obj(self, dumper, s): return self.Class_new(self.Class)
  
  def undump_data(self, obj, dumper, s):
    if self.Class_setstate: self.Class_setstate(obj, dumper.undump_ref(s))
    else:                   obj.__dict__ =           dumper.undump_ref(s)
    
class SlotedObjHandler(ObjHandler):
  """SlotedObjHandler

A Cerealizer Handler that can support new-style class instances with __slot__."""
  def __init__(self, Class, classname = ""):
    ObjHandler.__init__(self, Class, classname)
    self.Class_slots = Class.__slots__
    
  def collect(self, obj, dumper):
    i = id(obj)
    if not i in dumper.objs_id:
      dumper.priorities_objs.append((-1, obj))
      dumper.objs_id.add(i)
      
      if self.Class_getstate: state = self.Class_getstate(obj)
      else:                   state = dict([(slot, getattr(obj, slot, None)) for slot in self.Class_slots])
      dumper.obj2state[i] = state
      dumper.collect(state)
      return 1
    
  def undump_data(self, obj, dumper, s):
    if self.Class_setstate: self.Class_setstate(obj, dumper.undump_ref(s))
    else:
      state = dumper.undump_ref(s)
      for slot in self.Class_slots: setattr(obj, slot, state[slot])
      
class InitArgsObjHandler(ObjHandler):
  """InitArgsObjHandler

A Cerealizer Handler that can support class instances with __getinitargs__."""
  def __init__(self, Class, classname = ""):
    ObjHandler.__init__(self, Class, classname)
    self.Class_getinitargs = Class.__getinitargs__
    self.Class_init        = Class.__init__
    
  def collect(self, obj, dumper):
    i = id(obj)
    if not i in dumper.objs_id:
      dumper.priorities_objs.append((-1, obj))
      dumper.objs_id.add(i)
      
      dumper.obj2state[i] = state = self.Class_getinitargs(obj)
      dumper.collect(state)
      return 1
    
  def undump_data(self, obj, dumper, s): self.Class_init(obj, *dumper.undump_ref(s))
      
class NewArgsObjHandler(ObjHandler):
  """NewArgsObjHandler

A Cerealizer Handler that can support class instances with __getnewargs__."""
  def __init__(self, Class, classname = ""):
    ObjHandler.__init__(self, Class, classname)
    self.Class_getnewargs = Class.__getnewargs__
    
  def collect(self, obj, dumper):
    i = id(obj)
    if not i in dumper.objs_id:
      dumper.obj2newargs[i] = newargs = self.Class_getnewargs(obj)
      dumper.collect(newargs)
      
      dumper.priorities_objs.append((dumper.immutable_depth(newargs), obj))
      dumper.objs_id.add(i)
      
      if self.Class_getstate: state = self.Class_getstate(obj)
      else:                   state = obj.__dict__
      dumper.obj2state[i] = state
      dumper.collect(state)
      return 1
    
  def dump_obj (self, obj, dumper, s):
    s.write(self.classname.encode("utf8"))
    newargs = dumper.obj2newargs[id(obj)]
    _HANDLERS_[newargs.__class__].dump_ref(newargs, dumper, s)
    
  def undump_obj(self, dumper, s): return self.Class_new(self.Class, *dumper.undump_ref(s))
  
  
_configurable = 1
_HANDLERS  = {}
_HANDLERS_ = {}
def register(Class, handler = None, classname = ""):
  """register(Class, handler = None, classname = "")

Registers CLASS as a serializable and secure class.
By calling register, YOU HAVE TO ASSUME THAT THE FOLLOWING METHODS ARE SECURE:
  - CLASS.__new__
  - CLASS.__del__
  - CLASS.__getstate__
  - CLASS.__setstate__
  - CLASS.__getinitargs__
  - CLASS.__init__ (only if CLASS.__getinitargs__ exists)

HANDLER is the Cerealizer Handler object that handles serialization and deserialization for Class.
If not given, Cerealizer create an instance of ObjHandler, which is suitable for old-style and
new_style Python class, and also C-defined types (although if it has some C-side data, you may
have to write a custom Handler or a __getstate__ and __setstate__ pair).

CLASSNAME is the classname used in Cerealizer files. It defaults to the full classname (module.class)
but you may choose something shorter -- as long as there is no risk of name clash."""
  if not _configurable: raise Exception("Cannot register new classes after freeze_configuration has been called!")
  if "\n" in classname: raise ValueError("CLASSNAME cannot have \\n (Cerealizer automatically add a trailing \\n for performance reason)!")
  if not handler:
    if   hasattr(Class, "__getnewargs__" ): handler = NewArgsObjHandler (Class, classname)
    elif hasattr(Class, "__getinitargs__"): handler = InitArgsObjHandler(Class, classname)
    elif hasattr(Class, "__slots__"      ): handler = SlotedObjHandler  (Class, classname)
    else:                                   handler = ObjHandler        (Class, classname)
  if Class in _HANDLERS_: raise ValueError("Class %s has already been registred!" % Class)
  if not isinstance(handler, RefHandler):
    if handler.classname in _HANDLERS: raise ValueError("A class has already been registred under the name %s!" % handler.classname[:-1])
    _HANDLERS [handler.classname] = handler
    if handler.__class__ is ObjHandler:
      logger.info("Registring class %s as '%s'" % (Class, handler.classname[:-1]))
    else:
      logger.info("Registring class %s as '%s' (using %s)" % (Class, handler.classname[:-1], handler.__class__.__name__))
  else:
    logger.info("Registring reference '%s'" % Class)
    
  _HANDLERS_[Class] = handler

register_class = register # For backward compatibility

def unregister(Class_or_alias):
  """unregister(Class_or_alias)

Unregister the given CLASS or ALIAS."""
  if isinstance(Class_or_alias, str): Class_or_alias = Class_or_alias + "\n"
  del _HANDLERS_[Class_or_alias]
 
  
def register_alias(Class, alias):
  """register_alias(Class, alias)

Registers ALIAS as an alias classname for CLASS.
Usefull for keeping backward compatibility in files: e.g. if you have renamed OldClass to
NewClass, just do:

    cerealizer.register_alias(NewClass, "OldClass")

and you'll be able to open old files containing OldClass serialized."""
  handler = _HANDLERS_.get(Class)
  if not handler:
    raise ValueError("Cannot register alias '%s' to Class %s: the class is not yet registred!" % (alias, Class))
  if alias in _HANDLERS:
    raise ValueError("Cannot register alias '%s' to Class %s: another class is already registred under the alias name!" % (alias, Class))
  logger.info("Registring alias '%s' for %s" % (alias, Class))
  _HANDLERS[alias + "\n"] = handler


def freeze_configuration():
  """freeze_configuration()

Ends Cerealizer configuration. When freeze_configuration() is called, it is no longer possible
to register classes, using register().
Calling freeze_configuration() is not mandatory, but it may enforce security, by forbidding
unexpected calls to register()."""
  global _configurable
  _configurable = 0
  logger.info("Configuration frozen")
  
register(type(None), NoneHandler     ())
register(bytes     , BytesHandler    ())
register(str       , StrHandler      ())
register(bool      , BoolHandler     ())
register(int       , IntHandler      ())
register(float     , FloatHandler    ())
register(complex   , ComplexHandler  ())
register(dict      , DictHandler     ())
register(list      , ListHandler     ())
register(set       , SetHandler      ())
register(tuple     , TupleHandler    ())
register(frozenset , FrozensetHandler())


def dump(obj, file, protocol = 0):
  """dump(obj, file, protocol = 0)

Serializes object OBJ in FILE.
FILE should be an opened file in *** binary *** mode.
PROTOCOL is unused, it exists only for compatibility with Pickle."""
  Dumper().dump(obj, file)
  
def load(file):
  """load(file) -> obj

De-serializes an object from FILE.
FILE should be an opened file in *** binary *** mode."""
  return Dumper().undump(file)

def dumps(obj, protocol = 0):
  """dumps(obj, protocol = 0) -> str

Serializes object OBJ and returns the serialized string.
PROTOCOL is unused, it exists only for compatibility with Pickle."""
  s = BytesIO()
  Dumper().dump(obj, s)
  return s.getvalue()

def loads(string):
  """loads(file) -> obj

De-serializes an object from STRING."""
  return Dumper().undump(BytesIO(string))


def dump_class_of_module(*modules):
  """dump_class_of_module(*modules)

Utility function; for each classes found in the given module, print the needed call to register."""
  class D: pass
  class O(object): pass
  s = {c for module in modules for c in list(module.__dict__.values()) if isinstance(c, type(D)) or  isinstance(c, type(O))}
  l = ['cerealizer.register(%s.%s)' % (c.__module__, c.__name__) for c in s]
  l.sort()
  for i in l: print(i)
  
