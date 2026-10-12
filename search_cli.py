import sys
from findex.index import open_index
from findex.search import execute_search
from findex.ranking import BM25, TfIdf

# ТУТ ВКАЖИ ШЛЯХ ДО СВОГО ФАЙЛУ З ДАНИМИ (index.json або index.bin)
INDEX_PATH = "index.json" 

def main():
    print(f"Завантаження індексу з {INDEX_PATH}...")
    
    # Використовуємо наш context manager
    with open_index(INDEX_PATH) as index:
        print(f"Індекс завантажено! Документів: {index.num_docs}, Термінів: {len(index)}")
        print("Введіть запит (або 'exit' щоб вийти).")
        print("Підтримуються: AND, OR, NOT, ( ), та \"точні фрази\"")
        
        # Для тестів використовуємо BM25 за замовчуванням
        scorer = BM25() 
        
        while True:
            query = input("\nПошук > ").strip()
            if query.lower() in ('exit', 'quit', 'q'):
                break
            if not query:
                continue
                
            # Команда для перемикання алгоритму
            if query.lower() == "/tfidf":
                scorer = TfIdf()
                print("Перемкнуто на TF-IDF")
                continue
            if query.lower() == "/bm25":
                scorer = BM25()
                print("Перемкнуто на BM25")
                continue

            try:
                # Оскільки у нас зараз немає текстів самих книг у пам'яті (corpus), 
                # сніпети будуть порожніми, але пошук працюватиме.
                results = execute_search(query, index, scorer)
                
                if not results:
                    print("Нічого не знайдено.")
                    continue
                    
                for rank, res in enumerate(results, 1):
                    print(f"{rank}. [{res.score:.4f}] {res.title} (Doc ID: {res.doc_id})")
                    if res.snippet:
                        print(f"   {res.snippet}")
                        
            except Exception as e:
                print(f"Помилка виконання запиту: {e}")

if __name__ == "__main__":
    main()