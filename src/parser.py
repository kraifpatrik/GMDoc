# -*- coding: utf-8 -*-
import re

from .tokenizer import Token


class Entity(object):
    def __init__(self, _name="", _docs=None):
        self.name = _name
        self.parent = None
        self.docs = _docs


class Macro(Entity):
    pass


class Member(Entity):
    pass


class Variable(Entity):
    def __init__(self, **kwargs):
        super(Variable, self).__init__(**kwargs)
        self.is_global = False


class Scope(Entity):
    def __init__(self, **kwargs):
        super(Scope, self).__init__(**kwargs)
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
    def __init__(self):
        pass

    @staticmethod
    def from_string(_str):
        docs = Documentation()

        _str = _str.replace("///", "")

        while True:
            # Tag
            m = re.match(r"\s*@([a-z]+)", _str)
            if not m:
                break

            tag = m.group(1)
            print("Tag", tag)
            _str = _str[m.end(0):]

            # Optional type
            m = re.match(r"\s*\{([^\}]*)\}", _str)
            if m:
                typestr = m.group(1)
                print("Type", typestr)
                _str = _str[m.end(0):]
            else:
                typestr = None

            # Param name
            name = None
            if tag == "param":
                m = re.match(r"\s*\[?([a-z_]+[a-z0-9_]*)\]?", _str, flags=re.IGNORECASE)
                if m:
                    name = m.group(1)
                    print("Name", name)
                    _str = _str[m.end(0):]

            # Description
            s = re.search(r"@[a-z]+", _str)
            end = s.start(0) if s else len(_str)
            desc = _str[:end].strip()

            # Handle markdown code
            split = desc.split("```")
            for i in range(len(split)):
                if i % 2:
                    # TODO: Delete spaces based on indent of opening ```
                    split[i] = re.sub(r"\n ", "\n", split[i])
                else:
                    split[i] = "\n" + re.sub(r"\s+", " ", split[i]).strip() + "\n"
            desc = "```".join(split).strip()
            print(desc)

            _str = _str[end:]

        return docs


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
        documentation = None

        # TODO: Error handling!

        while self.available():
            token = self.peek()

            # Documentation
            if token.type == Token.Type.DOCUMENTATION:
                docstr = ""
                while True:
                    docs = self.consume(
                        _type=Token.Type.DOCUMENTATION, _ignore_comments=False)
                    if docs:
                        docstr += docs.value + "\n"
                    else:
                        documentation = Documentation.from_string(docstr)
                        break

            # Macros
            elif token.type == Token.Type.MACRO:
                self.next()
                name = self.consume(_type=Token.Type.NAME)
                macro = Macro(_name=name.value, _docs=documentation)
                documentation = None
                current.add_child(macro)

            # Enums
            elif token.type == Token.Type.ENUM:
                self.next()
                name = self.consume(_type=Token.Type.NAME)
                if self.consume(_type=Token.Type.BRACKET_CURLY_LEFT):
                    enum = Enum(_name=name.value, _docs=documentation)
                    documentation = None
                    current.add_child(enum)
                    current = enum

            # Global variables
            elif token.type == Token.Type.GLOBAL:
                self.next()
                self.consume(_type=Token.Type.DOT)
                name = self.consume(_type=Token.Type.NAME)
                variable = Variable(_name=name.value, _docs=documentation)
                documentation = None
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
                        function.docs = documentation
                        documentation = None
                        if not function.name:
                            function.name = token.value
                        current.add_child(function)
                        current = function
                        continue

                    # Other
                    if isinstance(current, Constructor):
                        variable = Variable(_name=token.value, _docs=documentation)
                        documentation = None
                        current.add_child(variable)
                        continue

                # Enum members
                if isinstance(current, Enum):
                    member = Member(_name=token.value, _docs=documentation)
                    documentation = None
                    current.add_child(member)
                    continue

            # Named functions
            elif token.type == Token.Type.FUNCTION:
                function = self._parse_function()
                if function:
                    function.docs = documentation
                    documentation = None
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
