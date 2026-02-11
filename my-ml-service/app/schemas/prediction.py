"""
Prediction Schemas
Mendefinisikan request dan response models menggunakan Pydantic
"""
from pydantic import BaseModel, Field
from typing import Union, List, Dict, Optional, Any
from datetime import datetime


class PlateData(BaseModel):
    """Model untuk data plat nomor terdeteksi"""
    plat: str = Field(..., description="Nomor plat kendaraan")
    confidence: float = Field(..., description="Tingkat kepercayaan deteksi (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "plat": "B 1234 XYZ",
                "confidence": 0.95
            }
        }


class PredictionResponse(BaseModel):
    """
    Model response untuk endpoint /predict
    Format sederhana sesuai kebutuhan
    """
    success: bool = Field(..., description="Status keberhasilan prediksi")
    message: str = Field(..., description="Pesan hasil prediksi")
    timestamp: str = Field(..., description="Waktu prediksi dalam format ISO")
    data: Union[PlateData, List] = Field(..., description="Data plat nomor atau list kosong jika tidak terdeteksi")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Plat nomor berhasil dideteksi",
                "timestamp": "2026-01-21T10:28:43.685509",
                "data": {
                    "plat": "B 1234 XYZ",
                    "confidence": 0.95
                }
            }
        }


class ErrorResponse(BaseModel):
    """
    Model response untuk validation error
    """
    success: bool = Field(default=False, description="Status keberhasilan (selalu False untuk error)")
    message: str = Field(..., description="Pesan error")
    timestamp: str = Field(..., description="Waktu error terjadi")
    error: Dict[str, List[str]] = Field(default={}, description="Detail error per field")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Validation error",
                "timestamp": "2026-01-21T10:28:43.685509",
                "error": {
                    "file": [
                        "File tidak valid",
                        "Format harus JPG/PNG"
                    ]
                }
            }
        }


# ============ PUSAKO Tax Data Schemas ============

class VehicleTaxData(BaseModel):
    """Data pajak kendaraan dari PUSAKO Bengkulu"""
    nopol: str
    nama: str
    merek: str
    model: str
    warna: str
    warna_plat: str
    th_buat: str
    jumlah_cc: str
    bbm: str
    no_rangka: str
    no_mesin: str
    akhir_pkb: str
    akhir_stnkb: str
    bea_pkb: str
    opsen_pkb: str
    pnbp_stnk: str
    pnbp_plat: str
    jumlah_total: str
    
    # Optional fields yang mungkin kosong
    bbn_pok: Optional[str] = ""
    pkb_lama: Optional[str] = "0"
    denda_pkb_lama: Optional[str] = "0"
    denda_bea_pkb: Optional[str] = "0"
    denda_opsen_pkb: Optional[str] = "0"
    pokok_sw: Optional[str] = "0"
    total_tgk_sw: Optional[str] = "0"
    total_denda_sw: Optional[str] = "0"
    pnbp_bpkb: Optional[str] = ""


class TaxCheckRequest(BaseModel):
    """Request untuk check pajak"""
    plate_number: str = Field(..., description="Nomor plat kendaraan (e.g., BD 6397 GE)")


class TaxCheckResponse(BaseModel):
    """Response untuk check pajak"""
    success: bool
    message: str
    timestamp: str
    data: Optional[VehicleTaxData] = None


class CombinedOcrTaxResponse(BaseModel):
    """Response untuk OCR + Tax check combined"""
    success: bool
    message: str
    timestamp: str
    ocr_result: Optional[Dict[str, Any]] = None
    tax_data: Optional[VehicleTaxData] = None
