# lefts.md – Status of the Udyam Saathi build
_Last updated: 2026-11-06 23:59 · Current phase: 11 (complete)_

## ✅ Done
- Phase 0: repo structure, `.gitignore`, `.env.example`, `lefts.md`; data moved to `data/raw/YTL_TrackA_Udyam_Digital_Data/`
- Phase 1: `backend/app/{config,db,models,schemas}.py`, `scripts/load_data.py` (→ `app/services/data_loader.py`, API self-loads an empty DB), `utils/validators.py` (positional OCR normalisation, never repairs checksum), `utils/masking.py` (+ masking log formatter), `/api/gstin`, `/api/udyam`, `/api/products`, rate-limited lookups; `tests/test_validators.py` 12/12 pass
- Phase 2: `services/rules_engine.py` (eligibility, segment bases, needs→products, dependencies, segment default bundles, quantities, pricing, savings line, EN/HI "why" text, final validation that raises), `services/audit.py` + `scripts/audit_sold_bundles.py` → `docs/rules_audit.md` (+ `.json`); `tests/test_rules_engine.py` incl. 500-profile property test – all pass
- Phase 3: `services/advisor.py` (slot state machine, free-text parsing for numbers/cities/business types/needs/products/GSTIN, EN/HI guided mode with chips, clarifying questions, refusal of "ignore the rules", callback → back-office lead, LLM mode with tools `lookup_city_tier`/`map_business_type`/`lookup_gstin`/`recommend_bundle`/`save_profile_slot`/`request_callback`, automatic fallback to guided mode if the LLM call fails), `services/llm_client.py` (provider-agnostic `LLMClient`, Anthropic implementation), `services/propensity.py`, `routers/advisor.py`; `tests/test_advisor_scenarios.py` 15/15 → `docs/advisor_test_results.md`
- Phase 4: `services/quote.py` (quote from session/profile, toggles + quantities re-validated by the rules engine, base-off removes dependents with a warning, WhatsApp share text/link), `routers/quote.py` (`POST/GET/PATCH /quotes`, `/accept` → order), `routers/consent.py` (DPDP consent record: purposes, notice version, language, hashed IP; `require_consent` gate for KYC), `services/storage.py` (Fernet-encrypted document store, audit log, retention job), `routers/privacy.py`, `services/tracker.py` + `routers/orders.py` (order creation and stage events)
- Phase 5: Smart KYC – `services/kyc/ocr.py` (saturation-based watermark removal, Laplacian blur score, projection-profile deskew + OCR-label fallback −12°…+12°, Tesseract psm 6 with word positions, extra adaptive/Otsu/psm-4 passes for identifiers), `parsers.py` (doc-type detection, column-aware label/value parsing, wrapped-address joining, signatory stacked layout), `checks.py` (C01–C18), `service.py` (encrypted store, evaluation, verify → order status, sample loader), `routers/kyc.py` (all endpoints consent-gated, 403 without consent), `scripts/calibrate_blur.py`, `scripts/run_kyc_samples.py` → `docs/kyc_results.md`; `tests/test_kyc_samples.py` 15/15, `tests/test_api.py` 12/12
- Phase 6: `services/tracker.py` – stages QUOTE_ACCEPTED → CONSENT_GIVEN → KYC_VERIFIED/KYC_REVIEW → INSTALL_SCHEDULED → INSTALLED → ACTIVATED (+ DELAYED, CANCELLED), install date = KYC date + max install days skipping Sundays, activation +1 day, EN/HI WhatsApp-style notifications for every event, fictional technician card, proactive delay (reason + new date + apology + automatic ₹100 credit), NPS after activation, referral → back-office lead; demo endpoints `/orders/{id}/advance` and `/delay`
- Phase 7 (built by the parallel session `airtel-50`, commit 584f0df): `frontend/` – React 18 + Vite 5 + TS + Tailwind 3 + Framer Motion, react-router, react-i18next (EN/HI on every screen; advisor chat in 10 languages). Screens: Landing (scroll-driven tilted hero window, count-up stats, step progress line), Advisor (chips incl. multi-select needs, Web Speech mic, typing indicator, AI/Guided badge, bundle card, abandon beacon), Quote (animated total, toggles/steppers re-validated by PATCH, warnings, WhatsApp share, print-to-PDF), Consent (DPDP notice), Smart KYC (GSTIN/Udyam lookup card, 4 upload tiles with per-check fix-it text, K01–K12 sample loader, DigiLocker mock, OTP sheet), Tracker (15 s auto-refresh, delay banner + credit, technician card, WhatsApp-style updates, NPS + referral, `?demo=1` controls, copy link), Privacy centre, Back office (dark theme, PIN, 4 tabs). Mobile-first 430px app frame; landing and back office are full-width responsive.
- Phase 8: `routers/backoffice.py` (PIN via `X-Backoffice-Pin`; advisor leads not closed incl. abandoned >30 min and referrals, historical dropped leads with propensity score + recommended action and filters, KYC review queue with approve/reject, audited full-ID reviewer view, rules audit), `scripts/train_propensity.py` (ROC-AUC 0.68, model in `backend/models/propensity.joblib`, scores stored on leads), `scripts/analyze_leads.py` → `docs/insights.md` + `docs/charts/*.png` (all spec figures reproduced exactly); back-office tests added – full suite 64 passed, 1 skipped
- Phase 9: `routers/whatsapp.py` – Twilio-format webhook `POST /api/webhooks/whatsapp` (form `From`/`Body`), same advisor engine, numbered options instead of chips, "See quote" replies with the quote link, deterministic session per sender (hashed number, never stored raw), optional `X-Twilio-Signature` validation when `TWILIO_AUTH_TOKEN` is set, TwiML reply; `tests/test_whatsapp.py` (fake Twilio payloads) 2/2. Voice input (Web Speech API, hi-IN/en-IN/ta-IN…) is in the advisor screen (frontend session).
- Phase 10: `docs/architecture.md` (Mermaid) + `docs/architecture.png` (rendered with `@mermaid-js/mermaid-cli` using the installed Chrome), `docs/privacy_note.md` (1-page DPDP note), `docs/demo_script.md` (3-minute, step by step), `README.md`, `e2e/` (Playwright: `smoke.spec.ts` full guided journey + consent gate + EN/HI toggle on all 8 screens; `screenshots.spec.ts` → `docs/screenshots/01_landing … 10_backoffice.png`, 390×844 @2x)
- Phase 11: `backend/Dockerfile` (python:3.11-slim + tesseract-ocr, loads data on start), `.dockerignore`, `docker-compose.yml` (backend + frontend via node:20-alpine `vite preview`), `render.yaml` (Render blueprint), `frontend/vercel.json` (frontend session). Final from-scratch run: fresh data load ✓, backend 66 passed / 1 skipped, Playwright 4/4 passed.

