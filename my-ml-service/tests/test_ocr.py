"""
Unit Tests untuk OCR Service
Contoh testing untuk keperluan KP
"""
import pytest
from app.services.model_service import OCRService


class TestOCRService:
    """Test cases untuk OCR Service"""
    
    def test_is_license_plate_valid(self):
        """Test validasi plat nomor yang valid"""
        service = OCRService()
        
        # Test various valid formats
        assert service.is_license_plate("B 1234 XYZ") == True
        assert service.is_license_plate("DK 123 AB") == True
        assert service.is_license_plate("AB 9999 ZZZ") == True
    
    def test_is_license_plate_invalid(self):
        """Test validasi plat nomor yang tidak valid"""
        service = OCRService()
        
        # Test invalid formats
        assert service.is_license_plate("HELLO WORLD") == False
        assert service.is_license_plate("12345") == False
        assert service.is_license_plate("") == False
    
    def test_format_license_plate(self):
        """Test formatting plat nomor"""
        service = OCRService()
        
        # Test formatting
        assert service.format_license_plate("b  1234   xyz") == "B 1234 XYZ"
        assert service.format_license_plate("dk123ab") == "DK123AB"


# Untuk menjalankan test:
# pytest tests/test_ocr.py -v
