import time
import tracemalloc
import gc
from src.findex.reader import iter_documents
from src.findex.tokenizer import tokenize

def run_lazy_pipeline(data_dir: str) -> None:
    print("Запуск лінивого конвеєра (читання по одному)...")
    
    gc.collect() 
    tracemalloc.start()
    start_time = time.time()

    total_docs = 0
    total_tokens = 0

    for text in iter_documents(data_dir):
        total_docs += 1
        for _ in tokenize(text):
            total_tokens += 1

    end_time = time.time()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Документів: {total_docs}")
    print(f"Загальна кількість токенів: {total_tokens}")
    print(f"Час виконання: {end_time - start_time:.2f} сек")
    print(f"Пікова пам'ять (Лінивий): {peak_mem / 10**6:.4f} МБ")
    print("-" * 30)

def run_greedy_pipeline(data_dir: str) -> None:
    print("\nЗапуск жадібного конвеєра (усі файли в оперативку)...")
    
    gc.collect()
    tracemalloc.start()
    start_time = time.time()

    all_texts: list[str] = list(iter_documents(data_dir))
    
    total_docs = len(all_texts)
    total_tokens = 0

    for text in all_texts:
        for _ in tokenize(text):
            total_tokens += 1

    end_time = time.time()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Документів: {total_docs}")
    print(f"Загальна кількість токенів: {total_tokens}")
    print(f"Час виконання: {end_time - start_time:.2f} сек")
    print(f"Пікова пам'ять (Жадібний): {peak_mem / 10**6:.4f} МБ")
    print("-" * 30)

if __name__ == "__main__":
    data_folder = "data"
    run_lazy_pipeline(data_folder)
    run_greedy_pipeline(data_folder)