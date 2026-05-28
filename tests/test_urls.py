from worksummary import urls


def test_extract_urls_empty():
    assert urls.extract_urls("plain text with no urls") == []


def test_extract_urls_single_http():
    assert urls.extract_urls("see http://example.com") == ["http://example.com"]


def test_extract_urls_single_https():
    assert urls.extract_urls("see https://example.com") == ["https://example.com"]


def test_extract_urls_strips_trailing_sentence_punctuation():
    assert urls.extract_urls("see https://example.com.") == ["https://example.com"]
    assert urls.extract_urls("see https://example.com,") == ["https://example.com"]
    assert urls.extract_urls("see https://example.com!") == ["https://example.com"]
    assert urls.extract_urls("see https://example.com?") == ["https://example.com"]


def test_extract_urls_strips_trailing_brackets():
    assert urls.extract_urls("(see https://example.com)") == ["https://example.com"]
    assert urls.extract_urls("[see https://example.com]") == ["https://example.com"]


def test_extract_urls_multiple():
    text = "fixed https://a.com and also https://b.com here"
    assert urls.extract_urls(text) == ["https://a.com", "https://b.com"]


def test_extract_urls_preserves_query_strings():
    url = "https://example.com/path?a=1&b=2"
    assert urls.extract_urls(f"see {url}") == [url]


def test_rewrite_with_footnotes_no_urls():
    text, extracted, next_n = urls.rewrite_with_footnotes("plain text", start_n=1)
    assert text == "plain text"
    assert extracted == []
    assert next_n == 1


def test_rewrite_with_footnotes_single_url():
    text, extracted, next_n = urls.rewrite_with_footnotes(
        "Fixed bug 128 https://example.com/issues/597", start_n=1
    )
    assert text == "Fixed bug 128 [¹]"
    assert extracted == ["https://example.com/issues/597"]
    assert next_n == 2


def test_rewrite_with_footnotes_multiple_urls_sequential():
    text, extracted, next_n = urls.rewrite_with_footnotes(
        "Reviewed https://a.com and https://b.com", start_n=1
    )
    assert text == "Reviewed [¹] and [²]"
    assert extracted == ["https://a.com", "https://b.com"]
    assert next_n == 3


def test_rewrite_with_footnotes_continues_numbering():
    text, extracted, next_n = urls.rewrite_with_footnotes("Reviewed https://c.com", start_n=3)
    assert text == "Reviewed [³]"
    assert extracted == ["https://c.com"]
    assert next_n == 4


def test_rewrite_with_footnotes_collapses_whitespace_around_removed_url():
    text, extracted, _ = urls.rewrite_with_footnotes(
        "Reviewed https://a.com https://b.com today", start_n=1
    )
    assert text == "Reviewed [¹][²] today"
    assert extracted == ["https://a.com", "https://b.com"]


def test_rewrite_with_footnotes_preserves_trailing_punctuation():
    text, extracted, _ = urls.rewrite_with_footnotes("See https://example.com.", start_n=1)
    assert text == "See [¹]."
    assert extracted == ["https://example.com"]


def test_rewrite_with_footnotes_multi_digit_footnote():
    text, extracted, _ = urls.rewrite_with_footnotes("Reviewed https://x.com", start_n=12)
    # 12 -> superscript "¹²"
    assert text == "Reviewed [¹²]"
    assert extracted == ["https://x.com"]
