# -*- coding: utf-8 -*-
import os
import re

import mistune
from jinja2 import Template

from .parser import *


def trim_code(code):
    return re.sub(r"\s+</code>", "</code>", code)


def add_bootstrap(code, table_class=""):
    code = re.sub(
        r"<table>", '<div class="table-responsive"><table class="table table-sm {table_class}">'.format(
            table_class=table_class), code)
    code = re.sub(r"</table>", '</table></div>', code)
    code = code.replace('<pre>', '<pre class="rounded">')
    return code


def make_menu(toc, path):
    counter = 0

    def make_menu_item(k, v):
        nonlocal counter
        counter += 1
        isfolder = isinstance(v, dict)
        fpath = v["file"] if isfolder else v
        fname, _ = os.path.splitext(os.path.basename(fpath))
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


def make_pages(meta, flattened, docs_src_dir="", docs_dir="", template="", datestr="", yearstr=""):
    toc = meta.toc

    flattened_index = 0
    jinja_template = Template(template)

    data = meta.serialize()
    data["header"] = meta.title
    data["date"] = datestr
    data["year"] = yearstr

    def make_page(k, v, path, breadcrumb):
        nonlocal flattened_index
        link_prev = None if flattened_index == 0 else flattened[flattened_index - 1]
        # link_curr = flattened[flattened_index]
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
            data["menu"] = menu
            data["title"] = "{}: {}".format(meta.title, k)
            data["content"] = content
            data["page"] = fname_html
            data["link_prev"] = link_prev if link_prev is not None else "#"
            data["link_next"] = link_next if link_next is not None else "#"
            fcontent = jinja_template.render(**data)
            f.write(fcontent)

        if isfolder and "pages" in v:
            for a, b in v["pages"].items():
                make_page(a, b, path, breadcrumb)

    for k, v in toc.items():
        make_page(k, v, [], [])


def resource_to_markdown(r):
    docs = r.docs

    if not docs:
        return None

    if docs.get_tag("private"):
        return None

    content = []

    def _add_basic(tag, title):
        _tag = tag if isinstance(tag, Tag) else docs.get_tag(tag)
        if _tag:
            content.append(
                "## {}\n".format(title) +
                ("`{}` ".format(_tag.type) if _tag.type else "") +
                _tag.desc)

    # Name and type
    content.append("# {}".format(r.name))
    content.append("`{}`".format(type(r).__name__.lower()))

    # Function signature
    if isinstance(r, Function):
        _func = docs.get_tag("func")
        if _func:
            content.append("```gml\n{}\n```".format(_func.desc))

    # Description
    _desc = docs.get_tag("desc")

    if not _desc:
        if isinstance(r, Macro):
            _desc = docs.get_tag("macro")
        elif isinstance(r, Enum):
            _desc = docs.get_tag("enum")
        elif isinstance(r, Variable):
            _desc = docs.get_tag("var")

    _add_basic(_desc, "Description")

    # Enum members
    if isinstance(r, Enum):
        if r.children:
            members_header = (
                "## Members\n"
                "| Name | Description |\n"
                "| ---- | ----------- |\n"
            )

            members_row = "| `{name}` | {desc} |"

            content.append(
                members_header + "\n".join([members_row.format(**{"name": c.name, "desc": c.docs.get_tag("member").desc}) for c in r.children]))

    # Function arguments
    if isinstance(r, Function):
        _params = docs.get_tag("param", single=False)
        if _params:
            arguments_header = (
                "## Arguments\n"
                "| Name | Type | Description |\n"
                "| ---- | ---- | ----------- |\n"
            )

            arguments_row = "| {name} | `{type}` | {desc} |"

            content.append(
                arguments_header + "\n".join([arguments_row.format(**{"name": p.name, "type": p.type, "desc": p.desc}) for p in _params]))

    # Function return value
    if isinstance(r, Function):
        _add_basic("return", "Returns")

    # Example
    _add_basic("example", "Example")

    # Note
    _add_basic("note", "Note")

    # References
    _see = docs.get_tag("see", single=False)
    if _see:
        cnt = "## See\n"
        cnt += ", ".join(["[{s}]({s}.html)".format(s=s.desc) for s in _see])
        content.append(cnt)

    # Source
    _add_basic("source", "Source")

    return "\n\n".join(content)
