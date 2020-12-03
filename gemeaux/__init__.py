import collections
import sys
import time
from argparse import ArgumentParser
from socket import AF_INET, SOCK_STREAM, socket
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from urllib.parse import urlparse

from .exceptions import ImproperlyConfigured, TemplateError
from .handlers import Handler, StaticHandler, TemplateHandler
from .responses import (
    DirectoryListingResponse,
    DocumentResponse,
    InputResponse,
    NotFoundResponse,
    PermanentFailureResponse,
    PermanentRedirectResponse,
    RedirectResponse,
    Response,
    SensitiveInputResponse,
    TemplateResponse,
    TextResponse,
)


def get_path(url):
    """
    Parse a URL and return a path relative to the root
    """
    url = url.strip()
    parsed = urlparse(url, "gemini")
    path = parsed.path
    return path


class Config:
    def __init__(self):

        parser = ArgumentParser("Gemeaux: a Python Gemini server")
        parser.add_argument(
            "--ip",
            default="localhost",
            help="IP/Host of your server — default: localhost.",
        )
        parser.add_argument(
            "--port", default=1965, type=int, help="Listening port — default: 1965."
        )
        parser.add_argument("--certfile", default="cert.pem")
        parser.add_argument("--keyfile", default="key.pem")
        parser.add_argument(
            "--nb-connections",
            default=5,
            type=int,
            help="Maximum number of connections — default: 5",
        )

        args = parser.parse_args()
        self.ip = args.ip
        self.port = args.port
        self.certfile = args.certfile
        self.keyfile = args.keyfile
        self.nb_connections = args.nb_connections


BANNER = """
♊ Welcome to your Gémeaux server ♊
"""


class App:

    TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"

    def __init__(self, urls):
        # Check the urls
        if not isinstance(urls, collections.Mapping):
            # Not of the dict type
            raise ImproperlyConfigured("Bad url configuration: not a dict or dict-like")

        if not urls:
            # Empty dictionary or Falsy value
            raise ImproperlyConfigured("Bad url configuration: empty dict")

        for k, v in urls.items():
            if not isinstance(v, (Handler, Response)):
                msg = f"URL configuration: wrong type for `{k}`. Should be of type Handler or Response."
                raise ImproperlyConfigured(msg)

        self.urls = urls

    def log(self, message, error=False):
        """
        Log to standard output
        """
        out = sys.stdout
        if error:
            out = sys.stderr
        print(message, file=out)

    def log_access(self, address, url, response=None):
        """
        Log for access to the server
        """
        message = '{} [{}] "{}" {} {}'.format(
            address,
            time.strftime(self.TIMESTAMP_FORMAT, time.localtime()),
            url.strip(),
            response.status if response else "??",
            len(response) if response else 0,
        )
        self.log(message, error=(not response or response.status != 20))

    def get_route(self, path):

        matching = []

        for k_url, k_value in self.urls.items():
            if not k_url:  # Skip the catchall
                continue
            if path.startswith(k_url):
                matching.append(k_url)

        # One match or more. We'll take the "biggest" match.
        if len(matching) >= 1:
            k_url = max(matching, key=len)
            return (k_url, self.urls[k_url])

        # Catch all
        if "" in self.urls:
            return "", self.urls[""]

        raise FileNotFoundError("Route Not Found")

    def get_response(self, url):

        path = get_path(url)
        reason = None
        try:
            k_url, k_value = self.get_route(path)
            if isinstance(k_value, Handler):
                return k_value.handle(k_url, path)
            elif isinstance(k_value, Response):
                return k_value
        except TemplateError as exc:
            if exc.args:
                reason = exc.args[0]
            return PermanentFailureResponse(reason)
        except Exception as exc:
            if exc.args:
                reason = exc.args[0]
            self.log(f"Error: {type(exc)} / {reason}", error=True)

        return NotFoundResponse(reason)

    def mainloop(self, tls):
        connection = response = None
        while True:
            do_log = True
            try:
                connection, (address, _) = tls.accept()
                url = connection.recv(1024).decode()
                response = self.get_response(url)
                connection.sendall(bytes(response))
            except ConnectionResetError:
                self.log("Connection reset by peer...")
            except KeyboardInterrupt:
                do_log = False
                print("bye")
                sys.exit()
            finally:
                if connection:
                    connection.close()
                if do_log:
                    self.log_access(address, url, response)

    def run(self):
        """
        Main run function.

        Load the configuration from the command line args.
        Launch the server
        """
        # Loading config only at runtime, not initialization
        config = Config()
        context = SSLContext(PROTOCOL_TLS_SERVER)
        context.load_cert_chain(config.certfile, config.keyfile)

        with socket(AF_INET, SOCK_STREAM) as server:
            server.bind((config.ip, config.port))
            server.listen(config.nb_connections)
            print(BANNER)
            with context.wrap_socket(server, server_side=True) as tls:
                print(f"Application started…, listening to {config.ip}:{config.port}")
                self.mainloop(tls)


__all__ = [
    # Core
    "App",
    # Exceptions
    "ImproperlyConfigured",
    "TemplateError",
    # Handlers
    "Handler",
    "StaticHandler",
    "TemplateHandler",
    # Responses
    "Response",
    "InputResponse",
    "SensitiveInputResponse",
    "RedirectResponse",
    "PermanentRedirectResponse",
    "PermanentFailureResponse",
    "NotFoundResponse",
    # Advanced responses
    "DocumentResponse",
    "DirectoryListingResponse",
    "TextResponse",
    "TemplateResponse",
]
