from collections.abc import Mapping, Iterator, Generator, Iterable
from functools import cached_property
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(slots=True)
class Posting:
    doc_id: int
    term_frequency: int
    positions: list[int] = field(default_factory=list[int])

@dataclass(slots=True)
class DocMeta:
    doc_id: int
    title: str
    length: int

class Index(Mapping[str, list[Posting]]):
    def __init__(self) -> None:
        self.index: dict[str, list[Posting]] = {}
        self.documents: dict[int, DocMeta] = {}

    def __getitem__(self, term: str) -> list[Posting]:
        if term not in self.index:
            raise KeyError(f"Термін '{term}' не знайдено.")
        return self.index[term]

    def __iter__(self) -> Iterator[str]:
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
        return float(total_length) / self.num_docs

    def df(self, term: str) -> int:
        return len(self.index.get(term, []))

    def doc_length(self, doc_id: int) -> int:
        meta = self.documents.get(doc_id)
        return meta.length if meta else 0

@contextmanager
def open_index(path: str | Path) -> Generator[Index, None, None]:
    from findex.store import load_index_pickle, load_index_json
    
    path_str = str(path)
    if path_str.endswith(".json"):
        index_instance, _ = load_index_json(path)
    else:
        index_instance, _ = load_index_pickle(path)
        
    try:
        yield index_instance
    finally:
        pass
    
@dataclass(slots=True)
class PartialIndex:
    index: dict[str, list[Posting]] = field(default_factory=lambda: {})
    documents: dict[int, DocMeta] = field(default_factory=lambda: {})

def build_partial(chunk: list[Path], start_doc_id: int) -> PartialIndex:
    """Будує частковий індекс для заданого списку файлів (працює у воркері)."""
    from findex.tokenizer import tokenize
    
    partial = PartialIndex()
    current_id = start_doc_id
    
    for file_path in chunk:
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
            
        tokens = list(tokenize(text))
        partial.documents[current_id] = DocMeta(doc_id=current_id, title=file_path.name, length=len(tokens))
        
        counts: dict[str, int] = {}
        positions_map: dict[str, list[int]] = {}
        
        for pos, t in enumerate(tokens):
            counts[t] = counts.get(t, 0) + 1
            if t not in positions_map:
                positions_map[t] = []
            positions_map[t].append(pos)
            
        for term, freq in counts.items():
            if term not in partial.index:
                partial.index[term] = []
            partial.index[term].append(Posting(doc_id=current_id, term_frequency=freq, positions=positions_map[term]))
            
        current_id += 1
        
    return partial

def merge(partials: Iterable[PartialIndex]) -> Index:
    """Зливає часткові індекси в один глобальний."""
    final_idx = Index()
    
    for p in partials:
        final_idx.documents.update(p.documents)
        for term, postings in p.index.items():
            if term not in final_idx.index:
                final_idx.index[term] = []
            final_idx.index[term].extend(postings)
            
    # Постінги повинні бути відсортовані за doc_id (вимога для оптимізацій)
    for term in final_idx.index:
        final_idx.index[term].sort(key=lambda x: x.doc_id)
        
    return final_idx