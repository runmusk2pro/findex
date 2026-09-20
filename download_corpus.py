import requests
import time
from pathlib import Path

def download_wikipedia_articles(target_dir: str = "data", total_articles: int = 1000, batch_size: int = 20):
    target_path = Path(target_dir)
    target_path.mkdir(exist_ok=True)
    
    # Рахуємо, скільки файлів вже є в папці, щоб продовжити з того ж місця
    articles_downloaded = len(list(target_path.glob("*.txt")))
    
    url = "https://en.wikipedia.org/w/api.php"
    headers = {
        "User-Agent": "FindexLabProject/1.0 (University Lab Work; bot)"
    }
    
    print(f"Вже завантажено {articles_downloaded} статей. Продовжуємо до {total_articles}...")
    
    with requests.Session() as session:
        session.headers.update(headers)
        
        while articles_downloaded < total_articles:
            params = {
                "action": "query",
                "format": "json",
                "generator": "random",
                "grnnamespace": 0,
                "grnlimit": batch_size,
                "prop": "extracts",
                "explaintext": 1,
                "exintro": 0
            }
            
            try:
                response = session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                pages = data.get("query", {}).get("pages", {})
                
                for page_id, page_data in pages.items():
                    title = page_data.get("title", "Unknown_Title").replace("/", "_").replace("\\", "_")
                    text = page_data.get("extract", "")
                    
                    if len(text) < 1000:
                        continue
                        
                    file_path = target_path / f"{page_id}.txt"
                    
                    # Записуємо тільки якщо файлу ще немає
                    if not file_path.exists():
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(f"{title}\n\n{text}")
                        articles_downloaded += 1
                    
                    if articles_downloaded >= total_articles:
                        break
                        
                print(f"Прогрес: {articles_downloaded} / {total_articles} статей")
                time.sleep(2)  # Збільшено стандартну затримку до 2 секунд
                
            except requests.exceptions.HTTPError as e:
                # Обробка ліміту запитів
                if e.response.status_code == 429:
                    print("Зловили ліміт запитів (429). Відпочиваємо 15 секунд...")
                    time.sleep(15)
                else:
                    print(f"HTTP помилка: {e}")
                    time.sleep(5)
            except Exception as e:
                print(f"Сталася помилка: {e}")
                time.sleep(5)
                
    print(f"Готово! Статті збережено у {target_path.absolute()}")

if __name__ == "__main__":
    download_wikipedia_articles()