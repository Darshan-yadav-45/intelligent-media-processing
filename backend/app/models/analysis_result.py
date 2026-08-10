import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"),
                       unique=True, nullable=False, index=True)

    blur_score = Column(Float, nullable=True)
    is_blurry = Column(Boolean, nullable=True)
    blur_confidence = Column(Float, nullable=True)

    brightness_score = Column(Float, nullable=True)
    is_low_light = Column(Boolean, nullable=True)
    brightness_confidence = Column(Float, nullable=True)

    is_duplicate = Column(Boolean, nullable=True)
    duplicate_of = Column(UUID(as_uuid=True), nullable=True)
    duplicate_similarity = Column(Float, nullable=True)
    phash = Column(String(64), nullable=True, index=True)

    ocr_text = Column(String(2000), nullable=True)
    ocr_confidence = Column(Float, nullable=True)

    vehicle_number = Column(String(20), nullable=True, index=True)
    vehicle_number_valid = Column(Boolean, nullable=True)

    # Registration state derived from the vehicle number's prefix.
    # This identifies where the plate was REGISTERED, not the vehicle's
    # current physical location - see app/analysis/vehicle_state_codes.py.
    state_code = Column(String(4), nullable=True, index=True)
    state_name = Column(String(80), nullable=True, index=True)
    state_confidence = Column(Float, nullable=True)

    screenshot_detected = Column(Boolean, nullable=True)
    screenshot_confidence = Column(Float, nullable=True)

    photo_of_photo_detected = Column(Boolean, nullable=True)
    photo_of_photo_confidence = Column(Float, nullable=True)

    has_exif = Column(Boolean, nullable=True)
    camera_make = Column(String(100), nullable=True)
    camera_model = Column(String(100), nullable=True)
    exif_datetime = Column(String(50), nullable=True)
    has_gps = Column(Boolean, nullable=True)
    editing_software = Column(String(200), nullable=True)

    tampering_detected = Column(Boolean, nullable=True)
    tampering_confidence = Column(Float, nullable=True)

    aspect_ratio = Column(Float, nullable=True)
    dimensions_flagged = Column(Boolean, nullable=True)

    overall_score = Column(String(30), nullable=True)  # "GOOD" | "REVIEW_REQUIRED"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    image = relationship("Image", back_populates="analysis_result")

    __table_args__ = (
        Index("ix_analysis_state_code_name", "state_code", "state_name"),
    )
