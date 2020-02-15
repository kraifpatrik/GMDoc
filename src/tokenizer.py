# -*- coding: utf-8 -*-
import re
from enum import Enum


class Token:
    class Type(Enum):
        COMMENT_START = 0
        TAG = 1
        TYPE = 2
        COMMENT = 3
        COMMENT_END = 4
        CODE = 5
        EOF = 6

    def __init__(self, value, type_):
        self.value = value
        self.type = type_

    def __repr__(self):
        return "<{}, {}>".format(repr(self.value), self.type)

    def is_tag(self, name):
        return self.type == Token.Type.TAG and self.value == name


def string_char_at(string, idx):
    try:
        return string[idx]
    except:
        return ""


def tokenize(f):
    tokens = []
    is_comment = False

    for line in f:
        # Ignore all / comment lines
        m = re.match(r"\s*(/){4,}\s*", line)
        if m:
            continue

        m = re.match(r"(.*)///([\s\S]*)", line)

        # Line does not have any documentation comments
        if not m:
            # Insert comment end tag
            if is_comment:
                tokens.append(Token("", Token.Type.COMMENT_END))
                is_comment = False
            # Append code
            line = line.rstrip()
            tokens.append(Token(line, Token.Type.CODE))
            continue

        # Part before the comment start
        rest = m.group(1)
        if rest:
            tokens.append(Token(rest, Token.Type.CODE))

        # Insert comment start tag
        if not is_comment:
            tokens.append(Token("", Token.Type.COMMENT_START))
            is_comment = True

        # Split comment at tags
        comment = m.group(2)[1:]
        tokenized = [t for t in re.split(r"(@\w+)", comment)]
        tokenized = list(
            filter(lambda t: True if t.strip() else None, tokenized))

        # Turn into tokens
        i = len(tokenized) - 1
        while i >= 0:
            token = tokenized[i]
            m = re.match(r"\s*\{\s*([^}]+)\s*\}([\s\S]*)", token)

            if not m:
                if string_char_at(token, 0) == "@":
                    tokenized[i] = Token(token[1:], Token.Type.TAG)
                else:
                    tokenized[i] = Token(token, Token.Type.COMMENT)
                i -= 1
                continue

            tokenized[i] = Token(m.group(1), Token.Type.TYPE)
            tokenized.insert(
                i + 1, Token(m.group(2).lstrip(), Token.Type.COMMENT))
            i -= 1

        tokens += tokenized

    # Insert comment end tag (in case it's not followed by any code, just for consistency)
    if is_comment:
        tokens.append(Token("", Token.Type.COMMENT_END))
        is_comment = False

    # Add end of file token
    tokens.append(Token("", Token.Type.EOF))

    return tokens
