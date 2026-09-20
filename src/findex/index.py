from dataclasses import dataclass
from typing import Dict, List
from collections import defaultdict
from pathlib import Path
import sys
import time
import tracemalloc
from findex.reader import iter_documents
from findex.tokenizer import tokenize
from findex.store import save_index_pickle, save_index_json

@dataclass(frozen=True, slots=True)
class Posting:
    doc_id: int
    term_frequency: int

@dataclass(frozen=True, slots=True)
class DocMeta:
    doc_id: int
    title: str
    length: int

class InvertedIndex:
    def __init__(self):
        self.index: Dict[str, List[Posting]] = {}
        self.documents: Dict[int, DocMeta] = {}

    @classmethod
    def build_from_corpus(cls, data_dir: str | Path) -> "InvertedIndex":
        instance = cls()
        raw_index: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        doc_counter = 0

        for file_path in Path(data_dir).rglob("*.txt"):
            if not file_path.is_file():
                continue
            
            doc_counter += 1
            doc_id = doc_counter
            
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            tokens = list(tokenize(text))
            
            instance.documents[doc_id] = DocMeta(
                doc_id=doc_id,
                title=file_path.name,
                length=len(tokens)
            )

            for token in tokens:
                raw_index[token][doc_id] += 1

        for term, docs_freqs in raw_index.items():
            postings = [
                Posting(doc_id=d_id, term_frequency=freq)
                for d_id, freq in sorted(docs_freqs.items())
            ]
            instance.index[term] = postings

        return instance

def main():
    if len(sys.argv) < 2:
        print("Використання: python -m findex.index <corpus_dir> [--out index.bin] [--format pickle|json]")
        sys.exit(1)
        
    corpus_dir = sys.argv[1]
    out_path = "index.bin"
    file_format = "pickle"
    
    if "--out" in sys.argv:
        out_idx = sys.argv.index("--out")
        if out_idx + 1 < len(sys.argv):
            out_path = sys.argv[out_idx + 1]
            
    if "--format" in sys.argv:
        fmt_idx = sys.argv.index("--format")
        if fmt_idx + 1 < len(sys.argv):
            file_format = sys.argv[fmt_idx + 1]

    print(f"Будуємо індекс із корпусу: {corpus_dir}...")
    
    tracemalloc.start()
    start_time = time.perf_counter()
    
    index = InvertedIndex.build_from_corpus(corpus_dir)
    
    elapsed = time.perf_counter() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    peak_mb = peak / (1024 * 1024)
    print(f"Індекс збудовано за {elapsed:.2f} сек. Пік пам'яті: {peak_mb:.2f} МБ")
    print(f"Опрацьовано документів: {len(index.documents)}, унікальних термінів: {len(index.index)}")
    
    if file_format == "json":
        save_time, size = save_index_json(index, out_path)
    else:
        save_time, size = save_index_pickle(index, out_path)
        
    size_mb = size / (1024 * 1024)
    print(f"Збережено у {out_path} ({size_mb:.2f} МБ) за {save_time:.2f} сек.")

if __name__ == "__main__":
    main()