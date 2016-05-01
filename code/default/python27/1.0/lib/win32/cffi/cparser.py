
from . import api, model
from .commontypes import COMMON_TYPES, resolve_common_type
try:
    from . import _pycparser as pycparser
except ImportError:
    import pycparser
import weakref, re, sys

try:
    if sys.version_info < (3,):
        import thread as _thread
    else:
        import _thread
    lock = _thread.allocate_lock()
except ImportError:
    lock = None

_r_comment = re.compile(r"/\*.*?\*/|//.*?$", re.DOTALL | re.MULTILINE)
_r_define  = re.compile(r"^\s*#\s*define\s+([A-Za-z_][A-Za-z_0-9]*)\s+(.*?)$",
                        re.MULTILINE)
_r_partial_enum = re.compile(r"=\s*\.\.\.\s*[,}]|\.\.\.\s*\}")
_r_enum_dotdotdot = re.compile(r"__dotdotdot\d+__$")
_r_partial_array = re.compile(r"\[\s*\.\.\.\s*\]")
_r_words = re.compile(r"\w+|\S")
_parser_cache = None
_r_int_literal = re.compile(r"^0?x?[0-9a-f]+u?l?$", re.IGNORECASE)

def _get_parser():
    global _parser_cache
    if _parser_cache is None:
        _parser_cache = pycparser.CParser()
    return _parser_cache

def _preprocess(csource):
    # Remove comments.  NOTE: this only work because the cdef() section
    # should not contain any string literal!
    csource = _r_comment.sub(' ', csource)
    # Remove the "#define FOO x" lines
    macros = {}
    for match in _r_define.finditer(csource):
        macroname, macrovalue = match.groups()
        macros[macroname] = macrovalue
    csource = _r_define.sub('', csource)
    # Replace "[...]" with "[__dotdotdotarray__]"
    csource = _r_partial_array.sub('[__dotdotdotarray__]', csource)
    # Replace "...}" with "__dotdotdotNUM__}".  This construction should
    # occur only at the end of enums; at the end of structs we have "...;}"
    # and at the end of vararg functions "...);".  Also replace "=...[,}]"
    # with ",__dotdotdotNUM__[,}]": this occurs in the enums too, when
    # giving an unknown value.
    matches = list(_r_partial_enum.finditer(csource))
    for number, match in enumerate(reversed(matches)):
        p = match.start()
        if csource[p] == '=':
            p2 = csource.find('...', p, match.end())
            assert p2 > p
            csource = '%s,__dotdotdot%d__ %s' % (csource[:p], number,
                                                 csource[p2+3:])
        else:
            assert csource[p:p+3] == '...'
            csource = '%s __dotdotdot%d__ %s' % (csource[:p], number,
                                                 csource[p+3:])
    # Replace all remaining "..." with the same name, "__dotdotdot__",
    # which is declared with a typedef for the purpose of C parsing.
    return csource.replace('...', ' __dotdotdot__ '), macros

def _common_type_names(csource):
    # Look in the source for what looks like usages of types from the
    # list of common types.  A "usage" is approximated here as the
    # appearance of the word, minus a "definition" of the type, which
    # is the last word in a "typedef" statement.  Approximative only
    # but should be fine for all the common types.
    look_for_words = set(COMMON_TYPES)
    look_for_words.add(';')
    look_for_words.add('typedef')
    words_used = set()
    is_typedef = False
    previous_word = ''
    for word in _r_words.findall(csource):
        if word in look_for_words:
            if word == ';':
                if is_typedef:
                    words_used.discard(previous_word)
                    look_for_words.discard(previous_word)
                    is_typedef = False
            elif word == 'typedef':
                is_typedef = True
            else:   # word in COMMON_TYPES
                words_used.add(word)
        previous_word = word
    return words_used


