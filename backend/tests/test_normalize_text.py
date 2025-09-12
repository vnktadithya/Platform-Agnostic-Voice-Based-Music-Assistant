from backend.utils.normalize_text import normalize_query

def test_basic_normalization():
    assert normalize_query("Hello, World!") == "hello world"

def test_unicode_normalization():
    assert normalize_query("Beyoncé") == "beyonce"

def test_multiple_spaces():
    assert normalize_query("  a    b  ") == "a b"

def test_empty_and_non_string():
    assert normalize_query("") == ""
    assert normalize_query(None) == ""
    assert normalize_query(123) == ""
