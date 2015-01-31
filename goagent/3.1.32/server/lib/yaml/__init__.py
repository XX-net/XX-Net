
from error import *

from tokens import *
from events import *
from nodes import *

from loader import *
from dumper import *

try:
    from cyaml import *
except ImportError:
    pass

def scan(stream, Loader=Loader):
    """
    Scan a YAML stream and produce scanning tokens.
    """
    loader = Loader(stream)
    while loader.check_token():
        yield loader.get_token()

def parse(stream, Loader=Loader):
    """
    Parse a YAML stream and produce parsing events.
    """
    loader = Loader(stream)
    while loader.check_event():
        yield loader.get_event()

def compose(stream, Loader=Loader):
    """
    Parse the first YAML document in a stream
    and produce the corresponding representation tree.
    """
    loader = Loader(stream)
    if loader.check_node():
        return loader.get_node()

def compose_all(stream, Loader=Loader):
    """
    Parse all YAML documents in a stream
    and produce corresponsing representation trees.
    """
    loader = Loader(stream)
    while loader.check_node():
        yield loader.get_node()

def load_all(stream, Loader=Loader):
    """
    Parse all YAML documents in a stream
    and produce corresponding Python objects.
    """
    loader = Loader(stream)
    while loader.check_data():
        yield loader.get_data()

def load(stream, Loader=Loader):
    """
    Parse the first YAML document in a stream
    and produce the corresponding Python object.
    """
    loader = Loader(stream)
    if loader.check_data():
        return loader.get_data()

def safe_load_all(stream):
    """
    Parse all YAML documents in a stream
    and produce corresponding Python objects.
    Resolve only basic YAML tags.
    """
    return load_all(stream, SafeLoader)

def safe_load(stream):
    """
    Parse the first YAML document in a stream
    and produce the corresponding Python object.
    Resolve only basic YAML tags.
    """
    return load(stream, SafeLoader)

def emit(events, stream=None, Dumper=Dumper,
        canonical=None, indent=None, width=None,
        allow_unicode=None, line_break=None):
    """
    Emit YAML parsing events into a stream.
    If stream is None, return the produced string instead.
    """
    getvalue = None
    if stream is None:
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        stream = StringIO()
        getvalue = stream.getvalue
    dumper = Dumper(stream, canonical=canonical, indent=indent, width=width,
            allow_unicode=allow_unicode, line_break=line_break)
    for event in events:
        dumper.emit(event)
    if getvalue:
        return getvalue()

def serialize_all(nodes, stream=None, Dumper=Dumper,
        canonical=None, indent=None, width=None,
        allow_unicode=None, line_break=None,
        encoding='utf-8', explicit_start=None, explicit_end=None,
        version=None, tags=None):
    """
    Serialize a sequence of representation trees into a YAML stream.
    If stream is None, return the produced string instead.
    """
    getvalue = None
    if stream is None:
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        stream = StringIO()
        getvalue = stream.getvalue
    dumper = Dumper(stream, canonical=canonical, indent=indent, width=width,
            allow_unicode=allow_unicode, line_break=line_break,
            encoding=encoding, version=version, tags=tags,
            explicit_start=explicit_start, explicit_end=explicit_end)
    dumper.open()
    for node in nodes:
        dumper.serialize(node)
    dumper.close()
    if getvalue:
        return getvalue()

def serialize(node, stream=None, Dumper=Dumper, **kwds):
    """
    Serialize a representation tree into a YAML stream.
    If stream is None, return the produced string instead.
    """
    return serialize_all([node], stream, Dumper=Dumper, **kwds)

def dump_all(documents, stream=None, Dumper=Dumper,
        default_style=None, default_flow_style=None,
        canonical=None, indent=None, width=None,
        allow_unicode=None, line_break=None,
        encoding='utf-8', explicit_start=None, explicit_end=None,
        version=None, tags=None):
    """
    Serialize a sequence of Python objects into a YAML stream.
    If stream is None, return the produced string instead.
    """
    getvalue = None
    if stream is None:
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        stream = StringIO()
        getvalue = stream.getvalue
    dumper = Dumper(stream, default_style=default_style,
            default_flow_style=default_flow_style,
            canonical=canonical, indent=indent, width=width,
            allow_unicode=allow_unicode, line_break=line_break,
            encoding=encoding, version=version, tags=tags,
            explicit_start=explicit_start, explicit_end=explicit_end)
    dumper.open()
    for data in documents:
        dumper.represent(data)
    dumper.close()
    if getvalue:
        return getvalue()

