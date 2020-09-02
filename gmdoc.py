#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from src.parser import Parser
from src.tokenizer import Tokenizer
from pprint import pprint

if __name__ == "__main__":
    fname = sys.argv[1]
    with open(fname, "r") as f:
        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize(f.read())
        pprint(tokens)
        parser = Parser(tokens)
        parsed = parser.parse()
        parsed.name = fname
        pprint(parsed)
    exit()

import os
import sys

from src.targets import HelpTarget, InitTarget, BuildTarget

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("TARGET not defined!")
        print(HelpTarget.MESSAGE)
        exit()

    target_name = sys.argv[1]
    targets = {
        "help": HelpTarget,
        "init": InitTarget,
        "build": BuildTarget,
    }

    if not target_name in targets:
        print("Invalid TARGET {}!".format(target_name))
        exit()

    try:
        current_dir = os.getcwd()
        gmdoc_dir = os.path.dirname(os.path.realpath(__file__))
        targets[target_name](gmdoc_dir, current_dir).execute()
    except KeyboardInterrupt:
        # Ignore Ctrl+C
        print()
    except Exception as e:
        print(str(e))
