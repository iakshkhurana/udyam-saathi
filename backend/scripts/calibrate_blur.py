"""Print the Laplacian-variance blur score of every specimen image and suggest BLUR_THRESHOLD."""
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.services.kyc.ocr import blur_score


def scores() -> list[tuple[str, float]]:
    files = sorted(get_settings().kyc_docs_path.glob("*.png"))
    return sorted(((f.name, blur_score(cv2.imread(str(f), cv2.IMREAD_GRAYSCALE))) for f in files), key=lambda t: t[1])


def suggest(rows: list[tuple[str, float]]) -> float:
    return round((rows[0][1] + rows[1][1]) / 2, 1)


if __name__ == "__main__":
    rows = scores()
    for name, s in rows:
        print(f"{s:10.1f}  {name}")
    print(f"\nLowest: {rows[0][0]}; suggested BLUR_THRESHOLD = {suggest(rows)}")
