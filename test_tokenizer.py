from src.findex.tokenizer import tokenize

def test_tokenize_basic():
    assert list(tokenize("Hello, world!")) == ["hello", "world"]

def test_tokenize_apostrophe():
    assert list(tokenize("It's a computer's monitor")) == ["it's", "a", "computer's", "monitor"]

def test_tokenize_hyphen():
    assert list(tokenize("State-of-the-art design.")) == ["state-of-the-art", "design"]

def test_tokenize_numbers():
    assert list(tokenize("Year 2026 is coming")) == ["year", "2026", "is", "coming"]