"""
PUSAKO Tax Check API Endpoints
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
import logging

from app.schemas.pusako import TaxCheckRequest
from app.services.pusako_service import pusako_service
from app.services.model_service import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/check-tax")
async def check_tax(request: TaxCheckRequest):
    """
    Check data pajak kendaraan dari PUSAKO Bengkulu
    
    Args:
        request: TaxCheckRequest dengan plate_number
    
    Returns:
        TaxCheckResponse dengan data pajak
    
    Example:
        ```
        POST /api/v1/check-tax
        {
            "plate_number": "BD 6397 GE"
        }
        
        Response:
        {
            "tax_data": {
                "status": true,
                "status_pajak": "tahunan",
                "message": "Data pajak berhasil diambil",
                "data": { ... }
            }
        }
        ```
    """
    try:
        logger.info(f"Checking tax for plate: {request.plate_number}")
        
        # Call scraping service
        result = await pusako_service.get_tax_info(request.plate_number)
        
        # Simplify and filter response data
        simplified_data = None
        if result['status'] and result['data']:
            data = result['data']
            simplified_data = {
                'status': data.get('status', True),
                'nopol': data.get('nopol', '').strip(),
                'nama': data.get('nama', '').strip(),
                'merek': data.get('merek', '').strip(),
                'model': data.get('model', '').strip(),
                'warna': data.get('warna', '').strip(),
                'warna_plat': data.get('warna_plat', '').strip(),
                'th_buatan': data.get('th_buatan', '').strip(),
                'jumlah_cc': data.get('jumlah_cc', '').strip(),
                'bbm': data.get('bbm', '').strip(),
                'no_rangka': data.get('no_rangka', '').strip(),
                'no_mesin': data.get('no_mesin', '').strip(),
                'akhir_pkb': data.get('akhir_pkb', '').strip(),
                'akhir_stnkb': data.get('akhir_stnkb', '').strip(),
                'bbn_pok': data.get('bbn_pok', '').strip(),
                'pkb_lama': data.get('pkb_lama', '0').strip(),
                'denda_pkb_lama': data.get('denda_pkb_lama', '0').strip(),
                'bea_pkb': data.get('bea_pkb', '0').strip(),
                'denda_bea_pkb': data.get('denda_bea_pkb', '0').strip(),
                'opsen_pkb': data.get('opsen_pkb', '0').strip(),
                'denda_opsen_pkb': data.get('denda_opsen_pkb', '0').strip(),
                'pokok_sw': data.get('pokok_sw', '0').strip(),
                'total_tgk_sw': data.get('total_tgk_sw', '0').strip(),
                'total_denda_sw': data.get('total_denda_sw', '0').strip(),
                'pnbp_bpkb': data.get('pnbp_bpkb', '').strip(),
                'pnbp_stnk': data.get('pnbp_stnk', '0').strip(),
                'pnbp_plat': data.get('pnbp_plat', '0').strip(),
                'jumlah_total': data.get('jumlah_total', '0').strip()
            }
        
        # Prepare response with tax_data wrapper
        response = {
            'tax_data': {
                'status': result['status'],
                'status_pajak': result['status_pajak'],
                'message': result['message'],
                'data': simplified_data
            }
        }
        
        logger.info(f"Tax check result: {result['status']}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in check_tax: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/ocr-and-check-tax")
async def ocr_and_check_tax(file: UploadFile = File(...)):
    """
    Combined OCR + Tax Check:
    1. Upload foto plat nomor
    2. OCR untuk extract plat
    3. Automatic fetch data pajak dari PUSAKO
    
    Args:
        file: Image file (jpg, jpeg, png)
    
    Returns:
        Simplified tax_data response dengan data pajak
    
    Example:
        ```
        POST /api/v1/ocr-and-check-tax
        Content-Type: multipart/form-data
        file: <image file>
        ```
    """
    try:
        logger.info(f"OCR + Tax check for file: {file.filename}")
        
        # Step 1: Read file
        image_bytes = await file.read()
        
        # Step 2: OCR (async method)
        ocr_result = await ocr_service.perform_ocr(image_bytes)
        
        # Step 3: Check if plate detected
        if not ocr_result.get('license_plate'):
            logger.warning("No plate detected from OCR")
            
            # Check if there's a specific message (e.g., non-BD plate)
            specific_message = ocr_result.get('message', 'Tidak dapat mendeteksi plat nomor dari gambar')
            
            return {
                'tax_data': {
                    'status': False,
                    'status_pajak': '',
                    'message': specific_message,
                    'data': None
                }
            }
        
        plate_number = ocr_result['license_plate']
        logger.info(f"Plate detected: {plate_number}")
        
        # Step 3.5: Validate Bengkulu (BD) prefix
        # Remove spaces and get prefix
        plate_prefix = plate_number.strip().upper().replace(' ', '')[:2]
        
        if plate_prefix != 'BD':
            logger.warning(f"Non-Bengkulu plate detected: {plate_number} (prefix: {plate_prefix})")
            return {
                'tax_data': {
                    'status': False,
                    'status_pajak': '',
                    'message': 'Plat yang terdeteksi bukan plat Bengkulu',
                    'data': None
                }
            }
        
        # Step 4: Fetch tax data
        tax_result = await pusako_service.get_tax_info(plate_number)
        
        # Step 5: Prepare simplified tax data
        simplified_tax_data = None
        if tax_result['status'] and tax_result['data']:
            data = tax_result['data']
            simplified_tax_data = {
                'status': data.get('status', True),
                'nopol': data.get('nopol', '').strip(),
                'nama': data.get('nama', '').strip(),
                'merek': data.get('merek', '').strip(),
                'model': data.get('model', '').strip(),
                'warna': data.get('warna', '').strip(),
                'warna_plat': data.get('warna_plat', '').strip(),
                'th_buatan': data.get('th_buatan', '').strip(),
                'jumlah_cc': data.get('jumlah_cc', '').strip(),
                'bbm': data.get('bbm', '').strip(),
                'no_rangka': data.get('no_rangka', '').strip(),
                'no_mesin': data.get('no_mesin', '').strip(),
                'akhir_pkb': data.get('akhir_pkb', '').strip(),
                'akhir_stnkb': data.get('akhir_stnkb', '').strip(),
                'bbn_pok': data.get('bbn_pok', '').strip(),
                'pkb_lama': data.get('pkb_lama', '0').strip(),
                'denda_pkb_lama': data.get('denda_pkb_lama', '0').strip(),
                'bea_pkb': data.get('bea_pkb', '0').strip(),
                'denda_bea_pkb': data.get('denda_bea_pkb', '0').strip(),
                'opsen_pkb': data.get('opsen_pkb', '0').strip(),
                'denda_opsen_pkb': data.get('denda_opsen_pkb', '0').strip(),
                'pokok_sw': data.get('pokok_sw', '0').strip(),
                'total_tgk_sw': data.get('total_tgk_sw', '0').strip(),
                'total_denda_sw': data.get('total_denda_sw', '0').strip(),
                'pnbp_bpkb': data.get('pnbp_bpkb', '').strip(),
                'pnbp_stnk': data.get('pnbp_stnk', '0').strip(),
                'pnbp_plat': data.get('pnbp_plat', '0').strip(),
                'jumlah_total': data.get('jumlah_total', '0').strip()
            }
        
        # Step 6: Build simplified combined response
        response = {
            'tax_data': {
                'status': tax_result['status'],
                'status_pajak': tax_result['status_pajak'],
                'message': tax_result['message'],
                'data': simplified_tax_data
            }
        }
        
        logger.info(f"Combined result - OCR: {plate_number}, Tax: {tax_result['status']}")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in ocr_and_check_tax: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
