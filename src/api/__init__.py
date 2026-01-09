from fastapi import APIRouter

from src.api.health import router as health_router
from src.api.scrape import router as scrape_router

main_router = APIRouter()

main_router.include_router(health_router)
main_router.include_router(scrape_router)