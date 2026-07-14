"""Static master data for Karnataka — districts + CEN PSes.

Sourced from the same `All District CEN_PS.xlsx` used by
CyberFraudDataEntry, deduplicated and typed here so the seed run
doesn't depend on any Excel file being present on the host.

31 revenue districts of Karnataka × 44 CEN police stations. Names
are canonical (matches how NCRP addresses them in incoming payloads
so the receive-side PS resolver hits on exact match). Codes are the
short forms used by KSP for CEN units.

Sources cross-checked: KSP CID Cybercrime directory, KA Revenue
Department district list. Update this file when a new CEN PS opens
or a district reorganisation happens — do NOT hand-edit the
database.
"""
from __future__ import annotations

from typing import Sequence


# ── Districts ────────────────────────────────────────────────────
# (name, code) — code is the short slug used across KSP systems.

DISTRICTS: Sequence[tuple[str, str]] = (
    ("Bagalkote", "BGK"),
    ("Ballari", "BLY"),
    ("Belagavi City", "BGM-C"),
    ("Belagavi District", "BGM-D"),
    ("Bengaluru City", "BLR-C"),
    ("Bengaluru Rural", "BLR-R"),
    ("Bidar", "BDR"),
    ("Chamarajanagara", "CMR"),
    ("Chikkaballapura", "CBP"),
    ("Chikkamagaluru", "CKM"),
    ("Chitradurga", "CTA"),
    ("Dakshina Kannada", "DK"),
    ("Davanagere", "DVG"),
    ("Dharwad", "DWD"),
    ("Gadag", "GDG"),
    ("Hassan", "HSN"),
    ("Haveri", "HVR"),
    ("Hubballi-Dharwad City", "HDC"),
    ("Kalaburagi City", "KLB-C"),
    ("Kalaburagi District", "KLB-D"),
    ("Kodagu", "KDG"),
    ("Kolar", "KLR"),
    ("Koppal", "KPL"),
    ("Mandya", "MDY"),
    ("Mangaluru City", "MNG-C"),
    ("Mysuru City", "MYS-C"),
    ("Mysuru District", "MYS-D"),
    ("Raichur", "RCR"),
    ("Ramanagara", "RMN"),
    ("Shivamogga", "SMG"),
    ("Tumakuru", "TMK"),
    ("Udupi", "UDP"),
    ("Uttara Kannada", "UK"),
    ("Vijayanagara", "VJN"),
    ("Vijayapura", "VJP"),
    ("Yadgir", "YDG"),
)


# ── CEN PSes ─────────────────────────────────────────────────────
# (ps_name, ps_code, district_name) — one row per operational CEN
# unit. Matches the KSP CID CEN PS roster.

CEN_POLICE_STATIONS: Sequence[tuple[str, str, str]] = (
    ("Bagalkote CEN PS", "BGK-CEN", "Bagalkote"),
    ("Ballari CEN PS", "BLY-CEN", "Ballari"),
    ("Belagavi City CEN PS", "BGM-C-CEN", "Belagavi City"),
    ("Belagavi District CEN PS", "BGM-D-CEN", "Belagavi District"),
    ("Bengaluru City East CEN PS", "BLR-C-E-CEN", "Bengaluru City"),
    ("Bengaluru City West CEN PS", "BLR-C-W-CEN", "Bengaluru City"),
    ("Bengaluru City North CEN PS", "BLR-C-N-CEN", "Bengaluru City"),
    ("Bengaluru City South CEN PS", "BLR-C-S-CEN", "Bengaluru City"),
    ("Bengaluru City Central CEN PS", "BLR-C-CTR-CEN", "Bengaluru City"),
    ("Bengaluru City Whitefield CEN PS", "BLR-C-WF-CEN", "Bengaluru City"),
    ("Bengaluru City South East CEN PS", "BLR-C-SE-CEN", "Bengaluru City"),
    ("Bengaluru City North East CEN PS", "BLR-C-NE-CEN", "Bengaluru City"),
    ("Bengaluru Rural CEN PS", "BLR-R-CEN", "Bengaluru Rural"),
    ("Bidar CEN PS", "BDR-CEN", "Bidar"),
    ("Chamarajanagara CEN PS", "CMR-CEN", "Chamarajanagara"),
    ("Chikkaballapura CEN PS", "CBP-CEN", "Chikkaballapura"),
    ("Chikkamagaluru CEN PS", "CKM-CEN", "Chikkamagaluru"),
    ("Chitradurga CEN PS", "CTA-CEN", "Chitradurga"),
    ("Dakshina Kannada CEN PS", "DK-CEN", "Dakshina Kannada"),
    ("Davanagere CEN PS", "DVG-CEN", "Davanagere"),
    ("Dharwad CEN PS", "DWD-CEN", "Dharwad"),
    ("Gadag CEN PS", "GDG-CEN", "Gadag"),
    ("Hassan CEN PS", "HSN-CEN", "Hassan"),
    ("Haveri CEN PS", "HVR-CEN", "Haveri"),
    ("Hubballi-Dharwad City CEN PS", "HDC-CEN", "Hubballi-Dharwad City"),
    ("Kalaburagi City CEN PS", "KLB-C-CEN", "Kalaburagi City"),
    ("Kalaburagi District CEN PS", "KLB-D-CEN", "Kalaburagi District"),
    ("Kodagu CEN PS", "KDG-CEN", "Kodagu"),
    ("Kolar CEN PS", "KLR-CEN", "Kolar"),
    ("Koppal CEN PS", "KPL-CEN", "Koppal"),
    ("Mandya CEN PS", "MDY-CEN", "Mandya"),
    ("Mangaluru City CEN PS", "MNG-C-CEN", "Mangaluru City"),
    ("Mysuru City CEN PS", "MYS-C-CEN", "Mysuru City"),
    ("Mysuru District CEN PS", "MYS-D-CEN", "Mysuru District"),
    ("Raichur CEN PS", "RCR-CEN", "Raichur"),
    ("Ramanagara CEN PS", "RMN-CEN", "Ramanagara"),
    ("Shivamogga CEN PS", "SMG-CEN", "Shivamogga"),
    ("Tumakuru CEN PS", "TMK-CEN", "Tumakuru"),
    ("Udupi CEN PS", "UDP-CEN", "Udupi"),
    ("Uttara Kannada CEN PS", "UK-CEN", "Uttara Kannada"),
    ("Vijayanagara CEN PS", "VJN-CEN", "Vijayanagara"),
    ("Vijayapura CEN PS", "VJP-CEN", "Vijayapura"),
    ("Yadgir CEN PS", "YDG-CEN", "Yadgir"),
    ("KSP CID Cyber Crime CEN PS", "CID-CEN", "Bengaluru City"),
)


