# lefts.md – Status of the Udyam Saathi build
_Last updated: 2026-11-06 · Current phase: 3_

## ✅ Done
- Phase 0: repo structure, `.gitignore`, `.env.example`, `lefts.md`; data moved to `data/raw/YTL_TrackA_Udyam_Digital_Data/`
- Phase 1: `backend/app/{config,db,models,schemas}.py`, `scripts/load_data.py` (→ `app/services/data_loader.py`, API self-loads an empty DB), `utils/validators.py` (positional OCR normalisation, never repairs checksum), `utils/masking.py` (+ masking log formatter), `/api/gstin`, `/api/udyam`, `/api/products`, rate-limited lookups; `tests/test_validators.py` 12/12 pass
- Phase 2: `services/rules_engine.py` (eligibility, segment bases, needs→products, dependencies, segment default bundles, quantities, pricing, savings line, EN/HI "why" text, final validation that raises), `services/audit.py` + `scripts/audit_sold_bundles.py` → `docs/rules_audit.md` (+ `.json`); `tests/test_rules_engine.py` incl. 500-profile property test – all pass
- Phase 3: `services/advisor.py` (slot state machine, free-text parsing for numbers/cities/business types/needs/products/GSTIN, EN/HI guided mode with chips, clarifying questions, refusal of "ignore the rules", callback → back-office lead, LLM mode with tools `lookup_city_tier`/`map_business_type`/`lookup_gstin`/`recommend_bundle`/`save_profile_slot`/`request_callback`, automatic fallback to guided mode if the LLM call fails), `services/llm_client.py` (provider-agnostic `LLMClient`, Anthropic implementation), `services/propensity.py`, `routers/advisor.py`; `tests/test_advisor_scenarios.py` 15/15 → `docs/advisor_test_results.md`

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

- Employee chips use the lower bound of each band (1–2→1, 3–4→3, 5–9→5, 10–24→10, 25+→25), aligned with catalogue thresholds so eligibility is never overstated; quantities are editable in the quote.
- Spend chips map to representative values (under ₹1,000→800, ₹1,000–3,000→2,000, ₹3,000–10,000→6,000, above ₹10,000→12,000).
- Guided mode speaks EN/HI only; other languages get an English reply with a note (AI mode replies in all 10 languages). Hinglish text switches guided mode to Hindi.
- In LLM mode the backend overrides `gstin_status` and `city_tier` with its own lookups before calling the rules engine, so the model cannot fake eligibility.
- LLM calls use `claude-sonnet-5-5` (spec default, `LLM_MODEL` overrides) with `effort: low` and the server-side refusal fallback (`fallbacks: "default"`, beta `server-side-fallback-2026-07-01`).
- Advisor leads are scored with `lead_source = "Website form"`, `has_udyam = N`, turnover `< 40 lakh` (unknown in chat).

## ❌ Known issues / failing tests
- none yet

## 📊 Key results (for the PPT)
- Rules audit: 48 / 368 sold bundles (13%) break catalogue rules – city tier 24, GSTIN 12, dependency 9, employees 8 (exact match with the expected counts)
- Advisor tests: 15/15 pass in guided mode (scenario 6 asserts the English fallback note; the Tamil reply test runs only with `TEST_ANTHROPIC_API_KEY`)

## ▶️ How to run (short)
- pending

## 🔜 Suggested next steps (finale)
- pending
