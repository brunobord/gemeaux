from unittest.mock import patch

import pytest

from gemeaux import App, ImproperlyConfigured, ZeroConfig


def test_no_urls():
    with pytest.raises(ImproperlyConfigured):
        App(urls=None, config=ZeroConfig())


def test_not_a_dict_urls():
    with pytest.raises(ImproperlyConfigured):
        App(urls="", config=ZeroConfig())


def test_empty_urls():
    with pytest.raises(ImproperlyConfigured):
        App(urls={}, config=ZeroConfig())


def test_not_a_handler_or_response_urls():
    with pytest.raises(ImproperlyConfigured):
        App(urls={"": "I am not a Handler/Response obj"}, config=ZeroConfig())


@patch("ssl.SSLContext.load_cert_chain")
def test_urls_handler(mock_ssl_context, fake_handler):
    app = App(urls={"": fake_handler}, config=ZeroConfig())
    assert app


@patch("ssl.SSLContext.load_cert_chain")
def test_urls_response(mock_ssl_context, fake_response):
    app = App(urls={"": fake_response}, config=ZeroConfig())
    assert app
