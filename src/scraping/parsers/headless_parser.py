import logging
from playwright.async_api import async_playwright
import re

from src.scraping.schemas import MovieDetails
from src.config.scraping import scraping_config
from src.scraping.parsers.base import KinoriumBaseParser 

logger = logging.getLogger(__name__)

class KinoriumHeadlessParser(KinoriumBaseParser): 
    
    async def parse(self, movie_title: str) -> MovieDetails:
        async with async_playwright() as p:
            
            
            browser = await self._launch_browser(p)
            
            page = await browser.new_page(user_agent=scraping_config.user_agent)
            
           
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "media", "font", "stylesheet"] # optimize loading by blocking unnecessary resources
                else route.continue_()
            )
            
           
            # Getting the movie URL and navigating to it
            try:
                kinorium_url = await self._search_movie_url(page, movie_title)
                logger.info(f"Found movie URL: {kinorium_url}")
                await page.goto(kinorium_url, wait_until="domcontentloaded")
            except ValueError as e:
                await browser.close()
                raise e

            
            # --- Extracting movie details ---
            # wait for main title to load
            try:
                await page.wait_for_selector("h1.film-page__title-text", timeout=15000)
            except:
                await browser.close()
                raise ValueError("Page loaded but title element not found")

            # Title 
            title = await page.text_content("h1.film-page__title-text")

            
            # Original Title
            original_title = None
            try:
                orig_title_loc = page.locator("span[itemprop='alternativeHeadline']")
                if await orig_title_loc.count() > 0:
                    original_title = await orig_title_loc.text_content()
            except: pass 

            # Year
            year = None
            try:
                year_loc = page.locator("span.film-page__date a")
                if await year_loc.count() > 0:
                    year_text = await year_loc.text_content()
                    if year_text and year_text.isdigit():
                        year = int(year_text)
            except: pass

            # Rating
            rating = None
            try:
                rating_loc = page.locator("div.film-page__title-rating")
                if await rating_loc.count() > 0:
                    rating_text = await rating_loc.text_content()
                    if rating_text:
                        clean_rating = rating_text.strip().replace(".", "")
                        if clean_rating.isdigit():
                            rating = float(rating_text.strip())
            except Exception as e:
                logger.debug(f"Failed to parse rating: {str(e)}")
                pass

            # Description
            description = None
            try:
                desc_loc = page.locator("section.film-page__text[itemprop='description']")
                if await desc_loc.count() > 0:
                    description = await desc_loc.text_content()
            except: pass

            genres = await page.eval_on_selector_all(
                "li[itemprop='genre'] a", "els => els.map(e => e.textContent.trim())"
            )

            countries = await page.eval_on_selector_all(
                "a[itemprop='countryOfOrigin']", "els => els.map(e => e.textContent.trim())"
            )
            
            production_studios = await page.eval_on_selector_all(
                "span.film-page__company a nobr", "els => els.map(e => e.textContent.trim())"
            )

            actors = await page.eval_on_selector_all(
                "div.film-page__cast-item[itemprop='actor'] span[itemprop='name']",
                "els => els.slice(0, 10).map(e => e.textContent.trim())"
            )

            # Duration 
            duration_minutes = None
            rows = page.locator("tr")
            count = await rows.count()
            if count > 0:
                for i in range(count):
                    try:
                        row = rows.nth(i)
                        legend_loc = row.locator("td.legend")
                        legend = await legend_loc.text_content() if await legend_loc.count() > 0 else ""
                        
                        if legend and "тривалість" in legend.lower():
                            data_loc = row.locator("td.data")
                            duration_text = await data_loc.text_content() if await data_loc.count() > 0 else ""
                            
                            if duration_text:
                                match = re.search(r"(\d+)\s*год\s*(\d+)\s*хв|(\d+)\s*хв", duration_text)
                                if match:
                                    if match.group(3): 
                                        duration_minutes = int(match.group(3))
                                    else: 
                                        h = int(match.group(1) or 0)
                                        m = int(match.group(2) or 0)
                                        duration_minutes = h * 60 + m
                            break
                    except: continue

            await browser.close()

            return MovieDetails(
                title=title.strip() if title else "Unknown",
                original_title=original_title.strip() if original_title else None,
                year=year,
                rating=rating,
                genres=genres,
                countries=countries,
                duration_minutes=duration_minutes,
                description=description.strip() if description else None,
                production_studios=production_studios,
                actors=actors,
                kinorium_url=kinorium_url, # type: ignore
            )