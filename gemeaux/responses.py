from itertools import chain
from os import listdir
from os.path import abspath, isdir, isfile


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


class InputResponse(Response):
    """
    Input response. Status code: 10.
    """

    status = 10

    def __init__(self, prompt):
        self.prompt = prompt

    def __meta__(self):
        meta = f"{self.status} {self.prompt}"
        return bytes(meta, encoding="utf-8")


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
