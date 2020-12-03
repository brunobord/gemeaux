from unittest.mock import patch

from gemeaux import App, NotFoundResponse


@patch("ssl.SSLContext.load_cert_chain")
def test_get_response_handler(mock_ssl_context, fake_handler, fake_response):
    app = App(urls={"/handler": fake_handler, "/response": fake_response})

    # Just to make sure we're going through the get_route
    response = app.get_response("")
    assert isinstance(response, NotFoundResponse)
    assert response.reason == "Route Not Found"

    # Response from handler
    response = app.get_response("/handler")
    assert response.origin == "handler"

    # Direct response
    response = app.get_response("/response")
    assert response.origin == "direct"


@patch("ssl.SSLContext.load_cert_chain")
def test_get_response_exception(mock_ssl_context, fake_handler_exception):
    app = App(urls={"": fake_handler_exception})

    response = app.get_response("")
    assert isinstance(response, NotFoundResponse)

    response = app.get_response("/other")
    assert isinstance(response, NotFoundResponse)
