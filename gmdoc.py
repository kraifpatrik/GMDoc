#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import json
import os
import re
import shutil
import sys

import mistune

from src.parser import Parser
from src.tokenizer import Token, tokenize
from src.utils import *

VERSION = 2
""" Version of the gmdoc.json file format. """

TEMPLATE_ANALYTICS = """
  <!-- Global site tag (gtag.js) - Google Analytics -->
  <script async src="https://www.googletagmanager.com/gtag/js?id={id}"></script>
  <script>
    if (location.hostname !== 'localhost') {
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{id}');
    }
  </script>"""


def trim_code(code):
    return re.sub(r"\s+</code>", "</code>", code)


def add_bootstrap(code, table_class=""):
    code = re.sub(
        r"<table>", '<div class="table-responsive"><table class="table table-sm {table_class}">'.format(
            table_class=table_class), code)
    code = re.sub(r"</table>", '</table></div>', code)
    code = code.replace('<pre>', '<pre class="rounded">')
    return code


def function_to_markdown(fn):
    content = []

    content.append("""
# {name}
`script`
```gml
{signature}
```
"""[1:-1].format(**fn))

    if fn.get("desc"):
        content.append("""
## Description
{desc}
"""[1:-1].format(**fn))

    params = fn.get("params", [])
    if params:
        for p in params:
            p["desc"] = re.sub(r"\n+", " ", p["desc"])
        content.append("""### Arguments
| Name | Type | Description |
| ---- | ---- | ----------- |
""" + "\n".join(["| {name} | `{type}` | {desc} |".format(**p) for p in params]))

    retval = fn.get("return", {})
    if retval:
        content.append("""
## Returns
`{type}` {desc}
"""[1:-1].format(**retval))

    if fn.get("example"):
        content.append("""
## Example
{example}
"""[1:-1].format(**fn))

    if fn.get("note"):
        content.append("""
## Note
{note}
"""[1:-1].format(**fn))

    if fn.get("source"):
        content.append("""
## Source
{source}
"""[1:-1].format(**fn))

    see = fn.get("see")
    if see:
        cnt = "### See\n"
        cnt += ", ".join(["[{s}]({s}.html)".format(s=s) for s in see])
        content.append(cnt)

    return "\n\n".join(content)


def enum_to_markdown(en):
    content = []

    content.append("""
# {name}
`enum`
## Description
{desc}
"""[1:-1].format(**en))

    members = en.get("members", [])
    if members:
        for p in members:
            p["desc"] = re.sub(r"\n+", " ", p["desc"])
        content.append("""### Members
| Name | Description |
| ---- | ----------- |
""" + "\n".join(["| `{name}` | {desc} |".format(**p) for p in members]))

    return "\n\n".join(content)


def macro_to_markdown(macro):
    content = []

    content.append("""
# {name}
`macro`
## Description
`{type}` {desc}
"""[1:-1].format(**macro))

    return "\n\n".join(content)


def format_template(template, tag, value):
    return template.replace("{" + tag + "}", value)


def make_menu(toc, path):
    counter = 0

    def make_menu_item(k, v):
        nonlocal counter
        counter += 1
        isfolder = isinstance(v, dict)
        fpath = v["file"] if isfolder else v
        fname, fext = os.path.splitext(os.path.basename(fpath))
        isinpath = fname in path
        iscurrent = fname == path[-1]

        res = "<li>"

        if isfolder:
            res += """<i data-target="#folder-{}" class="fas fa-{}-square text-primary cursor-pointer"></i>""".format(
                counter,
                "minus" if isinpath else "plus")
        else:
            res += """<i data-target="#folder-{}" class="fas fa-circle text-primary bullet"></i>""".format(
                counter)

        res += """ <a href="{file}.html" class="text-dark{classes}">{link}</a>""".format(
            file=fname,
            link=k,
            classes=" font-weight-bold active" if iscurrent else "")

        if isfolder:
            res += """\n<ul id="folder-{}"{}>\n""".format(
                counter,
                "" if isinpath else ' style="display: none;"')
            for a, b in v.get("pages", {}).items():
                res += make_menu_item(a, b)
            res += "</ul>\n"

        res += "</li>\n"
        return res

    menu = ""
    for k, v in toc.items():
        menu += make_menu_item(k, v)
    return menu


