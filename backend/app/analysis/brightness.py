"""
Brightness / low-light detection based on mean grayscale pixel intensity (0-255).
"""
import cv2
import numpy as np

LOW_LIGHT_THRESHOLD = 60.0


def detect_brightness(image_bgr: np.ndarray) -> dict:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(np.mean(gray))

    is_low_light = mean_brightness < LOW_LIGHT_THRESHOLD

    distance = abs(mean_brightness - LOW_LIGHT_THRESHOLD)
    confidence = min(0.95, 0.5 + distance / (LOW_LIGHT_THRESHOLD * 3))

    return {
        "score": round(mean_brightness, 2),
        "is_low_light": bool(is_low_light),
        "confidence": round(float(confidence), 2),
    }
