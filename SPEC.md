# Product Specification — zeroFIR (Karnataka State Police)

## Purpose

Track Zero FIR filings — FIRs registered under BNSS §173(1) (formerly
CrPC §154) at a police station outside the crime's jurisdiction and
subsequently transferred to the jurisdictional PS.

The system captures:
- Receipt at the registering PS (duty officer).
- FIR content — parties, sections, brief facts, incident location.
- Transfer to the jurisdictional PS + acknowledgement.
- Downstream copy marking (DC/DM, CJM, complainant).
- Final status once the jurisdictional PS assumes charge.

---

## Users & Roles

**Pending user specification (2026-07-08).** Placeholder role model
used in Phase 0 scaffolding matches CyberFraud:

- `super_admin` — bootstrap operator, cross-PS oversight.
- `admin` — per-PS administrator.
- `unit_user` — data-entry operator at a PS.

The final role model will be locked in Phase 1 once the user
provides the specific role list.

---

## Feature Areas

**Pending detailed specification.** Provisional areas informed by
BNSS §173(1) practice:

### 1. Zero FIR Registration
- Registering PS captures: date/time of receipt, complainant details,
  brief facts, sections, incident location (district + PS), Zero
  FIR number series.

### 2. Transfer Workflow
- Identify jurisdictional PS (address / incident location).
- Forward the file — email / physical / system-to-system copy.
- Acknowledgement from jurisdictional PS + final FIR number assigned.

### 3. Status Tracking
- Draft → Registered → Transferred → Acknowledged → Closed.
- SLA aging on the transfer step so overdue files are visible.

### 4. Copy Marking
- To DC/DM, CJM, complainant. Signed PDF notifications (matches the
  eParole eSign facade pattern once wired in a later phase).

### 5. Reports & Dashboards
- Per-PS registration count, transfer turnaround, pending
  acknowledgements.
- Statewide dashboard mirrors CyberFraud's Overview shape.

---

## Business Rules

Pending detailed specification. Provisional:

1. A Zero FIR gets a unique registering-PS number series distinct
   from regular FIR numbering.
2. Transfer to jurisdictional PS is mandatory within statutory time
   (to be confirmed with the user).
3. Complainant identity is captured but Aadhar/PII redaction follows
   the same rules as CyberFraud.

---

## Non-Functional Requirements

Same as CyberFraud + eParole:

- Multi-user KSWAN-internal application.
- Concurrent access across 44 CEN PSes (mirror seed).
- Nightly backups.
- JWT auth with fail-loud secret hardening from day one.
- bcrypt pinned `<4.1` (passlib compat lesson from CyberFraud).
- Signed release orders / transfer receipts (facade in later phase,
  same shape as eParole).
- Retention per Karnataka Police Manual (25 years for the FIR
  register).
