import logging
import webbrowser
from playwright.async_api import async_playwright

from src.scraping.schemas import UIActionResponse
from src.scraping.parsers.base import KinoriumBaseParser  

logger = logging.getLogger(__name__)

class KinoriumUIParser(KinoriumBaseParser): 
    
    async def parse(self, movie_title: str) -> dict:
        logger.info(f"Starting UI mode for '{movie_title}'")

        try:
            final_url = await self._find_movie_url_helper(movie_title)
        except ValueError as e:
            return {"status": "error", "message": str(e)}

        self._open_in_system_browser(final_url)
        return UIActionResponse(
            opened_url=final_url, # type: ignore
        )
        
    def _open_in_system_browser(self, url: str) -> None:
        logger.info(f"Opening system browser: {url}")
        webbrowser.open(url, new=2)

    async def _find_movie_url_helper(self, movie_title: str) -> str:
        async with async_playwright() as p:
            browser = await self._launch_browser(p)
            try:
                page = await browser.new_page()
                return await self._search_movie_url(page, movie_title)
            finally:
                await browser.close()