## ⏳ Left for humans (do these yourself)
- [ ] **Enable AI mode** (optional – the demo works without it). Why: Claude runs the advisor in all 10 languages and cross-checks OCR. Steps: get a key at console.anthropic.com → copy `.env.example` to `.env` in the repo root → set `ANTHROPIC_API_KEY=sk-ant-…` → restart the backend → `/api/health` shows `"mode": "AI"` and the chat shows the "AI mode" badge. Then run `TEST_ANTHROPIC_API_KEY=<key> python -m pytest tests/test_advisor_scenarios.py` for the Tamil test (scenario 6) and try a few judge-style prompts by hand.
- [ ] **Tesseract on other machines.** Why: Smart KYC reads documents with it (installed here at `C:\Program Files\Tesseract-OCR`). Steps: Ubuntu `sudo apt install tesseract-ocr` · macOS `brew install tesseract` · Windows UB Mannheim installer (default path is auto-detected; otherwise set `TESSERACT_CMD`). The Docker image already includes it.
- [ ] **Set a real encryption key and PIN.** Why: without `DOC_ENCRYPTION_KEY` a dev key is generated in `backend/storage/.dev_key`. Steps: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` → put it in `.env` / Render env; change `BACKOFFICE_PIN` from `2026`.
- [ ] **Deploy the backend on Render.** Steps: push the repo to GitHub → render.com → New → Blueprint → pick the repo (`render.yaml`) → fill `FRONTEND_ORIGIN` with the Vercel URL (required – otherwise CORS blocks the deployed frontend), `DOC_ENCRYPTION_KEY`, `BACKOFFICE_PIN`, optional `ANTHROPIC_API_KEY` → deploy → open `https://<service>.onrender.com/api/health`. Free instances sleep: open the URL a minute before the demo.
- [ ] **Deploy the frontend on Vercel.** Steps: vercel.com → Add New Project → import the repo → Root Directory `frontend` (Vite settings come from `vercel.json`) → Settings → Environment Variables: `VITE_API_URL=https://<service>.onrender.com` (no trailing slash, no `/api`) → Deploy → put the Vercel URL into Render's `FRONTEND_ORIGIN` and redeploy the backend.
- [ ] **Docker check.** Why: the Docker daemon was not running here, so `docker compose up --build` was not executed. Steps: start Docker Desktop → `docker compose up --build` in the repo root → open http://localhost:5173.
- [ ] **Twilio WhatsApp sandbox.** Steps: twilio.com → Messaging → Try it out → WhatsApp sandbox → join from your phone → "When a message comes in" = `https://<service>.onrender.com/api/webhooks/whatsapp` (POST) → set `TWILIO_AUTH_TOKEN` in Render so signatures are verified → send "hi" to the sandbox number. Quote links use the first `FRONTEND_ORIGIN`.
- [ ] **Record the 3-minute backup demo video** following `docs/demo_script.md` (mobile view 390×844; each sample applicant takes ~5–10 s of OCR).
- [ ] **Review `docs/kyc_results.md` against the judges' answer key** when released; update `EXPECTED` in `backend/app/services/kyc/service.py` if it differs.
- [ ] **Rebrand** name/colours if the team wants ("Udyam Saathi by Accel Business" is used in the UI, README and docs).
- [ ] **Hand to Member B:** `docs/screenshots/*`, `docs/architecture.png`, `docs/kyc_results.md`, `docs/insights.md`, `docs/charts/*`, `docs/privacy_note.md`, `docs/demo_script.md`, plus the demo link + a QR code (create it after deploying).
- [ ] **Push to a remote.** No git remote is configured; create one (GitHub) and `git push -u origin main`.

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

