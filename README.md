# Gemeaux: a Python Gemini Server

[![PyPI version of gemeaux](https://badge.fury.io/py/gemeaux.svg)](https://pypi.python.org/pypi/gemeaux/) [![PyPI license](https://img.shields.io/pypi/l/gemeaux.svg)](https://pypi.python.org/pypi/gemeaux/) [![PyPI pyversions](https://img.shields.io/pypi/pyversions/gemeaux.svg)](https://pypi.python.org/pypi/gemeaux/)

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

`Gemeaux` is built around **the standard Python 3.8+ library** and syntax. There are **no external dependencies**.

Automated tests are launched using Python 3.8 and 3.9, so the internals of `Gemeaux` are safe with these versions of Python.

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

Several classes are provided in this library. **All classes described below can be imported from the `gemeaux` module directly**, as in `from gemeaux import <MyClass>`.

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

### Responses

Response classes are the direct links when it comes to returning content to the client. All responses are inheriting from the `gemeaux.responses.Response`.
Reponses are blocks of text, returned as Python `bytes` to the client via the communication socket. Responses are composed of two main elements:

* the `meta` block: It's a line containing the status code (a two-digit code) and an (optional) meta text, in which you'll return the mimetype of the content for "OK" responses, while for error responses, you may also send a human-readable explanation about this error.
* the `body`: if you're returning a "OK" response, this block will be the contents of your content (page, file, etc).

**Note:** If you check with the Gemini project specification, you may see that some response types are missing. They'll eventually be added in a further release.

#### 10: InputResponse

*Usage*:

```python
InputResponse(prompt="What's your name?")
```

This response will prompt the user. When the user will answer the question, the client is supposed to send a new request, adding the answer to the prompt at the end of the originating URL. For example:

* The client requests the <gemini://localhost/register/>
* The server returns an `InputResponse` with the appropriate prompt.
* The end-user may answer to the prompt. Let's say they enter "Forty-Two".
* The client will then send a request to <gemini://localhost/register/?Forty-Two>

It's the integrator duty to proceed with the client answer, then.

#### 11: SensitiveInputResponse

*Usage*:

```python
SensitiveInputResponse(prompt="What's your name?")
```

Same as for the `InputResponse`, except that your answer will be hidden on your client interface when you'll type it.

#### 20: SuccessResponse

*Usage*:

```python
SuccessResponse()
```

You'll probably never use this response class directly, since it'll return no response body. It'll be your parent class for your custom responses, when the request is successful. See the Custom Responses below.

#### 30: RedirectResponse

*Usage*:

```python
RedirectResponse(target="gemini://localhost/moon/")
```

This class will send a Redirect response, with `target` being the next URL. This default redirection is supposed to be temporary, for example if it follows an application workflow.

#### 31: PermanentRedirectResponse

*Usage*:

```python
PermanentRedirectResponse(target="gemini://localhost/moon/base/")
```

Whether the redirection is permanent or temporary, clients will behave alike. But crawlers and search engine spiders will consider the permanent redirections differently, and should remember to crawl the new target and deprecate the previous URL.

#### 50: PermanentFailureResponse

*Usage*:

```python
PermanentFailureResponse(reason="You forgot to say 'please'")
```

Your application has failed for a "good" reason and it'll always fail when your user requests this resource this way. The `reason` argument is optional. If omitted, the message will read `50 PERMANENT FAILURE`.

#### 51: NotFoundResponse

*Usage*:

```python
NotFoundResponse(reason="These are not the droids you are looking for")
```

The requested resource is not found (its code is `51`, because you'll never find what's in the *Area 51*). The `reason` argument is optional. If omitted, the message will read `51 NOT FOUND`.

#### 54: ProxyRequestRefusedResponse

*Usage*:

```python
ProxyRequestRefusedResponse()
```

This response is returned when the server is receiving a query not directly related to its host(name).

##### The proxy use case

You're building a Gemini server called `moonbase`. It receives requests for local resources, but you're allowing your server to act as a proxy for the server named `lunarstation`. It can be another Gemini server *or* an HTTP(s) server, or Gopher, etc. So if you allow it, you can authorize incoming requests for `https://lunarstation/example/resource`, fetch this resource by yourself, transcribe it into a regular Gemini `Response` and return it to your client.

Otherwise, if you don't allow it, simply return the `ProxyRequestRefusedResponse` as described above.

**Note:** The proxy feature is not implemented yet in ``Gemeaux``, but it's planned for a future release.

#### 59: BadRequestResponse

*Usage*:

```python
BadRequestResponse(reason="You've been very naughty, no cake for you")
```

Return this Bad Request response whenever the request doesn't fulfill the Gemini specs or is wrong in a way or another. The `reason` argument is optional. If omitted, the response will read: `59: BAD REQUEST`.

### Custom Response classes

In order to ease development of Gemini websites / applications, *Gemeaux* is providing a few Response classes to return classic Gemini content.

#### TextResponse

The text response is composed of a `title` and a `body` content. It's one of the most direct way to return Gemini markup. You may use it to return dynamic content.

Here is an example:

```python
from random import randint
from gemeaux import TextResponse
response = TextResponse(
    title="Fancy a game?",
  body=f"Rolled: {randint(1, 6)}\r\nRefresh the page to make another roll."
)
```

The arguments `title` and `body` are both optional. But of course, returning an empty content can be puzzling for your users.

The `title` will be rendered as `# Fancy a game?`. The rest of the content (the `body` variable) will be flushed to the user. Please note that all combinations of `\n` & `\r` will be converted into `\r\n`.

#### DocumentResponse

Another quick way to return Gemini content is write it down in a text file. You can then return your response to the client as if it was served by a static web server, except that it'll be a Gemini response.

Example:

```python
DocumentResponse(
    full_path="/var/gemini/content/file.gmi",
    root_dir="/var/gemini/content"
)
```

Please note that both `full_path` and `root_dir` arguments are **mandatory**. The `root_dir` argument should prevent your application to try to access a file that doesn't belong to the root directory of your static content. You wouldn't like your `/etc/passwd` file to be revealed using a `DocumentResponse` instance, would you?

#### DirectoryListingResponse

One may consider too annoying to make a homepage for a static directory yourself. The `DirectoryListingResponse` is providing you a way to display the list of the given directory.

Example:

```python
DirectoryListingResponse(
    full_path="/var/gemini/content/moon/base/",
    root_dir="/var/gemini/content"
)
```

**Note**: if the provided path is not a directory, or is not part of the `root_dir`path, a `FileNotFoundError` will be raised.

#### TemplateResponse

When you want your dynamic content to respect some sort of structure, you may want to leverage templates to avoid repeating yourself.

The `TemplateResponse` class constructor has one mandatory argument: `template_file`, which is the path to the template file. Then there's a `context` kwargs, that will be transmitted to the template.

A template file is a text file that respects the [String subsitution API described here](https://docs.python.org/3/library/string.html#template-strings).

*Example template:*

```
Hello, $full_name! Welcome aboard.
```

Now let's imagine your `TemplateResponse` class is instantiated like this:

```python
TemplateResponse("/path/to/hello.txt", full_name="Gus Grissom")
```

When returned to the client as a Response, This will be rendered as:

```
Hello, Gus Grissom! Welcome aboard.
```

You can pass as many context variables as you want, but here are some important notes:

1. For each template variable (like `$stuff`), you must give it a value.
2. Basic Python types will be properly rendered, but the stdlib `string.Template` has no advanced template features: no loops over a list of items, etc. *There are plans to make it easier to plug your favorite template engine in the future (in the meantime, you can try to make the mix of your templates and dynamic variables in your Handler class and return a `TextResponse` yourself).*

## Known bugs & limitations

This project is mostly for education purposes, although it can possibly be used through a local network, serving Gemini content. There are important steps & bugs to fix before becoming a more solid alternative to other Gemini server software.

* The internals of `Gemeaux` are being tested on Python3.8+, but not the mainloop mechanics.
* The vast majority of Gemini Standard responses are not implemented.
* The Response documentation is missing, along with docstrings.
* Performances are probably very low, there might be room for optimisation.

----

## What's in the name?

*"Gémeaux"* is the French word for *"Gemini"*. And incidentally, I was born a Gemini. In French it's pronounced \\ʒe.mo\\.

*Disclaimer*: I don't believe in astrology.

## Other projects

* [Jetforce](https://github.com/michael-lazar/jetforce) is a Python-based Gemini server, using the Twisted framework.
* [GeGoBi](https://tildegit.org/solderpunk/gegobi) uses a single Python file ; it's a dual-protocol server, for both Gopher & Gemini.

## License

`Gemeaux` server is distributed as Free Software under the terms of the MIT License. See the contents of the `LICENSE` file for more details.
