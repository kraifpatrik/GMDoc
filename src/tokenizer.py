# -*- coding: utf-8 -*-
import re
from enum import Enum


class TokenizationError(Exception):
    pass


class Token(object):
    class Type(Enum):
        BOOL = 0
        COMMENT = 1
        DELIMITER = 2
        EOF = 3
        KEYWORD = 4
        MACRO = 5
        NAME = 6
        NEWLINE = 7
        NUMBER = 8
        STRING = 9
        UNDEFINED = 10
        WHITESPACE = 11

    def __init__(self, _value: str, _type: int, _at: int, _len: int):
        self.value = _value
        self.type = _type
        self.at = _at
        self.len = _len

    def __repr__(self):
        return "<{}, {}, {}, {}>".format(
            repr(self.value),
            self.type,
            self.at,
            self.len)


RESERVED = {
    "all": Token.Type.KEYWORD,
    "begin": Token.Type.KEYWORD,
    "break": Token.Type.KEYWORD,
    "case": Token.Type.KEYWORD,
    "catch": Token.Type.KEYWORD,
    "constructor": Token.Type.KEYWORD,
    "continue": Token.Type.KEYWORD,
    "delete": Token.Type.KEYWORD,
    "div": Token.Type.KEYWORD,
    "do": Token.Type.KEYWORD,
    "else": Token.Type.KEYWORD,
    "end": Token.Type.KEYWORD,
    "enum": Token.Type.KEYWORD,
    "exit": Token.Type.KEYWORD,
    "finally": Token.Type.KEYWORD,
    "for": Token.Type.KEYWORD,
    "function": Token.Type.KEYWORD,
    "if": Token.Type.KEYWORD,
    "mod": Token.Type.KEYWORD,
    "new": Token.Type.KEYWORD,
    "noone": Token.Type.KEYWORD,
    "other": Token.Type.KEYWORD,
    "repeat": Token.Type.KEYWORD,
    "return": Token.Type.KEYWORD,
    "self": Token.Type.KEYWORD,
    "switch": Token.Type.KEYWORD,
    "throw": Token.Type.KEYWORD,
    "try": Token.Type.KEYWORD,
    "var": Token.Type.KEYWORD,
    "while": Token.Type.KEYWORD,
}


class Tokenizer(object):
    def tokenize(self, _code: str):
        tokens = []
        at = 0

        def get_token(_regex, _type):
            m = re.match(_regex, _code, flags=re.IGNORECASE)
            if m:
                _start = m.start(0)
                _len = m.end(0)
                token = Token(m.group(0), _type, at + _start, _len - _start)
                return token
            return None

        while _code:
            token = None

            for k, v in RESERVED.items():
                token = get_token(r"^" + k + r"\b", v)
                if token:
                    break

            if not token:
                token = (get_token(r"^#macro\b", Token.Type.MACRO) or
                        get_token(r"^\/\*[\s\S]*\*\/", Token.Type.COMMENT) or
                        get_token(r"^\/\/+[^\n]*", Token.Type.COMMENT) or
                        get_token(r"^[a-z_][a-z0-9_]*", Token.Type.NAME) or
                        get_token(r"^\d+\.?\d*|\.\d+", Token.Type.NUMBER) or
                        get_token(r"^\$[a-f0-9]+", Token.Type.NUMBER) or
                        get_token(r"^@\"(\\\"|[^\"])*\"", Token.Type.STRING) or
                        get_token(r"^\"(\\\"|[^\"\n])*\"", Token.Type.STRING) or
                        get_token(r"^\n", Token.Type.NEWLINE) or
                        get_token(r"^\s+", Token.Type.WHITESPACE) or
                        get_token(r"^[~!@#$%^&*()-_=+[\]{};:,<.>/?|]", Token.Type.DELIMITER))

            if token:
                tokens.append(token)
                _code = _code[token.len:]
                at += token.len
            else:
                raise TokenizationError()
        tokens.append(Token("", Token.Type.EOF, at, 0))

        return tokens
