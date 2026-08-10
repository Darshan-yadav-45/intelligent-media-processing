"""
Photo-of-photo heuristic (someone photographing a printed/screen photo
instead of uploading the original).

Cheap, explainable signals used:
  - presence of a strong rectangular border/frame near the image edges
    (common when photographing a printed photo or a screen bezel)
  - absence of camera EXIF combined with presence of a border signal
  - detectable moire-like high-frequency periodic patterns (common when
    photographing a screen) via a simple FFT energy check
"""
import cv2
import numpy as np


def _has_strong_border(image_bgr: np.ndarray) -> bool:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    h, w = edges.shape
    border_thickness = max(2, int(min(h, w) * 0.02))

    top = edges[:border_thickness, :]
    bottom = edges[-border_thickness:, :]
    left = edges[:, :border_thickness]
    right = edges[:, -border_thickness:]

    border_edge_density = (
        np.mean(top > 0) + np.mean(bottom > 0) + np.mean(left > 0) + np.mean(right > 0)
    ) / 4
    return border_edge_density > 0.15


def _moire_energy(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray = cv2.resize(gray, (256, 256))
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = np.abs(fshift)

    h, w = magnitude.shape
    cy, cx = h // 2, w // 2
    # Mid-frequency ring energy (moire artifacts concentrate here, away from
    # both the DC component and the highest frequencies)
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((y - cy) ** 2 + (x - cx) ** 2)
    ring_mask = (dist > h * 0.15) & (dist < h * 0.35)
    ring_energy = magnitude[ring_mask].mean()
    total_energy = magnitude.mean()
    return float(ring_energy / (total_energy + 1e-6))


def detect_photo_of_photo(image_bgr: np.ndarray, has_exif: bool) -> dict:
    score = 0.0

    if _has_strong_border(image_bgr):
        score += 0.4
    if not has_exif:
        score += 0.15

    moire_ratio = _moire_energy(image_bgr)
    if moire_ratio > 1.6:
        score += 0.35
    elif moire_ratio > 1.3:
        score += 0.15

    detected = score >= 0.5
    confidence = round(min(0.9, score), 2)

    return {"detected": bool(detected), "confidence": confidence}
