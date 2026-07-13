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
