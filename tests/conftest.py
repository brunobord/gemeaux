from os.path import abspath, dirname, join

import pytest

from gemeaux import Handler, Response, TemplateResponse


class FakeResponse(Response):
    def __init__(self, origin):
        self.origin = origin


class FakeHandler(Handler):
    def handle(self, *args, **kwargs):
        return FakeResponse(origin="handler")


class FakeHandlerRaiseException(Handler):
    def handle(self, *args, **kwargs):
        raise Exception


@pytest.fixture
def fake_response():
    return FakeResponse(origin="direct")


@pytest.fixture
def fake_handler():
    return FakeHandler()


@pytest.fixture
def fake_handler_exception():
    return FakeHandlerRaiseException()


@pytest.fixture()
def index_content():
    return """# Title\r\nI am the content of index"""


@pytest.fixture()
def other_content():
    return """# Title\r\nI am the content of other"""


@pytest.fixture()
def sub_content():
    return """# Title\r\nI am the content of sub"""


@pytest.fixture()
def multi_line_content():
    return "First line\nSecond line\rThird line\r\nLast line."


@pytest.fixture()
def multi_line_content_crlf():
    return "First line\r\nSecond line\r\nThird line\r\nLast line.\r\n"


@pytest.fixture()
def image_content():
    path = dirname(abspath(__file__))
    with open(join(path, "caffeine.png"), "rb") as fd:
        return fd.read()


@pytest.fixture()
def index_directory(
    tmpdir_factory,
    index_content,
    other_content,
    sub_content,
    multi_line_content,
    image_content,
):
    p = tmpdir_factory.mktemp("var")
    # Create index file
    pp = p.join("index.gmi")
    pp.write_text(index_content, encoding="utf-8")
    # Other file
    pp = p.join("other.gmi")
    pp.write_text(other_content, encoding="utf-8")
    # Multi line file
    pp = p.join("multi_line.gmi")
    pp.write_text(multi_line_content, encoding="utf-8")

    sub = p.mkdir("subdir").join("sub.gmi")
    sub.write_text(sub_content, encoding="utf-8")

    # Write the image content into the image file
    image = p.join("image.png")
    image.write_binary(image_content)

    # Return directory
    return p


class FakeTemplateResponse(TemplateResponse):
    pass


@pytest.fixture()
def template_file(tmpdir_factory):
    p = tmpdir_factory.mktemp("templates")
    pp = p.join("template.txt")
    pp.write_text("First var: $var1 / Second var: $var2", encoding="utf-8")
    return pp
