"""
Optional seed script for dashboard demonstration data.
Creates a demo user + sample processing records with sample analysis
results. Does NOT fabricate results for real uploaded images.

Run with: python seed.py
"""
import uuid
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.image import Image, ImageStatus
from app.models.analysis_result import AnalysisResult
from app.utils.security import hash_password

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "DemoPass123!"


def seed():
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if not user:
            user = User(name="Demo User", email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created demo user: {DEMO_EMAIL} / {DEMO_PASSWORD}")

        sample_defs = [
            {"status": ImageStatus.COMPLETED, "blurry": False, "low_light": False, "dup": False, "vehicle": "KA05MN1234", "valid": True, "state_code": "KA", "state": "Karnataka"},
            {"status": ImageStatus.COMPLETED, "blurry": True, "low_light": False, "dup": False, "vehicle": None, "valid": False, "state_code": None, "state": "Unknown"},
            {"status": ImageStatus.COMPLETED, "blurry": False, "low_light": True, "dup": False, "vehicle": "MH12AB4321", "valid": True, "state_code": "MH", "state": "Maharashtra"},
            {"status": ImageStatus.COMPLETED, "blurry": False, "low_light": False, "dup": True, "vehicle": "TN38CD1234", "valid": True, "state_code": "TN", "state": "Tamil Nadu"},
            {"status": ImageStatus.COMPLETED, "blurry": False, "low_light": False, "dup": False, "vehicle": "KL07EF1234", "valid": True, "state_code": "KL", "state": "Kerala"},
            {"status": ImageStatus.COMPLETED, "blurry": False, "low_light": False, "dup": False, "vehicle": "DL01AB1234", "valid": True, "state_code": "DL", "state": "Delhi"},
            {"status": ImageStatus.FAILED, "blurry": None, "low_light": None, "dup": None, "vehicle": None, "valid": None, "state_code": None, "state": "Unknown"},
            {"status": ImageStatus.PROCESSING, "blurry": None, "low_light": None, "dup": None, "vehicle": None, "valid": None, "state_code": None, "state": "Unknown"},
        ]

        for i, d in enumerate(sample_defs):
            created = datetime.now(timezone.utc) - timedelta(days=len(sample_defs) - i)
            image = Image(
                user_id=user.id,
                filename=f"seed_sample_{i}.jpg",
                file_path=f"/app/uploads/seed_sample_{i}.jpg",
                mime_type="image/jpeg",
                file_size=250_000,
                width=1920, height=1080,
                status=d["status"],
                created_at=created,
                completed_at=created + timedelta(seconds=8) if d["status"] == ImageStatus.COMPLETED else None,
                error_message="Simulated failure: OCR engine timeout" if d["status"] == ImageStatus.FAILED else None,
            )
            db.add(image)
            db.commit()
            db.refresh(image)

            if d["status"] == ImageStatus.COMPLETED:
                analysis = AnalysisResult(
                    image_id=image.id,
                    blur_score=45.0 if d["blurry"] else 245.5,
                    is_blurry=d["blurry"], blur_confidence=0.85,
                    brightness_score=40.0 if d["low_light"] else 132.5,
                    is_low_light=d["low_light"], brightness_confidence=0.85,
                    is_duplicate=d["dup"], duplicate_similarity=0.96 if d["dup"] else None,
                    phash=uuid.uuid4().hex[:16],
                    ocr_text=d["vehicle"] or "", ocr_confidence=0.87 if d["vehicle"] else 0.0,
                    vehicle_number=d["vehicle"], vehicle_number_valid=d["valid"],
                    state_code=d["state_code"], state_name=d["state"],
                    state_confidence=0.9 if d["state_code"] else 0.0,
                    screenshot_detected=False, screenshot_confidence=0.2,
                    photo_of_photo_detected=False, photo_of_photo_confidence=0.15,
                    has_exif=True, camera_make="Samsung", camera_model="Galaxy S21",
                    has_gps=False, tampering_detected=False, tampering_confidence=0.3,
                    aspect_ratio=1.78, dimensions_flagged=False,
                    overall_score="REVIEW_REQUIRED" if any([d["blurry"], d["low_light"], d["dup"]]) else "GOOD",
                )
                db.add(analysis)
                db.commit()

        print("Seed data created successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
