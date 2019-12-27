# -*- coding: utf-8 -*-
import json

from .utils import get_input


class Meta(object):
    VERSION = 2
    """ Current version of the gmdoc.json file format. """

    def __init__(self, *args, **kwargs):
        self._version = kwargs.get("_version", Meta.VERSION)
        self.project = kwargs.get("project", "")
        self.project_name = kwargs.get("project_name", "")
        self.title = kwargs.get("title", "")
        self.author = kwargs.get("author", "")
        self.prefix = kwargs.get("prefix", "")
        self.analytics = kwargs.get("analytics", "")
        self.api = kwargs.get("api", {
            "rating": ""
        })
        self.toc = kwargs.get("toc", {})

    def serialize(self):
        return {
            "_version": self._version,
            "project": self.project,
            "project_name": self.project_name,
            "title": self.title,
            "author": self.author,
            "prefix": self.prefix,
            "analytics": self.analytics,
            "api": self.api,
            "toc": self.toc,
        }

    @staticmethod
    def new(old={}):
        project = get_input(
            "Project file (*.yyp)",
            default=old["project"] if "project" in old else None
        )

        project_name = get_input(
            "Project name",
            default=old["project_name"] if "project_name" in old else None
        )

        title = get_input(
            "Document title",
            default=old["title"] if "title" in old else project_name + " Docs"
        )

        author = get_input(
            "Author name",
            default=old["author"] if "author" in old else None
        )

        prefix = get_input(
            "Prefix required for scripts",
            default=old["prefix"] if "prefix" in old else ""
        )

        analytics = get_input(
            "Google Analytics code",
            default=old["analytics"] if "analytics" in old else ""
        )

        api = old.get("api", {})

        api["rating"] = get_input(
            "Page rating API URL",
            default=api["rating"] if "rating" in api else ""
        )

        toc = old.get("toc", {})
        toc[title] = toc.get(title, "index.md")

        return Meta(
            project=project,
            project_name=project_name,
            title=title,
            author=author,
            prefix=prefix,
            analytics=analytics,
            api=api,
            toc=toc,
        )

    @staticmethod
    def load(fpath):
        with open(fpath, "r") as f:
            meta = json.load(f)

        _version = int(meta["_version"])

        if _version > Meta.VERSION:
            raise Exception((
                "You are trying to load a project created with a newer version "
                "of GMDoc! Please download the latest version before proceeding."
            ))

        if _version < Meta.VERSION:
            print((
                "You are trying to load a project created with an older version "
                "of GMDoc! This requires rebuilding the gmdoc.json file."
            ))

            _default = "Y/n"
            _proceed = get_input("Do you want to proceed", default=_default, end="?")

            if _proceed != _default and _proceed.lower() != "y":
                raise Exception("Canceled")

            meta_new = Meta.new(meta)
            meta_new.save(fpath)
            print("Saved new meta")
            return meta_new

        return Meta(**meta)

    def save(self, fpath):
        with open(fpath, "w") as f:
            json.dump(self.serialize(), f, indent=2)
