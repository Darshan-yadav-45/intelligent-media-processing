"""
Image dimension / aspect-ratio validation.
Flags images that are too small to be useful for downstream analysis
(e.g. thumbnails, corrupted partial uploads).
"""
MIN_WIDTH = 300
MIN_HEIGHT = 300
MIN_FILE_SIZE_BYTES = 5 * 1024  # 5 KB


def validate_dimensions(width: int, height: int, file_size: int) -> dict:
    aspect_ratio = round(width / height, 3) if height else None
    too_small = width < MIN_WIDTH or height < MIN_HEIGHT or file_size < MIN_FILE_SIZE_BYTES

    return {
        "aspect_ratio": aspect_ratio,
        "flagged": bool(too_small),
    }
