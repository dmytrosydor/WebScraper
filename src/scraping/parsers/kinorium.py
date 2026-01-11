import httpx
from bs4 import BeautifulSoup
from src.scraping.schemas import MovieShort
class KinoriumParser:
    #TODO currently working with local data (index.html) downloaded from https://ua.kinorium.com (filtered by genre = 'комедія') due to 429 error
    BASE_URL = "https://ua.kinorium.com"

    GENRES_MAP = {
        "комедія": 13,
        "аніме":1
    }

   

    def __init__(self):
        self.client = httpx.AsyncClient(
            # headers=self.HEADERS,
            timeout=15.0,
            follow_redirects=True,
        )

    async def scrape_by_genre(self, genre_name: str):
        results = []

        with open("src/scraping/parsers/index.html", "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        items = soup.find_all("div", class_="item")

        for item in items:
            link_tag = item.find("a", class_="filmList__item-title")

            if not link_tag:
                continue

            title_span = link_tag.find("span", class_="title")
            title = title_span.get_text(strip=True) if title_span else None

            link = link_tag.get("href")

            results.append(MovieShort(
                title=title,
                link=link))

        return results

    async def scrape_movie_details(self, movie_id):
        # Implementation for scraping movie details
        pass