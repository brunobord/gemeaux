from gemeaux import crlf


def test_crlf(multi_line_content, multi_line_content_crlf):
    multi_line_content = bytes(multi_line_content, encoding="utf-8")
    multi_line_content_crlf = bytes(multi_line_content_crlf, encoding="utf-8")
    assert crlf(multi_line_content) == multi_line_content_crlf


def test_crlf_several_lf():
    content = bytes("line\n\n\nlast line", encoding="utf-8")
    content_expected = bytes("line\r\n\r\n\r\nlast line\r\n", encoding="utf-8")
    assert crlf(content) == content_expected
