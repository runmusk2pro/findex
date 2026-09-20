import pickle
import json
from pathlib import Path
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from findex.index import InvertedIndex

def save_index_pickle(index: "InvertedIndex", filepath: str | Path):
    """Зберігає індекс за допомогою pickle."""
    # ПРИМІТКА З БЕЗПЕКИ: Ніколи не завантажуйте pickle-файли з неперевірених 
    # джерел, оскільки pickle.load може виконувати довільний код.
    start_time = time.perf_counter()
    with open(filepath, "wb") as f:
        pickle.dump(index, f)
    elapsed = time.perf_counter() - start_time
    size_bytes = Path(filepath).stat().st_size
    return elapsed, size_bytes

def load_index_pickle(filepath: str | Path):
    """Завантажує індекс за допомогою pickle."""
    start_time = time.perf_counter()
    with open(filepath, "rb") as f:
        index = pickle.load(f)
    elapsed = time.perf_counter() - start_time
    return index, elapsed

def save_index_json(index: "InvertedIndex", filepath: str | Path):
    """Зберігає індекс у форматі JSON."""
    start_time = time.perf_counter()
    
    data = {
        "documents": {
            str(doc_id): {"doc_id": m.doc_id, "title": m.title, "length": m.length}
            for doc_id, m in index.documents.items()
        },
        "index": {
            term: [{"doc_id": p.doc_id, "term_frequency": p.term_frequency} for p in postings]
            for term, postings in index.index.items()
        }
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    elapsed = time.perf_counter() - start_time
    size_bytes = Path(filepath).stat().st_size
    return elapsed, size_bytes

def load_index_json(filepath: str | Path):
    """Завантажує індекс із JSON-файлу."""
    start_time = time.perf_counter()
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Локальний імпорт всередині функції повністю усуває проблему циклічного імпорту
    from findex.index import InvertedIndex, Posting, DocMeta
    
    instance = InvertedIndex()
    
    for doc_id_str, m_dict in data["documents"].items():
        doc_id = int(doc_id_str)
        instance.documents[doc_id] = DocMeta(
            doc_id=m_dict["doc_id"],
            title=m_dict["title"],
            length=m_dict["length"]
        )
        
    for term, p_list in data["index"].items():
        instance.index[term] = [
            Posting(doc_id=p["doc_id"], term_frequency=p["term_frequency"])
            for p in p_list
        ]
        
    elapsed = time.perf_counter() - start_time
    return instance, elapsed