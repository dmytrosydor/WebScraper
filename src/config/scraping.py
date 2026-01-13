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

# --- For http parser ---

GENRES_MAP = {
    "аніме": 1,
    "біографія": 2,
    "бойовик": 3,
    "вестерн": 4,
    "військовий": 5,
    "детектив": 6,
    "документальний": 9,
    "драма": 10,
    "жахи": 11,
    "історія": 12,
    "комедія": 13,
    "концерт": 14,
    "короткометражка": 15,
    "кримінал": 16,
    "мелодрама": 17,
    "містика": 18,
    "музика": 19,
    "мультфільм": 20,
    "мюзикл": 21,
    "пригоди": 22,
    "сімейний": 24,
    "спорт": 25,
    "трилер": 27,
    "фантастика": 29,
    "фентезі": 31,
}

KINORIUM_ENDPOINTS = {
    "film_list": "/handlers/filmList/",
}
