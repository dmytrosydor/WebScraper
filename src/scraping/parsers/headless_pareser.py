import logging
from playwright.async_api import async_playwright
import re

import urllib

from src.scraping.schemas import MovieDetails
from src.config.scraping import (
    scraping_config,
)


logger = logging.getLogger(__name__)

    


class KinoriumHeadlessParser:
    async def parse(self, movie_title: str) -> MovieDetails:
        async with async_playwright() as p:
            
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"] # a bit optimization
            )
            page = await browser.new_page(
                user_agent=scraping_config.user_agent
            )
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in [ "image", "media", "font", "stylesheet"] # block all unneeded resources
                else route.continue_()
            )
            # Film search 
            encoded_query = urllib.parse.quote(movie_title) # type: ignore
            search_url = f"{scraping_config.base_url}/search/?q={encoded_query}"
            logger.info(f"Searching for movie: {movie_title} using URL: {search_url}")
            
            await page.goto(search_url, timeout=30000)
            results = page.locator("a.search-page__title-link")
            
            if await results.count() == 0:
                await browser.close()
                raise ValueError("Movie not found in search results")

            movie_href = await results.first.get_attribute("href")

            if not movie_href:
                await browser.close()
                raise ValueError("Movie link attribute is empty")

            kinorium_url = (
                scraping_config.base_url + movie_href
                if movie_href.startswith("/")
                else movie_href
            )

            
            await page.goto(kinorium_url, wait_until="domcontentloaded")
            
            # wait for main title to load
            try:
                await page.wait_for_selector("h1.film-page__title-text", timeout=15000)
            except:
                await browser.close()
                raise ValueError("Page loaded but title element not found")

            

            # Title 
            title = await page.text_content("h1.film-page__title-text")

            # Original Title (may be absent)
            original_title = None
            try:
                orig_title_loc = page.locator("span[itemprop='alternativeHeadline']")
                # Чекаємо зовсім трохи (200мс)
                await orig_title_loc.wait_for(state="attached", timeout=200)
                original_title = await orig_title_loc.text_content()
            except:
                pass 

            # Year
            year = None
            try:
                year_loc = page.locator("span.film-page__date a")
                await year_loc.wait_for(state="attached", timeout=200)
                year_text = await year_loc.text_content()
                if year_text and year_text.isdigit():
                    year = int(year_text)
            except:
                pass

            # Rating (may be absent)
            rating = None
            rating_locator = page.locator("div.film-page__title-rating")
            try:
                await rating_locator.wait_for(state="attached", timeout=200)
                rating_text = await rating_locator.text_content()
                rating_text = rating_text.strip() # type: ignore
                if rating_text and rating_text.replace(".", "").isdigit():
                    rating = float(rating_text)
            except:
                pass 

            # Description
            description = None
            try:
                desc_loc = page.locator("section.film-page__text[itemprop='description']")
                await desc_loc.wait_for(state="attached", timeout=200)
                description = await desc_loc.text_content()
            except:
                pass

            genres = await page.eval_on_selector_all(
                "li[itemprop='genre'] a",
                "els => els.map(e => e.textContent.trim())"
            )

            countries = await page.eval_on_selector_all(
                "a[itemprop='countryOfOrigin']",
                "els => els.map(e => e.textContent.trim())"
            )
            
            production_studios = await page.eval_on_selector_all(
                "span.film-page__company a nobr",
                "els => els.map(e => e.textContent.trim())"
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
                        
                        await legend_loc.wait_for(state="attached", timeout=100)
                        legend = await legend_loc.text_content()
                        
                        if legend and "тривалість" in legend.lower():
                            data_loc = row.locator("td.data")
                            await data_loc.wait_for(state="attached", timeout=100)
                            duration_text = await data_loc.text_content()
                            
                            if duration_text:
                                # Regex для "1 год 30 хв" АБО "38 хв"
                                match = re.search(r"(\d+)\s*год\s*(\d+)\s*хв|(\d+)\s*хв", duration_text)
                                if match:
                                    if match.group(3): # Тільки хвилини (наприклад "38 хв")
                                        duration_minutes = int(match.group(3))
                                    else: # Години і хвилини
                                        h = int(match.group(1) or 0)
                                        m = int(match.group(2) or 0)
                                        duration_minutes = h * 60 + m
                            break
                    except:
                        continue

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