"""
Screenshot-detection heuristic.

This is NOT a trained classifier - it combines a few cheap, explainable
signals that correlate with screenshots:
  - common device/screen aspect ratios (e.g. 16:9, 19.5:9, 4:3 phone screens)
  - absence of any EXIF/camera metadata (screenshots rarely carry camera EXIF)
  - very "flat" colour histograms (UI screenshots tend to have large solid-
    colour regions compared to natural photos)
"""
import cv2
import numpy as np

COMMON_SCREEN_RATIOS = [16 / 9, 9 / 16, 19.5 / 9, 9 / 19.5, 4 / 3, 3 / 4, 1.0]
RATIO_TOLERANCE = 0.03


def _matches_common_ratio(width: int, height: int) -> bool:
    if height == 0:
        return False
    ratio = width / height
    return any(abs(ratio - r) < RATIO_TOLERANCE for r in COMMON_SCREEN_RATIOS)


def _flat_region_fraction(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
    flat_pixels = np.sum(gradient_magnitude < 5)
    return float(flat_pixels) / gradient_magnitude.size


def detect_screenshot(image_bgr: np.ndarray, width: int, height: int, has_exif: bool) -> dict:
    score = 0.0

    if _matches_common_ratio(width, height):
        score += 0.35
    if not has_exif:
        score += 0.25

    flat_fraction = _flat_region_fraction(image_bgr)
    if flat_fraction > 0.55:
        score += 0.30
    elif flat_fraction > 0.40:
        score += 0.15

    detected = score >= 0.5
    confidence = round(min(0.95, score), 2)

    return {"detected": bool(detected), "confidence": confidence}
