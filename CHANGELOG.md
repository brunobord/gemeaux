# Gemeaux changelog

## master (unreleased)

Nothing here yet.

## v0.0.3 (2025-04-06)

### Features

* Fix `InputResponse` handling when transmitting the answer to the prompt.
* Added unittests to the `check_url` function.
* Small refactor of basic classes, to force users to define their status code in derivative classes.
* Change strategy for loading configuration / arguments. Easier testing and less naughty side-effects.

### Maintenance

* [BREAKING CHANGE] Removed support of Python 3.6, 3.7 and 3.8.
* Confirm support of Python 3.9, 3.10, 3.11, 3.12, 3.13
* Fixed the collections import in main file so its code is future-proof. Thanks @JonStratton (#13)
* Switched from Travis CI to Github Workflows
* Added the option `SO_REUSEADDR` to the severs socket. Thanks @airmack (#11)
* Switch from `setup.cfg` to `pyproject.toml`, as all cool kids do (#20).

### Documentation

* Added `BadRequestResponse` and `ProxyRequestRefusedResponse` to the example application.
* Added documentation about the available `Response` classes.
* Added the phonetics of the word "gémeaux" in French.
* Added nice badges to `README.md` file.
* Added a small badge for GH workflows
* Updating links to the Gemini Protocol canonical website and Bollux project page on the README

## v0.0.2 (2020-12-07)

### Following the Specs

* Added `TemplateResponse` & `TemplateHandler` classes for generating Gemini content using template files.
* Make sure returned responses endlines are not mixed, only CRLF.
* Handling mimetypes other than `text/gemini`. Clients would have to download them instead of trying to display them. Example app is amended.
* Redirect clients when pointing at a static subdirectory without a trailing slash. It caused misdirections because the client was requesting the "/document.gmi" instead of the "/subdir/document.gmi".
* Improve application resilience after auditing it with [gemini-diagnostic](https://github.com/michael-lazar/gemini-diagnostics). Everything is not perfect, but that's a good start, to be honest.
* Added `BadRequestResponse`, `ProxyRequestRefusedResponse` classes

### Other changes

* Improved conftest for pytest using fixtures for document content.
* Return version number when using the `--version` option.
* Display version number at startup on the welcome message.
* Added mimetype of response to the access log.
* Added documentation for Handlers.

## v0.0.1 (2020-12-04)

This is the first release of `Gemeaux` server.

### Main features

* Implementation of the TLS-required Gemini protocol communication workflow. The most used parts of the specifications are covered, but there are still lots of improvements to make,
* Serving a static directory tree made of `.gmi` files. Configuration options: index file name, directory listing,
* Serving a textual content,
* Redirection (permanent or temporary) responses,
* Customizable Handlers,
* Tested with Python 3.6, 3.7, 3.8 through pytest and Travis-CI.
* Example application to show how to use the core features.
