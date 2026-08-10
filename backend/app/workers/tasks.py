"""
Celery task(s) that execute the image-analysis pipeline asynchronously.

Concurrency / consistency notes:
- Each task loads its own DB session (never shares one across tasks/threads).
- The Image row is claimed with a status transition (pending -> processing)
  guarded by a WHERE status='pending' filter, so two workers racing on the
  same job can't both "win" and double-process it.
- task_acks_late + task_reject_on_worker_lost (celery_app.py) ensure a task
  is re-queued if its worker process dies mid-job, instead of being silently
  dropped.
"""
import logging
from datetime import datetime, timezone
from app.models import User, Image, ImageStatus, ProcessingJob, AnalysisResult

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models.image import Image, ImageStatus
from app.models.analysis_result import AnalysisResult
from app.models.processing_job import ProcessingJob
from app.analysis.pipeline import run_full_analysis
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 10


@celery_app.task(bind=True, max_retries=MAX_RETRIES)
def process_image_task(self, image_id: str):
    db = SessionLocal()
    try:
        image = db.execute(select(Image).where(Image.id == image_id)).scalar_one_or_none()
        if image is None:
            logger.error("process_image_task: image %s not found", image_id)
            return

        job = ProcessingJob(image_id=image.id, status="processing", started_at=datetime.now(timezone.utc))
        db.add(job)

        # Claim the job atomically: only proceed if still pending, to avoid
        # double-processing under concurrent workers.
        if image.status != ImageStatus.PENDING:
            logger.warning("Image %s already %s, skipping duplicate task", image_id, image.status)
            db.commit()
            return

        image.status = ImageStatus.PROCESSING
        db.commit()

        logger.info("Processing started processing_id=%s", image.processing_id)

        # Build candidate hash list from this user's completed images for
        # duplicate detection.
        prior = db.execute(
            select(AnalysisResult.image_id, AnalysisResult.phash)
            .join(Image, Image.id == AnalysisResult.image_id)
            .where(Image.user_id == image.user_id, Image.id != image.id, AnalysisResult.phash.isnot(None))
        ).all()
        candidate_hashes = [(str(row[0]), row[1]) for row in prior]

        result = run_full_analysis(image.file_path, image.file_size, candidate_hashes)

        analysis = AnalysisResult(
            image_id=image.id,
            blur_score=result["blur"]["score"],
            is_blurry=result["blur"]["is_blurry"],
            blur_confidence=result["blur"]["confidence"],
            brightness_score=result["brightness"]["score"],
            is_low_light=result["brightness"]["is_low_light"],
            brightness_confidence=result["brightness"]["confidence"],
            is_duplicate=result["duplicate"]["is_duplicate"],
            duplicate_of=result["duplicate"]["duplicate_of"],
            duplicate_similarity=result["duplicate"]["similarity"],
            phash=result["phash"],
            ocr_text=result["ocr"]["text"],
            ocr_confidence=result["ocr"]["confidence"],
            vehicle_number=result["vehicle"]["value"],
            vehicle_number_valid=result["vehicle"]["valid_format"],
            state_code=result["state"]["state_code"],
            state_name=result["state"]["state"],
            state_confidence=result["state"]["confidence"],
            screenshot_detected=result["screenshot"]["detected"],
            screenshot_confidence=result["screenshot"]["confidence"],
            photo_of_photo_detected=result["photo_of_photo"]["detected"],
            photo_of_photo_confidence=result["photo_of_photo"]["confidence"],
            has_exif=result["metadata"]["has_exif"],
            camera_make=result["metadata"]["camera_make"],
            camera_model=result["metadata"]["camera_model"],
            exif_datetime=result["metadata"]["exif_datetime"],
            has_gps=result["metadata"]["has_gps"],
            editing_software=result["metadata"]["editing_software"],
            tampering_detected=result["tampering"]["detected"],
            tampering_confidence=result["tampering"]["confidence"],
            aspect_ratio=result["dimensions"]["aspect_ratio"],
            dimensions_flagged=result["dimensions"]["flagged"],
            overall_score=result["overall_score"],
        )
        db.add(analysis)

        image.width = result["width"]
        image.height = result["height"]
        image.status = ImageStatus.COMPLETED
        image.completed_at = datetime.now(timezone.utc)
        image.error_message = None

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)

        db.commit()
        logger.info("Processing completed processing_id=%s", image.processing_id)

    except Exception as exc:
        db.rollback()
        logger.error("Processing failed processing_id=%s error=%s", image_id, exc)

        # Re-fetch in a clean transaction to record the failure.
        image = db.execute(select(Image).where(Image.id == image_id)).scalar_one_or_none()
        if image:
            retry_count = self.request.retries
            is_last_attempt = retry_count >= MAX_RETRIES

            if is_last_attempt:
                image.status = ImageStatus.FAILED
                image.error_message = str(exc)[:1000]
                db.commit()
            else:
                db.commit()
                raise self.retry(exc=exc, countdown=RETRY_BACKOFF_SECONDS * (retry_count + 1))
    finally:
        db.close()