class Parser(object):

    def __init__(self):
        self._declarations = {}
        self._anonymous_counter = 0
        self._structnode2type = weakref.WeakKeyDictionary()
        self._override = False
        self._packed = False
        self._int_constants = {}

    def _parse(self, csource):
        csource, macros = _preprocess(csource)
        # XXX: for more efficiency we would need to poke into the
        # internals of CParser...  the following registers the
        # typedefs, because their presence or absence influences the
        # parsing itself (but what they are typedef'ed to plays no role)
        ctn = _common_type_names(csource)
        typenames = []
        for name in sorted(self._declarations):
            if name.startswith('typedef '):
                name = name[8:]
                typenames.append(name)
                ctn.discard(name)
        typenames += sorted(ctn)
        #
        csourcelines = ['typedef int %s;' % typename for typename in typenames]
        csourcelines.append('typedef int __dotdotdot__;')
        csourcelines.append(csource)
        csource = '\n'.join(csourcelines)
        if lock is not None:
            lock.acquire()     # pycparser is not thread-safe...
        try:
            ast = _get_parser().parse(csource)
        except pycparser.c_parser.ParseError as e:
            self.convert_pycparser_error(e, csource)
        finally:
            if lock is not None:
                lock.release()
        # csource will be used to find buggy source text
        return ast, macros, csource

    def _convert_pycparser_error(self, e, csource):
        # xxx look for ":NUM:" at the start of str(e) and try to interpret
        # it as a line number
        line = None
        msg = str(e)
        if msg.startswith(':') and ':' in msg[1:]:
            linenum = msg[1:msg.find(':',1)]
            if linenum.isdigit():
                linenum = int(linenum, 10)
                csourcelines = csource.splitlines()
                if 1 <= linenum <= len(csourcelines):
                    line = csourcelines[linenum-1]
        return line

    def convert_pycparser_error(self, e, csource):
        line = self._convert_pycparser_error(e, csource)

        msg = str(e)
        if line:
            msg = 'cannot parse "%s"\n%s' % (line.strip(), msg)
        else:
            msg = 'parse error\n%s' % (msg,)
        raise api.CDefError(msg)

    def parse(self, csource, override=False, packed=False):
        prev_override = self._override
        prev_packed = self._packed
        try:
            self._override = override
            self._packed = packed
            self._internal_parse(csource)
        finally:
            self._override = prev_override
            self._packed = prev_packed

    def _internal_parse(self, csource):
        ast, macros, csource = self._parse(csource)
        # add the macros
        self._process_macros(macros)
        # find the first "__dotdotdot__" and use that as a separator
        # between the repeated typedefs and the real csource
        iterator = iter(ast.ext)
        for decl in iterator:
            if decl.name == '__dotdotdot__':
                break
        #
        try:
            for decl in iterator:
                if isinstance(decl, pycparser.c_ast.Decl):
                    self._parse_decl(decl)
                elif isinstance(decl, pycparser.c_ast.Typedef):
                    if not decl.name:
                        raise api.CDefError("typedef does not declare any name",
                                            decl)
                    if (isinstance(decl.type.type, pycparser.c_ast.IdentifierType)
                            and decl.type.type.names == ['__dotdotdot__']):
                        realtype = model.unknown_type(decl.name)
                    elif (isinstance(decl.type, pycparser.c_ast.PtrDecl) and
                          isinstance(decl.type.type, pycparser.c_ast.TypeDecl) and
                          isinstance(decl.type.type.type,
                                     pycparser.c_ast.IdentifierType) and
                          decl.type.type.type.names == ['__dotdotdot__']):
                        realtype = model.unknown_ptr_type(decl.name)
                    else:
                        realtype = self._get_type(decl.type, name=decl.name)
                    self._declare('typedef ' + decl.name, realtype)
                else:
                    raise api.CDefError("unrecognized construct", decl)
        except api.FFIError as e:
            msg = self._convert_pycparser_error(e, csource)
            if msg:
                e.args = (e.args[0] + "\n    *** Err: %s" % msg,)
            raise

    def _add_constants(self, key, val):
        if key in self._int_constants:
            raise api.FFIError(
                "multiple declarations of constant: %s" % (key,))
        self._int_constants[key] = val

    def _process_macros(self, macros):
        for key, value in macros.items():
            value = value.strip()
            match = _r_int_literal.search(value)
            if match is not None:
                int_str = match.group(0).lower().rstrip("ul")

                # "010" is not valid oct in py3
                if (int_str.startswith("0") and
                        int_str != "0" and
                        not int_str.startswith("0x")):
                    int_str = "0o" + int_str[1:]

                pyvalue = int(int_str, 0)
                self._add_constants(key, pyvalue)
            elif value == '...':
                self._declare('macro ' + key, value)
            else:
                raise api.CDefError('only supports the syntax "#define '
                                    '%s ..." (literally) or "#define '
                                    '%s 0x1FF" for now' % (key, key))

    def _parse_decl(self, decl):
        node = decl.type
        if isinstance(node, pycparser.c_ast.FuncDecl):
            tp = self._get_type(node, name=decl.name)
            assert isinstance(tp, model.RawFunctionType)
            tp = self._get_type_pointer(tp)
            self._declare('function ' + decl.name, tp)
        else:
            if isinstance(node, pycparser.c_ast.Struct):
                # XXX do we need self._declare in any of those?
                if node.decls is not None:
                    self._get_struct_union_enum_type('struct', node)
            elif isinstance(node, pycparser.c_ast.Union):
                if node.decls is not None:
                    self._get_struct_union_enum_type('union', node)
            elif isinstance(node, pycparser.c_ast.Enum):
                if node.values is not None:
                    self._get_struct_union_enum_type('enum', node)
            elif not decl.name:
                raise api.CDefError("construct does not declare any variable",
                                    decl)
            #
            if decl.name:
                tp = self._get_type(node, partial_length_ok=True)
                if self._is_constant_globalvar(node):
                    self._declare('constant ' + decl.name, tp)
                else:
                    self._declare('variable ' + decl.name, tp)

    def parse_type(self, cdecl):
        ast, macros = self._parse('void __dummy(\n%s\n);' % cdecl)[:2]
        assert not macros
        exprnode = ast.ext[-1].type.args.params[0]
        if isinstance(exprnode, pycparser.c_ast.ID):
            raise api.CDefError("unknown identifier '%s'" % (exprnode.name,))
        return self._get_type(exprnode.type)

    def _declare(self, name, obj):
        if name in self._declarations:
            if self._declarations[name] is obj:
                return
            if not self._override:
                raise api.FFIError(
                    "multiple declarations of %s (for interactive usage, "
                    "try cdef(xx, override=True))" % (name,))
        assert '__dotdotdot__' not in name.split()
        self._declarations[name] = obj

    def _get_type_pointer(self, type, const=False):
        if isinstance(type, model.RawFunctionType):
            return type.as_function_pointer()
        if const:
            return model.ConstPointerType(type)
        return model.PointerType(type)

    def _get_type(self, typenode, name=None, partial_length_ok=False):
        # first, dereference typedefs, if we have it already parsed, we're good
        if (isinstance(typenode, pycparser.c_ast.TypeDecl) and
            isinstance(typenode.type, pycparser.c_ast.IdentifierType) and
            len(typenode.type.names) == 1 and
            ('typedef ' + typenode.type.names[0]) in self._declarations):
            type = self._declarations['typedef ' + typenode.type.names[0]]
            return type
        #
        if isinstance(typenode, pycparser.c_ast.ArrayDecl):
            # array type
            if typenode.dim is None:
                length = None
            else:
                length = self._parse_constant(
                    typenode.dim, partial_length_ok=partial_length_ok)
            return model.ArrayType(self._get_type(typenode.type), length)
        #
        if isinstance(typenode, pycparser.c_ast.PtrDecl):
            # pointer type
            const = (isinstance(typenode.type, pycparser.c_ast.TypeDecl)
                     and 'const' in typenode.type.quals)
            return self._get_type_pointer(self._get_type(typenode.type), const)
        #
        if isinstance(typenode, pycparser.c_ast.TypeDecl):
            type = typenode.type
            if isinstance(type, pycparser.c_ast.IdentifierType):
                # assume a primitive type.  get it from .names, but reduce
                # synonyms to a single chosen combination
                names = list(type.names)
                if names != ['signed', 'char']:    # keep this unmodified
                    prefixes = {}
                    while names:
                        name = names[0]
                        if name in ('short', 'long', 'signed', 'unsigned'):
                            prefixes[name] = prefixes.get(name, 0) + 1
                            del names[0]
                        else:
                            break
                    # ignore the 'signed' prefix below, and reorder the others
                    newnames = []
                    for prefix in ('unsigned', 'short', 'long'):
                        for i in range(prefixes.get(prefix, 0)):
                            newnames.append(prefix)
                    if not names:
                        names = ['int']    # implicitly
                    if names == ['int']:   # but kill it if 'short' or 'long'
                        if 'short' in prefixes or 'long' in prefixes:
                            names = []
                    names = newnames + names
                ident = ' '.join(names)
                if ident == 'void':
                    return model.void_type
                if ident == '__dotdotdot__':
                    raise api.FFIError(':%d: bad usage of "..."' %
                            typenode.coord.line)
                return resolve_common_type(ident)
            #
            if isinstance(type, pycparser.c_ast.Struct):
                # 'struct foobar'
                return self._get_struct_union_enum_type('struct', type, name)
            #
            if isinstance(type, pycparser.c_ast.Union):
                # 'union foobar'
                return self._get_struct_union_enum_type('union', type, name)
            #
            if isinstance(type, pycparser.c_ast.Enum):
                # 'enum foobar'
                return self._get_struct_union_enum_type('enum', type, name)
        #
        if isinstance(typenode, pycparser.c_ast.FuncDecl):
            # a function type
            return self._parse_function_type(typenode, name)
        #
        # nested anonymous structs or unions end up here
        if isinstance(typenode, pycparser.c_ast.Struct):
            return self._get_struct_union_enum_type('struct', typenode, name,
                                                    nested=True)
        if isinstance(typenode, pycparser.c_ast.Union):
            return self._get_struct_union_enum_type('union', typenode, name,
                                                    nested=True)
        #
        raise api.FFIError(":%d: bad or unsupported type declaration" %
                typenode.coord.line)

    def _parse_function_type(self, typenode, funcname=None):
        params = list(getattr(typenode.args, 'params', []))
        ellipsis = (
            len(params) > 0 and
            isinstance(params[-1].type, pycparser.c_ast.TypeDecl) and
            isinstance(params[-1].type.type,
                       pycparser.c_ast.IdentifierType) and
            params[-1].type.type.names == ['__dotdotdot__'])
        if ellipsis:
            params.pop()
            if not params:
                raise api.CDefError(
                    "%s: a function with only '(...)' as argument"
                    " is not correct C" % (funcname or 'in expression'))
        elif (len(params) == 1 and
            isinstance(params[0].type, pycparser.c_ast.TypeDecl) and
            isinstance(params[0].type.type, pycparser.c_ast.IdentifierType)
                and list(params[0].type.type.names) == ['void']):
            del params[0]
        args = [self._as_func_arg(self._get_type(argdeclnode.type))
                for argdeclnode in params]
        result = self._get_type(typenode.type)
        return model.RawFunctionType(tuple(args), result, ellipsis)

    def _as_func_arg(self, type):
        if isinstance(type, model.ArrayType):
            return model.PointerType(type.item)
        elif isinstance(type, model.RawFunctionType):
            return type.as_function_pointer()
        else:
            return type

    def _is_constant_globalvar(self, typenode):
        if isinstance(typenode, pycparser.c_ast.PtrDecl):
            return 'const' in typenode.quals
        if isinstance(typenode, pycparser.c_ast.TypeDecl):
            return 'const' in typenode.quals
        return False

    def _get_struct_union_enum_type(self, kind, type, name=None, nested=False):
        # First, a level of caching on the exact 'type' node of the AST.
        # This is obscure, but needed because pycparser "unrolls" declarations
        # such as "typedef struct { } foo_t, *foo_p" and we end up with
        # an AST that is not a tree, but a DAG, with the "type" node of the
        # two branches foo_t and foo_p of the trees being the same node.
        # It's a bit silly but detecting "DAG-ness" in the AST tree seems
        # to be the only way to distinguish this case from two independent
        # structs.  See test_struct_with_two_usages.
        try:
            return self._structnode2type[type]
        except KeyError:
            pass
        #
        # Note that this must handle parsing "struct foo" any number of
        # times and always return the same StructType object.  Additionally,
        # one of these times (not necessarily the first), the fields of
        # the struct can be specified with "struct foo { ...fields... }".
        # If no name is given, then we have to create a new anonymous struct
        # with no caching; in this case, the fields are either specified
        # right now or never.
        #
        force_name = name
        name = type.name
        #
        # get the type or create it if needed
        if name is None:
            # 'force_name' is used to guess a more readable name for
            # anonymous structs, for the common case "typedef struct { } foo".
            if force_name is not None:
                explicit_name = '$%s' % force_name
            else:
                self._anonymous_counter += 1
                explicit_name = '$%d' % self._anonymous_counter
            tp = None
        else:
            explicit_name = name
            key = '%s %s' % (kind, name)
            tp = self._declarations.get(key, None)
        #
        if tp is None:
            if kind == 'struct':
                tp = model.StructType(explicit_name, None, None, None)
            elif kind == 'union':
                tp = model.UnionType(explicit_name, None, None, None)
            elif kind == 'enum':
                tp = self._build_enum_type(explicit_name, type.values)
            else:
                raise AssertionError("kind = %r" % (kind,))
            if name is not None:
                self._declare(key, tp)
        else:
            if kind == 'enum' and type.values is not None:
                raise NotImplementedError(
                    "enum %s: the '{}' declaration should appear on the first "
                    "time the enum is mentioned, not later" % explicit_name)
        if not tp.forcename:
            tp.force_the_name(force_name)
        if tp.forcename and '$' in tp.name:
            self._declare('anonymous %s' % tp.forcename, tp)
        #
        self._structnode2type[type] = tp
        #
        # enums: done here
        if kind == 'enum':
            return tp
        #
        # is there a 'type.decls'?  If yes, then this is the place in the
        # C sources that declare the fields.  If no, then just return the
        # existing type, possibly still incomplete.
        if type.decls is None:
            return tp
        #
        if tp.fldnames is not None:
            raise api.CDefError("duplicate declaration of struct %s" % name)
        fldnames = []
        fldtypes = []
        fldbitsize = []
        for decl in type.decls:
            if (isinstance(decl.type, pycparser.c_ast.IdentifierType) and
                    ''.join(decl.type.names) == '__dotdotdot__'):
                # XXX pycparser is inconsistent: 'names' should be a list
                # of strings, but is sometimes just one string.  Use
                # str.join() as a way to cope with both.
                self._make_partial(tp, nested)
                continue
            if decl.bitsize is None:
                bitsize = -1
            else:
                bitsize = self._parse_constant(decl.bitsize)
            self._partial_length = False
            type = self._get_type(decl.type, partial_length_ok=True)
            if self._partial_length:
                self._make_partial(tp, nested)
            if isinstance(type, model.StructType) and type.partial:
                self._make_partial(tp, nested)
            fldnames.append(decl.name or '')
            fldtypes.append(type)
            fldbitsize.append(bitsize)
        tp.fldnames = tuple(fldnames)
        tp.fldtypes = tuple(fldtypes)
        tp.fldbitsize = tuple(fldbitsize)
        if fldbitsize != [-1] * len(fldbitsize):
            if isinstance(tp, model.StructType) and tp.partial:
                raise NotImplementedError("%s: using both bitfields and '...;'"
                                          % (tp,))
        tp.packed = self._packed
        return tp

    def _make_partial(self, tp, nested):
        if not isinstance(tp, model.StructOrUnion):
            raise api.CDefError("%s cannot be partial" % (tp,))
        if not tp.has_c_name() and not nested:
            raise NotImplementedError("%s is partial but has no C name" %(tp,))
        tp.partial = True

    def _parse_constant(self, exprnode, partial_length_ok=False):
        # for now, limited to expressions that are an immediate number
        # or negative number
        if isinstance(exprnode, pycparser.c_ast.Constant):
            return int(exprnode.value, 0)
        #
        if (isinstance(exprnode, pycparser.c_ast.UnaryOp) and
                exprnode.op == '-'):
            return -self._parse_constant(exprnode.expr)
        # load previously defined int constant
        if (isinstance(exprnode, pycparser.c_ast.ID) and
                exprnode.name in self._int_constants):
            return self._int_constants[exprnode.name]
        #
        if partial_length_ok:
            if (isinstance(exprnode, pycparser.c_ast.ID) and
                    exprnode.name == '__dotdotdotarray__'):
                self._partial_length = True
                return '...'
        #
        raise api.FFIError(":%d: unsupported expression: expected a "
                           "simple numeric constant" % exprnode.coord.line)

    def _build_enum_type(self, explicit_name, decls):
        if decls is not None:
            enumerators1 = [enum.name for enum in decls.enumerators]
            enumerators = [s for s in enumerators1
                             if not _r_enum_dotdotdot.match(s)]
            partial = len(enumerators) < len(enumerators1)
            enumerators = tuple(enumerators)
            enumvalues = []
            nextenumvalue = 0
            for enum in decls.enumerators[:len(enumerators)]:
                if enum.value is not None:
                    nextenumvalue = self._parse_constant(enum.value)
                enumvalues.append(nextenumvalue)
                self._add_constants(enum.name, nextenumvalue)
                nextenumvalue += 1
            enumvalues = tuple(enumvalues)
            tp = model.EnumType(explicit_name, enumerators, enumvalues)
            tp.partial = partial
        else:   # opaque enum
            tp = model.EnumType(explicit_name, (), ())
        return tp

    def include(self, other):
        for name, tp in other._declarations.items():
            kind = name.split(' ', 1)[0]
            if kind in ('typedef', 'struct', 'union', 'enum'):
                self._declare(name, tp)
        for k, v in other._int_constants.items():
            self._add_constants(k, v)
