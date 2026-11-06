# lefts.md – Status of the Udyam Saathi build
_Last updated: 2026-11-06 · Current phase: 1_

## ✅ Done
- Phase 0: repo structure, `.gitignore`, `.env.example`, `lefts.md`; data moved to `data/raw/YTL_TrackA_Udyam_Digital_Data/`
- Phase 1: `backend/app/{config,db,models,schemas}.py`, `scripts/load_data.py` (→ `app/services/data_loader.py`, API self-loads an empty DB), `utils/validators.py` (positional OCR normalisation, never repairs checksum), `utils/masking.py` (+ masking log formatter), `/api/gstin`, `/api/udyam`, `/api/products`, rate-limited lookups; `tests/test_validators.py` 12/12 pass

## ⏳ Left for humans (do these yourself)
- [ ] (filled in as the build progresses)

## ⚠️ Assumptions made
- Data was at `./YTL_TrackA_Udyam_Digital_Data/`; moved (unchanged) to the spec path `data/raw/YTL_TrackA_Udyam_Digital_Data/`.
- Repo root is `K:\airtel` (spec calls it `udyam-saathi/`). Default branch `main`.
- `smb_leads.csv` has a literal `None` value in `current_internet` (meaning no internet); it is read as the string "None", not NULL.
- GSTIN positional normalisation maps only O↔0, I↔1, S↔5, B↔8 (plus `2→Z` at index 13); the checksum character (index 14) and index 12 are never altered.
- Tooling found: Python 3.14.5 (spec says 3.11+), Node 24.16, npm 11.13, Docker 29.5, Tesseract 5.4.0 at `C:\Program Files\Tesseract-OCR` (not on PATH → auto-detected via `TESSERACT_CMD` / default install path).

## ❌ Known issues / failing tests
- none yet

## 📊 Key results (for the PPT)
- pending

## ▶️ How to run (short)
- pending

## 🔜 Suggested next steps (finale)
- pending
