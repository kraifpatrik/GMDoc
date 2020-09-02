# -*- coding: utf-8 -*-
import re

from .tokenizer import Token


class Entity(object):
    def __init__(self, _name=""):
        self.name = _name
        self.parent = None
        self.docs = None


class Macro(Entity):
    pass


class Member(Entity):
    pass


class Variable(Entity):
    def __init__(self, _name=""):
        super(Variable, self).__init__(_name)
        self.is_global = False


class Scope(Entity):
    def __init__(self, _name=""):
        self.name = _name
        self.parent = None
        self.children = []

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def __repr__(self):
        def _print(entity, indent):
            s = (" " * indent * 4) + "* " + \
                (entity.name if entity.name else "<anonymous>") + \
                " ({})\n".format(type(entity).__name__)
            if isinstance(entity, Scope):
                for c in entity.children:
                    s += _print(c, indent + 1)
            return s
        return _print(self, 0)


class Script(Scope):
    pass


class Function(Scope):
    pass


class Constructor(Function):
    pass


class Enum(Scope):
    pass


class Documentation(object):
    pass


class Parser(object):
    def __init__(self, tokens):
        self.index = 0
        self.tokens = tokens

    def mark(self):
        return (self.index,)

    def reset(self, _mark):
        self.index = _mark[0]

    def available(self):
        return len(self.tokens) - self.index

    def peek(self):
        return self.tokens[self.index]

    def next(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    def consume(self, _value=None, _type=None, _ignore_whitespace=True, _ignore_comments=True):
        mark = self.mark()
        while self.available():
            token = self.next()
            if _ignore_whitespace and token.is_whitespace():
                continue
            if _ignore_comments and token.is_comment():
                continue
            if _value != None and token.value != _value:
                self.reset(mark)
                return None
            if _type != None and token.type != _type:
                self.reset(mark)
                return None
            return token
        self.reset(mark)
        return None

    def find(self, _value=None, _type=None):
        mark = self.mark()
        while self.available():
            token = self.next()
            if _value != None and token.value != _value:
                continue
            if _type != None and token.type != _type:
                continue
            return token
        self.reset(mark)
        return None

    def _parse_function(self, _method=False):
        # TODO: Mark and reset on errors

        if not self.consume(_type=Token.Type.FUNCTION):
            return None

        name = self.consume(_type=Token.Type.NAME)
        self.consume(_type=Token.Type.BRACKET_LEFT)

        while self.consume(_type=Token.Type.NAME):
            self.consume(_type=Token.Type.COMMA)

        self.consume(_type=Token.Type.BRACKET_RIGHT)

        constructor = self.consume(_type=Token.Type.CONSTRUCTOR)

        self.consume(_type=Token.Type.BRACKET_CURLY_LEFT)

        if constructor:
            return Constructor(_name=name.value if name else None)

        return Function(_name=name.value if name else None)

    def parse(self, prefix=""):
        script = Script()
        current = script

        # TODO: Error handling!

        while self.available():
            token = self.peek()

            # Macros
            if token.type == Token.Type.MACRO:
                self.next()
                name = self.consume(_type=Token.Type.NAME)
                current.add_child(Macro(_name=name.value))

            # Enums
            elif token.type == Token.Type.ENUM:
                self.next()
                name = self.consume(_type=Token.Type.NAME)
                if self.consume(_type=Token.Type.BRACKET_CURLY_LEFT):
                    enum = Enum(_name=name.value)
                    current.add_child(enum)
                    current = enum

            # Global variables
            elif token.type == Token.Type.GLOBAL:
                self.next()
                self.consume(_type=Token.Type.DOT)
                name = self.consume(_type=Token.Type.NAME)
                variable = Variable(_name=name.value)
                variable.is_global = True
                current.add_child(variable)

            # Variables and names
            elif token.type == Token.Type.NAME:
                self.next()

                # Variable assignments
                if self.consume(_type=Token.Type.EQUALS):

                    # Functions
                    function = self._parse_function(_method=True)
                    if function:
                        if not function.name:
                            function.name = token.value
                        current.add_child(function)
                        current = function
                        continue

                    # Other
                    if isinstance(current, Constructor):
                        current.add_child(Variable(_name=token.value))
                        continue

                # Enum members
                if isinstance(current, Enum):
                    current.add_child(Member(_name=token.value))
                    continue

            # Named functions
            elif token.type == Token.Type.FUNCTION:
                function = self._parse_function()
                if function:
                    current.add_child(function)
                    current = function

            # Other scopes
            elif token.type == Token.Type.BRACKET_CURLY_LEFT:
                self.next()
                scope = Scope()
                current.add_child(scope)
                current = scope

            # Scope end
            elif token.type == Token.Type.BRACKET_CURLY_RIGHT:
                self.next()
                current = current.parent

            else:
                self.next()

        return script
