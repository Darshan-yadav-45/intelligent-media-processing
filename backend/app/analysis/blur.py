"""
Blur detection using the variance of the Laplacian.
Higher variance = sharper image (more high-frequency edge content).
Lower variance = blurrier image.

Threshold of 100.0 is a commonly-used starting point for this heuristic;
it should be tuned against real sample images for a given camera/use-case.
"""
import cv2
import numpy as np

BLUR_THRESHOLD = 100.0


def detect_blur(image_bgr: np.ndarray) -> dict:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    is_blurry = laplacian_var < BLUR_THRESHOLD

    # Confidence grows the further the score is from the threshold, in either
    # direction, saturating at 0.95. This is a heuristic confidence, not a
    # calibrated probability.
    distance = abs(laplacian_var - BLUR_THRESHOLD)
    confidence = min(0.95, 0.5 + distance / (BLUR_THRESHOLD * 4))

    return {
        "score": round(float(laplacian_var), 2),
        "is_blurry": bool(is_blurry),
        "confidence": round(float(confidence), 2),
    }
