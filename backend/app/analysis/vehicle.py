"""
Indian vehicle registration number FORMAT validation only.
This does NOT verify the number is genuine / registered - it only checks
that OCR'd text matches the expected structural pattern.

Standard format: SS DD LL(L) NNNN
  SS   - 2-letter state code (e.g. KA)
  DD   - 2-digit RTO district code
  L(L) - 1 or 2 letter series
  NNNN - 4-digit unique number

Also handles the newer BH-series format: YY BH NNNN LL

State/UT detection: once a number matches the STANDARD_PATTERN, its first
two letters are the registration state/UT code (e.g. "KA" -> Karnataka).
This is looked up via the data-driven mapping in vehicle_state_codes.py.
The BH-series format has no state prefix by design (it's a nationwide
series), so state detection is not applicable there.
"""
import re

from app.analysis.vehicle_state_codes import lookup_state

STANDARD_PATTERN = re.compile(r"^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$")
BH_PATTERN = re.compile(r"^\d{2}BH\d{4}[A-Z]{1,2}$")


def normalize_ocr_text(raw_text: str) -> str:
    """Uppercase, strip whitespace/punctuation, and fix a few common OCR
    confusions (O/0, I/1) is intentionally NOT applied automatically since
    that could mask genuine format issues - normalization here is limited
    to whitespace/case/punctuation only.
    """
    text = raw_text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


def validate_vehicle_number(raw_text: str) -> dict:
    normalized = normalize_ocr_text(raw_text)

    if not normalized:
        return {"value": None, "valid_format": False}

    is_valid = bool(STANDARD_PATTERN.match(normalized) or BH_PATTERN.match(normalized))

    return {"value": normalized, "valid_format": is_valid}


def detect_registration_state(value: str | None, valid_format: bool, ocr_confidence: float) -> dict:
    """Given an already-normalized/validated vehicle number, extracts the
    registration state/UT.

    This identifies the REGISTRATION state encoded in the plate's prefix -
    it must never be presented as the vehicle's current physical location.

    Confidence is derived from OCR confidence, discounted further if the
    overall plate format didn't validate (a bad format means the state
    prefix itself is less trustworthy) or if the prefix isn't a recognized
    code at all.
    """
    if not value or not valid_format or STANDARD_PATTERN.match(value) is None:
        return {"state_code": None, "state": "Unknown", "confidence": 0.0}

    state_code = value[:2]
    state_name = lookup_state(state_code)

    if state_name == "Unknown":
        return {"state_code": state_code, "state": "Unknown", "confidence": round(ocr_confidence * 0.3, 2)}

    # Format is valid and the prefix is a recognized code: confidence
    # tracks OCR confidence directly, with a small floor since a regex
    # match on a known code is itself corroborating evidence.
    confidence = min(0.99, round(max(ocr_confidence, 0.5) * 1.05, 2))

    return {"state_code": state_code, "state": state_name, "confidence": confidence}
