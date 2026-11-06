import logging
import shutil
from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
DEFAULT_DATA_DIR = ROOT_DIR / "data" / "raw" / "YTL_TrackA_Udyam_Digital_Data"
log = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(ROOT_DIR / ".env", BACKEND_DIR / ".env"), extra="ignore")

    app_today: date = date(2026, 7, 15)
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5-5"
    doc_encryption_key: str = ""
    backoffice_pin: str = "2026"
    frontend_origin: str = "http://localhost:5173"
    tesseract_cmd: str = ""
    twilio_auth_token: str = ""
    data_dir: str = ""
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'app.db').as_posix()}"
    storage_dir: str = str(BACKEND_DIR / "storage")

    @property
    def ai_mode(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def data_path(self) -> Path:
        if self.data_dir:
            return Path(self.data_dir)
        if (DEFAULT_DATA_DIR / "product_catalogue.csv").exists():
            return DEFAULT_DATA_DIR
        found = next(ROOT_DIR.rglob("product_catalogue.csv"), None)
        if not found:
            raise FileNotFoundError("product_catalogue.csv not found in workspace")
        log.warning("Data folder not at default path, using %s", found.parent)
        return found.parent

    @property
    def kyc_docs_path(self) -> Path:
        return self.data_path / "kyc_documents"

    @property
    def tesseract_path(self) -> str | None:
        candidates = [self.tesseract_cmd, shutil.which("tesseract"),
                      r"C:\Program Files\Tesseract-OCR\tesseract.exe", "/usr/bin/tesseract", "/opt/homebrew/bin/tesseract"]
        return next((c for c in candidates if c and Path(c).exists()), None)


@lru_cache
def get_settings() -> Settings:
    return Settings()
