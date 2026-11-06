from dataclasses import dataclass, field
from functools import cached_property, lru_cache

import cv2
import numpy as np
import pytesseract

from ...config import get_settings

BLUR_THRESHOLD = 466.0
LABEL_HINTS = ("GSTIN", "Legal name", "Trade name", "Udyam", "Enterprise", "Consumer", "Billed", "Designation",
               "Valid till")


@dataclass
class Line:
    words: list[tuple[int, str]]

    @property
    def text(self) -> str:
        return " ".join(w for _, w in self.words)

    def split(self, x: int) -> tuple[str, str]:
        return (" ".join(w for left, w in self.words if left < x), " ".join(w for left, w in self.words if left >= x))


@dataclass
class OcrResult:
    lines: list[Line]
    width: int
    blur_score: float
    angle: float
    image: np.ndarray = field(repr=False)

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)

    @cached_property
    def alternative_texts(self) -> list[str]:
        """Extra passes (adaptive threshold, Otsu, psm 4) used only to re-read identifiers."""
        adaptive = cv2.adaptiveThreshold(self.image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 20)
        otsu = cv2.threshold(self.image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        return [_string(adaptive, 6), _string(otsu, 6), _string(self.image, 4)]


@lru_cache
def ocr_available() -> bool:
    path = get_settings().tesseract_path
    if not path:
        return False
    pytesseract.pytesseract.tesseract_cmd = path
    try:
        pytesseract.get_tesseract_version()
        return True
    except (pytesseract.TesseractNotFoundError, OSError):
        return False


def decode(data: bytes) -> np.ndarray:
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Not a readable image")
    return img


def remove_watermark(img: np.ndarray) -> np.ndarray:
    """Whiten coloured (pink/red) pixels; black text has near-zero saturation."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    out = img.copy()
    out[(hsv[..., 1] > 25) & (hsv[..., 2] > 120)] = 255
    return cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)


def blur_score(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def rotate(img: np.ndarray, angle: float, border: int = 255) -> np.ndarray:
    h, w = img.shape
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_CUBIC, borderValue=border)


def estimate_skew(gray: np.ndarray) -> float:
    """Projection profile: the rotation whose row sums vary most puts text lines horizontal."""
    small = cv2.resize(gray, None, fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA)
    binary = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    def score(a: float) -> float:
        return float(np.var(rotate(binary, a, border=0).sum(axis=1, dtype=np.float64)))

    coarse = max(np.arange(-12, 12.5, 1.0), key=score)
    return float(max(np.arange(coarse - 1, coarse + 1.05, 0.1), key=score))


def upscale(gray: np.ndarray) -> np.ndarray:
    return cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)


def _string(img: np.ndarray, psm: int) -> str:
    return pytesseract.image_to_string(img, lang="eng", config=f"--psm {psm}")


def _lines(img: np.ndarray, psm: int) -> list[Line]:
    d = pytesseract.image_to_data(img, lang="eng", config=f"--psm {psm}", output_type=pytesseract.Output.DICT)
    grouped: dict[tuple, list] = {}
    for i, word in enumerate(d["text"]):
        if word.strip() and float(d["conf"][i]) > 0:
            grouped.setdefault((d["block_num"][i], d["par_num"][i], d["line_num"][i]), []).append(
                (d["left"][i], d["top"][i], word.strip()))
    rows = sorted(grouped.values(), key=lambda ws: min(t for _, t, _ in ws))
    return [Line(sorted((left, w) for left, _, w in ws)) for ws in rows]


def _label_hits(lines: list[Line]) -> int:
    text = "\n".join(line.text for line in lines).lower()
    return sum(h.lower() in text for h in LABEL_HINTS)


def run_ocr(data: bytes) -> OcrResult:
    if not ocr_available():
        raise RuntimeError("Tesseract is not installed")
    img = decode(data)
    score = blur_score(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    gray = remove_watermark(img)
    angle = estimate_skew(gray)
    if abs(angle) <= 1:
        angle = 0.0
    image = upscale(rotate(gray, angle) if angle else gray)
    lines = _lines(image, 6)
    if _label_hits(lines) < 2:
        candidates = [(0.0, image, _lines(image, 4))]
        for a in range(-12, 13, 2):
            rotated = upscale(rotate(gray, a))
            candidates.append((float(a), rotated, _lines(rotated, 6)))
        angle, image, lines = max(candidates, key=lambda c: _label_hits(c[2]))
    return OcrResult(lines=lines, width=image.shape[1], blur_score=round(score, 1), angle=round(angle, 1), image=image)
