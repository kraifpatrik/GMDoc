import datetime
import json
import os
import re
import shutil
import sys
import zipfile
from enum import Enum

import mistune


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


class Parser:
    def __init__(self, tokens):
        self.index = 0
        self.tokens = tokens

    def _next(self):
        self.index += 1

    def _peek(self):
        if self.index < len(self.tokens):
            token = self.tokens[self.index]
            return token
        return None

    def _find_comment_block(self):
        while True:
            peek = self._peek()
            if peek.type == Token.Type.EOF:
                return False
            if peek.type == Token.Type.COMMENT_START:
                break
            self._next()
        self._next()
        return True

    def _parse_var(self):
        # Check if the current token is a var tag
        t = self._peek()
        if not t.is_tag("var"):
            return None
        self._next()

        # Type
        t = self._peek()
        type_ = None
        if t.type == Token.Type.TYPE:
            type_ = t.value
            self._next()

        # Description
        t = self._peek()
        desc = ""
        while t.type != Token.Type.COMMENT_END:
            desc += t.value + " "
            self._next()
            t = self._peek()
        desc = desc.strip()
        self._next()

        # Name
        t = self._peek()
        name = ""
        while name == "" and t.type == Token.Type.CODE:
            m = re.match(r"\s*((global\.)?\w+)", t.value)
            if not m:
                self._next()
                t = self._peek()
                continue
            name = m.group(1)
        self._next()

        if name and desc:
            return {
                "_type": "variable",
                "name": name,
                "type": type_,
                "desc": desc,
            }

        return None

    def _parse_enum(self):
        # Check if the current token is an enum tag
        t = self._peek()
        if not t.is_tag("enum"):
            return None
        self._next()

        # Description
        t = self._peek()
        desc = ""
        while t.type != Token.Type.COMMENT_END:
            desc += t.value + " "
            self._next()
            t = self._peek()
        desc = desc.strip()
        self._next()

        # Name
        t = self._peek()
        name = ""
        while name == "" and t.type == Token.Type.CODE:
            m = re.match(r"\s*enum\s+(\w+)", t.value)
            if not m:
                self._next()
                t = self._peek()
                continue
            name = m.group(1)
        self._next()

        # Members
        members = []
        while True:
            _backup = self.index
            if not self._find_comment_block():
                break
            member = self._parse_member()
            if member:
                members.append(member)
            else:
                self.index = _backup
                break

        if name and desc:
            return {
                "_type": "enum",
                "name": name,
                "desc": desc,
                "members": members
            }

        return None

    def _parse_member(self):
        # Check if the current token is an enum tag
        t = self._peek()
        if not t.is_tag("member"):
            return None
        self._next()

        # Description
        t = self._peek()
        desc = ""
        while t.type != Token.Type.COMMENT_END:
            desc += t.value + " "
            self._next()
            t = self._peek()
        desc = desc.strip()
        self._next()

        # Name
        t = self._peek()
        name = ""
        while name == "" and t.type == Token.Type.CODE:
            m = re.match(r"\s*(\w+)", t.value)
            if not m:
                self._next()
                t = self._peek()
                continue
            name = m.group(1)
        self._next()

        if name and desc:
            return {
                "name": name,
                "desc": desc,
            }

        return None

    def _parse_macro(self):
        # Check if the current token is a macro tag
        t = self._peek()
        if not t.is_tag("macro"):
            return None
        self._next()

        # Type
        t = self._peek()
        type_ = None
        if t.type == Token.Type.TYPE:
            type_ = t.value
            self._next()

        # Description
        t = self._peek()
        desc = ""
        while t.type != Token.Type.COMMENT_END:
            desc += t.value + " "
            self._next()
            t = self._peek()
        desc = desc.strip()
        self._next()

        # Name
        t = self._peek()
        name = ""
        while name == "" and t.type == Token.Type.CODE:
            m = re.match(r"\s*#macro\s+(\w+)", t.value)
            if not m:
                self._next()
                t = self._peek()
                continue
            name = m.group(1)
        self._next()

        if name and desc:
            return {
                "_type": "macro",
                "name": name,
                "type": type_,
                "desc": desc
            }

        return None

    def _parse_function(self):
        # Check if the current token is a function tag
        t = self._peek()
        if not t.is_tag("func"):
            return None
        self._next()

        # Signature and name
        t = self._peek()
        name = ""
        signature = ""
        if t.type == Token.Type.COMMENT:
            signature = t.value.strip()
            name = signature.split("(")[0].strip()
            self._next()

        # Tags
        desc = ""
        params = []
        returns = None
        example = ""
        see = []
        note = ""
        source = ""

        while True:
            _desc = self._parse_function_desc()
            if _desc:
                desc = _desc
                continue

            _param = self._parse_function_param()
            if _param:
                params.append(_param)
                continue

            _retval = self._parse_function_retval()
            if _retval:
                returns = _retval
                continue

            _example = self._parse_function_example()
            if _example:
                example = _example
                continue

            _note = self._parse_function_note()
            if _note:
                note = _note
                continue

            _see = self._parse_function_see()
            if _see:
                see.append(_see)
                continue

            _source = self._parse_function_source()
            if _source:
                source = _source
                continue

            break

        if name:
            return {
                "_type": "script",
                "name": name,
                "signature": signature,
                "desc": desc,
                "params": params,
                "return": returns,
                "example": example,
                "see": see,
                "note": note,
                "source": source,
            }

        return None

    def _parse_function_desc(self):
        t = self._peek()
        if not t.is_tag("desc"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value + " "
            self._next()

        return desc.strip()

    def _parse_function_param(self):
        t = self._peek()
        if not t.is_tag("param"):
            return None
        self._next()

        # Type
        t = self._peek()
        type_ = None
        if t.type == Token.Type.TYPE:
            type_ = t.value
            self._next()

        # Name and desc
        name = ""
        desc = ""

        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            if not name:
                m = re.match(r"([\S]+)([\s\S]*)?", t.value)
                if not m:
                    m = re.match(r"(\w+)\b([\s\S]*)?", t.value)
                if m:
                    name = m.group(1)
                    desc = m.group(2).strip()
            else:
                desc += " " + t.value
            self._next()
        desc = desc.strip()

        if name:
            return {
                "name": name,
                "type": type_,
                "desc": desc,
            }

        return None

    def _parse_function_retval(self):
        t = self._peek()
        if not t.is_tag("return"):
            return None
        self._next()

        # Type
        t = self._peek()
        type_ = None
        if t.type == Token.Type.TYPE:
            type_ = t.value
            self._next()

        # Description
        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value + " "
            self._next()
        desc = desc.strip()

        if type_ or desc:
            return {
                "desc": desc,
                "type": type_
            }

        return None

    def _parse_function_example(self):
        t = self._peek()
        if not t.is_tag("example"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value
            self._next()

        return desc.rstrip()

    def _parse_function_see(self):
        t = self._peek()
        if not t.is_tag("see"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value
            self._next()

        return desc.strip()

    def _parse_function_note(self):
        t = self._peek()
        if not t.is_tag("note"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value
            self._next()

        return desc.rstrip()

    def _parse_function_source(self):
        t = self._peek()
        if not t.is_tag("source"):
            return None
        self._next()

        desc = ""
        while True:
            t = self._peek()
            if t.type != Token.Type.COMMENT:
                break
            desc += t.value + " "
            self._next()

        return desc.strip()

    def parse(self):
        enums = []
        functions = []
        macros = []
        variables = []

        while True:
            if not self._find_comment_block():
                break

            _enum = self._parse_enum()
            if _enum:
                enums.append(_enum)
                continue

            _fn = self._parse_function()
            if _fn:
                functions.append(_fn)
                continue

            _macro = self._parse_macro()
            if _macro:
                macros.append(_macro)
                continue

            _var = self._parse_var()
            if _var:
                variables.append(_var)
                continue

            break

        t = self._peek()
        if t and t.type != Token.Type.EOF:
            print(t)
            raise Exception("File was not parsed entirely!")

        return {
            "enums": enums,
            "functions": functions,
            "macros": macros,
            "variables": variables,
        }


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


def merge(source, destination):
    for key, l in source.items():
        for i in l:
            if not key in destination:
                destination[key] = []
            destination[key].append(i)
    return destination


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
        exit()

    target = sys.argv[1]
    project_dir = current_dir

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
