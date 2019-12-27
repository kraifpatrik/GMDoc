#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import json
import os
import shutil
import sys

from src.parser import Parser
from src.printer import *
from src.tokenizer import Token, tokenize
from src.utils import *

VERSION = 2
""" Version of the gmdoc.json file format. """


if __name__ == "__main__":
    current_dir = os.getcwd()
    gmdoc_dir = os.path.dirname(os.path.realpath(__file__))

    if len(sys.argv) < 2:
        print("TARGET not defined!")
        print("Correct usage: gmdoc TARGET")
        print()
        print("  TARGET - init  - Initialize gmdoc in the current directory")
        print("         - build - Build documentation")
        exit()

    target = sys.argv[1]
    project_dir = current_dir

    if target == "init":
        _project = get_input("Project file (*.yyp)")
        _project_name = get_input("Project name")
        _title = get_input("Document title", default=_project_name + " Docs")
        _author = get_input("Author name")
        _prefix = get_input("Prefix required for scripts")
        _analytics = get_input("Google Analytics code")
        _rating_api = get_input("Page rating API URL")

        data = {
            "_version": VERSION,
            "project": _project,
            "project_name": _project_name,
            "title": _title,
            "author": _author,
            "prefix": _prefix,
            "analytics": _analytics,
            "api": {
                "rating": _rating_api
            },
            "toc": {}
        }
        data["toc"][_title] = "index.md"

        with open("gmdoc.json", "w") as f:
            json.dump(data, f, indent=2)

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
                    cnt = f.read().format(**data)
                with open(fname, "w") as f:
                    f.write(cnt)

        exit()

    if target != "build":
        print("Unknown target {}".format(target))
        exit()

    meta_path = os.path.join(project_dir, "gmdoc.json")
    docs_src_dir = os.path.join(project_dir, "docs_src")
    if len(sys.argv) > 2:
        docs_dir = sys.argv[2]
    else:
        docs_dir = os.path.join(project_dir, "docs_build")
        os.makedirs(docs_dir, exist_ok=True)
    template_dir = os.path.join(gmdoc_dir, "template")

    print("Loading meta")
    with open(meta_path) as f:
        meta = json.load(f)

    title = meta["title"]
    author = meta["author"]
    prefix = meta["prefix"]
    toc = meta["toc"]
    analytics = meta.get("analytics", None)
    datestr = datetime.datetime.now().strftime("%B %d, %Y")
    yearstr = datetime.datetime.now().strftime("%Y")

    try:
        print("Deleting {}".format(docs_dir))
        shutil.rmtree(docs_dir)
    except:
        pass

    print("Copying resources from {} to {}".format(template_dir, docs_dir))
    shutil.copytree(template_dir, docs_dir)

    print("Loading template")
    with open(os.path.join(template_dir, "index.html")) as f:
        template = f.read()

    print("Parsing scripting API documentation")
    parsed = {}

    for root, _, files in os.walk(project_dir):
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

    out_dir = os.path.join(docs_src_dir, "ScriptingAPI")
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
        toc,
        flatten_toc(toc),
        docs_src_dir=docs_src_dir,
        docs_dir=docs_dir,
        template=template,
        analytics=analytics,
        title=title,
        author=author,
        datestr=datestr,
        yearstr=yearstr,
        meta=meta,
    )
