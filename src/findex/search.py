from typing import List, Set
import sys
import time
from src.findex.store import load_index_pickle, load_index_json
from findex.index import InvertedIndex, Posting, DocMeta

class BooleanSearch:
    def __init__(self, index):
        self.index = index

    def search_merge(self, term1: str, term2: str, operator: str = "AND") -> List[int]:
        postings1 = self.index.index.get(term1, [])
        postings2 = self.index.index.get(term2, [])

        i, j = 0, 0
        result: List[int] = []

        if operator == "AND":
            while i < len(postings1) and j < len(postings2):
                p1 = postings1[i]
                p2 = postings2[j]
                if p1.doc_id == p2.doc_id:
                    result.append(p1.doc_id)
                    i += 1
                    j += 1
                elif p1.doc_id < p2.doc_id:
                    i += 1
                else:
                    j += 1

        elif operator == "OR":
            while i < len(postings1) and j < len(postings2):
                p1 = postings1[i]
                p2 = postings2[j]
                if p1.doc_id == p2.doc_id:
                    result.append(p1.doc_id)
                    i += 1
                    j += 1
                elif p1.doc_id < p2.doc_id:
                    result.append(p1.doc_id)
                    i += 1
                else:
                    result.append(p2.doc_id)
                    j += 1
            while i < len(postings1):
                result.append(postings1[i].doc_id)
                i += 1
            while j < len(postings2):
                result.append(postings2[j].doc_id)
                j += 1

        return result

    def search_set(self, term1: str, term2: str, operator: str = "AND") -> Set[int]:
        docs1 = {p.doc_id for p in self.index.index.get(term1, [])}
        docs2 = {p.doc_id for p in self.index.index.get(term2, [])}

        if operator == "AND":
            return docs1 & docs2
        elif operator == "OR":
            return docs1 | docs2
        return set()

def main():
    if len(sys.argv) < 3:
        print("Використання: python -m findex.search <index_file> \"term1 AND term2\" [--engine merge|set] [--format pickle|json]")
        sys.exit(1)
        
    index_file = sys.argv[1]
    query_str = sys.argv[2]
    
    engine = "merge"
    file_format = "pickle"
    
    if "--engine" in sys.argv:
        eng_idx = sys.argv.index("--engine")
        if eng_idx + 1 < len(sys.argv):
            engine = sys.argv[eng_idx + 1]
            
    if "--format" in sys.argv:
        fmt_idx = sys.argv.index("--format")
        if fmt_idx + 1 < len(sys.argv):
            file_format = sys.argv[fmt_idx + 1]

    print(f"Завантаження індексу з {index_file}...")
    if file_format == "json":
        index, load_time = load_index_json(index_file)
    else:
        index, load_time = load_index_pickle(index_file)
        
    print(f"Індекс завантажено за {load_time:.2f} сек.")
    
    parts = query_str.split()
    term1 = parts[0].lower()
    operator = "AND"
    term2 = parts[2].lower() if len(parts) > 2 else (parts[1].lower() if len(parts) > 1 else "")
    if len(parts) >= 3:
        operator = parts[1].upper()
        term2 = parts[2].lower()

    searcher = BooleanSearch(index)
    
    start_time = time.perf_counter()
    if engine == "set":
        doc_ids = searcher.search_set(term1, term2, operator)
    else:
        doc_ids = searcher.search_merge(term1, term2, operator)
    elapsed = time.perf_counter() - start_time
    
    print(f"\nЗнайдено документів: {len(doc_ids)} (за {elapsed:.5f} сек, рушій: {engine})")
    for d_id in list(doc_ids)[:10]:
        meta = index.documents.get(d_id)
        if meta:
            print(f" - [Doc {d_id}] {meta.title}")

if __name__ == "__main__":
    main()