# -*- coding: utf-8 -*-
import re

from .tokenizer import Token


class Parser:
    def __init__(self, tokens):
        self.index = 0
        self.tokens = tokens

    def _next(self):
        self.index += 1

    def _peek(self):
        if self.index < len(self.tokens):
            token = self.tokens[self.index]
            return token
        return None

    def _find_comment_block(self):
        while True:
            peek = self._peek()
            if peek.type == Token.Type.EOF:
                return False
            if peek.type == Token.Type.COMMENT_START:
                break
            self._next()
        self._next()
        return True

    def _parse_var(self):
        # Check if the current token is a var tag
        t = self._peek()
        if not t.is_tag("var"):
            return None
        self._next()

        # Type
        t = self._peek()
        type_ = None
        if t.type == Token.Type.TYPE:
            type_ = t.value
            self._next()

        # Description
        t = self._peek()
        desc = ""
        while t.type != Token.Type.COMMENT_END:
            desc += t.value + " "
            self._next()
            t = self._peek()
        desc = desc.strip()
        self._next()

        # Name
        t = self._peek()
        name = ""
        while name == "" and t.type == Token.Type.CODE:
            m = re.match(r"\s*((global\.)?\w+)", t.value)
            if not m:
                self._next()
                t = self._peek()
                continue
            name = m.group(1)
        self._next()

        if name and desc:
            return {
                "_type": "variable",
                "name": name,
                "type": type_,
                "desc": desc,
            }

        return None

    def _parse_enum(self):
        # Check if the current token is an enum tag
        t = self._peek()
        if not t.is_tag("enum"):
            return None
        self._next()

        # Description
        t = self._peek()
        desc = ""
        while t.type != Token.Type.COMMENT_END:
            desc += t.value + " "
            self._next()
            t = self._peek()
        desc = desc.strip()
        self._next()

        # Name
        t = self._peek()
        name = ""
        while name == "" and t.type == Token.Type.CODE:
            m = re.match(r"\s*enum\s+(\w+)", t.value)
            if not m:
                self._next()
                t = self._peek()
                continue
            name = m.group(1)
        self._next()

        # Members
        members = []
        while True:
            _backup = self.index
            if not self._find_comment_block():
                break
            member = self._parse_member()
            if member:
                members.append(member)
            else:
                self.index = _backup
                break

        if name and desc:
            return {
                "_type": "enum",
                "name": name,
                "desc": desc,
                "members": members
            }

        return None

    def _parse_member(self):
        # Check if the current token is an enum tag
        t = self._peek()
        if not t.is_tag("member"):
            return None
        self._next()

        # Description
        t = self._peek()
        desc = ""
        while t.type != Token.Type.COMMENT_END:
            desc += t.value + " "
            self._next()
            t = self._peek()
        desc = desc.strip()
        self._next()

        # Name
        t = self._peek()
        name = ""
        while name == "" and t.type == Token.Type.CODE:
            m = re.match(r"\s*(\w+)", t.value)
            if not m:
                self._next()
                t = self._peek()
                continue
            name = m.group(1)
        self._next()

        if name and desc:
            return {
                "name": name,
                "desc": desc,
            }

        return None

    def _parse_macro(self):
        # Check if the current token is a macro tag
        t = self._peek()
        if not t.is_tag("macro"):
            return None
        self._next()

        # Type
        t = self._peek()
        type_ = None
        if t.type == Token.Type.TYPE:
            type_ = t.value
            self._next()

        # Description
        t = self._peek()
        desc = ""
        while t.type != Token.Type.COMMENT_END:
            desc += t.value + " "
            self._next()
            t = self._peek()
        desc = desc.strip()
        self._next()

        # Name
        t = self._peek()
        name = ""
        while name == "" and t.type == Token.Type.CODE:
            m = re.match(r"\s*#macro\s+(\w+)", t.value)
            if not m:
                self._next()
                t = self._peek()
                continue
            name = m.group(1)
        self._next()

        if name and desc:
            return {
                "_type": "macro",
                "name": name,
                "type": type_,
                "desc": desc
            }

        return None

    def _parse_function(self):
        # Check if the current token is a function tag
        t = self._peek()
        if not t.is_tag("func"):
            return None
        self._next()

        # Signature and name
        t = self._peek()
        name = ""
        signature = ""
        if t.type == Token.Type.COMMENT:
            signature = t.value.strip()
            name = signature.split("(")[0].strip()
            self._next()

        # Tags
        desc = ""
        params = []
        returns = None
        example = ""
        see = []
        note = ""
        source = ""

        while True:
            _desc = self._parse_function_desc()
            if _desc:
                desc = _desc
                continue

            _param = self._parse_function_param()
            if _param:
                params.append(_param)
                continue

            _retval = self._parse_function_retval()
            if _retval:
                returns = _retval
                continue

            _example = self._parse_function_example()
            if _example:
                example = _example
                continue

            _note = self._parse_function_note()
            if _note:
                note = _note
                continue

            _see = self._parse_function_see()
            if _see:
                see.append(_see)
                continue

            _source = self._parse_function_source()
            if _source:
                source = _source
                continue

            break

        if name:
            return {
                "_type": "script",
                "name": name,
                "signature": signature,
                "desc": desc,
                "params": params,
                "return": returns,
                "example": example,
                "see": see,
                "note": note,
                "source": source,
            }

        return None

    def _parse_function_desc(self):
        t = self._peek()
        if not t.is_tag("desc"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value + " "
            self._next()

        return desc.strip()

    def _parse_function_param(self):
        t = self._peek()
        if not t.is_tag("param"):
            return None
        self._next()

        # Type
        t = self._peek()
        type_ = None
        if t.type == Token.Type.TYPE:
            type_ = t.value
            self._next()

        # Name and desc
        name = ""
        desc = ""

        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            if not name:
                m = re.match(r"([\S]+)([\s\S]*)?", t.value)
                if not m:
                    m = re.match(r"(\w+)\b([\s\S]*)?", t.value)
                if m:
                    name = m.group(1)
                    desc = m.group(2).strip()
            else:
                desc += " " + t.value
            self._next()
        desc = desc.strip()

        if name:
            return {
                "name": name,
                "type": type_,
                "desc": desc,
            }

        return None

    def _parse_function_retval(self):
        t = self._peek()
        if not t.is_tag("return"):
            return None
        self._next()

        # Type
        t = self._peek()
        type_ = None
        if t.type == Token.Type.TYPE:
            type_ = t.value
            self._next()

        # Description
        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value + " "
            self._next()
        desc = desc.strip()

        if type_ or desc:
            return {
                "desc": desc,
                "type": type_
            }

        return None

    def _parse_function_example(self):
        t = self._peek()
        if not t.is_tag("example"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value
            self._next()

        return desc.rstrip()

    def _parse_function_see(self):
        t = self._peek()
        if not t.is_tag("see"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value
            self._next()

        return desc.strip()

    def _parse_function_note(self):
        t = self._peek()
        if not t.is_tag("note"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value
            self._next()

        return desc.rstrip()

    def _parse_function_source(self):
        t = self._peek()
        if not t.is_tag("source"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value + " "
            self._next()

        return desc.strip()

    def parse(self):
        enums = []
        functions = []
        macros = []
        variables = []

        while True:
            if not self._find_comment_block():
                break

            _enum = self._parse_enum()
            if _enum:
                enums.append(_enum)
                continue

            _fn = self._parse_function()
            if _fn:
                functions.append(_fn)
                continue

            _macro = self._parse_macro()
            if _macro:
                macros.append(_macro)
                continue

            _var = self._parse_var()
            if _var:
                variables.append(_var)
                continue

            break

        t = self._peek()
        if t and t.type != Token.Type.EOF:
            print(t)
            raise Exception("File was not parsed entirely!")

        return {
            "enums": enums,
            "functions": functions,
            "macros": macros,
            "variables": variables,
        }
