# Gemeaux changelog

## master (unreleased)

* Added `TemplateResponse` & `TemplateHandler` classes for generating Gemini content using template files.
* Improved conftest for pytest using fixtures for document content.
* Make sure returned responses endlines are not mixed, only CRLF.
* Return version number when using the `--version` option.
* Display version number at startup on the welcome message.
* Handling mimetypes other than `text/gemini`. Clients would have to download them instead of trying to display them. Example app is amended.
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
