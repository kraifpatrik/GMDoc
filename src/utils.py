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


def get_input(text, default=""):
    if default:
        text += " [{}]".format(default)
    text += ": "
    val = input(text)
    if not val:
        return default
    return val


def merge(source, destination):
    for key, l in source.items():
        for i in l:
            if not key in destination:
                destination[key] = []
            destination[key].append(i)
    return destination
