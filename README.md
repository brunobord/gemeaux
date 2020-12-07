# Gemeaux: a Python Gemini Server

![travis build badge for "main" branch](https://travis-ci.com/brunobord/gemeaux.svg?branch=main) [![PyPI version of gemeaux](https://badge.fury.io/py/gemeaux.svg)](https://pypi.python.org/pypi/gemeaux/)

The [Gemini protocol](https://gemini.circumlunar.space/) is an ongoing initiative to build a clutter-free content-focused Internet browsing, *à la* [Gopher](https://en.wikipedia.org/wiki/Gopher_(protocol)), but modernized. It focuses on Privacy (TLS + no user tracking) and eliminates the fluff around the modern web: cookies, ads, overweight Javascript apps, browser incompatibilities, etc.

It has been designed for enabling a developer to build a client or a server within a few hours of work. I have been able to serve Gemini static content after two afternoons, so I guess I'm an average developer. But after that, I've tried to improve it, make it more flexible and extensible.

So, here it is: the `Gemeaux` server.

**IMPORTANT NOTE**: since this project is still in its earliest stages, it's worth saying that this software **IS DEFINITELY NOT READY FOR PRODUCTION** — and would probably never will ;o).

## Clients

A quick word about Gemini protocol. Since it's a different protocol from HTTP, or Gopher, or FTP, etc., it means that you'll have to drop your beloved Web Browser to access Gemini content. Hopefully, several clients are available.

* [A list of clients on the canonical Gemini Space](https://gemini.circumlunar.space/clients.html)
* [A curated list of clients on "awesome Gemini"](https://github.com/kr1sp1n/awesome-gemini#clients)

Download and install a couple of clients, pick one that fits your needs, or if you feel like it, build one yourself, and you'll be ready to spacewalk the Gemini ecosystem.

For development purposes, I'd recommend [bollux](https://sr.ht/~acdw/bollux/), a browser made for bash, because it displays helpful debug messages (and it's as fast as you can dream).

## Requirements

`Gemeaux` is built around **the standard Python 3.6+ library** and syntax. There are **no external dependencies**.

Automated tests are launched using Python 3.6, 3.7 and 3.8, so the internals of `Gemeaux` are safe with these versions of Python.

You'll also need `openssl` to generate certificates.

## Quickstart

### Install via PyPI

To install the latest release of `gemeaux` package, inside a virtualenv, or in a safe environment, run the following:

```sh
pip install gemeaux
```

### Developer mode

```sh
git clone https://github.com/brunobord/gemeaux.git
# You may also want to use this source: git@github.com:brunobord/gemeaux.git
cd gemeaux/
pip install -e .
```

### Generate certificates

Since TLS is mandatory, you'll have to generate your own SSL certificate files. Use the following command to generate self-signed certificate files, targeting a localhost/developer mode:

```sh
make cert
```

This command will generate two files: `cert.pem` and `key.pem`.

Again, this will probably not be safe for production.

### Usage

The "hello world" of this *proof of concept* would be to serve a directory containing an ``index.gmi`` file.

For example, the `index.gmi` can look like this:

```
# Hello World!

Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
```

Then you'll create a python file (e.g.: `app.py`) containing the following:

```python
from gemeaux import App, StaticHandler

if __name__ == "__main__":
    urls = {
        "": StaticHandler(
            static_dir="path/to/your/directory/"
        ),
    }
    app = App(urls)
    app.run()
```

*Note*: The `static_dir` argument can be a relative or an absolute path.

Then you'll run your program using Python 3+:

```sh
python app.py
```

You can then point your client at `gemini://localhost/` and you'll see the content of your home page.

By default, the application will listen at port `1965` on your `localhost` (`127.0.0.1`) host, and will use the previously generated `cert.pem` and `key.pem` files.

In order to open your server to "the world", you can change the `--ip` option like this:

```sh
python app.py --ip 0.0.0.0
```

**BIG WARNING**: opening your server to external connections is **DEFINITELY NOT A GOOD IDEA**, since this software **IS NOT PRODUCTION-READY**.

You can change the default configuration values using the optional arguments. For more details, run:

```sh
python app.py --help
```

## Advanced usage

The `urls` configuration is at the core of the application workflow. By combining the available `Handler` and `Response` classes, you have the ability to create more complex Gemini spaces.

You may read the example application, in the `example_app.py` file if you want to see an advanced usage of handlers & responses.

Several classes are provided in this library:

### Handlers

Most of the time, when working with `Handler` basic classes, you'll have to implement/override two methods:

* `Handler.__init__(*args, **kwargs)`: The class constructor will accept `args` and `kwargs` for providing parameters.
* `Handler.get_response(*args, *kwargs)`: Based on the parameters and your current context, you would generate a Gemini-compatible response, either based on the `Response` classes provided, or ones you can build yourself.

#### StaticHandler

This handler is used for serving a static directory and its subdirectories.

How to instantiate:

```python
StaticHandler(
    static_dir,
    directory_listing=True,
    index_file="index.gmi"
)
```

* `static_dir`: the path (relative to your program or absolute) of the root directory to serve.
* `directory_listing` (default: `True`): if set to `True`, in case there's no "index file" in a directory, the application will display the directory listing. If set to `False`, and if there's still no index file in this directory, it'll return a `NotFoundResponse` to the client.
* `index_file` (default: `"index.gmi"`): when the client tries to reach a directory, it's this filename that would be searched to be rendered as the "homepage".

*Note*: If your client is trying to reach a subdirectory like this: `gemini://localhost/subdirectory` (without the trailing slash), the client will receive a Redirection Response targetting `gemini://localhost/subdirectory/` (with the trailing slash).

#### TemplateHandler

This handler provides methods to render Gemini content, mixing a text template and context variables.

The constructor has no specific arguments, but accepts `*args` and `**kwargs`. You'll have to overwrite/override two methods in order to correctly mix the template content with the context variables.

To retrieve the template file, you can overwrite/override the `get_template_file()` method:

```python
TemplateHandler.get_template_file()
```

Alternatively, you may assign it a static `template_file` attribute, like this:
```python
class MyTemplateHandler(TemplateHandler):
    template_file = "/path/to/template.txt"
```
The template file name doesn't require a specific file extension. By default, `TemplateHandler` instances will use the [`string.Template` module from the standard library](https://docs.python.org/3/library/string.html#string.Template) to render content.

**Note**: we know that this "template engine" is a bit too minimalist for advanced purposes ; but as this project mantra is "no external dependencies". Still, this project is a Python project ; so you can plug your favorite template engine and serve dynamic content the way you want.

Example template:

```
I am a template file. Refresh me to see what time it is: $datetime
```

To generate your context variable(s), you'll have to overwrite/override the `get_context()` method:

```python
class DatetimeTemplateHandler(TemplateHandler):
    template_file = "/path/to/template.txt"

    def get_context(self, *args, **kwargs):
        return {"datetime": datetime.datetime.now()}
```

This `get_context()` method should return a dictionary. When accessed, the `$datetime` variable will be replaced by its value from the context dictionary.

## Known bugs & limitations

This project is mostly for education purposes, although it can possibly be used through a local network, serving Gemini content. There are important steps & bugs to fix before becoming a more solid alternative to other Gemini server software.

* The internals of `Gemeaux` are being tested on Python3.6+, but not the mainloop mechanics.
* The vast majority of Gemini Standard responses are not implemented.
* The Response documentation is missing, along with docstrings.
* Performances are probably very low, there might be room for optimisation.

----

## What's in the name?

*"Gémeaux"* is the French word for *"Gemini"*. And incidentally, I was born a Gemini.

*Disclaimer*: I don't believe in astrology.

## Other projects

* [Jetforce](https://github.com/michael-lazar/jetforce) is a Python-based Gemini server, using the Twisted framework.
* [GeGoBi](https://tildegit.org/solderpunk/gegobi) uses a single Python file ; it's a dual-protocol server, for both Gopher & Gemini.

## License

`Gemeaux` server is distributed as Free Software under the terms of the MIT License. See the contents of the `LICENSE` file for more details.
