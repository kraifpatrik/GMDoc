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

    def parse(self, prefix=""):
        script = Script()
        current = script

        while self.index < len(self.tokens):
            self.index += 1

        return script
