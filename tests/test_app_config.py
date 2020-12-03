from unittest.mock import patch

import pytest

from gemeaux import App
from gemeaux.exceptions import ImproperlyConfigured


def test_no_urls():
    with pytest.raises(ImproperlyConfigured):
        App(urls=None)


def test_not_a_dict_urls():
    with pytest.raises(ImproperlyConfigured):
        App(urls="")


def test_empty_urls():
    with pytest.raises(ImproperlyConfigured):
        App(urls={})


def test_not_a_handler_or_response_urls():
    with pytest.raises(ImproperlyConfigured):
        App(urls={"": "I am not a Handler/Response obj"})


@patch("ssl.SSLContext.load_cert_chain")
def test_urls_handler(mock_ssl_context, fake_handler):
    app = App(urls={"": fake_handler})
    assert app


@patch("ssl.SSLContext.load_cert_chain")
def test_urls_response(mock_ssl_context, fake_response):
    app = App(urls={"": fake_response})
    assert app
