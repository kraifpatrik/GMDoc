# GMDoc
> Documentation generator for GameMaker Studio 2. Now supports GMS2.3+!

![License](https://img.shields.io/github/license/kraifpatrik/gmdoc)

Donate: [PayPal.Me](https://www.paypal.me/kraifpatrik/5usd)

# Table of Contents
* [Installation](#installation)
* [Documenting projects](#documenting-projects)
  - [GMDoc initialization](#gmdoc-initialization)
  - [Supported tags](#supported-tags)
  - [Links](#links)
  - [Examples](#examples)
  - [Custom documentation pages](#custom-documentation-pages)
* [Building documentation](#building-documentation)
* [Extras](#extras)
  - [Analytics](#analytics)
  - [Page rating API](#page-rating-api)
* [Projects using GMDoc](#projects-using-gmdoc)

# Installation
* Requires [Python 3](https://www.python.org)

```cmd
git clone https://github.com/kraifpatrik/gmdoc.git
cd gmdoc
pip3 install -r requirements.txt
```

*It is recommended to add `C:\path\to\gmdoc\bin` into your `PATH` to be able to run gmdoc from anywhere.*

# Documenting projects
The general documentation format is:

```gml
/// @tag [{item_type}] [item_name] Tag description. It can span over multiple lines
/// like this.
```

`item_type` and `item_name` are optional and may not be applicable to all documented items. `item_name` can be surrounded by square bracket, which is used to indicate optional parameters of functions.

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

## Supported tags
Tag | Description
--- | -----------
`@deprecated` | Marks an API as deprecated.
`@desc` | Add a description to a documented item.
`@enum` | Add a description to an enum.
`@example` | Provide an example of how to use a documented item.
`@extends` | Indicate that a struct inherits from another struct.
`@func` | Document a function signature.
`@macro` | Add a description to a macro.
`@member` | Add a description to an enum member.
`@note` | Add a note to an item's documentation.
`@obsolete` | Mark a documented item as obsolete.
`@param` | Describe a function parameter.
`@private` | Disable printing out documentation for an item.
`@readonly` | Mark a documented item as read-only.
`@return` | Describe a return value of a function.
`@see` | Add a reference to another documented item.
`@source` | Provide credits or a link to the original implementation.
`@throws` | Indicate that a function throws an exception.
`@var` | Add a description to a variable.

## Links
You can add links to another documented items into tag descriptions using `{@link item_name}`.

## Examples
```gml
/// @macro {string} A hello string.
#macro HELLO_STRING "Hello, GMDoc!"

/// @var {bool} A read-only variable which won't show up in the generated
/// documentation.
/// @private
/// @readonly
global.__gmdoc_is_awesome = true;

/// @enum An enumeration of item qualities.
enum Quality
{
    /// @member The item is a poop!
    Poopy,
    /// @member The item is *s i c c*!
    Sicc
};

/// @func Error([_msg])
/// @desc Base class for all errors.
/// @param {string} [_msg] The error message. Defaults to an empty string.
function Error() constructor
{
    /// @var {string} The error message.
    /// @readonly
    msg = (argument_count > 0) ? argument[0] : "";
}

/// @func OopsieError()
/// @desc An oopsie error. Thrown when something goes wrong.
/// @extends Error
function OopsieError() : Error("Oopsie!") constructor {}

/// @func Example(_quality)
/// @desc An example.
/// @param {Quality} _quality The quality of the example.
/// @see Quality
function Example(_quality) constructor
{
    /// @var {Quality} The quality of the example.
    /// @private
    quality = _quality;

    /// @func say_hello()
    /// @desc Either prints {@link HELLO_STRING} to the console or throws
    /// an error - based on the quality of the example!
    /// @throws {OopsieError} If the quality of the example is poopy!
    static say_hello = function () {
        if (quality == Quality.Sicc)
        {
            show_debug_message(HELLO_STRING);
        }
        else
        {
            throw new OopsieError();
        }
    };
};

/// @func make_sicc_example()
/// @desc Creates a *s i c c* example!
/// @return {Example} The created example.
/// @obsolete This function is obsolete! Please use {@link make_random_example}
/// instead.
function make_sicc_example()
{
    return new Example(Quality.Sicc);
}

/// @func make_random_example()
/// @desc Creates {@link Example} of random {@link Quality}.
/// @return {Example} The created example.
/// @example
/// ```gml
/// var _example = make_random_example();
/// try
/// {
///     _example.say_hello();
/// }
/// catch (e)
/// {
///     show_debug_message(e.msg);
/// }
/// ```
/// @see Example.say_hello
function make_random_example()
{
    var _quality = (random(100) == 13.37) ? Quality.Sicc : Quality.Poopy;
    return new Example(_quality);
}
```

You may want to improve readability of your script documentation comments by indenting descriptions with spaces and putting `///` lines between parts with dense text like so:

```gml
/// @func function_name(arg, another_arg)
/// @desc Function description here.
///
/// @param {type} arg         Argument description here.
/// @param {type} another_arg Another argument description here.
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

**Note:** This is a shortened version of:
```json
"toc": {
  "Project Docs": {
    "file": "index.md"
  }
}
```

It is possible to include custom pages into the documentation by adding a new key-value pair into the table of contents like so:

```json
"toc": {
  "Project Docs": "index.md",
  "Page title": "path/to/source_file"
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
      "Page 2": "path/to/page_2"
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
          "Page within section 2": "page_source"
        }
      },
      "Page within section 1": "page_source"
    }
  }
}
```

You can also mark pages as deprecated or obsolete by adding a key `"deprecated": true` or `"obsolete": true` respectively.

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

# Projects using GMDoc
* [BBMOD](https://github.com/blueburn-cz/BBMOD)
* [CE](https://kraifpatrik.com/docs/ce)
* Your project here?
