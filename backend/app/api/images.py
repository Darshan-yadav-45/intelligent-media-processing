"""
Image upload, status, result, retry, list, delete endpoints.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.image import Image, ImageStatus
from app.models.analysis_result import AnalysisResult
from app.models.processing_job import ProcessingJob
from app.schemas.image import (
    UploadResponse, StatusResponse, ResultResponse, FailureResponse,
    ImageInfo, AnalysisPayload, BlurResult, BrightnessResult, DuplicateResult,
    OcrResult, VehicleNumberResult, VehicleStateResult, VehicleDetailResponse,
    ScreenshotResult, PhotoOfPhotoResult,
    TamperingResult, MetadataResult, ImageListResponse, ImageListItem,
)
from app.api.deps import get_current_user
from app.utils.files import (
    sanitize_and_build_path, validate_upload_size, validate_mime_type,
    validate_actual_image_content,
)
from app.workers.tasks import process_image_task
from app.config import get_settings
from app.rate_limit import limiter

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(settings.upload_rate_limit)
def upload_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_mime_type(file.content_type)
    size = validate_upload_size(file)
    file_bytes = file.file.read()
    validate_actual_image_content(file_bytes)

    safe_filename, absolute_path = sanitize_and_build_path(file.filename or "upload", file.content_type)
    with open(absolute_path, "wb") as f:
        f.write(file_bytes)

    image = Image(
        user_id=current_user.id,
        filename=safe_filename,
        file_path=absolute_path,
        mime_type=file.content_type,
        file_size=size,
        status=ImageStatus.PENDING,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    logger.info("Image uploaded processing_id=%s user_id=%s", image.processing_id, current_user.id)

    # Enqueue background processing; API returns immediately.
    process_image_task.delay(str(image.id))

    return UploadResponse(
        processing_id=image.processing_id,
        status=image.status,
        message="Image uploaded successfully",
    )


def _get_image_or_404(db: Session, processing_id: UUID, user: User) -> Image:
    image = db.execute(
        select(Image).where(Image.processing_id == processing_id, Image.user_id == user.id)
    ).scalar_one_or_none()
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    return image


@router.get("/{processing_id}/status", response_model=StatusResponse)
def get_status(processing_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = _get_image_or_404(db, processing_id, current_user)
    latest_job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.image_id == image.id)
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )
    return StatusResponse(
        processing_id=image.processing_id,
        status=image.status,
        retry_count=latest_job.retry_count if latest_job else 0,
        error_message=image.error_message,
    )


def _build_analysis_payload(analysis: AnalysisResult) -> AnalysisPayload:
    return AnalysisPayload(
        blur=BlurResult(score=analysis.blur_score, is_blurry=analysis.is_blurry, confidence=analysis.blur_confidence),
        brightness=BrightnessResult(
            score=analysis.brightness_score, is_low_light=analysis.is_low_light,
            confidence=analysis.brightness_confidence,
        ),
        duplicate=DuplicateResult(
            is_duplicate=analysis.is_duplicate, duplicate_of=analysis.duplicate_of,
            similarity=analysis.duplicate_similarity,
        ),
        ocr=OcrResult(text=analysis.ocr_text, confidence=analysis.ocr_confidence),
        vehicle_number=VehicleNumberResult(value=analysis.vehicle_number, valid_format=analysis.vehicle_number_valid),
        vehicle_state=VehicleStateResult(
            state_code=analysis.state_code, state=analysis.state_name or "Unknown",
            confidence=analysis.state_confidence or 0.0,
        ),
        screenshot=ScreenshotResult(detected=analysis.screenshot_detected, confidence=analysis.screenshot_confidence),
        photo_of_photo=PhotoOfPhotoResult(
            detected=analysis.photo_of_photo_detected, confidence=analysis.photo_of_photo_confidence,
        ),
        tampering=TamperingResult(detected=analysis.tampering_detected, confidence=analysis.tampering_confidence),
        metadata=MetadataResult(
            has_exif=analysis.has_exif, camera_make=analysis.camera_make, camera_model=analysis.camera_model,
            exif_datetime=analysis.exif_datetime, has_gps=analysis.has_gps, editing_software=analysis.editing_software,
        ),
        overall_score=analysis.overall_score,
    )


@router.get("/{processing_id}/result", response_model=ResultResponse)
def get_result(processing_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = _get_image_or_404(db, processing_id, current_user)

    image_info = ImageInfo(
        filename=image.filename, width=image.width, height=image.height,
        file_size=image.file_size, mime_type=image.mime_type,
    )

    analysis_payload = None
    if image.status == ImageStatus.COMPLETED and image.analysis_result:
        analysis_payload = _build_analysis_payload(image.analysis_result)

    return ResultResponse(
        processing_id=image.processing_id, status=image.status,
        image=image_info, analysis=analysis_payload,
    )


@router.get("/{processing_id}/vehicle", response_model=VehicleDetailResponse)
def get_vehicle_detail(processing_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns the detected vehicle number plus its REGISTRATION state
    (not the vehicle's current physical location - see VehicleDetailResponse).
    """
    image = _get_image_or_404(db, processing_id, current_user)
    analysis = image.analysis_result

    if not analysis or not analysis.vehicle_number:
        return VehicleDetailResponse(
            vehicle_number=None, valid_format=False,
            state_code=None, state="Unknown", confidence=0.0,
        )

    return VehicleDetailResponse(
        vehicle_number=analysis.vehicle_number,
        valid_format=bool(analysis.vehicle_number_valid),
        state_code=analysis.state_code,
        state=analysis.state_name or "Unknown",
        confidence=analysis.state_confidence or 0.0,
    )


