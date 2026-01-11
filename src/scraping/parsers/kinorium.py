import httpx
from bs4 import BeautifulSoup

from src.scraping.schemas import MovieShort
from src.config.scraping import (
    scraping_config,
    GENRES_MAP,
    KINORIUM_ENDPOINTS,
)


class KinoriumParser:
    async def scrape_by_genre(
        self,
        genre_name: str,
        page: int = 1,
        perpage: int = 50,
    ):
        genre_id = GENRES_MAP.get(genre_name, 13)

        url = scraping_config.base_url + KINORIUM_ENDPOINTS["film_list"]

        headers = {
            "User-Agent": scraping_config.user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": scraping_config.base_url,
        }

        params = {
            "type": "home",
            "order": "rating",
            "page": page,
            "perpage": perpage,
            "show_viewed": 1,
            "genres[]": genre_id,
        }

        async with httpx.AsyncClient(
            headers=headers,
            timeout=scraping_config.request_timeout,
        ) as client:
            response = await client.get(url, params=params)
            print(f"Status code: {response.status_code}")

            try:
                data = response.json()
                html = data.get("result", {}).get("html", "")
                if not html:
                    print("HTML не знайдено, повертаємо пустий список")
                    return []
            except ValueError:
                print("Не JSON:")
                print(response.text[:2000])
                return []

        soup = BeautifulSoup(html, "html.parser")

        results = []
        for item in soup.find_all("div", class_="item"):
            link_tag = item.find("a", class_="filmList__item-title")
            if not link_tag:
                continue

            title_span = link_tag.find("span", class_="title")
            title = title_span.get_text(strip=True) if title_span else None

            href = link_tag.get("href")
            if not href:
                continue

            full_link = (
                scraping_config.base_url + href
                if href.startswith("/")
                else href
            )

            results.append(MovieShort(title=title, link=full_link))

        return results

    async def scrape_movie_details(self, movie_id):
        pass



