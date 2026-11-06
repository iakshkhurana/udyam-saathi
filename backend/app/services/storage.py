import logging
import secrets
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import AuditLog, KycDocument, KycSubmission, Order

log = logging.getLogger(__name__)
RETENTION_DAYS = 90


def _dir() -> Path:
    d = Path(get_settings().storage_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


@lru_cache
def _fernet() -> Fernet:
    key = get_settings().doc_encryption_key
    if not key:
        key_file = _dir() / ".dev_key"
        if not key_file.exists():
            key_file.write_bytes(Fernet.generate_key())
            log.warning("DOC_ENCRYPTION_KEY not set – generated a dev key in storage/.dev_key")
        key = key_file.read_text().strip()
    return Fernet(key.encode() if isinstance(key, str) else key)


def save(data: bytes) -> str:
    key = secrets.token_hex(16)
    (_dir() / f"{key}.bin").write_bytes(_fernet().encrypt(data))
    return key


def load(key: str) -> bytes:
    return _fernet().decrypt((_dir() / f"{key}.bin").read_bytes())


def delete(key: str | None) -> None:
    if key:
        (_dir() / f"{key}.bin").unlink(missing_ok=True)


def audit(db: Session, actor: str, action: str, target: str, **detail) -> None:
    db.add(AuditLog(actor=actor, action=action, target=target, detail=detail))
    log.info("audit actor=%s action=%s target=%s", actor, action, target)


def delete_order_documents(db: Session, order_id: str, reason: str) -> int:
    sub = db.scalar(select(KycSubmission).where(KycSubmission.order_id == order_id))
    if not sub:
        return 0
    count = 0
    for doc in sub.documents:
        if doc.storage_key:
            delete(doc.storage_key)
            doc.storage_key = None
            count += 1
        doc.fields = {}
    if count:
        audit(db, "system", "documents_deleted", order_id, reason=reason, count=count)
    return count


def run_retention(db: Session) -> dict:
    today = get_settings().app_today
    orders = db.scalars(select(Order).where(
        (Order.cancelled.is_(True)) | (Order.activated_on <= today - timedelta(days=RETENTION_DAYS)))).all()
    deleted = {o.id: delete_order_documents(db, o.id, "retention") for o in orders}
    return {"orders_checked": len(orders), "documents_deleted": sum(deleted.values()),
            "orders": [k for k, v in deleted.items() if v]}
