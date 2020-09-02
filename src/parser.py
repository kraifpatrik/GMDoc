# -*- coding: utf-8 -*-
import re

from .tokenizer import Token


class Scope(object):
    def __init__(self, _name=""):
        self.name = _name
        self.parent = None
        self.children = []

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def __repr__(self):
        def _print(scope, indent):
            s = (" " * indent * 4) + "* " + \
                (scope.name if scope.name else "<anonymous>") + "\n"
            for c in scope.children:
                s += _print(c, indent + 1)
            return s
        return _print(self, 0)


class Script(Scope):
    pass


class Function(Scope):
    pass


class Constructor(Scope):
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

    def consume(self, _value=None, _type=None, _ignore_whitespace=True):
        mark = self.mark()
        while self.available():
            token = self.next()
            if _ignore_whitespace and token.is_whitespace():
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

    def parse(self, prefix=""):
        script = Script()
        current = script

        while self.available():
            token = self.next()

            if token.type == Token.Type.FUNCTION:
                name = self.consume(_type=Token.Type.NAME)
                if name:
                    if self.find(_type=Token.Type.BRACKET_CURLY_LEFT):
                        function = Function(_name=name.value)
                        current.add_child(function)
                        current = function

            elif token.type == Token.Type.BRACKET_CURLY_LEFT:
                scope = Scope()
                current.add_child(scope)
                current = scope

            elif token.type == Token.Type.BRACKET_CURLY_RIGHT:
                current = current.parent

        return script
