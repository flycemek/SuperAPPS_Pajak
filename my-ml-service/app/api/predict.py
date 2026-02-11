"""
Predict Routes
Endpoint untuk prediksi OCR plat nomor kendaraan
"""
from fastapi import APIRouter, UploadFile, File, Depends, status
from app.schemas.prediction import PredictionResponse, ErrorResponse
from app.services.model_service import ocr_service
from app.core.security import verify_api_key
from app.core.config import settings
import logging
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    responses={
        200: {"description": "Prediksi berhasil"},
        400: {"model": ErrorResponse, "description": "Request tidak valid"},
        401: {"model": ErrorResponse, "description": "API Key tidak valid"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="OCR Plat Nomor Kendaraan",
    description="Endpoint untuk melakukan OCR pada gambar plat nomor kendaraan"
)
async def predict_license_plate(
    file: UploadFile = File(..., description="File gambar plat nomor (JPG/PNG, max 10MB)"),
    api_key: str = Depends(verify_api_key)
):
    """
    Endpoint untuk prediksi plat nomor kendaraan menggunakan OCR
    
    Args:
        file: File gambar yang diupload (multipart/form-data)
        api_key: API key untuk autentikasi (dari dependency)
        
    Returns:
        PredictionResponse: Hasil prediksi dengan detail plat nomor
        
    Raises:
        HTTPException: Jika terjadi error dalam processing
    """
    try:
        # Log request
        logger.info(f"Menerima request OCR untuk file: {file.filename}")
        
        # Validate content type
        if not file.content_type.startswith('image/'):
            # Return error response dengan format yang konsisten
            return ErrorResponse(
                success=False,
                message="Validation error",
                timestamp=datetime.now().isoformat(),
                error={"file": ["File harus berupa gambar (image/jpeg, image/png)"]}
            )
        
        # Read file
        image_bytes = await file.read()
        
        # Perform OCR (async method)
        result = await ocr_service.perform_ocr(image_bytes)
        
        # Build response sederhana sesuai format yang diminta
        timestamp_iso = datetime.now().isoformat()
        
        if result['license_plate']:
            # Plat nomor terdeteksi - return data dengan plat dan confidence
            response = PredictionResponse(
                success=True,
                message="Plat nomor berhasil dideteksi",
                timestamp=timestamp_iso,
                data={
                    "plat": result['license_plate'],
                    "confidence": result['confidence']
                }
            )
            logger.info(f"OCR berhasil: {result['license_plate']}")
        else:
            # Tidak terdeteksi - return empty list
            response = PredictionResponse(
                success=True,
                message="Tidak ditemukan plat nomor yang valid, namun ada deteksi teks lain",
                timestamp=timestamp_iso,
                data=[]
            )
            logger.warning("Tidak ditemukan plat nomor yang valid dalam gambar")
        
        return response
        
    except ValueError as ve:
        # Validation errors
        logger.error(f"Validation error: {str(ve)}")
        
        # Return error response dengan format yang konsisten
        return ErrorResponse(
            success=False,
            message="Validation error",
            timestamp=datetime.now().isoformat(),
            error={"file": [str(ve)]}
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
        error_messages = [str(e)] if settings.DEBUG else ["Terjadi kesalahan dalam memproses gambar"]
        
        return ErrorResponse(
            success=False,
            message="Server error",
            timestamp=datetime.now().isoformat(),
            error={"server": error_messages}
        )
