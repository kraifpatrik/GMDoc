#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import datetime
import json
import os
import shutil
import sys

from src.meta import Meta
from src.parser import Parser
from src.printer import *
from src.tokenizer import Token, tokenize
from src.utils import *


class Target(object):
    def __init__(self, gmdoc_dir, project_dir, *args, **kwargs):
        self.gmdoc_dir = gmdoc_dir
        self.project_dir = project_dir
        self.meta_path = os.path.join(project_dir, "gmdoc.json")
        self.docs_src_dir = os.path.join(project_dir, "docs_src")
        self.template_dir = os.path.join(gmdoc_dir, "template")

    def execute(self, *args, **kwargs):
        pass


class HelpTarget(Target):
    MESSAGE = (
        "Usage: gmdoc TARGET\n"
        "\n"
        "  TARGET - init  - Initialize gmdoc in the current directory.\n"
        "         - build - Build documentation.\n"
        "         - help  - Display this message.\n"
    )

    def execute(self, *args, **kwargs):
        print(HelpTarget.MESSAGE)


class InitTarget(Target):
    def execute(self, *args, **kwargs):
        meta = Meta.new()
        meta.save(self.meta_path)
        meta_serialized = meta.serialize()

        _docs_src_dest = os.path.join(current_dir, "docs_src")
        os.makedirs(_docs_src_dest, exist_ok=True)

        copytree(
            os.path.join(gmdoc_dir, "docs_src"),
            _docs_src_dest,
        )

        for root, _, files in os.walk(_docs_src_dest):
            for name in files:
                fname = os.path.join(root, name)
                with open(fname, "r") as f:
                    cnt = f.read().format(**meta_serialized)
                with open(fname, "w") as f:
                    f.write(cnt)


class BuildTarget(Target):
    def execute(self, *args, **kwargs):
        if len(sys.argv) > 2:
            docs_dir = sys.argv[2]
        else:
            docs_dir = os.path.join(self.project_dir, "docs_build")
            os.makedirs(docs_dir, exist_ok=True)

        print("Loading meta")
        meta = Meta.load(self.meta_path)

        prefix = meta.prefix
        toc = meta.toc
        _now = datetime.datetime.now()
        datestr = _now.strftime("%B %d, %Y")
        yearstr = _now.strftime("%Y")

        try:
            print("Deleting {}".format(docs_dir))
            shutil.rmtree(docs_dir)
        except:
            pass

        print("Copying resources from {} to {}".format(
            self.template_dir, docs_dir))
        shutil.copytree(self.template_dir, docs_dir)

        print("Loading template")
        with open(os.path.join(self.template_dir, "index.html")) as f:
            template = f.read()

        print("Parsing scripting API documentation")
        parsed = {}

        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if not file.startswith(prefix):
                    continue
                if file[-4:] != ".gml":
                    continue
                fpath = os.path.join(root, file)
                print("Parsing", fpath)
                tokens = []
                with open(fpath) as f:
                    tokens += tokenize(f)
                parsed = merge(Parser(tokens).parse(), parsed)

        resources = []
        for k, v in parsed.items():
            for r in v:
                resources.append(r)
        resources.sort(key=lambda r: r["name"])

        out_dir = os.path.join(self.docs_src_dir, "ScriptingAPI")
        os.makedirs(out_dir, exist_ok=True)

        scripting_api_toc = {
            "file": "ScriptingAPI.md",
            "pages": {}
        }

        for r in resources:
            name = r["name"]
            _type = r["_type"]

            md = ""

            if _type == "macro":
                md = macro_to_markdown(r)
            elif _type == "enum":
                md = enum_to_markdown(r)
            elif _type == "script":
                md = function_to_markdown(r)
            else:
                print("Skipping {name} of type {_type}".format(**r))
                continue

            print("Generating Markdown for", name)

            fname = os.path.abspath("{}/{}.md".format(out_dir, name))
            with open(fname, "w") as f:
                f.write(md)

            scripting_api_toc["pages"][name] = fname

        toc["Scripting API"] = scripting_api_toc

        def flatten_toc(toc):
            flattened = []

            def get_name(v):
                return os.path.splitext(os.path.basename(v))[0] + ".html"

            for k, v in toc.items():
                if isinstance(v, dict):
                    flattened.append(get_name(v["file"]))
                    flattened += flatten_toc(v.get("pages", {}))
                else:
                    flattened.append(get_name(v))

            return flattened

        make_pages(
            meta,
            flatten_toc(toc),
            docs_src_dir=self.docs_src_dir,
            docs_dir=docs_dir,
            template=template,
            datestr=datestr,
            yearstr=yearstr
        )


if __name__ == "__main__":
    current_dir = os.getcwd()
    gmdoc_dir = os.path.dirname(os.path.realpath(__file__))

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
    else:
        try:
            targets[target_name](gmdoc_dir, current_dir).execute()
        except KeyboardInterrupt:
            # Ignore Ctrl+C
            print()
        except Exception as e:
            print(str(e))
