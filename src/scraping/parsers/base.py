import logging
import urllib.parse
from playwright.async_api import Page, Browser, Playwright
from src.config.scraping import scraping_config

logger = logging.getLogger(__name__)

class KinoriumBaseParser:

    async def _launch_browser(self, p: Playwright) -> Browser:
        return await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]
        )

    async def _search_movie_url(self, page: Page, movie_title: str) -> str:
        encoded_query = urllib.parse.quote(movie_title)
        search_url = f"{scraping_config.base_url}/search/?q={encoded_query}"
        
        logger.info(f"Searching for movie: {movie_title}")
        await page.goto(search_url, wait_until="domcontentloaded")

        results = page.locator("a.search-page__title-link")
        
        if await results.count() == 0:
            try:
                await results.first.wait_for(timeout=3000)
            except Exception:
                pass
        
        if await results.count() == 0:
             raise ValueError("Movie not found in search results")

        movie_href = await results.first.get_attribute("href")
        
        if not movie_href:
            raise ValueError("Movie link attribute is empty")

        return (
            scraping_config.base_url + movie_href
            if movie_href.startswith("/")
            else movie_href
        )