import time
import tracemalloc
from collections import Counter
from src.findex.reader import iter_documents
from src.findex.tokenizer import tokenize

def run_lazy_pipeline(data_dir: str):
    print("Запуск лінивого конвеєра (генератори)...")
    
    # Запускаємо відстеження пам'яті та часу
    tracemalloc.start()
    start_time = time.time()

    total_docs = 0
    total_tokens = 0
    vocabulary = set()
    term_frequencies = Counter()

    # Проходимо по корпусу рівно один раз
    for text in iter_documents(data_dir):
        total_docs += 1
        for token in tokenize(text):
            total_tokens += 1
            vocabulary.add(token)
            term_frequencies[token] += 1  # Counter сам рахує частоту слів

    # Фіксуємо результати вимірювань
    end_time = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Виводимо зібрану статистику
    print(f"Кількість документів: {total_docs}")
    print(f"Загальна кількість токенів: {total_tokens}")
    print(f"Розмір словника (унікальних слів): {len(vocabulary)}")
    
    print("\nТоп-10 найчастіших термів (для прикладу):")
    for term, freq in term_frequencies.most_common(10):
        print(f"  {term}: {freq}")

    print("-" * 30)
    print(f"Час виконання: {end_time - start_time:.2f} сек")
    print(f"Пікова пам'ять: {peak_mem / 10**6:.4f} МБ")
    print("-" * 30)

def run_greedy_pipeline(data_dir: str):
    print("\nЗапуск жадібного конвеєра (списки)...")
    
    tracemalloc.start()
    start_time = time.time()

    # ЖАДІБНИЙ ПІДХІД: примусово витягуємо всі тексти з генератора 
    # і зберігаємо їх у величезний список в оперативній пам'яті
    all_texts = list(iter_documents(data_dir))
    
    total_docs = len(all_texts)
    total_tokens = 0
    vocabulary = set()
    term_frequencies = Counter()

    # Тільки тепер починаємо обробку того, що вже висить у пам'яті
    for text in all_texts:
        # Для ще більшої "жадібності" можна було б і токени в список зібрати:
        # all_tokens = list(tokenize(text))
        for token in tokenize(text):
            total_tokens += 1
            vocabulary.add(token)
            term_frequencies[token] += 1

    end_time = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Час виконання (Жадібний): {end_time - start_time:.2f} сек")
    print(f"Пікова пам'ять (Жадібний): {peak_mem / 10**6:.4f} МБ")
    print("-" * 30)


if __name__ == "__main__":
    data_folder = "data"
    run_lazy_pipeline(data_folder)
    run_greedy_pipeline(data_folder)