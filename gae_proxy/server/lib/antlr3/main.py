"""ANTLR3 runtime package"""

# begin[licence]
#
# [The "BSD licence"]
# Copyright (c) 2005-2012 Terence Parr
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# end[licence]


import sys
import argparse

from .streams import ANTLRStringStream, ANTLRFileStream, \
     ANTLRInputStream, CommonTokenStream
from .tree import CommonTreeNodeStream


class _Main(object):
    def __init__(self):
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr


    def parseArgs(self, argv):
        argParser = argparse.ArgumentParser()
        argParser.add_argument("--input")
        argParser.add_argument("--interactive", "-i", action="store_true")
        argParser.add_argument("--no-output", action="store_true")
        argParser.add_argument("--profile", action="store_true")
        argParser.add_argument("--hotshot", action="store_true")
        argParser.add_argument("--port", type=int)
        argParser.add_argument("--debug-socket", action='store_true')
        argParser.add_argument("file", nargs='?')

        self.setupArgs(argParser)

        return argParser.parse_args(argv[1:])


    def setupArgs(self, argParser):
        pass


    def execute(self, argv):
        args = self.parseArgs(argv)

        self.setUp(args)

        if args.interactive:
            while True:
                try:
                    input_str = input(">>> ")
                except (EOFError, KeyboardInterrupt):
                    self.stdout.write("\nBye.\n")
                    break

                inStream = ANTLRStringStream(input_str)
                self.parseStream(args, inStream)

        else:
            if args.input:
                inStream = ANTLRStringStream(args.input)

            elif args.file and args.file != '-':
                inStream = ANTLRFileStream(args.file)

            else:
                inStream = ANTLRInputStream(self.stdin)

            if args.profile:
                try:
                    import cProfile as profile
                except ImportError:
                    import profile

                profile.runctx(
                    'self.parseStream(args, inStream)',
                    globals(),
                    locals(),
                    'profile.dat'
                    )

                import pstats
                stats = pstats.Stats('profile.dat')
                stats.strip_dirs()
                stats.sort_stats('time')
                stats.print_stats(100)

            elif args.hotshot:
                import hotshot

                profiler = hotshot.Profile('hotshot.dat')
                profiler.runctx(
                    'self.parseStream(args, inStream)',
                    globals(),
                    locals()
                    )

            else:
                self.parseStream(args, inStream)


    def setUp(self, args):
        pass


    def parseStream(self, args, inStream):
        raise NotImplementedError


    def write(self, args, text):
        if not args.no_output:
            self.stdout.write(text)


    def writeln(self, args, text):
        self.write(args, text + '\n')


class LexerMain(_Main):
    def __init__(self, lexerClass):
        super().__init__()

        self.lexerClass = lexerClass


    def parseStream(self, args, inStream):
        lexer = self.lexerClass(inStream)
        for token in lexer:
            self.writeln(args, str(token))


class ParserMain(_Main):
    def __init__(self, lexerClassName, parserClass):
        super().__init__()

        self.lexerClassName = lexerClassName
        self.lexerClass = None
        self.parserClass = parserClass


    def setupArgs(self, argParser):
        argParser.add_argument("--lexer", dest="lexerClass",
                               default=self.lexerClassName)
        argParser.add_argument("--rule", dest="parserRule")


    def setUp(self, args):
        lexerMod = __import__(args.lexerClass)
        self.lexerClass = getattr(lexerMod, args.lexerClass)


    def parseStream(self, args, inStream):
        kwargs = {}
        if args.port is not None:
            kwargs['port'] = args.port
        if args.debug_socket:
            kwargs['debug_socket'] = sys.stderr

        lexer = self.lexerClass(inStream)
        tokenStream = CommonTokenStream(lexer)
        parser = self.parserClass(tokenStream, **kwargs)
        result = getattr(parser, args.parserRule)()
        if result:
            if hasattr(result, 'tree') and result.tree:
                self.writeln(args, result.tree.toStringTree())
            else:
                self.writeln(args, repr(result))


class WalkerMain(_Main):
    def __init__(self, walkerClass):
        super().__init__()

        self.lexerClass = None
        self.parserClass = None
        self.walkerClass = walkerClass


    def setupArgs(self, argParser):
        argParser.add_argument("--lexer", dest="lexerClass")
        argParser.add_argument("--parser", dest="parserClass")
        argParser.add_argument("--parser-rule", dest="parserRule")
        argParser.add_argument("--rule", dest="walkerRule")


    def setUp(self, args):
        lexerMod = __import__(args.lexerClass)
        self.lexerClass = getattr(lexerMod, args.lexerClass)
        parserMod = __import__(args.parserClass)
        self.parserClass = getattr(parserMod, args.parserClass)


    def parseStream(self, args, inStream):
        lexer = self.lexerClass(inStream)
        tokenStream = CommonTokenStream(lexer)
        parser = self.parserClass(tokenStream)
        result = getattr(parser, args.parserRule)()
        if result:
            assert hasattr(result, 'tree'), "Parser did not return an AST"
            nodeStream = CommonTreeNodeStream(result.tree)
            nodeStream.setTokenStream(tokenStream)
            walker = self.walkerClass(nodeStream)
            result = getattr(walker, args.walkerRule)()
            if result:
                if hasattr(result, 'tree'):
                    self.writeln(args, result.tree.toStringTree())
                else:
                    self.writeln(args, repr(result))
