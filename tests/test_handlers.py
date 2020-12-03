import pytest

from gemeaux import (
    DirectoryListingResponse,
    DocumentResponse,
    ImproperlyConfigured,
    StaticHandler,
)

# Same as in conftest.py, but can't import it
INDEX_CONTENT = """# Title\r\nI am the content of index"""
OTHER_CONTENT = """# Title\r\nI am the content of other"""
SUB_CONTENT = """# Title\r\nI am the content of sub"""


def test_static_handler_not_a_directory():
    with pytest.raises(ImproperlyConfigured):
        StaticHandler("/tmp/not-a-directory")


def test_static_handler_document(index_directory):
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(INDEX_CONTENT, encoding="utf-8")

    # Reaching directly index.gmi
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/index.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(INDEX_CONTENT, encoding="utf-8")

    # Reaching directly index.gmi / no starting slash
    handler = StaticHandler(index_directory)
    response = handler.get_response("/", "index.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(INDEX_CONTENT, encoding="utf-8")

    # Reaching directly other.gmi
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/other.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(OTHER_CONTENT, encoding="utf-8")


def test_static_handler_subdir(index_directory):
    # Reaching direct /subdir/sub.gmi
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/subdir/sub.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(SUB_CONTENT, encoding="utf-8")

    # No Index -> Directory Listing
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/subdir/")
    assert isinstance(response, DirectoryListingResponse)
    assert response.content.startswith(b"# Directory listing for `/subdir`\r\n")


def test_static_handler_sub_url(index_directory):
    handler = StaticHandler(index_directory)
    response = handler.get_response("/test", "/test/index.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(INDEX_CONTENT, encoding="utf-8")


def test_static_handler_not_found(index_directory):
    handler = StaticHandler(index_directory)
    with pytest.raises(FileNotFoundError):
        handler.get_response("", "/not-found")

    with pytest.raises(FileNotFoundError):
        handler.get_response("", "/not-found.gmi")

    with pytest.raises(FileNotFoundError):
        handler.get_response("", "/subdir/not-found/")

    with pytest.raises(FileNotFoundError):
        handler.get_response("", "/subdir/not-found.gmi")


def test_static_handler_no_directory_listing(index_directory):
    handler = StaticHandler(index_directory, directory_listing=False)
    # No change in response for "/"
    response = handler.get_response("", "/")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(INDEX_CONTENT, encoding="utf-8")

    # Subdir -> no index -> no directory listing
    with pytest.raises(FileNotFoundError):
        handler.get_response("", "/subdir")

    # Subdir -> no index -> no directory listing
    with pytest.raises(FileNotFoundError):
        handler.get_response("", "/subdir/")

    # subdir/sub.gmi
    response = handler.get_response("", "/subdir/sub.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(SUB_CONTENT, encoding="utf-8")


def test_static_handler_alternate_index(index_directory):
    handler = StaticHandler(index_directory, index_file="other.gmi")
    # "/" returns other.gmi content
    response = handler.get_response("", "/")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(OTHER_CONTENT, encoding="utf-8")

    # Subdir -> no other.gmi -> directory listing
    response = handler.get_response("", "/subdir/")
    assert isinstance(response, DirectoryListingResponse)
    assert response.content.startswith(b"# Directory listing for `/subdir`\r\n")


def test_static_handler_alternate_index_no_dirlist(index_directory):
    handler = StaticHandler(
        index_directory, directory_listing=False, index_file="other.gmi"
    )
    # "/" returns other.gmi content
    response = handler.get_response("", "/")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(OTHER_CONTENT, encoding="utf-8")

    # Subdir -> no other.gmi -> no directory listing
    with pytest.raises(FileNotFoundError):
        response = handler.get_response("", "/subdir/")
