import logging
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import re

import urllib

from src.scraping.schemas import MovieShort, MovieDetails
from src.config.scraping import (
    scraping_config,
    GENRES_MAP,
    KINORIUM_ENDPOINTS,
)


logger = logging.getLogger(__name__)

    

class KinoriumParser:
    
    # Method 1
    async def scrape_by_genre(
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


    async def scrape_movie_details(self, movie_title: str) -> MovieDetails:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable=gpu"])
            page = await browser.new_page(
                user_agent=scraping_config.user_agent
            )

            # Search movie
            encoded_query = urllib.parse.quote(movie_title) # for cases like film "1 + 1", without this it will fail to find the movie # type: ignore 
            search_url = f"{scraping_config.base_url}/search/?q={encoded_query}"
            logger.info(f"Searching for movie: {movie_title} using URL: {search_url}")
            await page.goto(search_url, timeout=30000)
            results = page.locator("a.search-page__title-link")
            if await results.count() == 0:
                raise ValueError("Movie not found in search results")

            movie_href = await results.first.get_attribute("href")

            if not movie_href:
                raise ValueError("Movie not found in search results")

            kinorium_url = (
                scraping_config.base_url + movie_href
                if movie_href.startswith("/")
                else movie_href
            )

            await page.goto(kinorium_url, wait_until="networkidle")
            await page.wait_for_selector("h1.film-page__title-text", timeout=30000)

            # Parse fields

            title = await page.text_content("h1.film-page__title-text")

            original_title = await page.text_content(
                "span[itemprop='alternativeHeadline']"
            )

            year_text = await page.text_content(
                "span.film-page__date a"
            )
            year = int(year_text) if year_text and year_text.isdigit() else None

            rating_locator = page.locator("div.film-page__title-rating")
            
            try:
                await rating_locator.wait_for(state="attached", timeout=500) # if json is loading
                is_rating_present = True
            except:
                is_rating_present = False

            if is_rating_present:
                rating_text = await rating_locator.text_content()
                rating_text = rating_text.strip() # type: ignore
                rating = (
                    float(rating_text)
                    if rating_text and rating_text.replace(".", "").isdigit()
                    else None
                )
            else:
                logger.warning(f"Rating block not found for movie: {title}")
                rating = None

            genres = await page.eval_on_selector_all(
                "li[itemprop='genre'] a",
                "els => els.map(e => e.textContent.trim())"
            )

            countries = await page.eval_on_selector_all(
                "a[itemprop='countryOfOrigin']",
                "els => els.map(e => e.textContent.trim())"
            )

            duration_minutes = None
            rows = page.locator("tr")

            for i in range(await rows.count()):
                row = rows.nth(i)
                legend = await row.locator("td.legend").text_content()
                if legend and "тривалість" in legend.lower():
                    duration_text = await row.locator("td.data").text_content()
                    if duration_text:
                        match = re.search(r"(\d+)\s*год\s*(\d+)\s*хв", duration_text)
                        if match:
                            hours = int(match.group(1))
                            minutes = int(match.group(2))
                            duration_minutes = hours * 60 + minutes
                    break
            description = await page.text_content(
                "section.film-page__text[itemprop='description']"
            )

            production_studios = await page.eval_on_selector_all(
                "span.film-page__company a nobr",
                "els => els.map(e => e.textContent.trim())"
            )

            actors = await page.eval_on_selector_all(
                "div.film-page__cast-item[itemprop='actor'] span[itemprop='name']",
                "els => els.slice(0, 10).map(e => e.textContent.trim())"
            )

            poster_url = await page.get_attribute(
                "div.carousel_image-handler img",
                "src"
            )

            await browser.close()

            return MovieDetails(
                title=title.strip(), # type: ignore
                original_title=original_title.strip() if original_title else None,
                year=year,
                rating=rating,
                genres=genres,
                countries=countries,
                duration_minutes=duration_minutes,
                description=description.strip() if description else None,
                production_studios=production_studios,
                actors=actors,
                poster_url=poster_url,
                kinorium_url=kinorium_url, # type: ignore
            )