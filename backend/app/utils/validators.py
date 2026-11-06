import re

C = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
UDYAM_RE = re.compile(r"^UDYAM-[A-Z]{2}-\d{2}-\d{7}$")

TO_DIGIT = {"O": "0", "I": "1", "S": "5", "B": "8"}
TO_LETTER = {"0": "O", "1": "I", "5": "S", "8": "B"}
DIGIT_POS = {0, 1, 7, 8, 9, 10}
LETTER_POS = {2, 3, 4, 5, 6, 11}


def gstin_checksum_ok(g: str) -> bool:
    total = 0
    for i, ch in enumerate(g[:14]):
        v = C.index(ch) * (2 if i % 2 else 1)
        total += v // 36 + v % 36
    return C[(36 - total % 36) % 36] == g[14]


def gstin_valid(g: str) -> bool:
    g = g.strip().upper()
    return bool(GSTIN_RE.match(g)) and gstin_checksum_ok(g)


def clean_identifier(raw: str) -> str:
    return re.sub(r"[\s\-_.]", "", raw or "").upper()


def normalise_gstin(raw: str) -> str:
    """Positional OCR repair (O/0, I/1, S/5, B/8). Never touches the checksum character."""
    g = clean_identifier(raw)
    if len(g) != 15:
        return g
    chars = list(g)
    for i, ch in enumerate(chars):
        if i in DIGIT_POS:
            chars[i] = TO_DIGIT.get(ch, ch)
        elif i in LETTER_POS:
            chars[i] = TO_LETTER.get(ch, ch)
        elif i == 13 and ch == "2":
            chars[i] = "Z"
    return "".join(chars)


def gstin_format_ok(g: str) -> bool:
    return bool(GSTIN_RE.match(g))


def normalise_udyam(raw: str) -> str:
    u = re.sub(r"\s+", "", raw or "").upper()
    m = re.match(r"^UDYAM-?([A-Z0-9]{2})-?([A-Z0-9]{2})-?([A-Z0-9]{7})$", u)
    if not m:
        return u
    state, district, serial = m.groups()
    state = "".join(TO_LETTER.get(c, c) for c in state)
    district, serial = ("".join(TO_DIGIT.get(c, c) for c in part) for part in (district, serial))
    return f"UDYAM-{state}-{district}-{serial}"


def udyam_valid(u: str) -> bool:
    return bool(UDYAM_RE.match(u))
