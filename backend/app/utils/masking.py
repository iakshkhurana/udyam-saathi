import hashlib
import logging
import re

DOT = "•"
GSTIN_PATTERN = re.compile(r"\b(\d{2})[0-9A-Z]{10}([0-9A-Z]{3})\b")
UDYAM_PATTERN = re.compile(r"\b(UDYAM-[A-Z]{2}-\d{2}-)\s*\d{3}(\d{4})\b")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?([6-9]\d)\d{5}(\d{3})(?!\d)")
SYN_ID_PATTERN = re.compile(r"\bSYN-ID-\d{4}(\d{2})\b")


def mask_gstin(g: str | None) -> str:
    if not g:
        return ""
    return g[:2] + DOT * (len(g) - 5) + g[-3:] if len(g) > 5 else DOT * len(g)


def mask_udyam(u: str | None) -> str:
    if not u:
        return ""
    head, _, serial = u.rpartition("-")
    return f"{head}-{DOT * 3}{serial[-4:]}" if head else DOT * len(u)


def mask_phone(p: str | None) -> str:
    digits = re.sub(r"\D", "", p or "")[-10:]
    return f"{digits[:2]}{DOT * 5}{digits[-3:]}" if len(digits) == 10 else ""


def mask_name(name: str | None) -> str:
    return " ".join(f"{part[0]}." for part in (name or "").split() if part[0].isalpha())


def mask_signatory_id(s: str | None) -> str:
    return SYN_ID_PATTERN.sub(lambda m: f"SYN-ID-{DOT * 4}{m.group(1)}", s or "")


def mask_text(text: str) -> str:
    text = UDYAM_PATTERN.sub(lambda m: f"{m.group(1)}{DOT * 3}{m.group(2)}", text)
    text = GSTIN_PATTERN.sub(lambda m: m.group(1) + DOT * 10 + m.group(2), text)
    text = SYN_ID_PATTERN.sub(lambda m: f"SYN-ID-{DOT * 4}{m.group(1)}", text)
    return PHONE_PATTERN.sub(lambda m: f"{m.group(1)}{DOT * 5}{m.group(2)}", text)


def hash_ip(ip: str | None, salt: str = "udyam-saathi") -> str:
    return hashlib.sha256(f"{salt}:{ip or ''}".encode()).hexdigest()


class MaskingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return mask_text(super().format(record))


def configure_logging(log_file: str | None = None) -> None:
    formatter = MaskingFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    root = logging.getLogger()
    root.handlers.clear()
    for h in handlers:
        h.setFormatter(formatter)
        root.addHandler(h)
    root.setLevel(logging.INFO)
    for name in ("httpx", "httpx2"):
        logging.getLogger(name).setLevel(logging.WARNING)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
