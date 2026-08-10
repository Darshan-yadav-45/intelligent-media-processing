"""
OCR text extraction using Tesseract (pytesseract).
Requires the tesseract-ocr binary to be installed on the host / container
(see backend Dockerfile - apt-get install tesseract-ocr).
"""
import logging
import numpy as np
import pytesseract
import cv2

logger = logging.getLogger(__name__)


def extract_text(image_bgr: np.ndarray) -> dict:
    try:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        # Light preprocessing improves OCR accuracy on plate-style text
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
        words, confidences = [], []
        for i, word in enumerate(data["text"]):
            word = word.strip()
            conf = data["conf"][i]
            if word and str(conf) != "-1":
                try:
                    conf_val = float(conf)
                except ValueError:
                    continue
                if conf_val > 0:
                    words.append(word)
                    confidences.append(conf_val)

        text = " ".join(words).strip()
        avg_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0

        return {"text": text, "confidence": round(avg_confidence, 2)}
    except Exception as exc:  # pytesseract raises if the binary isn't installed
        logger.error("OCR failed: %s", exc)
        return {"text": "", "confidence": 0.0}
