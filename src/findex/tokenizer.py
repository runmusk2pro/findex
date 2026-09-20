import re
import unicodedata
from typing import Iterator

TOKEN_PATTERN = re.compile(r"\b\w+(?:[-']\w+)*\b")

def tokenize(text: str) -> Iterator[str]:
    normalized_text = unicodedata.normalize("NFKC", text)
    lower_text = normalized_text.lower()
    for match in TOKEN_PATTERN.finditer(lower_text):
        yield match.group(0)