@router.get("/{processing_id}/failure", response_model=FailureResponse)
def get_failure(processing_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = _get_image_or_404(db, processing_id, current_user)
    latest_job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.image_id == image.id)
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )
    return FailureResponse(
        processing_id=image.processing_id, status=image.status,
        retry_count=latest_job.retry_count if latest_job else 0,
        last_error=image.error_message or (latest_job.last_error if latest_job else None),
    )


@router.post("/{processing_id}/retry", response_model=UploadResponse)
def retry_image(processing_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = _get_image_or_404(db, processing_id, current_user)
    if image.status != ImageStatus.FAILED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only failed jobs can be retried")

    image.status = ImageStatus.PENDING
    image.error_message = None
    db.commit()

    process_image_task.delay(str(image.id))
    logger.info("Retry triggered processing_id=%s", image.processing_id)

    return UploadResponse(processing_id=image.processing_id, status=image.status, message="Retry queued")


@router.get("", response_model=ImageListResponse)
def list_images(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    state: Optional[str] = Query(None, description="Filter by registration state name, or 'Unknown'"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    query = db.query(Image).filter(Image.user_id == current_user.id)
    if status_filter:
        query = query.filter(Image.status == status_filter)
    if search:
        query = query.filter(Image.filename.ilike(f"%{search}%"))
    if date_from:
        query = query.filter(Image.created_at >= date_from)
    if date_to:
        query = query.filter(Image.created_at <= date_to)
    if state and state.lower() != "all":
        query = query.join(AnalysisResult, AnalysisResult.image_id == Image.id)
        if state.lower() == "unknown":
            query = query.filter((AnalysisResult.state_name.is_(None)) | (AnalysisResult.state_name == "Unknown"))
        else:
            query = query.filter(AnalysisResult.state_name == state)

    total = query.count()
    images = (
        query.order_by(Image.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for img in images:
        analysis = img.analysis_result
        items.append(ImageListItem(
            processing_id=img.processing_id, filename=img.filename, status=img.status,
            created_at=img.created_at,
            vehicle_number=analysis.vehicle_number if analysis else None,
            is_blurry=analysis.is_blurry if analysis else None,
            is_duplicate=analysis.is_duplicate if analysis else None,
            is_low_light=analysis.is_low_light if analysis else None,
            state_code=analysis.state_code if analysis else None,
            state_name=analysis.state_name if analysis else None,
        ))

    return ImageListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/{processing_id}", response_model=ResultResponse)
def get_image(processing_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_result(processing_id, db, current_user)


@router.delete("/{processing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(processing_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import os
    image = _get_image_or_404(db, processing_id, current_user)

    if os.path.exists(image.file_path):
        try:
            os.remove(image.file_path)
        except OSError as exc:
            logger.warning("Could not remove file %s: %s", image.file_path, exc)

    db.delete(image)
    db.commit()
    logger.info("Image deleted processing_id=%s", processing_id)
    return None
