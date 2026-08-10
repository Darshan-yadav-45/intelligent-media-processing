"""
Lightweight "possible editing/tampering" heuristic.
Not forensic-grade - combines cheap explainable signals:
  - EXIF Software tag naming a known editor (Photoshop, GIMP, Lightroom, etc.)
  - JPEG compression-artifact inconsistency via a simple block-level
    Error Level Analysis (ELA) proxy: re-compress and diff.
"""
import io
import cv2
import numpy as np
from PIL import Image as PILImage

KNOWN_EDITORS = ["photoshop", "gimp", "lightroom", "snapseed", "picsart", "affinity"]


def _software_flag(editing_software: str | None) -> bool:
    if not editing_software:
        return False
    lowered = editing_software.lower()
    return any(editor in lowered for editor in KNOWN_EDITORS)


def _ela_score(pil_image: PILImage.Image, quality: int = 90) -> float:
    """Re-saves the image at a known JPEG quality and measures the mean
    pixel difference from the original. Regions/images that were locally
    edited after the original save often show elevated, uneven error.
    This is a coarse proxy, not a substitute for forensic ELA tooling.
    """
    buffer = io.BytesIO()
    rgb = pil_image.convert("RGB")
    rgb.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    recompressed = PILImage.open(buffer)

    original_arr = np.array(rgb).astype(np.int16)
    recompressed_arr = np.array(recompressed).astype(np.int16)

    if original_arr.shape != recompressed_arr.shape:
        return 0.0

    diff = np.abs(original_arr - recompressed_arr)
    return float(np.mean(diff))


def detect_tampering(pil_image: PILImage.Image, editing_software: str | None) -> dict:
    score = 0.0

    if _software_flag(editing_software):
        score += 0.5

    ela = _ela_score(pil_image)
    # Higher mean ELA error suggests more localized re-compression artifacts
    if ela > 12:
        score += 0.35
    elif ela > 7:
        score += 0.15

    detected = score >= 0.5
    confidence = round(min(0.85, max(0.15, score)), 2)

    return {"detected": bool(detected), "confidence": confidence}
