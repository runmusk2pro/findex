import sys
import time
from pathlib import Path
from src.findex.store import load_index_pickle, load_index_json
from src.findex.search import BooleanSearch

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
    
    # Парсинг простого запиту типу "term1 AND term2" або "term1 OR term2"
    parts = query_str.split()
    term1 = parts[0]
    operator = "AND"
    term2 = parts[1] if len(parts) > 1 else ""
    
    if len(parts) >= 3:
        operator = parts[1].upper()
        term2 = parts[2]

    searcher = BooleanSearch(index)
    
    start_time = time.perf_counter()
    if engine == "set":
        doc_ids = searcher.search_set(term1, term2, operator)
    else:
        doc_ids = searcher.search_merge(term1, term2, operator)
    elapsed = time.perf_counter() - start_time
    
    print(f"\nЗнайдено документів: {len(doc_ids)} (за {elapsed:.5f} сек, рушій: {engine})")
    for d_id in list(doc_ids)[:10]: # Виводимо перші 10
        meta = index.documents.get(d_id)
        if meta:
            print(f" - [Doc {d_id}] {meta.title}")

if __name__ == "__main__":
    main()