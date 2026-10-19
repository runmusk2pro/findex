import math
from typing import Protocol
from findex.index import Index, Posting

class Scorer(Protocol):
    """Протокол для алгоритмів ранжування."""
    def score(self, term: str, posting: Posting, index: Index) -> float: ...

class TfIdf:
    def score(self, term: str, posting: Posting, index: Index) -> float:
        if posting.term_frequency == 0:
            return 0.0
        df = index.df(term)
        if df == 0:
            return 0.0
        idf = math.log(index.num_docs / df)
        return (1.0 + math.log(float(posting.term_frequency))) * idf

class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

    def score(self, term: str, posting: Posting, index: Index) -> float:
        if posting.term_frequency == 0:
            return 0.0
        df = index.df(term)
        if df == 0:
            return 0.0
        idf = math.log((index.num_docs - df + 0.5) / (df + 0.5) + 1.0)
        
        doc_len = index.doc_length(posting.doc_id)
        avg_len = index.avg_doc_length
        if avg_len == 0.0:
            return 0.0
            
        num = posting.term_frequency * (self.k1 + 1.0)
        den = posting.term_frequency + self.k1 * (1.0 - self.b + self.b * (doc_len / avg_len))
        
        return idf * (num / den)