"""
Pusako Schemas
Definisi schema untuk data pajak kendaraan dari PUSAKO Bengkulu
"""
from pydantic import BaseModel, Field
from typing import Optional


class TaxData(BaseModel):
    """Schema untuk data pajak kendaraan"""
    status: bool = Field(..., description="Status data ditemukan")
    nopol: str = Field(..., description="Nomor polisi kendaraan")
    nama: str = Field(..., description="Nama pemilik kendaraan")
    merek: str = Field(..., description="Merek kendaraan")
    model: str = Field(..., description="Model/tipe kendaraan")
    warna: str = Field(..., description="Warna kendaraan")
    warna_plat: str = Field(..., description="Warna plat nomor")
    th_buatan: str = Field(..., description="Tahun pembuatan")
    jumlah_cc: str = Field(..., description="Kapasitas mesin (CC)")
    bbm: str = Field(..., description="Jenis bahan bakar")
    no_rangka: str = Field(..., description="Nomor rangka kendaraan")
    no_mesin: str = Field(..., description="Nomor mesin kendaraan")
    akhir_pkb: str = Field(..., description="Tanggal akhir PKB")
    akhir_stnkb: str = Field(..., description="Tanggal akhir STNK")
    bbn_pok: str = Field(default="", description="BBN Pokok")
    pkb_lama: str = Field(default="0", description="PKB lama")
    denda_pkb_lama: str = Field(default="0", description="Denda PKB lama")
    bea_pkb: str = Field(..., description="Bea PKB")
    denda_bea_pkb: str = Field(default="0", description="Denda bea PKB")
    opsen_pkb: str = Field(..., description="Opsen PKB")
    denda_opsen_pkb: str = Field(default="0", description="Denda opsen PKB")
    pokok_sw: str = Field(..., description="Pokok SWDKLLJ")
    total_tgk_sw: str = Field(default="0", description="Total tunggakan SWDKLLJ")
    total_denda_sw: str = Field(default="0", description="Total denda SWDKLLJ")
    pnbp_bpkb: str = Field(default="", description="PNBP BPKB")
    pnbp_stnk: str = Field(..., description="PNBP STNK")
    pnbp_plat: str = Field(..., description="PNBP Plat nomor")
    jumlah_total: str = Field(..., description="Total pembayaran")


class TaxCheckRequest(BaseModel):
    """Schema untuk request pengecekan pajak"""
    plate_number: str = Field(
        ..., 
        description="Nomor plat kendaraan (contoh: BD 6397 GE)",
        min_length=3,
        max_length=15
    )


class TaxCheckResponse(BaseModel):
    """Schema untuk response pengecekan pajak"""
    status: bool = Field(..., description="Status request berhasil/gagal")
    status_pajak: str = Field(..., description="Status pajak (tahunan/5 tahunan)")
    message: str = Field(default="Success", description="Pesan response")
    data: Optional[TaxData] = Field(None, description="Data pajak kendaraan")


class OCRTaxCheckResponse(BaseModel):
    """Schema untuk response OCR + pengecekan pajak"""
    status: bool = Field(..., description="Status request berhasil/gagal")
    message: str = Field(default="Success", description="Pesan response")
    ocr_result: dict = Field(..., description="Hasil OCR plat nomor")
    tax_data: Optional[TaxCheckResponse] = Field(None, description="Data pajak kendaraan")
