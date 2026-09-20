import sys
import time
import tracemalloc
from pathlib import Path
from src.findex.index import InvertedIndex
from src.findex.store import save_index_pickle, save_index_json

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
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    peak_mb = peak / (1024 * 1024)
    print(f"Індекс збудовано за {elapsed:.2f} сек. Пік пам'яті: {peak_mb:.2f} МБ")
    print(f"Опрацьовано документів: {len(index.documents)}, унікальних термінів: {len(index.index)}")
    
    # Зберігаємо
    if file_format == "json":
        save_time, size = save_index_json(index, out_path)
    else:
        save_time, size = save_index_pickle(index, out_path)
        
    size_mb = size / (1024 * 1024)
    print(f"Збережено у {out_path} ({size_mb:.2f} МБ) за {save_time:.2f} сек.")

if __name__ == "__main__":
    main()