from pathlib import Path
from typing import Iterator

def iter_documents(directory: str | Path) -> Iterator[str]:
    corpus_path = Path(directory)
    for file_path in corpus_path.rglob("*.txt"):
        if file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                yield f.read()