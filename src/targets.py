# -*- coding: utf-8 -*-
import datetime
import os
import sys

from .meta import Meta
from .parser import Parser
from .printer import *
from .tokenizer import *
from .utils import *


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

        _docs_src_dest = os.path.join(self.project_dir, "docs_src")
        os.makedirs(_docs_src_dest, exist_ok=True)

        copytree(
            os.path.join(self.gmdoc_dir, "docs_src"),
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
    def flatten_toc(self, toc):
        flattened = []

        def get_name(v):
            return os.path.splitext(os.path.basename(v))[0] + ".html"

        for _, v in toc.items():
            if isinstance(v, dict):
                flattened.append(get_name(v["file"]))
                flattened += self.flatten_toc(v.get("pages", {}))
            else:
                flattened.append(get_name(v))

        return flattened

    def parse_resources(self, prefix):
        parsed = []

        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if not file.startswith(prefix):
                    continue
                if file[-4:] != ".gml":
                    continue
                fpath = os.path.join(root, file)
                print("Parsing", fpath)

                with open(fpath) as f:
                    tokenizer = Tokenizer()
                    tokens = tokenizer.tokenize(f.read())
                    parser = Parser(tokens)
                    scope = parser.parse()
                    scope.name = file
                    parsed.append(scope)

        return parsed

    def flatten_resources(self, parsed):
        resources = []
        for p in parsed:
            for c in p.children:
                resources.append(c)
        resources.sort(key=lambda r: r.name)
        return resources

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
        parsed = self.parse_resources(prefix)
        resources = self.flatten_resources(parsed)

        out_dir = os.path.join(self.docs_src_dir, "ScriptingAPI")
        os.makedirs(out_dir, exist_ok=True)

        scripting_api_toc = {
            "file": "ScriptingAPI.md",
            "pages": {}
        }

        for r in resources:
            name = r.name

            md = resource_to_markdown(r)
            if md is None:
                print("Skipping {} of type {}".format(r.name, type(r).__name__))
                continue

            print("Generating Markdown for", name)
            fname = os.path.abspath("{}/{}.md".format(out_dir, name))
            with open(fname, "w") as f:
                f.write(md)

            scripting_api_toc["pages"][name] = fname

        toc["Scripting API"] = scripting_api_toc

        make_pages(
            meta,
            self.flatten_toc(toc),
            docs_src_dir=self.docs_src_dir,
            docs_dir=docs_dir,
            template=template,
            datestr=datestr,
            yearstr=yearstr
        )
