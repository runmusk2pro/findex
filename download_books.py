import requests
import time
from pathlib import Path

def download_gutenberg_books(target_dir: str = "data", total_books: int = 50):
    target_path = Path(target_dir)
    target_path.mkdir(exist_ok=True)
    
    books_downloaded = 0
    # Починаємо з ID 11 (це "Аліса в Країні Див" та інші класичні твори)
    book_id = 11  
    
    print(f"Починаємо завантаження {total_books} великих книг у папку {target_dir}/...")
    
    with requests.Session() as session:
        while books_downloaded < total_books:
            # Пряме посилання на текстовий формат книги
            url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
            
            try:
                response = session.get(url, timeout=10)
                
                # Перевіряємо, чи файл існує і чи це дійсно текст
                if response.status_code == 200 and "text/plain" in response.headers.get("Content-Type", ""):
                    text = response.text
                    
                    # Беремо тільки відносно великі книги (від 100 КБ)
                    if len(text) > 100_000:
                        file_path = target_path / f"book_{book_id}.txt"
                        
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(text)
                            
                        books_downloaded += 1
                        size_mb = len(text.encode('utf-8')) / (1024 * 1024)
                        print(f"Завантажено {books_downloaded}/{total_books}: Книга #{book_id} ({size_mb:.2f} MB)")
                        
                        time.sleep(1) # Пауза, щоб сервери Гутенберга не заблокували нас
            except Exception as e:
                print(f"Помилка з книгою {book_id}: {e}")
                
            book_id += 1
            
    print(f"Готово! Книги збережено у {target_path.absolute()}")

if __name__ == "__main__":
    download_gutenberg_books()