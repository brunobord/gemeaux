from datetime import date

import pytest

from gemeaux import (
    DirectoryListingResponse,
    DocumentResponse,
    ImproperlyConfigured,
    RedirectResponse,
    StaticHandler,
    TemplateHandler,
    TemplateResponse,
)


def test_static_handler_not_a_directory():
    with pytest.raises(ImproperlyConfigured):
        StaticHandler("/tmp/not-a-directory")


def test_static_handler_document(index_directory, index_content, other_content):
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(index_content, encoding="utf-8")

    # Reaching directly index.gmi
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/index.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(index_content, encoding="utf-8")

    # Reaching directly index.gmi / no starting slash
    handler = StaticHandler(index_directory)
    response = handler.get_response("/", "index.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(index_content, encoding="utf-8")

    # Reaching directly other.gmi
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/other.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(other_content, encoding="utf-8")


def test_static_handler_subdir(index_directory, sub_content):
    # Reaching direct /subdir/sub.gmi
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/subdir/sub.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(sub_content, encoding="utf-8")

    # No Index -> Directory Listing
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/subdir/")
    assert isinstance(response, DirectoryListingResponse)
    assert response.content.startswith(b"# Directory listing for `/subdir`\r\n")

    # No Index + No slash -> Directory Listing
    handler = StaticHandler(index_directory)
    response = handler.get_response("", "/subdir")
    assert isinstance(response, RedirectResponse)
    assert response.target == "subdir/"


def test_static_handler_sub_url(index_directory, index_content):
    handler = StaticHandler(index_directory)
    response = handler.get_response("/test", "/test/index.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(index_content, encoding="utf-8")


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


def test_static_handler_no_directory_listing(
    index_directory, index_content, sub_content
):
    handler = StaticHandler(index_directory, directory_listing=False)
    # No change in response for "/"
    response = handler.get_response("", "/")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(index_content, encoding="utf-8")

    # Subdir + no slash -> Redirect to "/"
    response = handler.get_response("", "/subdir")
    assert isinstance(response, RedirectResponse)
    assert response.target == "subdir/"

    # Subdir -> no index -> no directory listing
    with pytest.raises(FileNotFoundError):
        handler.get_response("", "/subdir/")

    # subdir/sub.gmi
    response = handler.get_response("", "/subdir/sub.gmi")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(sub_content, encoding="utf-8")


def test_static_handler_alternate_index(index_directory, other_content):
    handler = StaticHandler(index_directory, index_file="other.gmi")
    # "/" returns other.gmi content
    response = handler.get_response("", "/")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(other_content, encoding="utf-8")

    # Subdir -> no other.gmi -> directory listing
    response = handler.get_response("", "/subdir/")
    assert isinstance(response, DirectoryListingResponse)
    assert response.content.startswith(b"# Directory listing for `/subdir`\r\n")


def test_static_handler_alternate_index_no_dirlist(index_directory, other_content):
    handler = StaticHandler(
        index_directory, directory_listing=False, index_file="other.gmi"
    )
    # "/" returns other.gmi content
    response = handler.get_response("", "/")
    assert isinstance(response, DocumentResponse)
    assert response.content == bytes(other_content, encoding="utf-8")

    # Subdir -> no other.gmi -> no directory listing
    with pytest.raises(FileNotFoundError):
        response = handler.get_response("", "/subdir/")


def test_template_handler_getter(template_file):
    class TemplateHandlerWithGetter(TemplateHandler):
        def get_context(self, *args, **kwargs):
            return {"var1": date.today(), "var2": "hello"}

        def get_template_file(self):
            return template_file

    handler = TemplateHandlerWithGetter()
    response = handler.get_response("", "/")

    assert isinstance(response, TemplateResponse)
    assert response.status == 20
    expected_body = f"First var: {date.today()} / Second var: hello"
    assert response.__body__().startswith(bytes(expected_body, encoding="utf-8"))


def test_template_handler_classattr(template_file):
    class TemplateHandlerWithClassattr(TemplateHandler):
        def get_context(self, *args, **kwargs):
            return {"var1": date.today(), "var2": "hello"}

    TemplateHandlerWithClassattr.template_file = template_file

    handler = TemplateHandlerWithClassattr()
    response = handler.get_response("", "/")

    assert isinstance(response, TemplateResponse)
    assert response.status == 20
    expected_body = f"First var: {date.today()} / Second var: hello"
    assert response.__body__().startswith(bytes(expected_body, encoding="utf-8"))
