# Product Specification — zeroFIR (Karnataka State Police)

## Purpose

**zeroFIR** is the **Masking Application** in Karnataka's NCRP → Police
IT V2 integration pipeline for cyber-fraud Zero FIRs. When a citizen
reports financial fraud on the National Cyber Crime Reporting Portal
(NCRP) — either through the 1930 call centre or the self-service
website — NCRP pushes the complaint to us. A KA CEN PS officer then
uses zeroFIR to review the NCRP data, fill in the additional fields
required for a formal Zero FIR under BNS §173(1), route it through
the auto-decisions (fraud-amount threshold, jurisdiction check),
and either

- register it as a **Zero FIR** in Police IT V2 and transfer to the
  jurisdictional PS (if within Karnataka) or to CRIMAC (if outside);
- or divert it to the **e-Lost Platform** when the amount is below
  threshold.

Every state change is echoed back to NCRP so the citizen's dashboard
stays in sync.

---

## Architecture (integration overview)

```
   ┌──────────────┐              ┌───────────────┐              ┌───────────────┐
   │  NCRP Portal │ ─── API 1 ──▶│   zeroFIR     │ ── eFIR ────▶│  Police IT V2 │
   │  (1930 / web)│              │ (Masking App) │              │  (FIR system) │
   │              │ ◀── API 2 ───│               │              │               │
   │              │ ─── API 3 ──▶│               │              │               │
   │              │ ◀── API 5 ───│               │              │               │
   └──────────────┘              └───────────────┘              └───────────────┘
```

- **API 1** *(NCRP → us)*: push complaint data on submission.
- **API 2** *(us → NCRP)*: push eFIR detail once created here.
- **API 3** *(NCRP → us, we call)*: pull Notice + Lien details already
  raised on the reported bank accounts.
- **API 5** *(us → NCRP)*: push the finalised FIR from Police IT V2.
- API 4 (transfer to CRIMAC) — separate integration handled outside
  zeroFIR's scope.

All four APIs (1, 2, 3, 5) will be provided by the NCRP side. Phase 1a
builds the **receive-side** for API 1; phases 1b/1c wire the calls out
for API 2/3/5.

---

## The Masking Application UX

Two-section screen per complaint:

1. **NCRP data (read-only)** — everything NCRP pushed us in API 1.
   Complainant, address, transaction details, suspect mobiles, e-FIR
   Y/N answers, category. Rendered from the typed columns
   (`ncrp_complaints` + child tables) so it's queryable, with the raw
   API 1 payload kept in a JSON column for audit and future field
   extraction.
2. **FIR entry fields (editable)** — the 15 sections from the V2 FIR
   entry deck, extended with the Karnataka-specific fields the officer
   fills in on top of the NCRP data. Structured as a tabbed form
   (same shape as CyberFraud's Case Entry so operators recognise it):
   - **1. Police Station Details** — District, sub-division, PS, date,
     last FIR no + time, FIR no (Zero FIR series), GSC no.
   - **2. FIR Summary** — free text ≥ 300 chars, Kannada supported.
   - **3. Acts & Sections** — Act code, act (BNS 2023 / BNSS / IT
     Act etc.), sections (multi-select), offence type, gravity, crime
     classification (major + minor head), offences involving Aadhaar
     Y/N.
   - **4. Time of Occurrence** — incident from/to date-time,
     information received at PS date-time, mode of complaint, FIR
     case type, SHD reference, reasons for delay, "complainant has
     seen the occurrence".
   - **5. Place of Incident** — full address block + beat, village,
     distance from PS, direction, MLA/MP constituency, forest/sea
     flag, nature-of-location (actual/temporary), lat/long, "belongs
     to another jurisdiction" (state/district/PS).
   - **6. Complainant / Informant** — full identity block + relation
     to victim + role (eye witness / police officer / victim).
   - **7. Details of Accused** — one row per accused, with
     "more details" drill-in.
   - **8. Details of Victims** — same pattern.
   - **9. Particulars of Property Stolen / Involved**.
   - **10. Action Taken** — "FIR read over" flag, reasons if PO does
     not proceed to spot.
   - **11. Complainant Signature / Thumb Impression** — e-pen or
     thumb capture, or "unable to sign" note.
   - **12. Details of Dispatch to Court** — court name, dispatch
     date-time.
   - **13. Name of PC/HC who carried the FIR** to court.
   - **14. Other Details** — special-case flags (TADA / NSA / tear
     gas / against police personnel), UDR / NCR-Zero FIR / MMR
     reference numbers, action taken, transfer state/district/PS,
     transferred PS + reason.
   - **15. Signature of the SHO** — read-over-and-found-correct flag,
     date-time, e-pen signature, copy-to list.

The exact field list is codified in the SQLAlchemy models. The
frontend renders sections progressively as they're implemented
across phases 1b onward.

---

## Auto-decisions

Two branching decisions run automatically once the officer submits
the FIR entry:

1. **Fraud-amount threshold** *(configurable parameter)* — sum of
   NCRP-reported transaction amounts vs. the current threshold
   (currently ₹10 lakh per the NCRP e-FIR questionnaire on slide
   10 of the KarnatakazeroFIR deck).
   - `≥ threshold` → create Zero FIR, proceed to jurisdiction check.
   - `< threshold` → route to **e-Lost Platform** (out of scope for
     zeroFIR).
2. **Jurisdiction check** — is the incident within Karnataka?
   - **Yes** → Transfer to jurisdictional PS. If NCRP already
     supplied the jurisdictional PS, this step is automated.
   - **No** → Transfer to CRIMAC Portal.

The complainant then has **3 days to sign** — if signed, the FIR is
registered in Police IT V2 and API 5 fires. If not signed within 3
days, the file closes as unregistered.

---

## Users & Roles

Placeholder roles from Phase 0 kept in Phase 1a scaffolding
(`super_admin` / `admin` / `unit_user`) so the login flow works.
The final KSP-specific role list (Duty Officer, SHO, Investigating
Officer, etc.) will be locked in a later phase once the user
specifies the exact role → workflow mapping. Every route already
declares its required role via `require_role(...)` so extending is
mechanical.

---

## Non-Functional Requirements

- Multi-user KSWAN-internal application (44 CEN PSes across 31
  Karnataka districts).
- **API 1 shared-secret auth** via `X-API-Key` header, secret in
  `ZFIR_NCRP_API_KEY` env var. NCRP-side rotates via config change.
- Fail-loud `ZFIR_JWT_SECRET` (day-one hardening from CyberFraud
  lessons).
- `bcrypt>=4.0.1,<4.1` pinned from day one.
- Kannada support in all free-text fields (FIR Summary, addresses,
  facts) — DB is `utf8mb4` / `utf8mb4_unicode_ci` from day one.
- Signed release orders / transfer receipts (facade in a later
  phase, same shape as eParole's).
- Retention per Karnataka Police Manual (25 years for FIR register).
