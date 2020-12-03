import collections
import sys
import time
from argparse import ArgumentParser
from os.path import abspath, isdir, isfile, join
from socket import AF_INET, SOCK_STREAM, socket
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from urllib.parse import urlparse

from .exceptions import ImproperlyConfigured
from .responses import (
    DirectoryListingResponse,
    DocumentResponse,
    NotFoundResponse,
    Response,
)


# ############## Handlers
class Handler:
    def __init__(self, *args, **kwargs):
        pass

    def get_response(self, *args, **kwargs):
        raise NotImplementedError

    def handle(self, url, path):
        raise NotImplementedError


class StaticHandler(Handler):
    """
    Handler for serving static Gemini pages from a directory on your filesystem.
    """

    def __init__(self, static_dir, directory_listing=True, index_file="index.gmi"):
        self.static_dir = abspath(static_dir)
        if not isdir(self.static_dir):
            raise ImproperlyConfigured(f"{self.static_dir} is not a directory")
        self.directory_listing = directory_listing
        self.index_file = index_file

    def __repr__(self):
        return f"<StaticHandler: {self.static_dir}>"

    def get_response(self, url, path):
        """
        Return the static page response according to the configuration & file tree.

        * If the path is a file -> return DocumentResponse for this file.
        * If the path is a directory -> search for "index_file"
          * If index is found => DocumentResponse
          * If not found, depending on the directory_listing arg:
            * If activated, it'll return the DirectoryListingResponse
            * If deactivated => raises a FileNotFoundError.
        * If none of the cases above is satisfied, it raises a FileNotFoundError
        """
        # A bit paranoid…
        if path.startswith(url):
            path = path[len(url) :]
        if path.startswith("/"):  # Should be a relative path
            path = path[1:]

        full_path = join(self.static_dir, path)
        # print(f"StaticHandler: path='{full_path}'")
        # The path leads to a directory
        if isdir(full_path):
            # Directory -> index?
            index_path = join(full_path, self.index_file)
            if isfile(index_path):
                return DocumentResponse(index_path, self.static_dir)
            elif self.directory_listing:
                return DirectoryListingResponse(full_path, self.static_dir)
        # The path is a file
        elif isfile(full_path):
            return DocumentResponse(full_path, self.static_dir)
        # Else, not found or error
        raise FileNotFoundError("Path not found")

    def handle(self, url, path):
        """
        Handle the StaticHandler.

        Override/write this method if you need extra processing before returning the
        standard Response.
        """
        response = self.get_response(url, path)
        return response


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

        args = parser.parse_args()
        self.ip = args.ip
        self.port = args.port
        self.certfile = args.certfile
        self.keyfile = args.keyfile


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

        for k_url, k_value in self.urls.items():
            if not k_url:  # Skip the catchall
                continue
            if path.startswith(k_url):
                return k_url, k_value

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
        ip = config.ip
        port = config.port
        context = SSLContext(PROTOCOL_TLS_SERVER)
        context.load_cert_chain(config.certfile, config.keyfile)

        with socket(AF_INET, SOCK_STREAM) as server:
            server.bind((ip, port))
            server.listen(5)
            print(BANNER)
            with context.wrap_socket(server, server_side=True) as tls:
                print(f"Application started…, listening to {ip}:{port}")
                self.mainloop(tls)
