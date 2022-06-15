import collections
import ssl
import sys
import time
from argparse import ArgumentParser
from socket import AF_INET, SOCK_STREAM, socket
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from urllib.parse import urlparse

from .exceptions import (
    BadRequestException,
    ImproperlyConfigured,
    ProxyRequestRefusedException,
    TemplateError,
    TimeoutException,
)
from .handlers import Handler, StaticHandler, TemplateHandler
from .responses import (
    BadRequestResponse,
    DirectoryListingResponse,
    DocumentResponse,
    InputResponse,
    NotFoundResponse,
    PermanentFailureResponse,
    PermanentRedirectResponse,
    ProxyRequestRefusedResponse,
    RedirectResponse,
    Response,
    SensitiveInputResponse,
    SuccessResponse,
    TemplateResponse,
    TextResponse,
    crlf,
)

__version__ = "0.0.3.dev0"


class ZeroConfig:
    ip = "localhost"
    port = 1965
    certfile = "cert.pem"
    keyfile = "key.pem"
    nb_connections = 5


class ArgsConfig:
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
        parser.add_argument(
            "--version",
            help="Return version and exits",
            action="store_true",
            default=False,
        )

        args = parser.parse_args()

        if args.version:
            sys.exit(__version__)

        self.ip = args.ip
        self.port = args.port
        self.certfile = args.certfile
        self.keyfile = args.keyfile
        self.nb_connections = args.nb_connections


def get_path(url):
    """
    Parse a URL and return a path relative to the root
    """
    url = url.strip()
    parsed = urlparse(url, "gemini")
    path = parsed.path
    return path


def check_url(url, server_port):
    """
    Check for the client URL conformity.

    Raise exception or return None
    """
    parsed = urlparse(url, "gemini")

    # Check for bad request
    # Note: the URL will be cleaned before being used
    if not url.endswith("\r\n"):
        # TimeoutException will cause no response
        raise TimeoutException((url, parsed))
    # Other than Gemini will trigger a PROXY ERROR
    if parsed.scheme != "gemini":
        raise ProxyRequestRefusedException
    # You need to provide the right scheme
    if not url.startswith("gemini://"):
        # BadRequestException will return BadRequestResponse
        raise BadRequestException
    # URL max length is 1024.
    if len(url.strip()) > 1024:
        # BadRequestException will return BadRequestResponse
        raise BadRequestException
    # Not the right port
    if ":" in parsed.netloc:
        location, port = parsed.netloc.split(":")
        if int(port) != server_port:
            raise ProxyRequestRefusedException
    return True


class App:

    TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"
    BANNER = f"""
♊ Welcome to your Gémeaux server (v{__version__}) ♊
"""

    def __init__(self, urls, config=None):
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
        self.config = config or ArgsConfig()

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
        status = mimetype = "??"
        response_size = 0
        if response:
            error = response.status > 20
            status = response.status
            response_size = len(response)
            mimetype = response.mimetype.split(";")[0]
        else:
            error = True
        message = '{} [{}] "{}" {} {} {}'.format(
            address,
            time.strftime(self.TIMESTAMP_FORMAT, time.localtime()),
            url.strip(),
            mimetype,
            status,
            response_size,
        )
        self.log(message, error=error)

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

    def exception_handling(self, exception, connection):
        """
        Handle exceptions and errors when the client is requesting a resource.
        """
        response = None
        if isinstance(exception, OSError):
            response = PermanentFailureResponse("OS Error")
        elif isinstance(exception, (ssl.SSLEOFError, ssl.SSLError)):
            response = PermanentFailureResponse("SSL Error")
        elif isinstance(exception, UnicodeDecodeError):
            response = BadRequestResponse("Unicode Decode Error")
        elif isinstance(exception, BadRequestException):
            response = BadRequestResponse()
        elif isinstance(exception, ProxyRequestRefusedException):
            response = ProxyRequestRefusedResponse()
        elif isinstance(exception, ConnectionResetError):
            # No response sent
            self.log("Connection reset by peer...", error=True)
        else:
            self.log(f"Exception: {exception} / {type(exception)}", error=True)

        try:
            if response and connection:
                connection.sendall(bytes(response))
        except Exception as exc:
            self.log(f"Exception while processing exception… {exc}", error=True)

    def get_response(self, url):
        path = get_path(url)
        reason = None
        try:
            k_url, k_value = self.get_route(path)
            if isinstance(k_value, Handler):
                query = urlparse(url).query
                return k_value.handle(k_url, path, query)
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
        while True:
            connection = response = None
            address = url = ""
            do_log = False
            try:
                connection, (address, _) = tls.accept()
                url = connection.recv(2048).decode()

                # Check URL conformity.
                check_url(url, self.port)

                response = self.get_response(url)
                connection.sendall(bytes(response))
                do_log = True
            except KeyboardInterrupt:
                print("bye")
                sys.exit()
            except Exception as exc:
                self.exception_handling(exc, connection)
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
        self.port = self.config.port
        context = SSLContext(PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.config.certfile, self.config.keyfile)

        with socket(AF_INET, SOCK_STREAM) as server:
            server.bind((self.config.ip, self.config.port))
            server.listen(self.config.nb_connections)
            print(self.BANNER)
            with context.wrap_socket(server, server_side=True) as tls:
                print(
                    f"Application started…, listening to {self.config.ip}:{self.config.port}"
                )
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
    "crlf",  # Response tool
    "Response",
    "SuccessResponse",  # Basic brick for building "OK" content
    "InputResponse",
    "SensitiveInputResponse",
    "RedirectResponse",
    "PermanentRedirectResponse",
    "PermanentFailureResponse",
    "NotFoundResponse",
    "BadRequestResponse",
    # Advanced responses
    "DocumentResponse",
    "DirectoryListingResponse",
    "TextResponse",
    "TemplateResponse",
]
