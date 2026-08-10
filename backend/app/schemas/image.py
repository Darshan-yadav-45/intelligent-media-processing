from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class UploadResponse(BaseModel):
    processing_id: UUID
    status: str
    message: str


class StatusResponse(BaseModel):
    processing_id: UUID
    status: str
    retry_count: int = 0
    error_message: Optional[str] = None


class BlurResult(BaseModel):
    score: Optional[float] = None
    is_blurry: Optional[bool] = None
    confidence: Optional[float] = None


class BrightnessResult(BaseModel):
    score: Optional[float] = None
    is_low_light: Optional[bool] = None
    confidence: Optional[float] = None


class DuplicateResult(BaseModel):
    is_duplicate: Optional[bool] = None
    duplicate_of: Optional[UUID] = None
    similarity: Optional[float] = None


class OcrResult(BaseModel):
    text: Optional[str] = None
    confidence: Optional[float] = None


class VehicleNumberResult(BaseModel):
    value: Optional[str] = None
    valid_format: Optional[bool] = None


class VehicleStateResult(BaseModel):
    state_code: Optional[str] = None
    state: Optional[str] = "Unknown"
    confidence: Optional[float] = 0.0


class VehicleDetailResponse(BaseModel):
    """Response for GET /api/images/{processing_id}/vehicle.
    'state' here is the plate's REGISTRATION state, not the vehicle's
    current physical location.
    """
    vehicle_number: Optional[str] = None
    valid_format: bool = False
    state_code: Optional[str] = None
    state: str = "Unknown"
    confidence: float = 0.0


class ScreenshotResult(BaseModel):
    detected: Optional[bool] = None
    confidence: Optional[float] = None


class PhotoOfPhotoResult(BaseModel):
    detected: Optional[bool] = None
    confidence: Optional[float] = None


class TamperingResult(BaseModel):
    detected: Optional[bool] = None
    confidence: Optional[float] = None


class MetadataResult(BaseModel):
    has_exif: Optional[bool] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    exif_datetime: Optional[str] = None
    has_gps: Optional[bool] = None
    editing_software: Optional[str] = None


class AnalysisPayload(BaseModel):
    blur: BlurResult
    brightness: BrightnessResult
    duplicate: DuplicateResult
    ocr: OcrResult
    vehicle_number: VehicleNumberResult
    vehicle_state: VehicleStateResult
    screenshot: ScreenshotResult
    photo_of_photo: PhotoOfPhotoResult
    tampering: TamperingResult
    metadata: MetadataResult
    overall_score: Optional[str] = None


class ImageInfo(BaseModel):
    filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: int
    mime_type: str


class ResultResponse(BaseModel):
    processing_id: UUID
    status: str
    image: ImageInfo
    analysis: Optional[AnalysisPayload] = None


class FailureResponse(BaseModel):
    processing_id: UUID
    status: str
    retry_count: int
    last_error: Optional[str] = None


class ImageListItem(BaseModel):
    processing_id: UUID
    filename: str
    status: str
    created_at: datetime
    vehicle_number: Optional[str] = None
    is_blurry: Optional[bool] = None
    is_duplicate: Optional[bool] = None
    is_low_light: Optional[bool] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None

    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ImageListItem]


class AnalyticsSummary(BaseModel):
    total_uploads: int
    completed: int
    processing: int
    failed: int
    pending: int
    duplicate_count: int
    blurry_count: int
    low_light_count: int
    suspicious_count: int
    success_rate: float
    failure_rate: float
    avg_processing_time_seconds: Optional[float] = None
    avg_blur_score: Optional[float] = None
    duplicate_rate: float
    low_light_rate: float
    ocr_detection_rate: float


class StateVehicleCount(BaseModel):
    state: str
    state_code: Optional[str] = None
    count: int


class StateAnalyticsResponse(BaseModel):
    total_vehicles_detected: int
    top_state: Optional[str] = None
    top_state_count: int = 0
    by_state: List[StateVehicleCount]
