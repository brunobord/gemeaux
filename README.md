# Gemeaux: a Python Gemini Server

The [Gemini protocol](https://gemini.circumlunar.space/) is an ongoing initiative to build a clutter-free content-focused Internet browsing, *à la* [Gopher](https://en.wikipedia.org/wiki/Gopher_(protocol)), but modernized. It focuses on Privacy (TLS + no user tracking) and eliminates the fluff around the modern web: cookies, ads, overweight Javascript apps, browser incompatibilities, etc.

It has been designed for enabling a developer to build a client or a server within a few hours of work. I have been able to serve Gemini static content after two afternoons, so I guess I'm an average developer. But after that, I've tried to improve it, make it more flexible and extensible.

So, here it is: the `Gemeaux` server.

**IMPORTANT NOTE**: since this project is still in its earliest stages, it's worth saying that this software **IS DEFINITELY NOT READY FOR PRODUCTION** — and would probably never will ;o).

## Clients

A quick word about Gemini protocol. Since it's a different protocol from HTTP, or Gopher, or FTP, etc., it means that you'll have to drop your beloved Web Browser to access Gemini content. Hopefully, several clients are available.

* [A list of clients on the canonical Gemini Space](https://gemini.circumlunar.space/clients.html)
* [A curated list of clients on "awesome Gemini"](https://github.com/kr1sp1n/awesome-gemini#clients)

Download and install a couple of clients, pick one that fits your needs, and you'll be ready to spacewalk the Gemini ecosystem.

For development purposes, I'd recommend [bollux](https://sr.ht/~acdw/bollux/), a browser made for bash, because it displays helpful debug messages (and it's as fast as you can dream).

## Requirements

`Gemeaux` is built around **the standard Python 3 library**, so no external dependencies.  
It has a few tests right now, but it'll probably work on Python 3.6+.

You'll also need `openssl` to generate certificates.

## Quickstart

To install `gemeaux` package, inside a virtualenv, or in a safe environment, run the following:

```sh
git clone <url of this repository>.git
cd gemeaux/
pip install -e .
```

*SOON: install via PyPI.*

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

Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
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

By default, the application will listen at port `1965` on your `localhost` (`127.0.0.1`) host, and will use the previously generated `cert.pem` and `key.pem` files. You can change these default using the optional arguments. For more details, run:

```sh
python app.py --help
```

## Advanced usage

The `urls` configuration is at the core of the application workflow. By combining the available `Handler` and `Response` classes, you have the ability to create more complex Gemini spaces.

See the example application, in the `example_app.py` file if you want to see an advanced usage of handlers & responses.

## Known bugs & limitations

This project is mostly for education purposes, although it can possibly be used through a local network, serving Gemini content. There are important steps & bugs to fix before becoming a more solid alternative to other Gemini server software.

* There are a few unittests.
* It has only been manually tested on Python 3.8. It should probably work on Python 3.6+.
* The vast majority of Gemini Standard responses are not implemented.
* The URL routeur is so basic that it won't work if you have a `/test` and `/test2` dict keys.
* The Handler & Response documentation is to be written, along with docstrings.
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
