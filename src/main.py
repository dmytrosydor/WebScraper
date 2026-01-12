import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from src.api import main_router 

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("__name__")

app = FastAPI()
app.include_router(main_router,prefix="/api")



@app.on_event("startup")
async def on_startup():
    logger.info("Application started")