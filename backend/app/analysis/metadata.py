"""
EXIF metadata extraction. Absence of metadata is common (many platforms strip
it) and must NOT be treated as evidence of fraud on its own.
"""
from PIL import Image as PILImage
from PIL.ExifTags import TAGS

GPS_TAG_IDS = {34853}  # GPSInfo


def extract_metadata(pil_image: PILImage.Image) -> dict:
    result = {
        "has_exif": False,
        "camera_make": None,
        "camera_model": None,
        "exif_datetime": None,
        "has_gps": False,
        "editing_software": None,
    }

    exif_data = pil_image.getexif()
    if not exif_data:
        return result

    result["has_exif"] = True
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        if tag_name == "Make":
            result["camera_make"] = str(value).strip()
        elif tag_name == "Model":
            result["camera_model"] = str(value).strip()
        elif tag_name == "DateTime":
            result["exif_datetime"] = str(value)
        elif tag_name == "Software":
            result["editing_software"] = str(value).strip()
        if tag_id in GPS_TAG_IDS:
            result["has_gps"] = True

    return result
