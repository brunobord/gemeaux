import pytest

from gemeaux import (
    BadRequestResponse,
    DirectoryListingResponse,
    DocumentResponse,
    InputResponse,
    NotFoundResponse,
    PermanentFailureResponse,
    PermanentRedirectResponse,
    ProxyRequestRefusedResponse,
    RedirectResponse,
    Response,
    SensitiveInputResponse,
    SuccessResponse,
    TemplateError,
    TemplateResponse,
    TextResponse,
    crlf,
)


def test_base_response():
    response = Response()
    with pytest.raises(NotImplementedError):
        response.status
    assert response.__body__() is None
    with pytest.raises(NotImplementedError):
        response.__meta__()


def test_success_response():
    response = SuccessResponse()
    assert response.status == 20
    assert response.__body__() is None
    assert response.__meta__() == b"20 text/gemini; charset=utf-8"


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


def test_permanent_failure_response():
    response = PermanentFailureResponse()
    assert response.status == 50
    assert response.__body__() is None
    assert bytes(response) == b"50 PERMANENT FAILURE\r\n"


def test_permanent_failure_response_reason():
    response = PermanentFailureResponse(reason="This resource is broken")
    assert response.status == 50
    assert response.__body__() is None
    assert bytes(response) == b"50 This resource is broken\r\n"


def test_not_found_response():
    response = NotFoundResponse()
    assert response.status == 51
    assert response.__body__() is None
    assert bytes(response) == b"51 NOT FOUND\r\n"


def test_not_found_response_reason():
    response = NotFoundResponse(reason="The document is unreadable")
    assert response.status == 51
    assert response.__body__() is None
    assert bytes(response) == b"51 The document is unreadable\r\n"


def test_proxy_refused_response():
    response = ProxyRequestRefusedResponse()
    assert response.status == 53
    assert response.__body__() is None
    assert bytes(response) == b"53 PROXY REQUEST REFUSED\r\n"


def test_bad_request_response():
    response = BadRequestResponse()
    assert response.status == 59
    assert response.__body__() is None
    assert bytes(response) == b"59 BAD REQUEST\r\n"


def test_bad_request_response_reason():
    response = BadRequestResponse(reason="You sent me a wrong request")
    assert response.status == 59
    assert response.__body__() is None
    assert bytes(response) == b"59 You sent me a wrong request\r\n"


def test_document_response(index_directory, index_content):
    response = DocumentResponse(
        index_directory.join("index.gmi").strpath, index_directory.strpath
    )
    assert response.status == 20
    bytes_content = bytes(index_content, encoding="utf-8")
    bytes_body = b"20 text/gemini\r\n" + bytes_content + b"\r\n"
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


def test_document_response_crlf(
    index_directory, multi_line_content, multi_line_content_crlf
):
    response = DocumentResponse(
        index_directory.join("multi_line.gmi").strpath, index_directory.strpath
    )
    assert response.status == 20
    multi_line_body_expected = bytes(multi_line_content_crlf, encoding="utf-8")
    bytes_body = b"20 text/gemini\r\n" + multi_line_body_expected
    assert bytes(response) == bytes_body


def test_document_response_binary(index_directory, image_content):
    response = DocumentResponse(
        index_directory.join("image.png").strpath, index_directory.strpath
    )
    assert response.status == 20
    bytes_body = b"20 image/png\r\n" + image_content
    assert bytes(response) == bytes_body


def test_directory_listing(index_directory):
    response = DirectoryListingResponse(
        index_directory.strpath, index_directory.strpath
    )

    assert response.status == 20
    assert response.__meta__() == b"20 text/gemini; charset=utf-8"
    assert response.__body__().startswith(b"# Directory listing for ``")
    assert b"=> /subdir" in response.__body__()
    assert b"=> /other.gmi" in response.__body__()


def test_directory_listing_crlf(index_directory):
    response = DirectoryListingResponse(
        index_directory.strpath, index_directory.strpath
    )
    assert bytes(response) == crlf(bytes(response))


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
        b"\r\n"  # empty line
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
        b"\r\n"  # Empty line
        b"My body\r\n"  # Body
    )


def test_template_response(template_file):
    response = TemplateResponse(template_file, **{"var1": "value1", "var2": "value2"})
    assert response.status == 20
    assert response.__body__() == b"First var: value1 / Second var: value2"

    response = TemplateResponse(
        template_file, **{"var1": "value1", "var2": "value2", "var_other": "other"}
    )
    assert response.status == 20
    assert response.__body__() == b"First var: value1 / Second var: value2"
    assert bytes(response) == (
        b"20 text/gemini; charset=utf-8\r\n"
        b"First var: value1 / Second var: value2\r\n"
    )


def test_template_response_wrong_context(template_file):
    # Empty context
    response = TemplateResponse(template_file)
    with pytest.raises(TemplateError):
        bytes(response)

    # Incomplete context
    response = TemplateResponse(template_file, **{"var1": "value1"})
    with pytest.raises(TemplateError):
        bytes(response)


def test_template_response_not_a_template():
    with pytest.raises(TemplateError):
        TemplateResponse("/tmp/not-a-template")
    try:
        TemplateResponse("/tmp/not-a-template")
    except Exception as exc:
        assert exc.args == ("Template file not found: `/tmp/not-a-template`",)
