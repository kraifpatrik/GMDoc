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


def function_to_markdown(fn):
    template = (
        "# {name}\n"
        "`function`\n"
        "```gml\n"
        "{signature}\n"
        "```"
    )

    template_desc = (
        "## Description\n"
        "{desc}"
    )

    template_header = (
        "### Arguments\n"
        "| Name | Type | Description |\n"
        "| ---- | ---- | ----------- |\n"
    )

    template_row = "| {name} | `{type}` | {desc} |"

    template_return = (
        "## Returns\n"
        "`{type}` {desc}"
    )

    template_example = (
        "## Example\n"
        "{example}"
    )

    template_note = (
        "## Note\n"
        "{note}"
    )

    template_source = (
        "## Source\n"
        "{source}"
    )

    content = []
    content.append(template.format(**{
        "name": fn.name,
        "signature": fn.docs.get_tag("func").desc
    }))

    _desc = fn.docs.get_tag("desc")
    if _desc:
        content.append(template_desc.format(**{
            "desc": _desc.desc
        }))

    _params = fn.docs.get_tag("param", single=False)
    if _params:
        content.append(
            template_header + "\n".join([template_row.format(**{ "name": p.name, "type": p.type, "desc": p.desc }) for p in _params]))

    _retval = fn.docs.get_tag("return")
    if _retval:
        content.append(template_return.format(**{
            "type": _retval.type,
            "desc": _retval.desc,
        }))

    _example = fn.docs.get_tag("example")
    if _example:
        content.append(template_example.format(**{
            "example": _example.desc
        }))

    _note = fn.docs.get_tag("note")
    if _note:
        content.append(template_note.format(**{
            "note": _note.desc
        }))

    _source = fn.docs.get_tag("source")
    if _source:
        content.append(template_source.format(**{
            "source": _source.desc
        }))

    _see = fn.docs.get_tag("see", single=False)
    if _see:
        cnt = "### See\n"
        cnt += ", ".join(["[{s}]({s}.html)".format(s=s.desc) for s in _see])
        content.append(cnt)

    return "\n\n".join(content)


def enum_to_markdown(en):
    template = (
        "# {name}\n"
        "`enum`\n"
        "## Description\n"
        "{desc}"
    )

    template_header = (
        "### Members\n"
        "| Name | Description |\n"
        "| ---- | ----------- |\n"
    )

    template_row = "| `{name}` | {desc} |"

    content = []
    content.append(template.format(**{
        "name": en.name,
        "desc": en.docs.get_tag("enum").desc
    }))

    if en.children:
        content.append(
            template_header + "\n".join([template_row.format(**{ "name": c.name, "desc": c.docs.get_tag("member").desc }) for c in en.children]))

    return "\n\n".join(content)


def macro_to_markdown(macro):
    template = (
        "# {name}\n"
        "`macro`\n"
        "## Description\n"
        "`{type}` {desc}"
    )

    return template.format(**{
        "name": macro.name,
        "type": macro.docs.get_tag("macro").type,
        "desc": macro.docs.get_tag("macro").desc,
    })


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
    if not r.docs:
        return None

    if r.docs.get_tag("private"):
        return None

    if isinstance(r, Macro):
        return macro_to_markdown(r)

    if isinstance(r, Enum):
        return enum_to_markdown(r)

    if isinstance(r, Variable):
        return None

    if isinstance(r, Constructor):
        return None

    if isinstance(r, Function):
        return function_to_markdown(r)

    return None
