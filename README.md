# GMDoc
> Documentation generator for GameMaker Studio 2

![License](https://img.shields.io/github/license/kraifpatrik/ce)

Donate: [PayPal.Me](https://www.paypal.me/kraifpatrik/5usd)

# Table of Contents
* [Installation](#installation)
* [Documenting projects](#documenting-projects)
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

_It is recommended to add `C:\path\to\gmdoc\bin` into your `PATH` to be able to run gmdoc from anywhere._

# Documenting projects
TODO

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
