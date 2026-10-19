import pytest
from findex.tokenizer import tokenize

@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello World!", ["hello", "world"]),
        ("Python 3.12 is AWESOME", ["python", "3", "12", "is", "awesome"]),
        ("event-driven async/await", ["event-driven", "async", "await"]),
        ("   multiple   spaces   ", ["multiple", "spaces"]),
        ("", []),
    ],
)
def test_tokenize_parametrized(text: str, expected: list[str]) -> None:
    assert list(tokenize(text)) == expected