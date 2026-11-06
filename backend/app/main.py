from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import inspect, select

from .config import BACKEND_DIR, get_settings
from .db import Base, SessionLocal, engine
from .limiter import limiter
from .models import Product
from .routers import registry
from .services.data_loader import load
from .utils.masking import configure_logging

settings = get_settings()
(BACKEND_DIR / "logs").mkdir(exist_ok=True)
configure_logging(str(BACKEND_DIR / "logs" / "app.log"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    if "products" not in inspect(engine).get_table_names():
        load()
    else:
        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            if db.scalar(select(Product).limit(1)) is None:
                load()
    yield


app = FastAPI(title="Udyam Saathi API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.frontend_origin.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (registry,):
    app.include_router(r.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "AI" if settings.ai_mode else "Guided",
            "ocr_available": settings.tesseract_path is not None, "today": settings.app_today.isoformat()}
