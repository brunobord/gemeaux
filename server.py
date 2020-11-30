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


class FlushResponse(Exception):
    """
    Triggers the response flushing
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


# ############## Handlers
class StaticHandler:
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

    def handle(self, url, filepath):
        response = self.get_response(url, filepath)
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

    def mainloop(self, tls):
        while True:
            response = connection = None
            do_log = True
            try:
                connection, (address, _) = tls.accept()
                url = connection.recv(1024).decode()
                path = get_path(url)

                for k_url, k_value in self.urls.items():
                    if not k_url:  # Skip the catchall
                        continue
                    if path.startswith(k_url):
                        response = k_value.handle(k_url, path)
                        raise FlushResponse

                if "" in self.urls:
                    # Catch all
                    response = self.urls[""].handle("", path)
                    raise FlushResponse

                raise FileNotFoundError

            except FlushResponse:
                connection.sendall(bytes(response))
            except ConnectionResetError:
                self.log("Connection reset by peer...")
            except FileNotFoundError:
                response = NotFoundResponse()
                connection.sendall(bytes(response))
            except KeyboardInterrupt:
                do_log = False
                raise
            finally:
                connection.close()
                if do_log:
                    self.log_access(address, url, response)

    def run(self):
        with socket(AF_INET, SOCK_STREAM) as server:
            server.bind((self.ip, self.port))
            server.listen(5)
            with self.context.wrap_socket(server, server_side=True) as tls:
                self.mainloop(tls)


if __name__ == "__main__":
    config = {
        "ip": "localhost",
        "port": 1965,
        "certfile": "cert.pem",
        "keyfile": "key.pem",
        "urls": {
            "": StaticHandler(static_dir="examples/static/", directory_listing=True),
            "/test": StaticHandler(
                static_dir="examples/static/", directory_listing=False
            ),
            "/with-sub": StaticHandler(
                static_dir="examples/static/sub-dir", directory_listing=True
            ),
        },
    }
    app = App(**config)
    try:
        app.run()
    except KeyboardInterrupt:
        print("bye")
        sys.exit()
