"""
Unit tests for individual analysis heuristics (no DB / API involved).
"""
import numpy as np
from PIL import Image as PILImage

from app.analysis import blur, brightness, vehicle, duplicate
from app.analysis.vehicle_state_codes import lookup_state, STATE_CODE_MAP


def _flat_gray_image(intensity=128, size=(200, 200)):
    arr = np.full((size[1], size[0], 3), intensity, dtype=np.uint8)
    return arr


def _noisy_image(size=(200, 200)):
    return np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)


def test_blur_detection_flags_flat_image_as_blurry():
    flat = _flat_gray_image()
    result = blur.detect_blur(flat)
    assert result["is_blurry"] is True
    assert 0 <= result["confidence"] <= 1


def test_blur_detection_does_not_flag_noisy_image():
    noisy = _noisy_image()
    result = blur.detect_blur(noisy)
    assert result["is_blurry"] is False


def test_brightness_detects_low_light():
    dark = _flat_gray_image(intensity=10)
    result = brightness.detect_brightness(dark)
    assert result["is_low_light"] is True


def test_brightness_detects_normal_light():
    bright = _flat_gray_image(intensity=150)
    result = brightness.detect_brightness(bright)
    assert result["is_low_light"] is False


def test_vehicle_number_valid_standard_format():
    result = vehicle.validate_vehicle_number("KA05MN1234")
    assert result["valid_format"] is True
    assert result["value"] == "KA05MN1234"


def test_vehicle_number_invalid_format():
    result = vehicle.validate_vehicle_number("NOT A PLATE")
    assert result["valid_format"] is False


def test_vehicle_number_normalizes_whitespace_and_case():
    result = vehicle.validate_vehicle_number("ka 05 mn 1234")
    assert result["value"] == "KA05MN1234"
    assert result["valid_format"] is True


def test_duplicate_hash_identical_images_are_similar():
    img = PILImage.new("RGB", (200, 200), color=(50, 100, 150))
    h1 = duplicate.compute_phash(img)
    h2 = duplicate.compute_phash(img)
    similarity = duplicate.compare_hashes(h1, h2)
    assert similarity == 1.0


def test_find_duplicate_flags_identical_hash():
    img = PILImage.new("RGB", (200, 200), color=(50, 100, 150))
    h = duplicate.compute_phash(img)
    result = duplicate.find_duplicate(h, [("existing-id", h)])
    assert result["is_duplicate"] is True
    assert result["duplicate_of"] == "existing-id"


# --- Registration state detection ---

def test_lookup_state_known_codes():
    assert lookup_state("KA") == "Karnataka"
    assert lookup_state("MH") == "Maharashtra"
    assert lookup_state("TN") == "Tamil Nadu"
    assert lookup_state("KL") == "Kerala"
    assert lookup_state("DL") == "Delhi"
    assert lookup_state("GJ") == "Gujarat"
    assert lookup_state("RJ") == "Rajasthan"
    assert lookup_state("UP") == "Uttar Pradesh"
    assert lookup_state("WB") == "West Bengal"


def test_lookup_state_handles_alternate_prefixes():
    assert lookup_state("OD") == "Odisha"
    assert lookup_state("OR") == "Odisha"
    assert lookup_state("TS") == "Telangana"
    assert lookup_state("TG") == "Telangana"
    assert lookup_state("UK") == "Uttarakhand"
    assert lookup_state("UA") == "Uttarakhand"


def test_lookup_state_unknown_code():
    assert lookup_state("ZZ") == "Unknown"
    assert lookup_state(None) == "Unknown"
    assert lookup_state("") == "Unknown"


def test_lookup_state_is_case_insensitive():
    assert lookup_state("ka") == "Karnataka"


def test_all_29_states_and_uts_present():
    # 28 states (with a few dual-code states) + 8 union territories
    expected_states = {
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
        "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
        "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
        "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
        "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
        "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
    }
    assert expected_states.issubset(set(STATE_CODE_MAP.values()))


def test_detect_registration_state_end_to_end():
    result = vehicle.validate_vehicle_number("KA 05 MN 1234")
    assert result["value"] == "KA05MN1234"
    state_result = vehicle.detect_registration_state(result["value"], result["valid_format"], 0.9)
    assert state_result["state_code"] == "KA"
    assert state_result["state"] == "Karnataka"
    assert state_result["confidence"] > 0


def test_detect_registration_state_handles_missing_number():
    state_result = vehicle.detect_registration_state(None, False, 0.0)
    assert state_result["state"] == "Unknown"
    assert state_result["confidence"] == 0.0


def test_normalize_handles_hyphens_and_spaces():
    assert vehicle.normalize_ocr_text("KA-05-MN-1234") == "KA05MN1234"
    assert vehicle.normalize_ocr_text("KA 05 MN 1234") == "KA05MN1234"
