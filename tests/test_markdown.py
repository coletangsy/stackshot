from stackshot.adapters.markdown import markdown_to_html_document


def test_markdown_to_html_document_includes_builtin_css_and_body_content():
    html = markdown_to_html_document("# Title\n\n- one\n- two", css_text=None)

    assert "<h1>Title</h1>" in html
    assert "<li>one</li>" in html
    assert ".markdown-body" in html
    assert "<body><main class=\"markdown-body\">" in html


def test_markdown_to_html_document_appends_custom_css():
    html = markdown_to_html_document("# Title", css_text="h1 { color: red; }")

    assert "h1 { color: red; }" in html
