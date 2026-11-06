# Architecture – Udyam Saathi

![Architecture](architecture.png)

```mermaid
flowchart TB
    subgraph CH["Channels"]
        direction LR
        WEB["Web app<br/>React · mobile-first · EN/HI · voice"]
        WA["WhatsApp<br/>Twilio webhook"]
        PC["Partner co-pilot<br/>same web app"]
    end

    subgraph API["API gateway – FastAPI /api"]
        direction LR
        ADV["Advisor<br/>state machine · LLM tools"] <--> RULES["Rules engine<br/>source of truth"]
        RULES --- CAT[("Catalogue<br/>25 products")]
        QUOTE["Quote service<br/>toggles · re-validation"]
        CONS["Consent service<br/>DPDP notice"]
        KYC["KYC service<br/>OCR · parsers · C01–C18"]
        ORD["Order & tracker<br/>stages · ETA · delay credit"]
        BO["Back office<br/>propensity · review queue · audit"]
        ADV --> QUOTE --> ORD
        ORD --> CONS --> KYC --> ORD
    end

    subgraph EXT["Verification (mocked) + optional LLM"]
        direction LR
        GST["GSTIN API"]
        UDY["Udyam API"]
        DL["DigiLocker mock"]
        ES["e-Sign mock"]
        LLM["Claude<br/>chat + vision cross-check"]
    end

    subgraph DATA["Data layer"]
        direction LR
        DB[("SQLite → Postgres")]
        DOCS[("Encrypted doc store")]
        CLOG[("Consent log")]
        ALOG[("Audit log")]
        RET["Retention job<br/>90 days"]
    end

    NOTIF["Notifications<br/>WhatsApp / SMS"]

    CH --> API
    KYC --> EXT
    ADV -.-> LLM
    ORD --> NOTIF
    ADV --> BO
    KYC --> BO
    API --> DATA
    RET --> DOCS
```

## How a request flows

1. **Advisor** – the owner chats (web, voice or WhatsApp). In guided mode a deterministic state machine asks one question at a time with quick-reply chips; in AI mode Claude runs the conversation but can only get products through the `recommend_bundle` tool. Either way, every product comes from the **rules engine**, which re-checks city tier, staff, sites, GSTIN status and dependencies and raises if anything ineligible slips through.
2. **Quote** – one monthly price (excl. GST), setup and contract shown separately. Toggling items re-runs the rules engine; switching off the base connection also switches off what depends on it.
3. **Consent** – a DPDP notice (what, why, who, how long, rights) is recorded per order before any upload; KYC endpoints return 403 without it.
4. **Smart KYC** – documents are encrypted at rest. OCR (watermark removal, blur score, deskew, Tesseract) → field parsers → 18 checks against the GSTIN/Udyam registries, the lead record and today's date. Pass → `KYC_VERIFIED`; warnings → human review queue; failures → plain fix-it messages.
5. **Tracker** – stage dates from install lead times (Sundays skipped), proactive WhatsApp-style updates, automatic credit on delay, NPS + referral after activation.
6. **Back office** – unclosed advisor leads and dropped historical leads ranked by a propensity model, the KYC review queue, and the audit of 48 mis-sold bundles.

## Components

| Layer | Code |
|---|---|
| API | `backend/app/main.py`, `backend/app/routers/*` |
| Advisor + LLM | `services/advisor.py`, `services/llm_client.py` |
| Rules engine | `services/rules_engine.py`, `services/catalogue.py` |
| Quote / orders | `services/quote.py`, `services/tracker.py` |
| KYC | `services/kyc/{ocr,parsers,checks,service}.py` |
| Privacy | `utils/masking.py`, `services/storage.py`, `routers/privacy.py`, `routers/consent.py` |
| Back office | `routers/backoffice.py`, `services/propensity.py`, `services/audit.py` |
| Frontend | `frontend/` (React + Vite + TypeScript + Tailwind) |