- Payment is mocked: "Pay first month later at activation" – no payment gateway.
- Withdrawing KYC consent before activation cancels the order and deletes documents; after activation it only deletes documents (the service keeps running).
- The quote is a "print-to-PDF" view (browser print) rather than a server-generated PDF.

- OCR preprocessing: the pink "SYNTHETIC SPECIMEN" watermark is removed by colour saturation before OCR, and the image is upscaled 1.5× for every document (spec: only if width < 1,200 px) – this read more accurately on the specimens. Adaptive threshold (spec step 4) is used as a secondary pass; the primary pass is the cleaned grayscale, which produced fewer digit errors (e.g. "2020-9210").
- Identifiers are re-read from up to 3 extra OCR passes only when the primary read is missing or fails validation; a pass is accepted only if it is checksum-valid as read. Characters are never changed to force a checksum (K06/K10 read identically invalid in every pass).
- `BLUR_THRESHOLD = 466` (midpoint of K04_gst 1.0 and next-lowest K07_udyam 930.7).
- C04 "closest registry GSTIN" uses edit distance ≤ 1 after collapsing OCR-ambiguous pairs (O≡0, I≡1); for K06 the closest is `08YKZXS5189L1ZO` (digit 5 changed to 8 = tampered), for K10 `27QHJXK0658U1ZL` (J→I). Reviewer evidence only; never used to pass.
- C05 is marked "skip" (neutral) when C04 already failed; a 4th status `skip` = not applicable.
- C07 for "<Person> (Prop. <Business>)" names compares the person and business parts separately (min score) – a whole-string comparison would only warn on K07.
- C17 constitution comes from the registry (by GSTIN); if the GST certificate is unreadable (K04) it is inferred from "LLP"/"Pvt Ltd" in the business name.
- C18 looks up the lead by the certificate GSTIN, then by Udyam number (K10's GSTIN is tampered, so the lead is found by Udyam).
- Final status mapping: C01 fail → INCOMPLETE; C02 fail → RETAKE; other fail → FAIL; warnings only → PASS_WITH_WARNINGS (order → `KYC_REVIEW`); clean → PASS (`KYC_VERIFIED`).
- Wrapped addresses are joined without a space when line 1 ends in a letter and line 2 starts lowercase ("Maharashtr|a" → "Maharashtra").
- "Fetch from DigiLocker" and "e-Sign with Aadhaar OTP" are simulated (OTP `123456`); DigiLocker in the demo loads the selected specimen applicant.

- DELAYED is shown as a banner/flag on the current stage (order keeps its stage) rather than replacing the stage, so progress stays meaningful; the event log records a DELAYED event. A delay adds 3 working days.
- Order IDs are 8-character hex short codes used directly in the public tracker link `/track/<id>` (no login; masked data only).
- Event dates follow the simulated clock (`APP_TODAY` + schedule) so the demo timeline reads naturally.

- "Fixable" drop reasons (1,485 of 4,632): owner had no time for a visit, visit not scheduled, quote too complex, quote too slow, missing GST/Udyam document, paperwork too long, signatory not available, document details mismatch. "Installation delayed" (98) is an ops fix, not counted.
- Propensity labels use the spec cut-offs (Hot ≥ 70, Warm 40–69, Cold < 40) on `class_weight="balanced"` probabilities, so many dropped leads score Hot; the list is meant to be read as a ranking (sorted by score). Calibrating cut-offs to call-centre capacity is a business decision.
- Charts avoid dual axes: activation rate and CAC by source are two side-by-side panels.

- Visual design is a purple/lavender theme (#5A3BF0) at the user's request instead of the spec's Airtel red `#E40000`. Design mockups: https://claude.ai/artifact/7tWS5opu6frigPgoPf3iHq (private unless shared).
- The DigiLocker button is a UI-only mock.
- The landing page uses 4 free photos under the Unsplash License, stored in `frontend/public/images/` and credited on each card: kirana.jpg (Zoshua Colah, Kamshet MH), office.jpg (Zulfugar Karimov), cafe.jpg (Kamal Kant, Bengaluru), factory.jpg (EqualStock). Segment cards list typical bundle items per segment; the only price shown is the verified Dukaan Digital ₹2,495 for a 2-person shop without a GSTIN.
- Every KYC check carries the document it belongs to (`doc`); only C01 (completeness) is order-level.

## ❌ Known issues / failing tests
- No failing tests (backend 66 passed, 1 skipped; Playwright 4/4).
- `test_06_tamil_llm` is skipped: AI mode needs an API key, so the LLM path (tool loop, refusal fallback, vision cross-check) has not been run against the live API. If an LLM call fails, the advisor falls back to guided mode for that turn.
- The Docker image and `docker compose` were not built (Docker daemon not running). The image uses Python 3.11; development and tests ran on Python 3.14. 3.11 compatibility was checked statically (no 3.12+ syntax such as PEP 701 f-strings), not by running.
- OCR takes ~5–10 s per sample applicant on this machine.
- Guided mode understands chips and common English/Hinglish phrasing; unusual free text may need a chip or an extra turn (AI mode handles open conversation).
- Propensity ROC-AUC is 0.68 – good for ranking, not precise probabilities.
- For ~2 minutes at the start of Phase 7 this session and the frontend session both wrote to `frontend/`; the frontend session restored its files. This session's Phase 5–6 commits contain some of its early in-progress frontend files, superseded by its own commits from 584f0df on.

## 📊 Key results (for the PPT)
- Rules audit: 48 / 368 sold bundles (13%) break catalogue rules – city tier 24, GSTIN 12, dependency 9, employees 8 (exact match with the expected counts)
- KYC: 12/12 applicants match the derived answer key (primary flag caught 12/12) – see `docs/kyc_results.md`
- Propensity model ROC-AUC: 0.68 (held-out 20%); top drivers: referral (+), WhatsApp campaign (−), micro segment (−), GSTIN (+), Tamil/Kannada (−)
- Insights reproduced: 368 activations, CAC ₹15,053, churn 15.2%, referral 14.8% / ₹4,099 vs field sales 7.3% / ₹24,335, churn 6% (1 call) → 28% (5 calls), GSTIN 9.6% vs 2.0%, segments 4.1 / 11.1 / 11.0 / 12.8%, fixable drops 1,485 / 4,632
- Advisor tests: 15/15 pass in guided mode (scenario 6 asserts the English fallback note; the Tamil reply test runs only with `TEST_ANTHROPIC_API_KEY`)

## ▶️ How to run (short)
- backend: `cd backend && python -m venv .venv && .venv/Scripts/activate && pip install -r requirements.txt && python scripts/load_data.py && uvicorn app.main:app --port 8000`
- frontend: `cd frontend && npm install && npm run dev` → http://localhost:5173 (needs the backend on :8000)
- tests: `cd backend && python -m pytest -q` · `cd e2e && npm install && npx playwright test`
- docs: from `backend/`: `python scripts/audit_sold_bundles.py`, `python scripts/run_kyc_samples.py`, `python scripts/train_propensity.py`, `python scripts/analyze_leads.py`
- demo shortcuts: sample applicants K01–K12 in the KYC dropdown · OTP `123456` · tracker controls at `/track/<id>?demo=1` · back-office PIN `2026`

## 🔜 Suggested next steps (finale)
- Turn on AI mode and run the 15 scenarios in Tamil/Kannada/Punjabi by hand; add LLM-mode assertions to the suite.
- Price within the min–max band (tier/volume/tenure) instead of always the "from" price; GST-inclusive toggle.
- Real integrations: GSP for GSTIN, Udyam API, DigiLocker pull, licensed Aadhaar e-sign, payment gateway for the first month.
- Partner co-pilot mode for channel partners/field sales (the costliest channel at ₹24,335 CAC) with lead hand-off.
- Calibrate propensity cut-offs to call-centre capacity; A/B test the WhatsApp nudge.
- Send tracker events as real WhatsApp Business templates (the EN/HI text already exists).
- Postgres + migrations, KMS-managed keys, background OCR worker, VAPT and a DPIA before any pilot.
