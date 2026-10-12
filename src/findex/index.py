from collections.abc import Mapping
from functools import cached_property
from contextlib import contextmanager
from dataclasses import dataclass, field

@dataclass
class Posting:
    doc_id: int
    term_frequency: int
    # Додаємо позиції для фраз (як вимагає лаба 3).
    # Якщо у твоєму індексі їх ще немає, буде просто порожній список.
    positions: list[int] = field(default_factory=list) 

@dataclass
class DocMeta:
    doc_id: int
    title: str
    length: int

class Index(Mapping):
    def __init__(self):
        self.index: dict[str, list[Posting]] = {}
        self.documents: dict[int, DocMeta] = {}

    def __getitem__(self, term: str) -> list[Posting]:
        if term not in self.index:
            raise KeyError(f"Термін '{term}' не знайдено.")
        return self.index[term]

    def __iter__(self):
        return iter(self.index)

    def __len__(self) -> int:
        return len(self.index)

    def __repr__(self) -> str:
        return f"Index(terms={len(self)}, docs={self.num_docs})"

    @property
    def num_docs(self) -> int:
        return len(self.documents)

    @cached_property
    def avg_doc_length(self) -> float:
        if self.num_docs == 0:
            return 0.0
        total_length = sum(meta.length for meta in self.documents.values())
        return total_length / self.num_docs

    def df(self, term: str) -> int:
        """Кількість документів, у яких зустрічається термін."""
        return len(self.index.get(term, []))

    def doc_length(self, doc_id: int) -> int:
        """Повертає довжину конкретного документа."""
        meta = self.documents.get(doc_id)
        return meta.length if meta else 0

@contextmanager
def open_index(path: str):
    """Контекстний менеджер для завантаження індексу."""
    # Робимо локальний імпорт, щоб уникнути помилки циклічного імпорту (Circular Import)
    from findex.store import load_index_pickle, load_index_json
    
    path_str = str(path)
    if path_str.endswith(".json"):
        index_instance, _ = load_index_json(path)
    else:
        index_instance, _ = load_index_pickle(path)
        
    try:
        yield index_instance
    finally:
        # У нас дані тримаються в пам'яті, тому тут нічого примусово закривати не треба.
        # Але блок finally гарантує правильну роботу with.
        pass