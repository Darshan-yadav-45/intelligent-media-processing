"""
Data-driven mapping of Indian vehicle registration state/UT codes.

Source of truth for "registration state" lookups - deliberately kept as a
single data structure (not if/else branches) so it's trivial to extend when
new codes are introduced (e.g. a state splits, or a new UT code appears).

IMPORTANT: this maps a REGISTRATION code prefix to the state/UT that issued
it. It says nothing about where the vehicle currently is - see the
docstring on `lookup_state`.
"""

# Maps every known 2-letter registration prefix to its issuing state/UT.
# Some states have more than one valid prefix (e.g. Odisha OD/OR, Telangana
# TS/TG, Uttarakhand UK/UA) - each prefix gets its own entry pointing at the
# same state name.
STATE_CODE_MAP: dict[str, str] = {
    # States
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BR": "Bihar",
    "CG": "Chhattisgarh",
    "GA": "Goa",
    "GJ": "Gujarat",
    "HR": "Haryana",
    "HP": "Himachal Pradesh",
    "JH": "Jharkhand",
    "KA": "Karnataka",
    "KL": "Kerala",
    "MP": "Madhya Pradesh",
    "MH": "Maharashtra",
    "MN": "Manipur",
    "ML": "Meghalaya",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "OD": "Odisha",
    "OR": "Odisha",
    "PB": "Punjab",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TS": "Telangana",
    "TG": "Telangana",
    "TR": "Tripura",
    "UP": "Uttar Pradesh",
    "UK": "Uttarakhand",
    "UA": "Uttarakhand",
    "WB": "West Bengal",
    # Union Territories
    "AN": "Andaman and Nicobar Islands",
    "CH": "Chandigarh",
    "DD": "Dadra and Nagar Haveli and Daman and Diu",
    "DL": "Delhi",
    "JK": "Jammu and Kashmir",
    "LA": "Ladakh",
    "LD": "Lakshadweep",
    "PY": "Puducherry",
}

# Canonical ordered list of every state/UT name, for building dropdowns
# ("All States" + "Unknown" are added by the frontend/API layer, not here).
ALL_STATE_NAMES: list[str] = sorted(set(STATE_CODE_MAP.values()))


def lookup_state(state_code: str | None) -> str:
    """Returns the state/UT name for a given 2-letter registration code, or
    "Unknown" if the code isn't recognized / is missing.

    This identifies the REGISTRATION state associated with the number
    plate only - it is not, and must never be presented as, the vehicle's
    current physical location.
    """
    if not state_code:
        return "Unknown"
    return STATE_CODE_MAP.get(state_code.upper(), "Unknown")
