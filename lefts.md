# lefts.md – Status of the Udyam Saathi build
_Last updated: 2026-11-06 · Current phase: 2_

## ✅ Done
- Phase 0: repo structure, `.gitignore`, `.env.example`, `lefts.md`; data moved to `data/raw/YTL_TrackA_Udyam_Digital_Data/`
- Phase 1: `backend/app/{config,db,models,schemas}.py`, `scripts/load_data.py` (→ `app/services/data_loader.py`, API self-loads an empty DB), `utils/validators.py` (positional OCR normalisation, never repairs checksum), `utils/masking.py` (+ masking log formatter), `/api/gstin`, `/api/udyam`, `/api/products`, rate-limited lookups; `tests/test_validators.py` 12/12 pass
- Phase 2: `services/rules_engine.py` (eligibility, segment bases, needs→products, dependencies, segment default bundles, quantities, pricing, savings line, EN/HI "why" text, final validation that raises), `services/audit.py` + `scripts/audit_sold_bundles.py` → `docs/rules_audit.md` (+ `.json`); `tests/test_rules_engine.py` incl. 500-profile property test – all pass

## ⏳ Left for humans (do these yourself)
- [ ] (filled in as the build progresses)

## ⚠️ Assumptions made
- Data was at `./YTL_TrackA_Udyam_Digital_Data/`; moved (unchanged) to the spec path `data/raw/YTL_TrackA_Udyam_Digital_Data/`.
- Repo root is `K:\airtel` (spec calls it `udyam-saathi/`). Default branch `main`.
- `smb_leads.csv` has a literal `None` value in `current_internet` (meaning no internet); it is read as the string "None", not NULL.
- GSTIN positional normalisation maps only O↔0, I↔1, S↔5, B↔8 (plus `2→Z` at index 13); the checksum character (index 14) and index 12 are never altered.
- Tooling found: Python 3.14.5 (spec says 3.11+), Node 24.16, npm 11.13, Docker 29.5, Tesseract 5.4.0 at `C:\Program Files\Tesseract-OCR` (not on PATH → auto-detected via `TESSERACT_CMD` / default install path).

- Pricing: unit price = `price_min_inr_per_month` ("from" price). Choosing a price between min and max (e.g. by tier or volume) is a business decision left open.
- Setup fee is charged per unit (`one_time_setup_inr × qty`).
- Contract = max(12, longest `min_contract_months`), so even a mobile-only plan shows 12 months (per spec).
- Bundle items: base connection + needs (or segment defaults) are "Recommended" and enabled; up to 4 eligible segment add-ons (e.g. CCTV, guest Wi-Fi, failover) are returned as optional "Add-ons", switched off, so the owner can toggle them on.
- When a requested connection is ineligible, the engine offers the next eligible one down a speed ladder (1G → 300 → 100; leased line 20 → 1G → 300 → 100).
- "Give me the cheapest" = cheapest eligible connection by monthly price (Biz 5G AirFiber, ₹899) + 1 mobile line.
- A product blocked *only* by GSTIN goes to `unlocks_with_gstin` instead of `excluded` (spec: either/or); a requested connection blocked by GSTIN is listed in both.
- P13 toll-free and P08 manager line are offered as optional add-ons (off) for prof/multi when the matching need is picked.

## ❌ Known issues / failing tests
- none yet

## 📊 Key results (for the PPT)
- Rules audit: 48 / 368 sold bundles (13%) break catalogue rules – city tier 24, GSTIN 12, dependency 9, employees 8 (exact match with the expected counts)

## ▶️ How to run (short)
- pending

## 🔜 Suggested next steps (finale)
- pending
