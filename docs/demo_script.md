# 3-minute demo script – Udyam Saathi

**Setup (before going on stage):** backend on :8000, frontend on :5173, browser in mobile view (390 × 844), UI in Hindi. Second tab open on `/backoffice` (PIN 2026). Optional: a tracker tab at `/track/<order>?demo=1` from a rehearsal run.

| Time | Screen | Do | Say |
|---|---|---|---|
| 0:00–0:15 | Landing | Show the page, tap **हिंदी में शुरू करें** | "Today an MSME owner waits 10–14 days and makes 3–4 status calls to get connected; only 7.4% of leads ever activate. Udyam Saathi does it on a phone, in their language, in one sitting." |
| 0:15–0:45 | Advisor (Hindi) | Tap **किराना / दुकान** → **1–2** → **1** → type *Lucknow* → **मोबाइल हॉटस्पॉट** → **छोड़ें** → **आप ही सुझाइए** → **GSTIN नहीं है** | "No typing needed – chips for every answer, voice too. It asks one thing at a time, like a shopkeeper would. Tamil, Punjabi and Kannada leads convert at half the Hindi rate today, so the advisor speaks ten languages." |
| 0:45–1:05 | Bundle card | Point at the "why" lines and "Active GSTIN जोड़ने पर…" | "Every product comes from our rules engine – 13% of bundles sold last quarter broke catalogue rules. Here: no GSTIN, so it builds the no-GST starter – leads without GSTIN convert at 2% vs 9.6% – and shows what unlocks later." |
| 1:05–1:25 | Quote | Switch to EN in the header; toggle **Cloud CCTV** on; show the total jump; tap **Share on WhatsApp** then back; **Accept & continue** | "One monthly price, setup and contract separate, no product codes. Toggle an add-on and the rules engine re-checks it instantly. Share to the partner on WhatsApp." |
| 1:25–1:40 | Consent | Read the five headings; tick KYC; **I agree & continue** | "DPDP-grade consent before any upload: what, why, who sees it, 90-day deletion, and their rights. No Aadhaar number, PAN or bank details – ever." |
| 1:40–2:05 | Smart KYC – K01 | Choose **K01** in the sample dropdown → **Check all documents** | "Real OCR on the specimen documents. K01: the GSTIN is *Cancelled* in the registry and the Udyam number is blank – the owner gets a plain fix-it message on the exact tile, not a rejection call three days later." |
| 2:05–2:25 | Smart KYC – K03 | Choose **K03** → **Check all documents** → **e-Sign with Aadhaar OTP** → `123456` → **Confirm** | "K03: OCR read 'GO767'; we repair O→0 only where a digit must be, never touching the checksum. All 18 checks pass – KYC done in minutes. Our checker catches the planted problem in all 12 specimen applicants." |
| 2:25–2:45 | Tracker | Show stages + technician card; open `?demo=1`, **Advance**, **Simulate delay** | "Churn goes from 6% at one status call to 28% at five, so the tracker is proactive: WhatsApp-style updates, and when install slips we say why, give the new date and credit ₹100 before they ask." |
| 2:45–3:00 | Back office | Switch tab: **Advisor leads** → **KYC review** → **Rules audit** | "Leads the advisor couldn't close land here with a propensity score and next action; warnings go to a human review queue; and the audit found the 48 mis-sold bundles. Referral costs ₹4,099 per activation vs ₹24,335 for field sales – this journey shifts the mix." |

**Backup lines if asked**
- *AI mode:* set `ANTHROPIC_API_KEY` and the same flow runs on Claude, which can only get products through the `recommend_bundle` tool – it cannot invent prices or bypass eligibility.
- *Hidden test scenarios:* the 15 advisor scenarios run as automated tests (15/15); a property test checks 500 random profiles never get an ineligible product.
- *Privacy:* identifiers masked everywhere, documents Fernet-encrypted, a test fails if any raw GSTIN/Udyam/phone reaches the logs.
