"""
Perceptual-hash based duplicate/near-duplicate detection.
Compares a new image's phash (Hamming distance) against previously stored
hashes for the same user. Smaller distance = more similar.
"""
import imagehash
from PIL import Image as PILImage

SIMILARITY_THRESHOLD = 0.90  # similarity >= this counts as a duplicate
MAX_HASH_DISTANCE = 64  # phash is a 64-bit hash


def compute_phash(pil_image: PILImage.Image) -> str:
    return str(imagehash.phash(pil_image))


def compare_hashes(new_hash: str, existing_hash: str) -> float:
    """Returns a similarity score in [0, 1], where 1.0 = identical."""
    h1 = imagehash.hex_to_hash(new_hash)
    h2 = imagehash.hex_to_hash(existing_hash)
    distance = h1 - h2
    return 1.0 - (distance / MAX_HASH_DISTANCE)


def find_duplicate(new_hash: str, candidates: list[tuple[str, str]]) -> dict:
    """candidates: list of (image_id_str, phash_str) for prior images (same user).
    Returns the best match, if any, above the similarity threshold.
    """
    best_match = None
    best_similarity = 0.0

    for image_id, existing_hash in candidates:
        similarity = compare_hashes(new_hash, existing_hash)
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = image_id

    is_duplicate = best_similarity >= SIMILARITY_THRESHOLD

    return {
        "is_duplicate": bool(is_duplicate),
        "duplicate_of": best_match if is_duplicate else None,
        "similarity": round(float(best_similarity), 4) if best_match else None,
    }
