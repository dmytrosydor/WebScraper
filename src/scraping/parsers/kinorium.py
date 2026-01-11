import httpx
from bs4 import BeautifulSoup

from src.scraping.schemas import MovieShort
from src.config.scraping import scraping_config, GENRES_MAP, KINORIUM_ENDPOINTS


class KinoriumParser:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=scraping_config.base_url,
            headers={
                "User-Agent": scraping_config.user_agent,
                "Referer": scraping_config.base_url + "/",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=scraping_config.request_timeout,
            follow_redirects=True,
        )

    async def scrape_by_genre(
        self,
        genre_name: str,
        kinorium_endpoint: str = KINORIUM_ENDPOINTS["film_list"],
    ):
        genre_id = GENRES_MAP.get(genre_name.lower())
        if not genre_id:
            return []

        params = {
            "type": "home",
            "order": "rating",
            "page": 1,
            "perpage": 50,
            "show_viewed": 1,
            "genres[]": genre_id,
        }

        response = await self.client.get(kinorium_endpoint, params=params)
        response.raise_for_status()

        data = response.json()

        html = data.get("result", {}).get("html", "")
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        results = []
        for item in soup.select("div.item"):
            link_tag = item.select_one("a.filmList__item-title")
            if not link_tag:
                continue

            title_span = link_tag.select_one("span.title")
            title = (
                title_span.get_text(strip=True)
                if title_span
                else link_tag.get_text(strip=True)
            )

            href = link_tag.get("href")
            if not href:
                continue

            full_link = (
                scraping_config.base_url + href # type: ignore
                if href.startswith("/") # type: ignore
                else href
            )

            results.append(MovieShort(title=title, link=full_link)) # type: ignore

        return results

    async def close(self):
        await self.client.aclose()

    async def scrape_movie_details(self, movie_id):
        pass