# ── Acts & Sections master (Phase 1b.1) ──────────────────────────
# Static list — the officer picks an act from this dropdown in FIR
# entry Section 3, then enters the applicable sections as free text
# (e.g. "318(4), 319, 340"). Not stored in a DB table (yet) — served
# via GET /api/v1/fir-master/acts/public. Add new codes here when
# statutes change.

ACTS_MASTER: tuple[tuple[str, str], ...] = (
    ("BNS",   "Bharatiya Nyaya Sanhita, 2023"),
    ("BNSS",  "Bharatiya Nagarik Suraksha Sanhita, 2023"),
    ("BSA",   "Bharatiya Sakshya Adhiniyam, 2023"),
    ("IT",    "Information Technology Act, 2000"),
    ("IPC",   "Indian Penal Code, 1860 (legacy)"),
    ("CrPC",  "Code of Criminal Procedure, 1973 (legacy)"),
    ("NDPS",  "Narcotic Drugs and Psychotropic Substances Act, 1985"),
    ("Other", "Other / Special Act"),
)


# ── Fixed dropdown lists (used by FIR entry sections) ────────────

MODE_OF_COMPLAINT_OPTIONS: tuple[str, ...] = (
    "Written", "Oral", "Phone", "Email", "NCRP", "1930 Helpline", "Walk-In", "Other",
)

FIR_CASE_TYPE_OPTIONS: tuple[str, ...] = (
    "Fresh", "Supplementary", "Re-registration",
)

OFFENCE_TYPE_OPTIONS: tuple[str, ...] = (
    "Cognisable", "Non-cognisable",
)

GRAVITY_OPTIONS: tuple[str, ...] = (
    "Major", "Minor", "Petty",
)

DIRECTION_OPTIONS: tuple[str, ...] = (
    "N", "NE", "E", "SE", "S", "SW", "W", "NW",
)

UID_TYPE_OPTIONS: tuple[str, ...] = (
    "Aadhaar", "PAN", "Passport", "Voter ID", "Driving Licence", "Other",
)

RELATION_TO_VICTIM_OPTIONS: tuple[str, ...] = (
    "Self", "Father", "Mother", "Spouse", "Son", "Daughter",
    "Brother", "Sister", "Guardian", "Friend", "Colleague", "Other",
)

COMPLAINANT_ROLE_OPTIONS: tuple[str, ...] = (
    "victim", "eye_witness", "police_officer", "informant_third_party",
)

RELIGION_OPTIONS: tuple[str, ...] = (
    "Hindu", "Muslim", "Christian", "Sikh", "Buddhist", "Jain",
    "Parsi", "Jewish", "Other", "Prefer not to say",
)

CASTE_OPTIONS: tuple[str, ...] = (
    "SC (Scheduled Caste)",
    "ST (Scheduled Tribe)",
    "OBC (Other Backward Class)",
    "General",
    "Other",
    "Prefer not to say",
)


# Crime classification (FIR entry Section 3 "Crime Classification").
# NCRB CCTNS heads — trimmed to what a KA CEN PS actually files under.
# Update these lists when SCRB publishes a new head/minor breakdown.

CRIME_MAJOR_HEAD_OPTIONS: tuple[str, ...] = (
    "Cyber Crime — Financial",
    "Cyber Crime — Non-Financial",
    "Cyber Crime — Economic Offence",
    "IPC / BNS Crime",
    "SLL (Special & Local Laws)",
    "Other",
)

CRIME_MINOR_HEAD_OPTIONS: tuple[str, ...] = (
    "Cheating (BNS 318)",
    "Impersonation (BNS 319)",
    "Criminal Intimidation (BNS 308)",
    "Forgery / Fake Document (BNS 340)",
    "OTP Fraud",
    "UPI / Wallet Fraud",
    "IMPS / NEFT Fraud",
    "Credit / Debit Card Fraud",
    "Investment / Trading Fraud",
    "Loan Fraud",
    "Job Fraud",
    "Matrimonial Fraud",
    "Sextortion",
    "Phishing / Vishing",
    "Hacking / Data Breach",
    "Identity Theft",
    "Cryptocurrency Fraud",
    "Other",
)


# NCRP Screen 1 "Where did the incident occur?" dropdown values.
# Kept short — the FIR entry section 5 (Place of Incident) captures
# structured address; this is the intake-time coarse category.
INCIDENT_PLACE_OPTIONS: tuple[str, ...] = (
    "Own residence / Home",
    "Office / Workplace",
    "Bank / ATM",
    "Public place",
    "Cyber cafe",
    "Online — Fraud call / SMS",
    "Online — Social media",
    "Online — Email",
    "Online — Website / App",
    "Other",
)


INDIAN_STATES: tuple[str, ...] = (
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
)
