# -*- coding: utf-8 -*-
import os
import shutil


def copytree(src, dst, symlinks=False, ignore=None):
    """
    Source: https://stackoverflow.com/a/12514470
    """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def get_input(text, default=None, end=":"):
    if default is not None:
        text += " [{}]".format(default)
    text += "{} ".format(end)

    while True:
        val = input(text).strip()
        if not val and default is not None:
            return default
        if val:
            return val
        print("This value is required!")


def merge(source, destination):
    for key, l in source.items():
        for i in l:
            if not key in destination:
                destination[key] = []
            destination[key].append(i)
    return destination
