"""
Analytics summary + state-wise vehicle analytics endpoints for the dashboard.
"""
import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.image import Image, ImageStatus
from app.models.analysis_result import AnalysisResult
from app.schemas.image import AnalyticsSummary, StateAnalyticsResponse, StateVehicleCount
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def analytics_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    base = db.query(Image).filter(Image.user_id == current_user.id)

    total = base.count()
    completed = base.filter(Image.status == ImageStatus.COMPLETED).count()
    processing = base.filter(Image.status == ImageStatus.PROCESSING).count()
    failed = base.filter(Image.status == ImageStatus.FAILED).count()
    pending = base.filter(Image.status == ImageStatus.PENDING).count()

    analysis_query = (
        db.query(AnalysisResult)
        .join(Image, Image.id == AnalysisResult.image_id)
        .filter(Image.user_id == current_user.id)
    )

    duplicate_count = analysis_query.filter(AnalysisResult.is_duplicate.is_(True)).count()
    blurry_count = analysis_query.filter(AnalysisResult.is_blurry.is_(True)).count()
    low_light_count = analysis_query.filter(AnalysisResult.is_low_light.is_(True)).count()
    suspicious_count = analysis_query.filter(
        (AnalysisResult.tampering_detected.is_(True))
        | (AnalysisResult.photo_of_photo_detected.is_(True))
    ).count()
    ocr_detected_count = analysis_query.filter(
        AnalysisResult.ocr_text.isnot(None), AnalysisResult.ocr_text != ""
    ).count()

    avg_blur_score = db.query(func.avg(AnalysisResult.blur_score)).join(
        Image, Image.id == AnalysisResult.image_id
    ).filter(Image.user_id == current_user.id).scalar()

    avg_processing_seconds = db.query(
        func.avg(func.extract("epoch", Image.completed_at - Image.created_at))
    ).filter(Image.user_id == current_user.id, Image.completed_at.isnot(None)).scalar()

    analyzed_total = completed if completed > 0 else 1  # avoid div by zero for rates

    return AnalyticsSummary(
        total_uploads=total,
        completed=completed,
        processing=processing,
        failed=failed,
        pending=pending,
        duplicate_count=duplicate_count,
        blurry_count=blurry_count,
        low_light_count=low_light_count,
        suspicious_count=suspicious_count,
        success_rate=round(completed / total, 3) if total else 0.0,
        failure_rate=round(failed / total, 3) if total else 0.0,
        avg_processing_time_seconds=round(avg_processing_seconds, 2) if avg_processing_seconds else None,
        avg_blur_score=round(avg_blur_score, 2) if avg_blur_score else None,
        duplicate_rate=round(duplicate_count / analyzed_total, 3),
        low_light_rate=round(low_light_count / analyzed_total, 3),
        ocr_detection_rate=round(ocr_detected_count / analyzed_total, 3),
    )


def _state_counts_query(
    db: Session, current_user: User,
    date_from: Optional[datetime], date_to: Optional[datetime], status_filter: Optional[str],
):
    query = (
        db.query(
            AnalysisResult.state_name,
            AnalysisResult.state_code,
            func.count(AnalysisResult.id).label("count"),
        )
        .join(Image, Image.id == AnalysisResult.image_id)
        .filter(Image.user_id == current_user.id)
        .filter(AnalysisResult.vehicle_number.isnot(None))
    )
    if date_from:
        query = query.filter(Image.created_at >= date_from)
    if date_to:
        query = query.filter(Image.created_at <= date_to)
    if status_filter:
        query = query.filter(Image.status == status_filter)

    return query.group_by(AnalysisResult.state_name, AnalysisResult.state_code)


@router.get("/state-wise", response_model=StateAnalyticsResponse)
def state_wise_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """State-wise Vehicle Analysis: count of successfully OCR'd + format-valid
    vehicle numbers grouped by REGISTRATION state (not current location).
    """
    rows = _state_counts_query(db, current_user, date_from, date_to, status_filter).all()

    by_state = sorted(
        [StateVehicleCount(state=r.state_name or "Unknown", state_code=r.state_code, count=r.count) for r in rows],
        key=lambda x: x.count, reverse=True,
    )

    total_detected = sum(item.count for item in by_state)
    top = by_state[0] if by_state else None

    return StateAnalyticsResponse(
        total_vehicles_detected=total_detected,
        top_state=top.state if top else None,
        top_state_count=top.count if top else 0,
        by_state=by_state,
    )


@router.get("/state-wise/export")
def export_state_analytics_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """Downloads the state-wise vehicle counts as a CSV file."""
    rows = _state_counts_query(db, current_user, date_from, date_to, status_filter).all()
    sorted_rows = sorted(rows, key=lambda r: r.count, reverse=True)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["state", "vehicle_count"])
    for r in sorted_rows:
        writer.writerow([r.state_name or "Unknown", r.count])
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=state_analysis.csv"},
    )
