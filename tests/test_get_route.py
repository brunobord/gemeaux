from unittest.mock import patch

import pytest

from gemeaux import App


@patch("ssl.SSLContext.load_cert_chain")
def test_get_route_handler(mock_ssl_context, fake_handler, fake_response):
    app = App(urls={"": fake_handler, "/other": fake_response})
    # direct route
    assert app.get_route("") == ("", fake_handler)
    assert app.get_route("/") == ("", fake_handler)
    # Other
    assert app.get_route("/other") == ("/other", fake_response)
    # Catchall
    assert app.get_route("/something") == ("", fake_handler)


@patch("ssl.SSLContext.load_cert_chain")
def test_get_route_no_catchall(mock_ssl_context, fake_response):
    app = App(urls={"/hello": fake_response})
    with pytest.raises(FileNotFoundError):
        app.get_route("")

    with pytest.raises(FileNotFoundError):
        app.get_route("/")

    with pytest.raises(FileNotFoundError):
        app.get_route("/something")
