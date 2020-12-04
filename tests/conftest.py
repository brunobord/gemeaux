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
def index_directory(tmpdir_factory, index_content, other_content, sub_content):
    p = tmpdir_factory.mktemp("var")
    # Create index file
    pp = p.join("index.gmi")
    pp.write_text(index_content, encoding="utf-8")
    # Other file
    pp = p.join("other.gmi")
    pp.write_text(other_content, encoding="utf-8")

    sub = p.mkdir("subdir").join("sub.gmi")
    sub.write_text(sub_content, encoding="utf-8")

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
