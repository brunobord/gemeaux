import pytest

from gemeaux.responses import (
    DirectoryListingResponse,
    DocumentResponse,
    InputResponse,
    NotFoundResponse,
    PermanentRedirectResponse,
    RedirectResponse,
    Response,
    SensitiveInputResponse,
    TextResponse,
)

# Same as in conftest.py, but can't import it
INDEX_CONTENT = """# Title\r\nI am the content of index"""
OTHER_CONTENT = """# Title\r\nI am the content of other"""
SUB_CONTENT = """# Title\r\nI am the content of sub"""


def test_base_response():
    response = Response()
    assert response.status == 20
    assert response.__body__() is None
    assert response.__meta__() == b"20 text/gemini; charset=utf-8"
    assert bytes(response) == response.__meta__() + b"\r\n"


def test_input_response():
    response = InputResponse("What's the meaning of life?")
    assert response.status == 10
    assert response.__body__() is None
    assert bytes(response) == b"10 What's the meaning of life?\r\n"


def test_sensitive_input_response():
    response = SensitiveInputResponse("What's the meaning of life?")
    assert response.status == 11
    assert response.__body__() is None
    assert bytes(response) == b"11 What's the meaning of life?\r\n"


def test_redirect_response():
    response = RedirectResponse("gemini://localhost/")
    assert response.status == 30
    assert response.__body__() is None
    assert bytes(response) == b"30 gemini://localhost/\r\n"


def test_permanent_redirect_response():
    response = PermanentRedirectResponse("gemini://localhost/")
    assert response.status == 31
    assert response.__body__() is None
    assert bytes(response) == b"31 gemini://localhost/\r\n"


def test_not_found_response():
    response = NotFoundResponse()
    assert response.status == 51
    assert response.__body__() is None
    assert bytes(response) == b"51 NOT FOUND\r\n"


def test_document_response(index_directory):
    response = DocumentResponse(
        index_directory.join("index.gmi").strpath, index_directory.strpath
    )
    assert response.status == 20
    bytes_content = bytes(INDEX_CONTENT, encoding="utf-8")
    bytes_body = b"20 text/gemini; charset=utf-8\r\n" + bytes_content + b"\r\n"
    assert response.__body__() == bytes_content
    assert bytes(response) == bytes_body


def test_document_response_not_in_root_dir(index_directory):
    with pytest.raises(FileNotFoundError):
        DocumentResponse(index_directory.join("index.gmi").strpath, "/you/do/not/exist")


def test_document_response_not_a_file(index_directory):
    with pytest.raises(FileNotFoundError):
        DocumentResponse(index_directory.strpath, index_directory.strpath)

    with pytest.raises(FileNotFoundError):
        DocumentResponse(
            index_directory.join("not-found.gmi").strpath, index_directory.strpath
        )


def test_directory_listing(index_directory):
    response = DirectoryListingResponse(
        index_directory.strpath, index_directory.strpath
    )

    assert response.status == 20
    assert response.__meta__() == b"20 text/gemini; charset=utf-8"
    assert response.__body__().startswith(b"# Directory listing for ``\r\n")
    assert b"=> /subdir\r\n" in response.__body__()
    assert b"=> /other.gmi\r\n" in response.__body__()


def test_directory_listing_subdir(index_directory):
    response = DirectoryListingResponse(
        index_directory.join("subdir").strpath, index_directory.strpath
    )

    assert response.status == 20
    assert response.__meta__() == b"20 text/gemini; charset=utf-8"
    assert response.__body__().startswith(b"# Directory listing for `/subdir`\r\n")
    assert b"=> /subdir/sub.gmi\r\n" in response.__body__()


def test_directory_listing_not_in_root_dir(index_directory):
    with pytest.raises(FileNotFoundError):
        DirectoryListingResponse(index_directory.strpath, "/you/do/not/exist")
    with pytest.raises(FileNotFoundError):
        DirectoryListingResponse(
            index_directory.join("subdir").strpath, "/you/do/not/exist"
        )


def test_text_response():
    # No title, no body
    response = TextResponse()
    assert bytes(response) == b"20 text/gemini; charset=utf-8\r\n"

    # A title, no body
    response = TextResponse(title="Title")
    assert bytes(response) == (
        b"20 text/gemini; charset=utf-8\r\n"  # header
        b"# Title\r\n"  # Title
        b"\r\n"  # Linefeed
    )

    # No title, A body
    response = TextResponse(body="My body")
    assert bytes(response) == (
        b"20 text/gemini; charset=utf-8\r\nMy body\r\n"  # header + Body
    )

    # A title and a body
    response = TextResponse(title="Title", body="My body")
    assert bytes(response) == (
        b"20 text/gemini; charset=utf-8\r\n"  # header
        b"# Title\r\n"  # Title
        b"\r\n"  # Linefeed
        b"My body\r\n"  # Body
    )
