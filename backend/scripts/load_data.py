"""Rebuild backend/app.db from the case CSVs (drops and recreates every table)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.data_loader import load

if __name__ == "__main__":
    print(load())
