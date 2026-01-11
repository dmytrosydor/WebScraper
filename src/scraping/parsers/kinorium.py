import asyncio
import httpx
from bs4 import BeautifulSoup
from src.scraping.schemas import MovieShort

class KinoriumParser:
    BASE_URL = "https://ua.kinorium.com"
    GENRES_MAP = {
        "комедія": 13,
        "аніме": 1,
    }

    async def scrape_by_genre(self, genre_name: str, page: int = 1, perpage: int = 50):
        genre_id = self.GENRES_MAP.get(genre_name, 13)
        url = f"{self.BASE_URL}/handlers/filmList/"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.BASE_URL,
        }

        params = {
            "type": "home",
            "order": "rating",
            "page": page,
            "perpage": perpage,
            "show_viewed": 1,
            "genres[]": genre_id,
        }

        async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
            response = await client.get(url, params=params)
            print(f"Status code: {response.status_code}")
            try:
                data = response.json()
                html = data.get("result", {}).get("html", "")
                soup = BeautifulSoup(html, "html.parser") if html else None
                if not soup:
                    print("HTML не знайдено, повертаємо пустий список")
                    return []
            except ValueError:
                print("Не JSON, вивід тексту:")
                print(response.text[:2000])
                return []

        items = soup.find_all("div", class_="item")
        results = []

        for item in items:
            link_tag = item.find("a", class_="filmList__item-title")
            if not link_tag:
                continue

            title_span = link_tag.find("span", class_="title")
            title = title_span.get_text(strip=True) if title_span else None

            link = link_tag.get("href")
            full_link = self.BASE_URL + link if link and link.startswith("/") else link

            results.append(MovieShort(title=title, link=full_link))

        return results


    async def close(self):
        await self.client.aclose()

    async def scrape_movie_details(self, movie_id):
        pass
