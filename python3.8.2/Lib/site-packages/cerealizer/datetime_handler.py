# Cerealizer
# Copyright (C) 2008 Steve Benson, Lann Martin
# Copyright (C) 2012 Jean-Baptiste LAMY
#
# This program is free software.
# It is available under the Python licence.


import datetime
import cerealizer

class DatetimeHandler(cerealizer.Handler):
  classname = 'datetime\n'
  
  def dump_obj(self, obj, dumper, s):
    assert issubclass(obj.__class__, datetime.datetime)
    
    # This works based on datetime.__reduce__():
    
    # datetime.__reduce__()[1] is a string of bytes that is an internal
    # representation of a datetime object (the data field
    # PyDateTime_DateTime struct, an unsigned char
    # _PyDateTime_DATETIME_DATASIZE bytes long). This should be platform
    # independent and is validated upon reconstruction of a datetime. 
    # Pickle uses it and guarantees backwards compatibility, so
    # presumably we can use it here too.
    
    # I haven't verified that tzinfo objects have the same properties,
    # which is why they're unsupported right now.

    # This string returned by __reduce__ is encoded because it can
    # return data that interferes with the cerealizer protocol.

    if obj.tzinfo != None:
      raise ValueError("DatetimeHandler doesn't yet know how to handle datetime objects with tzinfo.")
    
    s.write(self.classname.encode("utf8"))
    s.write(obj.__reduce__()[1][0].decode("latin").encode('unicode_escape'))
    s.write(b'\n')
    
  def undump_obj(self, dumper, s):
    line = s.readline().decode('unicode_escape')
    if line and (line[-1] == '\n'): line = line[:-1]
    return datetime.datetime(line.encode("latin"))


class DateHandler(cerealizer.Handler):
  classname = 'date\n'
  
  def dump_obj(self, obj, dumper, s):
    assert issubclass(obj.__class__, datetime.date)
    
    s.write(self.classname.encode("utf8"))
    s.write(obj.__reduce__()[1][0].decode("latin").encode('unicode_escape'))
    s.write(b'\n')
    
  def undump_obj(self, dumper, s):
    line = s.readline().decode('unicode_escape')
    if line and (line[-1] == '\n'): line = line[:-1]
    return datetime.date(line.encode("latin"))



class TimeHandler(cerealizer.Handler):
  classname = 'time\n'
  
  def dump_obj(self, obj, dumper, s):
    assert issubclass(obj.__class__, datetime.time)
    
    if obj.tzinfo != None:
      raise ValueError("DatetimeHandler doesn't yet know how to handle datetime objects with tzinfo.")
    
    s.write(self.classname.encode("utf8"))
    s.write(obj.__reduce__()[1][0].decode("latin").encode('unicode_escape'))
    s.write(b'\n')
    
  def undump_obj(self, dumper, s):
    line = s.readline().decode('unicode_escape')
    if line and (line[-1] == '\n'): line = line[:-1]
    return datetime.time(line.encode("latin"))


cerealizer.register(datetime.datetime, DatetimeHandler())
cerealizer.register(datetime.date    , DateHandler    ())
cerealizer.register(datetime.time    , TimeHandler    ())


