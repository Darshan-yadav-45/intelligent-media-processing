"""
Orchestrates the full analysis pipeline for a single image.
Called from the Celery task (app/workers/tasks.py).
"""
import logging
import cv2
import numpy as np
from PIL import Image as PILImage

from app.analysis import blur, brightness, duplicate, ocr, vehicle, metadata as meta_module
from app.analysis import screenshot, photo_of_photo, tampering, dimensions

logger = logging.getLogger(__name__)


def run_full_analysis(file_path: str, file_size: int, candidate_hashes: list[tuple[str, str]]) -> dict:
    """Runs every analysis check against the image at file_path.

    candidate_hashes: prior (image_id, phash) pairs for this user, used for
    duplicate detection.

    Returns a flat dict ready to persist onto AnalysisResult, plus a nested
    'payload' matching the API's AnalysisPayload schema.
    """
    pil_image = PILImage.open(file_path)
    pil_image.load()
    width, height = pil_image.size

    image_bgr = cv2.imread(file_path)
    if image_bgr is None:
        raise ValueError(f"OpenCV could not read image at {file_path}")

    blur_result = blur.detect_blur(image_bgr)
    brightness_result = brightness.detect_brightness(image_bgr)

    phash = duplicate.compute_phash(pil_image)
    duplicate_result = duplicate.find_duplicate(phash, candidate_hashes)

    ocr_result = ocr.extract_text(image_bgr)
    vehicle_result = vehicle.validate_vehicle_number(ocr_result["text"])
    state_result = vehicle.detect_registration_state(
        vehicle_result["value"], vehicle_result["valid_format"], ocr_result["confidence"]
    )

    metadata_result = meta_module.extract_metadata(pil_image)

    screenshot_result = screenshot.detect_screenshot(
        image_bgr, width, height, metadata_result["has_exif"]
    )
    photo_of_photo_result = photo_of_photo.detect_photo_of_photo(
        image_bgr, metadata_result["has_exif"]
    )
    tampering_result = tampering.detect_tampering(pil_image, metadata_result["editing_software"])
    dimension_result = dimensions.validate_dimensions(width, height, file_size)

    issues = [
        blur_result["is_blurry"],
        brightness_result["is_low_light"],
        duplicate_result["is_duplicate"],
        screenshot_result["detected"],
        photo_of_photo_result["detected"],
        tampering_result["detected"],
        dimension_result["flagged"],
    ]
    overall_score = "REVIEW_REQUIRED" if any(issues) else "GOOD"

    return {
        "phash": phash,
        "width": width,
        "height": height,
        "blur": blur_result,
        "brightness": brightness_result,
        "duplicate": duplicate_result,
        "ocr": ocr_result,
        "vehicle": vehicle_result,
        "state": state_result,
        "metadata": metadata_result,
        "screenshot": screenshot_result,
        "photo_of_photo": photo_of_photo_result,
        "tampering": tampering_result,
        "dimensions": dimension_result,
        "overall_score": overall_score,
    }
