# Privacy note – Udyam Saathi (DPDP Act, 2023)

All data in this prototype is synthetic, but it is handled as if it were real customer data.

**Consent.** Before any document is uploaded the owner sees a notice (English/Hindi) stating what we collect, why, who sees it, how long we keep it and their rights. Two separate checkboxes: KYC verification (required) and WhatsApp product updates (optional, off by default). Each consent is stored with order ID, purposes, notice version (`v1.0`), language, timestamp and a salted hash of the IP address – never the raw IP. Every KYC endpoint returns **403** until a valid, unwithdrawn KYC consent exists for that order.

**Purpose limitation.** Documents are used only to verify the business for the telecom connection and to install the service. Marketing use requires the separate opt-in.

**Data minimisation.** We collect GSTIN, Udyam number, GST certificate, Udyam certificate, authorised-signatory ID and one address proof. We never ask for Aadhaar number, PAN, date of birth or bank details; e-sign is an OTP step (mocked) and the advisor is instructed never to request documents in chat. WhatsApp senders are keyed by a hash of their number.

**Masking.** Identifiers are masked in the UI, APIs, back office and logs: GSTIN `27••••••••••1ZP`, Udyam `UDYAM-MH-00-•••6696`, phone `98•••••210`, person names as initials (`J. S.`), signatory IDs `SYN-ID-••••48`. A logging formatter re-masks every log line with regexes, and a test fails the build if any unmasked GSTIN, Udyam or phone number appears in the log file.

**Encryption.** Uploaded files are encrypted at rest with Fernet (AES-128-CBC + HMAC) using `DOC_ENCRYPTION_KEY`, stored outside the web root under `storage/` (git-ignored) and never served back by any endpoint – only extracted, masked fields are returned.

**Retention.** Documents are deleted 90 days after activation, or immediately when an order is cancelled or consent is withdrawn (`POST /api/admin/run-retention`, scheduled daily in production). Only the verification result (pass/fail and check IDs) is kept for the legal retention period. Every deletion is written to the audit log.

**Access control.** The public tracker link shows masked data only. The back office requires a PIN (production: SSO + roles). Full identifiers are shown only in the reviewer view, and each view creates an audit-log entry.

**User rights.** The Privacy centre (`/privacy`) shows what we hold (masked), lets the owner withdraw consent (cancels a not-yet-active order and deletes documents) and delete their documents on request (`DELETE /api/privacy/data/{order}`).

**Sharing with partners.** The installation partner receives only the installation address and the technician slot – no identifiers or documents.

**Other safeguards.** CORS is restricted to the frontend origin; lookup endpoints are rate-limited; the LLM (optional) never receives documents unless the vision cross-check is enabled, and it cannot decide products – the rules engine does.

**What we would add in production.** Real DigiLocker pull (with its consent artefact) and real Aadhaar e-sign via a licensed ASP; GSTN/Udyam APIs through a GSP; KMS-managed keys with rotation; Postgres with row-level security; VAPT and a DPIA before launch; a named Data Protection Officer and grievance contact in the notice; consent-manager integration; breach-notification runbook (72 h to the Data Protection Board).