def dump(data, stream=None, Dumper=Dumper, **kwds):
    """
    Serialize a Python object into a YAML stream.
    If stream is None, return the produced string instead.
    """
    return dump_all([data], stream, Dumper=Dumper, **kwds)

def safe_dump_all(documents, stream=None, **kwds):
    """
    Serialize a sequence of Python objects into a YAML stream.
    Produce only basic YAML tags.
    If stream is None, return the produced string instead.
    """
    return dump_all(documents, stream, Dumper=SafeDumper, **kwds)

def safe_dump(data, stream=None, **kwds):
    """
    Serialize a Python object into a YAML stream.
    Produce only basic YAML tags.
    If stream is None, return the produced string instead.
    """
    return dump_all([data], stream, Dumper=SafeDumper, **kwds)

def add_implicit_resolver(tag, regexp, first=None,
        Loader=Loader, Dumper=Dumper):
    """
    Add an implicit scalar detector.
    If an implicit scalar value matches the given regexp,
    the corresponding tag is assigned to the scalar.
    first is a sequence of possible initial characters or None.
    """
    Loader.add_implicit_resolver(tag, regexp, first)
    Dumper.add_implicit_resolver(tag, regexp, first)

def add_path_resolver(tag, path, kind=None, Loader=Loader, Dumper=Dumper):
    """
    Add a path based resolver for the given tag.
    A path is a list of keys that forms a path
    to a node in the representation tree.
    Keys can be string values, integers, or None.
    """
    Loader.add_path_resolver(tag, path, kind)
    Dumper.add_path_resolver(tag, path, kind)

def add_constructor(tag, constructor, Loader=Loader):
    """
    Add a constructor for the given tag.
    Constructor is a function that accepts a Loader instance
    and a node object and produces the corresponding Python object.
    """
    Loader.add_constructor(tag, constructor)

def add_multi_constructor(tag_prefix, multi_constructor, Loader=Loader):
    """
    Add a multi-constructor for the given tag prefix.
    Multi-constructor is called for a node if its tag starts with tag_prefix.
    Multi-constructor accepts a Loader instance, a tag suffix,
    and a node object and produces the corresponding Python object.
    """
    Loader.add_multi_constructor(tag_prefix, multi_constructor)

def add_representer(data_type, representer, Dumper=Dumper):
    """
    Add a representer for the given type.
    Representer is a function accepting a Dumper instance
    and an instance of the given data type
    and producing the corresponding representation node.
    """
    Dumper.add_representer(data_type, representer)

def add_multi_representer(data_type, multi_representer, Dumper=Dumper):
    """
    Add a representer for the given type.
    Multi-representer is a function accepting a Dumper instance
    and an instance of the given data type or subtype
    and producing the corresponding representation node.
    """
    Dumper.add_multi_representer(data_type, multi_representer)

class YAMLObjectMetaclass(type):
    """
    The metaclass for YAMLObject.
    """
    def __init__(cls, name, bases, kwds):
        super(YAMLObjectMetaclass, cls).__init__(name, bases, kwds)
        if 'yaml_tag' in kwds and kwds['yaml_tag'] is not None:
            cls.yaml_loader.add_constructor(cls.yaml_tag, cls.from_yaml)
            cls.yaml_dumper.add_representer(cls, cls.to_yaml)

class YAMLObject(object):
    """
    An object that can dump itself to a YAML stream
    and load itself from a YAML stream.
    """

    __metaclass__ = YAMLObjectMetaclass
    __slots__ = ()  # no direct instantiation, so allow immutable subclasses

    yaml_loader = Loader
    yaml_dumper = Dumper

    yaml_tag = None
    yaml_flow_style = None

    def from_yaml(cls, loader, node):
        """
        Convert a representation node to a Python object.
        """
        return loader.construct_yaml_object(node, cls)
    from_yaml = classmethod(from_yaml)

    def to_yaml(cls, dumper, data):
        """
        Convert a Python object to a representation node.
        """
        return dumper.represent_yaml_object(cls.yaml_tag, data, cls,
                flow_style=cls.yaml_flow_style)
    to_yaml = classmethod(to_yaml)

