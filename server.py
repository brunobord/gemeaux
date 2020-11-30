import sys
import time
from itertools import chain
from os import listdir
from os.path import abspath, dirname, isdir, isfile, join
from socket import AF_INET, SOCK_STREAM, socket
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from urllib.parse import urlparse


class NoIndexDirectory(Exception):
    def __init__(self, *args, **kwargs):
        self.filepath = kwargs.pop("filepath")
        super().__init__(*args, **kwargs)


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

    def __init__(self, filename, directory, directory_listing=True):
        """
        Open the document and read its content
        """
        filepath = abspath(join(directory, filename))
        if not filepath.startswith(directory):
            raise FileNotFoundError
        if isdir(filepath):
            filepath = join(filepath, "index.gmi")
            if not isfile(filepath):
                if directory_listing:
                    raise NoIndexDirectory(filepath=dirname(filepath))
                raise FileNotFoundError
        with open(filepath, "rb") as fd:
            self.content = fd.read()

    def __body__(self):
        return self.content


class DirectoryListingResponse(Response):
    def __init__(self, url, directory):

        url_path = parse_url(url, add_index=False)
        path = abspath(join(directory, url_path))
        if not path.startswith(directory):
            raise FileNotFoundError
        if not isdir(path):
            raise FileNotFoundError

        heading = [f"# Directory listing for `{url_path}`\r\n", "\r\n"]
        body = listdir(path)
        body = map(lambda x: f"=> {url_path}/{x}\r\n", body)
        body = chain(heading, body)
        body = map(lambda item: bytes(item, encoding="utf8"), body)
        body = list(body)
        self.content = b"".join(body)

    def __body__(self):
        return self.content


def parse_url(url, add_index=True):
    """
    Parse a URL and return a path
    """
    url = url.strip()
    parsed = urlparse(url, "gemini")
    path = parsed.path
    if path.startswith("/"):
        path = path[1:]
    if add_index and path == "":
        return "index.gmi"
    return path


class App:

    TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"

    def __init__(
        self,
        ip,
        port,
        certfile,
        keyfile,
        static_dir="static",
        directory_listing=True,
    ):
        self.ip = ip
        self.port = port
        self.static_dir = abspath(static_dir)
        self.context = SSLContext(PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(certfile, keyfile)
        self.directory_listing = directory_listing

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
        response = None
        while True:
            try:
                connection, (address, _) = tls.accept()

                url = connection.recv(1024).decode()

                filepath = parse_url(url)

                response = DocumentResponse(
                    filepath, self.static_dir, self.directory_listing
                )
                connection.sendall(bytes(response))
            except NoIndexDirectory:
                response = DirectoryListingResponse(url, self.static_dir)
                connection.sendall(bytes(response))
            except ConnectionResetError:
                self.log("Connection reset by peer...")
            except FileNotFoundError:
                response = NotFoundResponse()
                connection.sendall(bytes(response))
            finally:
                connection.close()
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
        "static_dir": "examples/static",
        "directory_listing": True,
    }
    app = App(**config)
    try:
        app.run()
    except KeyboardInterrupt:
        print("bye")
        sys.exit()
