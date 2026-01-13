import logging
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from src.scraping.schemas import MovieShort
from src.config.scraping import (
    scraping_config,
    GENRES_MAP,
    KINORIUM_ENDPOINTS,
)


logger = logging.getLogger(__name__)
class KinoriumHttpParser:
    async def parse(
        self,
        genre_name: str,
        page: int = 1,
        perpage: int = 50,
    ):
        genre_id = GENRES_MAP.get(genre_name, 13)

        if not genre_id:
            raise ValueError(f"Unknown genre: {genre_name}")


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
        try:    

            logger.info(f"Starting scraping for genre '{genre_name}' (ID: {genre_id}) - Page {page}")
            async with httpx.AsyncClient(
                headers=headers,
                timeout=scraping_config.request_timeout,
            ) as client:
                response = await client.get(url, params=params)

                logger.info(f"Received response status: {response.status_code}")
             
            try:
                data = response.json()
            except ValueError:
                raise ValueError("Invalid JSON response from Kinorium. Status code: {response.status_code}")
            
            html = data.get("result", {}).get("html", "")
            if not html:
                logger.warning("No HTML content found in the response")
                return [] 
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Kinorium did not respond in {scraping_config.request_timeout} seconds") 
        except httpx.HTTPStatusError as e:
            # Errors from website like: 404, 500 , 503
            raise RuntimeError(f"Kinorium returned HTTP error: {str(e)}")
        except httpx.RequestError as e:
            raise ConnectionError(f"Error connecting to Kinorium: {str(e)}")    
            


        soup = BeautifulSoup(html, "html.parser")

        results = []
        for item in soup.find_all("div", class_="item"):
            link_tag = item.find("a", class_="filmList__item-title")
            if not link_tag:
                continue

            title_span = link_tag.find("span", class_="title")
            title = title_span.get_text(strip=True) if title_span else None

            if not title:
                logger.warning(f"Skipping item without title. Link: {href}") # Case when title is missing (without this will be pydantic.ValidationError)
                continue

            href = link_tag.get("href")
            if not href:
                continue

            full_link = (
                scraping_config.base_url + href # type: ignore
                if href.startswith("/") # type: ignore
                else href
            )

            results.append(MovieShort(title=title, link=full_link)) # type: ignore

        logger.info(f"Successfully scraped {len(results)} movies for genre '{genre_name}' on page {page}")
        return results
