import collections
import sys
import time
from itertools import chain
from os import listdir
from os.path import abspath, isdir, isfile, join
from socket import AF_INET, SOCK_STREAM, socket
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from urllib.parse import urlparse


# ############## Exceptions
class ImproperlyConfigured(Exception):
    """
    When the configuration is a problem
    """


# ############## Reponses
class Response:
    """
    Basic Gemini response
    """

    status = 20

    def __meta__(self):
        """
        Default responses are OK responses (code: 20)
        """
        return b"20 text/gemini; charset=utf-8"

    def __body__(self):
        return None

    def __bytes__(self):
        """
        Return the response sent via the connection
        """
        # Composed of the META line and the body
        response = [self.__meta__(), self.__body__()]
        # Only non-empty items are sent
        response = filter(bool, response)
        # responses should be terminated by \r\n
        response = map(lambda x: x + b"\r\n", response)
        # Joined to be sent back
        response = b"".join(response)
        return response

    def __len__(self):
        """
        Return the length of the response
        """
        return len(bytes(self))


class NotFoundResponse(Response):
    """
    Not Found Error response. Status code: 51.
    """

    status = 51

    def __meta__(self):
        return b"51 NOT FOUND"


class RedirectResponse(Response):
    """
    Temporary redirect. Status code: 30
    """

    status = 30

    def __init__(self, target):
        self.target = target

    def __meta__(self):
        meta = f"{self.status} {self.target}"
        return bytes(meta, encoding="utf-8")


class PermanentRedirectResponse(RedirectResponse):
    """
    Permanent redirect. Status code: 31
    """

    status = 31


class DocumentResponse(Response):
    """
    Document response

    This reponse is the content a text document.
    """

    def __init__(self, full_path, root_dir):
        """
        Open the document and read its content
        """
        full_path = abspath(full_path)
        if not full_path.startswith(root_dir):
            raise FileNotFoundError
        if not isfile(full_path):
            raise FileNotFoundError
        with open(full_path, "rb") as fd:
            self.content = fd.read()

    def __body__(self):
        return self.content


class DirectoryListingResponse(Response):
    def __init__(self, full_path, root_dir):
        # Just in case
        full_path = abspath(full_path)
        if not full_path.startswith(root_dir):
            raise FileNotFoundError
        if not isdir(full_path):
            raise FileNotFoundError
        relative_path = full_path[len(root_dir) :]

        heading = [f"# Directory listing for `{relative_path}`\r\n", "\r\n"]
        body = listdir(full_path)
        body = map(lambda x: f"=> {relative_path}/{x}\r\n", body)
        body = chain(heading, body)
        body = map(lambda item: bytes(item, encoding="utf8"), body)
        body = list(body)
        self.content = b"".join(body)

    def __body__(self):
        return self.content


class TextResponse(Response):
    def __init__(self, title=None, body=None):
        content = []
        # Remove empty bodies
        if title:
            content.append(f"# {title}")
            content.append("")
        if body:
            content.append(body)

        content = map(lambda item: f"{item}\r\n", content)
        content = map(lambda item: bytes(item, encoding="utf8"), content)
        self.content = b"".join(content)

    def __body__(self):
        return self.content


# ############## Handlers
class Handler:
    def __init__(self, *args, **kwargs):
        pass

    def get_response(self, *args, **kwargs):
        raise NotImplementedError

    def handle(self, url, path):
        raise NotImplementedError


class StaticHandler(Handler):
    def __init__(self, static_dir, directory_listing=True, index_file="index.gmi"):
        self.static_dir = abspath(static_dir)
        if not isdir(self.static_dir):
            raise ImproperlyConfigured(f"{self.static_dir} is not a directory")
        self.directory_listing = directory_listing
        self.index_file = index_file

    def __repr__(self):
        return f"<StaticHandler: {self.static_dir}>"

    def get_response(self, url, path):

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
        raise FileNotFoundError

    def handle(self, url, path):
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


class App:

    TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"

    def __init__(
        self,
        ip,
        port,
        certfile,
        keyfile,
        urls,
    ):
        self.ip = ip
        self.port = port

        # Check the urls
        if not isinstance(urls, collections.Mapping):
            # Not of the dict type
            raise ImproperlyConfigured(
                f"Bad url configuration: not a dict or dict-like"
            )

        if not urls:
            # Empty dictionary or Falsy value
            raise ImproperlyConfigured(f"Bad url configuration: empty dict")

        for k, v in urls.items():
            if not isinstance(v, (Handler, Response)):
                raise ImproperlyConfigured(
                    f"Bad url configuration: wrong type for `k`. It should be of type Handler or Response"
                )

        self.urls = urls
        self.context = SSLContext(PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(certfile, keyfile)

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

        raise FileNotFoundError

    def get_response(self, url):

        path = get_path(url)
        k_url, k_value = self.get_route(path)
        try:
            if isinstance(k_value, Handler):
                return k_value.handle(k_url, path)
            elif isinstance(k_value, Response):
                return k_value
        except Exception as exc:
            self.log(f"Error: {type(exc)}", error=True)

        return NotFoundResponse()

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
        with socket(AF_INET, SOCK_STREAM) as server:
            server.bind((self.ip, self.port))
            server.listen(5)
            with self.context.wrap_socket(server, server_side=True) as tls:
                self.mainloop(tls)
