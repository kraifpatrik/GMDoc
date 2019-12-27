#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