def make_pages(toc, flattened):
    flattened_index = 0

    def make_page(k, v, path, breadcrumb):
        nonlocal flattened_index
        link_prev = None if flattened_index == 0 else flattened[flattened_index - 1]
        link_curr = flattened[flattened_index]
        link_next = None if flattened_index == len(
            flattened) - 1 else flattened[flattened_index + 1]
        flattened_index += 1

        isfolder = isinstance(v, dict)
        fpath = v["file"] if isfolder else v
        if not os.path.isabs(fpath):
            fpath = os.path.join(docs_src_dir, fpath)
        fname, fext = os.path.splitext(os.path.basename(fpath))

        print("Writing page {}.html from {}".format(fname, fpath))

        path = path.copy()
        path.append(fname)

        breadcrumb = breadcrumb.copy()
        breadcrumb.append(k)

        menu = make_menu(toc, path)

        # Make breadcrumb
        content = """<nav aria-label="breadcrumb"><ol class="breadcrumb">"""
        size = len(path)

        for i in range(size):
            if i == size - 1:
                content += """<li class="breadcrumb-item active">{text}</li>""".format(
                    text=breadcrumb[i])
            else:
                content += """<li class="breadcrumb-item"><a href="{link}.html">{text}</a></li>""".format(
                    text=breadcrumb[i],
                    link=path[i])

        content += "</nav></ol>\n"

        # Append content
        try:
            with open(fpath) as f:
                if fext == ".md":
                    content += add_bootstrap(
                        trim_code(mistune.markdown(f.read())),
                        table_class="table-arguments" if path[0] == "ScriptingAPI" else "")
                else:
                    content += f.read()
        except Exception as e:
            print(e)
            pass

        fname_html = "{}.html".format(fname)

        with open(os.path.join(docs_dir, fname_html), "w") as f:
            fcontent = template
            fcontent = format_template(template, "analytics", format_template(
                TEMPLATE_ANALYTICS, "id", analytics) if analytics else "")
            fcontent = format_template(
                fcontent, "title", "{}: {}".format(title, k))
            fcontent = format_template(fcontent, "author", author)
            fcontent = format_template(fcontent, "header", title)
            fcontent = format_template(fcontent, "date", datestr)
            fcontent = format_template(fcontent, "year", yearstr)
            fcontent = format_template(fcontent, "menu", menu)
            fcontent = format_template(fcontent, "content", content)
            fcontent = format_template(fcontent, "page", fname_html)
            fcontent = format_template(
                fcontent, "link_prev", link_prev if link_prev is not None else "#")
            fcontent = format_template(
                fcontent, "link_next", link_next if link_next is not None else "#")
            fcontent = format_template(
                fcontent, "api_rating", meta.get("api", {}).get("rating", ""))
            f.write(fcontent)

        if isfolder and "pages" in v:
            for a, b in v["pages"].items():
                make_page(a, b, path, breadcrumb)

    for k, v in toc.items():
        make_page(k, v, [], [])


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
        _title = get_input("Document title", _project_name + " Docs")
        _author = get_input("Author name")
        _prefix = get_input("Prefix")
        _analytics = get_input("Google Analytics code")

        data = {
            "_version": VERSION,
            "project": _project,
            "project_name": _project_name,
            "title": _title,
            "author": _author,
            "prefix": _prefix,
            "analytics": _analytics,
            "api": {
                "rating": "/api/page_rating"
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

    make_pages(toc, flatten_toc(toc))
