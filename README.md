# GMDoc
> Documentation generator for GameMaker Studio 2

![License](https://img.shields.io/github/license/kraifpatrik/ce)

Donate: [PayPal.Me](https://www.paypal.me/kraifpatrik/5usd)

# Table of Contents
* [Installation](#installation)
* [Documenting projects](#documenting-projects)
  - [GMDoc initialization](#gmdoc-initialization)
  - [Documenting enums](#documenting-enums)
  - [Documenting macros](#documenting-macros)
  - [Documenting scripts](#documenting-scripts)
  - [Custom documentation pages](#custom-documentation-pages)
* [Building documentation](#building-documentation)
* [Extras](#extras)
  - [Analytics](#analytics)
  - [Page rating API](#page-rating-api)

# Installation
* Requires [Python 3](https://www.python.org)

```cmd
git clone https://github.com/kraifpatrik/gmdoc.git
cd gmdoc
pip3 install -r requirements.txt
```

*It is recommended to add `C:\path\to\gmdoc\bin` into your `PATH` to be able to run gmdoc from anywhere.*

# Documenting projects
Each documentation line must start with three forward slashes `///`.

Tag descriptions can be split into multiple lines like so:
```gml
/// @tag A very descriptive documentation
/// that needs to be split into multiple lines.
```

*GMDoc currently collects documentation only from scripts!*

## GMDoc initialization
To generate a documentation you first have to initialize GMDoc in the project's directory using

```cmd
gmdoc init
```

During the initialization you will be asked to input following values:

| Value | Description |
| ----- |------------ |
| Author name | Used in the copyright notice. |
| Document title | The title of the documentation. This is by default equal to `project_name + ' Docs'`. |
| Google Analytics code | Optional. See [Analytics](#analytics) for more info. |
| Page rating API URL | Optional. See [Page rating API](#page-rating-api) for more info. |
| Prefix required for scripts | Optional. If provided, documentation will be collected only from scripts starting with the prefix. |
| Project file | The name of your *.yyp project file. |
| Project name | The name of your project. |

*The values are here in an alphabetical order, the actual order in the command line tool may differ.*

After the initialization is done, a `gmdoc.json` file will be created in the project's folder, as well as a new directory `docs_src`, where you can add [custom documentation pages](#custom-documentation-pages).

## Documenting enums
```gml
/// @enum Enum description goes here.
enum EnumName
{
    /// @member Enum member description.
    Some,
    /// @member Another member description.
    Member,
    // This one does not have a description, so it won't occur in the docs.
    Here,
};
```

## Documenting macros
```gml
/// @macro {type} Macro description goes here.
#macro MACRO_NAME macro_value
```

*The macro type can be omitted.*

## Documenting scripts
```gml
/// @func script_name(arg1[, arg2])
/// @desc Script description goes here.
/// @param {type} arg1 Argument description.
/// @param {type} [arg2] Optional argument description.
/// @return {type} Return value description.
/// @example You can write example code using Markdown like this:
/// ```gml
/// // Example code goes here...
/// ```
/// @note A note to the scripts usage or implementation for example.
/// @source https://url.to/the/original/implementation
/// @see another_script
/// @see AnEnum
/// @see OR_A_MACRO
```

*All tags except `@func` are optional. Parameter and return value types can be omitted.*

You may want to improve readability of your script documentation comments by indenting descriptions with spaces and putting `///` lines between parts with dense text like so:

```gml
/// @func script_name(arg, anotherArg)
/// @desc Script description here.
///
/// @param {type} arg        Argument description here.
/// @param {type} anotherArg Another argument description here.
///
/// @return {type} Return value description here.
```

## Custom documentation pages
By default unmodified gmdoc.json file contains a key "toc" (table of contents) which looks something like this:

```json
"toc": {
  "Project Docs": "index.md"
}
```

It is possible to include custom pages into the documentation by adding a new key-value pair into the table of contents like so:

```json
"toc": {
  "Project Docs": "index.md",
  "Page title": "path/to/source_file",
  ...
}
```

*All paths must be relative to the "docs_src" folder in the project's root. Supported file formats are HTML (\*.html) and Markdown (\*.md).*

It is also possible to compose pages into collapsible sections:

```json
"toc": {
  "Section name": {
    "file": "path/to/section_file",
    "pages": {
      "Page 1": "path/to/page_1",
      "Page 2": "path/to/page_2",
      ...
    }
  }
}
```

Entires of "pages" can also be another sections:

```json
"toc": {
  "Section 1": {
    "file": "section_1_source",
    "pages": {
      "Section 2": {
        "file": "section_2_source",
        "pages": {
          ...
        }
      },
      "Page withing section 1": "page_source",
      ...
    }
  }
}
```

*A special section called "Scripting API" is always put at the end of `toc` during the building process. This section contains documentation files generated by GMDoc.*

# Building documentation
To build an HTML documentation, simply run the following command from your project's directory:

```cmd
gmdoc build
```

This will create a folder `docs_build`, where you can find the documentation when the building process is finished.

# Extras
## Analytics
When initializing a new project with `gmdoc init`, you will be asked for an optional [Google Analytics](https://www.google.com/analytics) code (`UA-XXXXX-Y`). If this code is provided, Google Analytics script will be added into every generated HTML file. This is especially useful when creating public extensions for GMS2.

## Page rating API
Another optional setting is a page rating API URL. When this is provided, every generated HTML file will contain a thumbs up/thumbs down button and a modal through which users can send feedback for each documentation page. The feedback is sent onto the specified URL using an xhr POST request.

```php
<?php

// The URL of the rated page.
$page = $_POST["page"];
// Either +1 for like or -1 for dislike.
$like = $_POST["like"];
// The message that the user has left, can be an empty string.
$message = $_POST["message"];

// The rating can be then stored into a table for example:
$sql = "INSERT INTO page_ratings (`page`, `like`, `message`) VALUES (:page, :like, :message)";
$stmt = $conn->prepare($sql);
$stmt->bindParam(":page", $page);
$stmt->bindParam(":like", $like);
$stmt->bindParam(":message", $message);
$stmt->execute();
```
