import pytest

from gemeaux import Handler, Response


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
