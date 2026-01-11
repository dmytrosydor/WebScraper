from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapingConfig:
    base_url: str = "https://ua.kinorium.com"

    request_timeout: float = 20.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


scraping_config = ScrapingConfig()


GENRES_MAP = {
    "комедія": 13,
    "аніме": 1,
}

KINORIUM_ENDPOINTS = {
    "film_list": "/handlers/filmList/",
}
