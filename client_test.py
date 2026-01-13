import time
import requests

# Конфігурація
BASE_URL = "http://127.0.0.1:8000/api"

# Список жанрів (для підказки користувачу)
VALID_GENRES = [
    "аніме", "біографія", "бойовик", "вестерн", "військовий", "детектив",
    "документальний", "драма", "жахи", "історія", "комедія", "концерт",
    "короткометражка", "кримінал", "мелодрама", "містика", "музика",
    "мультфільм", "мюзикл", "пригоди", "сімейний", "спорт", "трилер",
    "фантастика", "фентезі"
]

def print_separator():
    print("-" * 50)

def poll_task_status(task_id):
    """Функція опитування статусу (Polling)"""
    print(f"[OK] Задача створена! ID: {task_id}")
    print("Очікування результату (оновлення кожні 1 сек)...")
    
    start_time = time.time()
    
    while True:
        time.sleep(1)
        elapsed = int(time.time() - start_time)
        
        try:
            status_resp = requests.get(f"{BASE_URL}/scrape/{task_id}")
            status_resp.raise_for_status()
            task_info = status_resp.json()
        except Exception as e:
            print(f"[ERROR] Помилка з'єднання: {e}")
            continue

        status = task_info["status"]
        print(f"   [{elapsed}s] Статус: {status}")

        if status == "completed":
            return task_info.get("result")
        
        elif status == "failed":
            print(f"\n[FAIL] ПОМИЛКА СЕРВЕРА: {task_info.get('error_message')}")
            return None

def run_genre_scraping():
    print("\n--- ПОШУК ЗА ЖАНРОМ ---")
    print(f"Доступні жанри: {', '.join(VALID_GENRES[:10])}...")
    
    genre = input("Введіть жанр (наприклад 'драма'): ").strip().lower()
    
    if not genre:
        print("[!] Жанр не може бути порожнім!")
        return

    print(f"Відправляю запит на топ фільмів у жанрі '{genre}'...")
    
    try:
        response = requests.post(f"{BASE_URL}/scrape", json={
            "query": genre,
            "mode": "http"  # Режим для жанрів
        })
        response.raise_for_status()
        task_id = response.json()["task_id"]
        
        result = poll_task_status(task_id)
        
        if result:
            print_separator()
            print(f"Знайдено фільмів: {len(result)}")
            # Виводимо перші 10 результатів
            for idx, movie in enumerate(result[:10], 1):
                print(f"{idx}. {movie['title']} ({movie['link']})")
            if len(result) > 10:
                print(f"... і ще {len(result) - 10} фільмів")
            print_separator()

    except requests.exceptions.HTTPError as e:
        print(f"Помилка API (400/500): {e.response.text}")
    except Exception as e:
        print(f"Критична помилка: {e}")

def run_movie_details_scraping():
    print("\n--- ДЕТАЛІ ФІЛЬМУ (HEADLESS) ---")
    movie_name = input("Введіть назву фільму (наприклад '1+1'): ").strip()
    
    if not movie_name:
        print("[!] Назва не може бути порожньою!")
        return

    print(f"Шукаю деталі про '{movie_name}' (це займе час)...")
    
    try:
        response = requests.post(f"{BASE_URL}/scrape", json={
            "query": movie_name,
            "mode": "headless"  
        })
        response.raise_for_status()
        task_id = response.json()["task_id"]
        
        result = poll_task_status(task_id)
        
        if result:
            print_separator()
            movie = result if isinstance(result, dict) else result[0]
            
            print(f"НАЗВА:      {movie.get('title')}")
            print(f"РІК:        {movie.get('year')}")
            print(f"РЕЙТИНГ:    {movie.get('rating')}")
            print(f"КРАЇНИ:     {', '.join(movie.get('countries', []))}")
            print(f"ЖАНРИ:      {', '.join(movie.get('genres', []))}")
            print(f"ТРИВАЛІСТЬ: {movie.get('duration_minutes')} хв")
            print(f"URL:        {movie.get('kinorium_url')}")
            print(f"\nОПИС:\n{movie.get('description', '')[:200]}...")
            print_separator()

    except Exception as e:
        print(f"[ERROR] Помилка: {e}")

def run_ui_scraping():
    print("\n--- ВІДКРИТТЯ В БРАУЗЕРІ (UI) ---")
    movie_name = input("Введіть назву фільму: ").strip()
    
    if not movie_name:
        print("[!] Назва не може бути порожньою!")
        return

    print(f"Шукаю посилання для '{movie_name}'...")
    
    try:
        response = requests.post(f"{BASE_URL}/scrape", json={
            "query": movie_name,
            "mode": "ui" 
        })
        response.raise_for_status()
        task_id = response.json()["task_id"]
        
        result = poll_task_status(task_id)
        
        if result:
            print_separator()
            print(f"[SUCCESS] Фільм відкрито у браузері.")
            print(f"URL: {result.get('opened_url')}")
            print_separator()

    except Exception as e:
        print(f"[ERROR] Помилка: {e}")

def main():
    while True:
        print("\n" + "="*30)
        print("   WEBSCRAPER CLIENT")
        print("="*30)
        print("1. Пошук фільмів за жанром (HTTP)")
        print("2. Знайти деталі фільму (Headless)")
        print("3. Відкрити сторінку фільму (UI)")
        print("4. Вихід")
        
        choice = input("\nВаш вибір (1-4): ").strip()
        
        if choice == "1":
            run_genre_scraping()
        elif choice == "2":
            run_movie_details_scraping()
        elif choice == "3":
            run_ui_scraping()
        elif choice == "4":
            print("До побачення!")
            break
        else:
            print("[!] Невірний вибір, спробуйте ще раз.")

if __name__ == "__main__":
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        main()
    except requests.exceptions.ConnectionError:
        print(f"\n[FAIL] Сервер недоступний за адресою {BASE_URL}")
        print("Запустіть сервер командою: uvicorn src.main:app --reload")