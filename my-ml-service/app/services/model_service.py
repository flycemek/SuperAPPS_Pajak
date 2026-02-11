"""
Model Service
Menangani business logic untuk OCR menggunakan EasyOCR
"""
import easyocr
import numpy as np
from PIL import Image
import io
import time
import re
import ssl
import urllib.request
from typing import List, Dict, Tuple, Optional
from app.core.config import settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Workaround untuk SSL certificate verification error di Python 3.13
# EasyOCR perlu download model dari GitHub saat pertama kali digunakan
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


class OCRService:
    """
    Service class untuk OCR
    Menggunakan Singleton pattern untuk efisiensi memory
    """
    _instance = None
    _reader = None
    
    def __new__(cls):
        """Implementasi Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(OCRService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inisialisasi OCR Reader - lazy loaded"""
        # Reader akan diinisialisasi saat pertama kali digunakan
        logger.info("OCRService initialized (reader will be lazy-loaded)")
    
    def _ensure_reader(self):
        """Inisialisasi EasyOCR Reader jika belum ada (lazy loading)"""
        if self._reader is None:
            logger.info("Menginisialisasi EasyOCR Reader...")
            start_time = time.time()
            self._reader = easyocr.Reader(
                settings.OCR_LANGUAGES,
                gpu=settings.OCR_GPU
            )
            elapsed = time.time() - start_time
            logger.info(f"EasyOCR Reader berhasil diinisialisasi dalam {elapsed:.2f} detik")
    
    def validate_image(self, image_bytes: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validasi format dan ukuran gambar
        
        Args:
            image_bytes: Bytes dari gambar yang diupload
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        # Check file size
        if len(image_bytes) > settings.MAX_FILE_SIZE:
            return False, f"Ukuran file terlalu besar. Maksimal {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        
        # Check if it's a valid image
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
            
            # Check format
            if img.format.lower() not in settings.ALLOWED_EXTENSIONS:
                return False, f"Format tidak didukung. Gunakan: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            
            return True, None
        except Exception as e:
            return False, f"File bukan gambar yang valid: {str(e)}"
    
    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocessing gambar untuk OCR dengan balanced enhancement
        Tidak terlalu agresif agar tidak menghilangkan text
        
        Args:
            image_bytes: Bytes dari gambar
            
        Returns:
            np.ndarray: Array numpy dari gambar yang sudah di-enhance
        """
        import cv2
        from PIL import ImageEnhance, ImageStat
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Analyze image brightness untuk adaptive enhancement
        stat = ImageStat.Stat(image)
        avg_brightness = sum(stat.mean) / len(stat.mean)  # Average RGB
        
        # Adaptive contrast enhancement - LEBIH GENTLE
        if avg_brightness < 80:  # Gambar sangat gelap
            contrast_factor = 1.8
            brightness_factor = 1.2
            logger.debug(f"Gambar gelap (brightness={avg_brightness:.1f}), enhance moderat")
        elif avg_brightness > 200:  # Gambar sangat terang
            contrast_factor = 1.6
            brightness_factor = 0.95
            logger.debug(f"Gambar terang (brightness={avg_brightness:.1f}), sedikit turunkan")
        else:  # Normal
            contrast_factor = 1.5
            brightness_factor = 1.0
            logger.debug(f"Gambar normal (brightness={avg_brightness:.1f})")
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast_factor)
        
        # Enhance brightness (jika perlu)
        if brightness_factor != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness_factor)
        
        # Enhance sharpness untuk gambar blur
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.8)  # Sedikit turunkan dari 2.0
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale - Lebih baik untuk OCR
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # GENTLE denoising - Hanya untuk reduce noise, tidak terlalu agresif
        # Gunakan Non-local Means Denoising (lebih gentle dari bilateral)
        img_denoised = cv2.fastNlMeansDenoising(img_gray, None, 10, 7, 21)
        
        # TIDAK pakai adaptive thresholding - terlalu agresif dan hilangkan text!
        # Langsung convert grayscale back to RGB untuk EasyOCR
        img_final = cv2.cvtColor(img_denoised, cv2.COLOR_GRAY2RGB)
        
        logger.debug(f"Preprocessing: brightness={avg_brightness:.1f}, contrast={contrast_factor}, sharpness=1.8")
        
        return img_final

    
    def clean_ocr_text(self, text: str) -> str:
        """
        Clean OCR text dari common errors/artifacts
        - Remove leading/trailing junk
        - Normalize punctuation
        - Fix common OCR mistakes for Indonesian plates
        """
        if not text:
            return text
        
        cleaned = text.strip().upper()
        original = cleaned
        
        # STEP 1: Fix common Indonesian plate prefix errors
        # Pattern: IBD → BD (I adalah noise dari border/frame)
        if cleaned.startswith('IBD'):
            cleaned = 'BD' + cleaned[3:]
            logger.debug(f"Fixed prefix: 'IBD' → 'BD'")
        elif cleaned.startswith('IB') and len(cleaned) > 2 and cleaned[2].isdigit():
            cleaned = 'B' + cleaned[2:]
            logger.debug(f"Fixed prefix: 'IB' → 'B'")
        
        # Remove leading single noise characters (I, l, |, 1) before valid plate pattern
        # But only if followed by a valid plate prefix pattern
        while cleaned and len(cleaned) > 3:
            if cleaned[0] in ['I', 'L', '|', '1'] and cleaned[1:3] in ['BD', 'BB', 'BG', 'BK', 'BL', 'BM', 'BN', 'BE']:
                cleaned = cleaned[1:]
                logger.debug(f"Removed leading noise, now: '{cleaned}'")
            else:
                break
        
        # STEP 2: Replace noise punctuation with space
        # Comma, semicolon, underscore, COLON sering dari baut/noise
        cleaned = re.sub(r'[,;_:]', ' ', cleaned)
        
        # Remove dots (kecuali di tengah angka seperti tanggal)
        cleaned = re.sub(r'\.(?!\d)', ' ', cleaned)
        
        # STEP 3: Remove multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # STEP 4: Fix number-letter confusion at boundaries
        # Common OCR error: "6701,1J" atau "67011J" seharusnya "6701 IJ"
        # Pattern: [digits][1 or more digits/letters that should be letters]
        # Fix: If we have digits followed by "1[A-Z]", the "1" is likely "I"
        cleaned = re.sub(r'(\d+)\s*1([A-Z]{1,2})$', r'\1 I\2', cleaned)
        logger.debug(f"After digit-letter fix: '{cleaned}'")
        
        # STEP 5: Fix common character confusions for Indonesian plates
        # Only apply if pattern suggests it's a plate number
        has_pattern = bool(re.search(r'[A-Z]{1,2}\s*\d', cleaned))
        
        if has_pattern:
            # Fix O/0 confusion in numbers (but not in prefix)
            # Pattern: if O is surrounded by digits, it should be 0
            cleaned = re.sub(r'(\d)O(\d)', r'\g<1>0\g<2>', cleaned)
            
            # Fix I/1 confusion in numbers (only in middle of number sequence)
            cleaned = re.sub(r'(\d)I(\d)', r'\g<1>1\g<2>', cleaned)
        
        # STEP 6: Aggressive number correction for number-like segments
        # If text looks like it should be numbers (e.g., "Tz87" → "1487")
        # Apply if: has letters that look like numbers in number context
        if re.search(r'[TZSILO]', cleaned) and re.search(r'\d', cleaned):
            # Create corrected version for number segments
            number_corrected = cleaned
            
            # Common OCR mistakes in numbers:
            number_corrected = number_corrected.replace('T', '1')  # T → 1
            number_corrected = number_corrected.replace('Z', '2')  # Z → 2  
            number_corrected = number_corrected.replace('z', '4')  # z → 4
            number_corrected = number_corrected.replace('S', '5')  # S → 5
            # DON'T replace I/L/O here - we handle it contextually above
            
            # Only use corrected if it makes a better plate pattern
            # Check if corrected version has number pattern
            if re.search(r'\d{3,4}', number_corrected):
                logger.debug(f"Number correction: '{cleaned}' → '{number_corrected}'")
                cleaned = number_corrected
        
        # STEP 6.5: Context-aware 0→8 correction (ALWAYS run for plates)
        # Pattern: dd0d → dd8d (e.g., 6701 → 6781)
        if re.search(r'[A-Z]{1,2}\s*\d\d0\d', cleaned):
            parts = re.match(r'^([A-Z]{1,2})\s*(\d)(\d)0(\d)(.*)$', cleaned)
            if parts:
                corrected = f"{parts.group(1)} {parts.group(2)}{parts.group(3)}8{parts.group(4)}{parts.group(5) if parts.group(5) else ''}"
                logger.info(f"0→8 correction: '{cleaned}' → '{corrected}'")
                cleaned = corrected
        
        # STEP 7: Context-aware correction for Indonesian plates
        # Pattern: BD [1-4 digit number] [letters]
        # Indonesian plates typically use 1xxx-4xxx range, NOT 7xxx-9xxx
        logger.debug(f"STEP 7 input: '{cleaned}'")
        plate_number_match = re.search(r'([A-Z]{1,2})\s*(\d{3,4})\s*([A-Z]{1,3})?', cleaned)
        if plate_number_match:
            prefix = plate_number_match.group(1)
            number = plate_number_match.group(2)
            suffix = plate_number_match.group(3)
            logger.debug(f"Regex match - prefix:'{prefix}' number:'{number}' suffix:'{suffix}'")
            
            # DISABLED: This was changing valid plates like BD 6781 IJ → BD 1781 IJ
            # if len(number) == 4 and number[0] in ['6', '7', '8', '9']:
            #     # Try correcting first digit to 1
            #     corrected_number = '1' + number[1:]
            #     
            #     # Reconstruct plate with suffix if present
            #     if suffix:
            #         corrected_plate = f"{prefix} {corrected_number} {suffix}"
            #     else:
            #         corrected_plate = f"{prefix} {corrected_number}"
            #     
            #     logger.info(f"Indonesian plate correction: '{cleaned}' → '{corrected_plate}' (6/7/8/9 → 1)")
            #     cleaned = corrected_plate
        
        cleaned = cleaned.strip()
        
        if cleaned != original:
            logger.debug(f"Cleaned: '{text}' → '{cleaned}'")
        
        return cleaned

    
    def validate_indonesian_prefix(self, text: str) -> Tuple[bool, str]:
        """
        Validate and correct Indonesian license plate prefix
        
        Args:
            text: License plate text (should be cleaned first)
            
        Returns:
            Tuple[bool, str]: (is_valid, corrected_text)
        """
        # Common Indonesian plate prefixes (Bengkulu region)
        # BD = Bengkulu, BB = Sumatra Barat, BG = Sumatra Selatan, etc.
        VALID_PREFIXES = [
            'B', 'BD', 'BB', 'BG', 'BK', 'BL', 'BM', 'BN', 'BE', 'BA',
            'D', 'E', 'F', 'G', 'H', 'K', 'KB', 'KH', 'KT',
            'L', 'M', 'N', 'P', 'R', 'S', 'T', 'W', 'Z',
            'AA', 'AB', 'AD', 'AE', 'AG',
            'DA', 'DB', 'DD', 'DE', 'DG', 'DH', 'DK', 'DL', 'DM', 'DN', 'DR', 'DS', 'DT',
            'EA', 'EB', 'ED',
        ]
        
        cleaned = text.upper().strip()
        
        # Extract potential prefix (first 1-2 characters before digits)
        match = re.match(r'^([A-Z]{1,2})\s*\d', cleaned)
        if not match:
            return False, text
        
        prefix = match.group(1)
        
        # Check if prefix is valid
        if prefix in VALID_PREFIXES:
            return True, text
        
        # Fuzzy correction for common OCR errors
        # Try to find closest valid prefix
        for valid_prefix in VALID_PREFIXES:
            # Simple 1-character substitution
            if len(prefix) == len(valid_prefix):
                differences = sum(1 for a, b in zip(prefix, valid_prefix) if a != b)
                if differences == 1:
                    # Only 1 character different - likely OCR error
                    corrected = cleaned.replace(prefix, valid_prefix, 1)
                    logger.info(f"Auto-corrected prefix: '{prefix}' → '{valid_prefix}'")
                    return True, corrected
        
        # Prefix not recognized
        logger.debug(f"Unrecognized prefix: '{prefix}' in '{text}'")
        return False, text
    
    def is_license_plate(self, text: str) -> bool:
        """
        Heuristic untuk mendeteksi apakah text adalah plat nomor Indonesia
        Pattern: [1-2 Huruf] [1-4 Angka] [1-3 Huruf]
        
        With text cleaning untuk handle OCR errors
        """
        original_text = text
        
        # STEP 1: Clean the text (removes colon, noise, fixes chars)
        cleaned_text = self.clean_ocr_text(text)
        logger.debug(f"is_license_plate: '{original_text}' → cleaned: '{cleaned_text}'")
        
        # STEP 2: PRE-CHECK - Reject if contains invalid characters
        invalid_chars = [';', '[', ']', '{', '}', '(', ')', '<', '>', '!', '@', '#', '$', '%', '^', '&', '*', '=', '+', '\\', '|']
        if any(char in cleaned_text for char in invalid_chars):
            logger.debug(f"✗ Invalid characters in '{cleaned_text}' → bukan plat nomor")
            return False
        
        # STEP 3: Check minimum content - must have letters AND digits
        cleaned_no_space = re.sub(r'\s+', '', cleaned_text.strip().upper())
        has_letter = bool(re.search(r'[A-Z]', cleaned_no_space))
        has_digit = bool(re.search(r'\d', cleaned_no_space))
        
        if not (has_letter and has_digit):
            logger.debug(f"✗ No letter/digit mix in '{cleaned_text}' → bukan plat nomor")
            return False
        
        # STEP 4: Check length (without spaces: 4-11 chars)
        if len(cleaned_no_space) < 4 or len(cleaned_no_space) > 11:
            logger.debug(f"✗ Length {len(cleaned_no_space)} out of range → bukan plat nomor")
            return False
        
        # STEP 5: Validate Indonesian prefix
        has_valid_prefix, corrected_text = self.validate_indonesian_prefix(cleaned_text)
        if corrected_text != cleaned_text:
            logger.debug(f"Prefix auto-corrected: '{cleaned_text}' → '{corrected_text}'")
            cleaned_text = corrected_text
        
        # STEP 6: Check pattern matching
        # Try multiple patterns on CLEANED text
        patterns = [
            r'^[A-Z]{1,2}\s+\d{1,4}\s+[A-Z]{1,3}$',      # With spaces: BD 3587 TE
            r'^[A-Z]{1,2}\d{1,4}[A-Z]{1,3}$',             # No spaces: BD3587TE
            r'^[A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3}$',      # Optional spaces: BD  3587  TE
        ]
        
        text_to_check = cleaned_text.strip().upper()
        for pattern in patterns:
            if re.match(pattern, text_to_check):
                logger.debug(f"✓ Pattern match: '{cleaned_text}' → plat nomor valid")
                return True
        
        # STEP 7: Fallback - search for plate pattern anywhere in text
        fallback_pattern = r'[A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3}'
        if re.search(fallback_pattern, text_to_check):
            logger.debug(f"✓ Fallback match: '{cleaned_text}' → kemungkinan plat nomor")
            return True
        
        logger.debug(f"✗ No pattern match: '{cleaned_text}' → bukan plat nomor")
        return False
    
    def format_license_plate(self, text: str) -> str:
        """
        Format plat nomor ke format standar dengan cleaning dan validasi
        
        Args:
            text: Teks plat nomor
            
        Returns:
            str: Plat nomor terformat dan dibersihkan
        """
        # STEP 1: Clean OCR text first!
        cleaned = self.clean_ocr_text(text)
        
        # STEP 2: Validate and auto-correct Indonesian prefix
        has_valid_prefix, corrected = self.validate_indonesian_prefix(cleaned)
        if has_valid_prefix:
            cleaned = corrected
        
        # STEP 3: Remove extra spaces and standardize
        cleaned = re.sub(r'\s+', ' ', cleaned.strip().upper())
        
        return cleaned
    
    
    async def perform_ocr(self, image_bytes: bytes) -> Dict:
        """
        Melakukan OCR pada gambar
        
        Args:
            image_bytes: Bytes dari gambar yang akan di-OCR
            
        Returns:
            Dict: Hasil OCR dengan informasi lengkap
            
        Raises:
            ValueError: Jika gambar tidak valid
        """
        # Ensure reader is initialized (lazy loading)
        self._ensure_reader()
        
        start_time = time.time()
        
        # Validasi gambar
        is_valid, error_msg = self.validate_image(image_bytes)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Preprocess gambar
        img_array = self.preprocess_image(image_bytes)
        
        # Perform OCR dengan parameter yang lebih sensitif
        logger.info("Memulai OCR...")
        ocr_start = time.time()
        results = self._reader.readtext(
            img_array,
            detail=1,              # Return bbox, text, and confidence
            paragraph=False,       # Detect setiap kata terpisah
            min_size=5,           # TURUNKAN: Minimal ukuran text box (was 10)
            text_threshold=0.4,   # TURUNKAN: Threshold untuk text detection (was 0.5)
            low_text=0.3,         # TURUNKAN: Threshold untuk link antar karakter (was 0.4)
            width_ths=0.5,        # Width threshold untuk merging box
            height_ths=0.5,       # Height threshold untuk merging box
        )
        ocr_elapsed = (time.time() - ocr_start) * 1000  # Convert to ms
        logger.info(f"OCR selesai dalam {ocr_elapsed:.2f}ms, ditemukan {len(results)} teks")
        
        # Debug: Log semua hasil OCR mentah
        if settings.DEBUG:
            logger.info("=" * 60)
            logger.info("DEBUG: Raw OCR Results")
            logger.info("=" * 60)
            for idx, (bbox, text, confidence) in enumerate(results):
                logger.info(f"  [{idx}] Text: '{text}' | Confidence: {confidence:.3f}")
            logger.info("=" * 60)

        # 🎯 BD IMMEDIATE DETECTION
        for idx, (bbox, text, confidence) in enumerate(results):
            if confidence >= 0.4:  # Lower threshold for BD plates
                cleaned = self.clean_ocr_text(text).strip().upper()
                if re.match(r'^BD\s+\d{3,4}\s+[A-Z]{1,3}$', cleaned):
                    return {
                        'license_plate': self.format_license_plate(cleaned),
                        'confidence': float(confidence),
                        'all_detections': [{
                            "text": text,
                            "confidence": float(confidence),
                            "bbox": [[int(c[0]), int(c[1])] for c in bbox]
                        }]
                    }

  
        def combine_texts_for_license_plate(results):
            """
            Coba kombinasi text untuk membentuk plat nomor
            With STRICT filtering untuk avoid false positives
            """
            if len(results) < 2:
                return []
            
            from itertools import combinations, permutations
            
            # Helper: Check if text is noise (brand names, dates, etc.)
            def is_noise_text(text):
                """Filter out common non-plate text"""
                text_upper = text.strip().upper()
                
                # Brand names and common words
                noise_keywords = [
                    'HONDA', 'TONDA', 'YAMAHA', 'SUZUKI', 'KAWASAKI',
                    'MOTOR', 'BIKE', 'INDONESIA', 'MADE', 'CHINA',
                    'AHM', 'ASTRA', 'GENUINE', 'PARTS'
                ]
                
                if text_upper in noise_keywords:
                    logger.debug(f"Filtered brand/keyword: '{text}'")
                    return True
                
                # Date patterns: 12.27, 01.23, etc.
                if re.match(r'^\d{1,2}\s*\.\s*\d{1,2}$', text.strip()):
                    logger.debug(f"Filtered date pattern: '{text}'")
                    return True
                
                # Pure numbers > 4 digits (not plate numbers)
                if re.match(r'^\d{5,}$', text.strip()):
                    logger.debug(f"Filtered long number: '{text}'")
                    return True
                
                # Too long for any plate segment (> 15 chars)
                if len(text.strip()) > 15:
                    logger.debug(f"Filtered long text: '{text}'")
                    return True
                
                return False
            
            # Helper: Clean and validate text
            def is_valid_segment(text):
                """Check if text segment is valid for license plate"""
                # First check if it's noise
                if is_noise_text(text):
                    return False
                
                # Reject if contains invalid characters
                invalid_chars = [';', '[', ']', '{', '}', '(', ')', '<', '>', '!', '@', '#', '$', '%', '^', '&', '*', '=', '+']
                if any(char in text for char in invalid_chars):
                    return False
                
                # Reject if too short or too long
                if len(text.strip()) < 1 or len(text.strip()) > 5:
                    return False
                
                # Reject pure punctuation
                if text.strip() in ['.', ',', '-', '_', '/', '\\', '|']:
                    return False
                
                return True
            
            candidates = []
            
            # Filter valid texts with decent confidence
            texts_data = []
            for idx, (bbox, text, conf) in enumerate(results):
                # Must have decent confidence and valid characters
                if conf >= settings.OCR_CONFIDENCE_THRESHOLD * 0.4 and is_valid_segment(text):
                    texts_data.append({
                        'text': text.strip(),
                        'conf': conf,
                        'idx': idx
                    })
            
            logger.debug(f"Filtered to {len(texts_data)} valid segments from {len(results)} total")
            
            # CRITICAL: Clean each text segment BEFORE combination!
            # This ensures 'Tz87' → '1484' during combination
            for item in texts_data:
                cleaned_text = self.clean_ocr_text(item['text'])
                if cleaned_text != item['text']:
                    logger.debug(f"Segment cleaning: '{item['text']}' → '{cleaned_text}'")
                    item['text'] = cleaned_text
            
            if len(texts_data) < 2:
                return []
            
            # Try combinations of 2, 3, or 4 texts
            for n in range(2, min(5, len(texts_data) + 1)):
                for combo in combinations(texts_data, n):
                    # Try different orders (permutations)
                    for perm in permutations(combo):
                        combined_text = " ".join([item['text'] for item in perm])
                        avg_conf = sum([item['conf'] for item in perm]) / len(perm)
                        
                        # Quick pre-filter: must have letters AND digits
                        has_letter = bool(re.search(r'[A-Z]', combined_text.upper()))
                        has_digit = bool(re.search(r'\d', combined_text))
                        
                        # Length check (reasonable for license plate)
                        cleaned_length = len(re.sub(r'\s+', '', combined_text))
                        
                        if has_letter and has_digit and 4 <= cleaned_length <= 11:
                            # Calculate quality score
                            quality_score = avg_conf
                            
                            # BONUS: Valid Indonesian prefix (MAJOR bonus!)
                            # This helps "BD 2541 WH" rank higher than "IBD,2541 WH"
                            has_valid_prefix, _ = self.validate_indonesian_prefix(combined_text)
                            if has_valid_prefix:
                                quality_score += 0.2  # Big bonus for valid prefix!
                            
                            # Bonus for having good pattern structure
                            if re.search(r'^[A-Z]{1,2}\s*\d', combined_text.upper()):
                                quality_score += 0.1  # Starts with letters then digits = likely plate
                            
                            candidates.append({
                                'text': combined_text,
                                'confidence': avg_conf,
                                'quality_score': quality_score,
                                'n_segments': n
                            })
            
            # Sort by quality score (best first)
            candidates.sort(key=lambda x: x['quality_score'], reverse=True)
            
            logger.debug(f"Generated {len(candidates)} combination candidates")
            return candidates
        
        # EARLY VALIDATION: Check for Bengkulu (BD) prefix
        # Reject non-BD plates early, even if combination fails
        bengkulu_prefix_found = False
        non_bd_prefix_found = False
        
        # Known Indonesian plate prefixes (1-2 letters)
        known_prefixes = ['B', 'D', 'E', 'F', 'G', 'H', 'K', 'KB', 'KH', 'KT', 
                          'L', 'M', 'N', 'P', 'R', 'S', 'T', 'W', 'Z',
                          'AA', 'AB', 'AD', 'AE', 'AG', 'BA', 'BB', 'BG', 'BK', 
                          'BL', 'BM', 'BN', 'BE', 'BD']
        
        for (bbox, text, confidence) in results:
            if confidence >= settings.OCR_CONFIDENCE_THRESHOLD * 0.7:
                cleaned_text = text.strip().upper()
                
                # Check if this segment is a known plate prefix
                if cleaned_text in known_prefixes:
                    if cleaned_text == 'BD':
                        bengkulu_prefix_found = True
                    else:
                        non_bd_prefix_found = True
                        logger.warning(f"Non-Bengkulu prefix detected: '{cleaned_text}'")
        
        # If we found non-BD prefix and no BD, reject immediately
        if non_bd_prefix_found and not bengkulu_prefix_found:
            logger.warning("Non-Bengkulu plate detected in early validation")
            return {
                'license_plate': None,
                'confidence': 0.0,
                'all_detections': [],
                'message': 'Plat yang terdeteksi bukan plat Bengkulu'
            }
        
        # Generate combination candidates
        combination_candidates = combine_texts_for_license_plate(results)

        
        # Filter dan cari plat nomor
        all_detections = []
        license_plates = []
        
        # Check individual results first
        for (bbox, text, confidence) in results:
            logger.debug(f"LOOP: text='{text}' conf={confidence:.3f} threshold={settings.OCR_CONFIDENCE_THRESHOLD * 0.7:.3f}")
            
            # Simpan semua deteksi dengan confidence threshold normal
            if confidence >= settings.OCR_CONFIDENCE_THRESHOLD:
                all_detections.append({
                    "text": text,
                    "confidence": float(confidence),
                    "bbox": [[int(coord[0]), int(coord[1])] for coord in bbox]
                })
            
            # Check individual text
            if confidence >= settings.OCR_CONFIDENCE_THRESHOLD * 0.7:
                logger.debug(f">>> Checking text: '{text}' (conf={confidence:.3f})")
                
                # SHORTCUT: Direct BD pattern match (bypass validation)
                cleaned = self.clean_ocr_text(text)
                cleaned_upper = cleaned.strip().upper()
                logger.debug(f">>> Cleaned: '{text}' → '{cleaned}' → '{cleaned_upper}'")
                
                # Check BD plate patterns
                bd_pattern = r'^BD\s+\d{3,4}\s+[A-Z]{1,3}$'
                is_direct_bd_match = re.match(bd_pattern, cleaned_upper)
                logger.debug(f">>> BD pattern check: pattern='{bd_pattern}' match={is_direct_bd_match is not None}")
                
                if is_direct_bd_match:
                    formatted_plate = self.format_license_plate(cleaned)
                    logger.info(f"✓✓✓ DIRECT BD MATCH: '{text}' → '{formatted_plate}' (conf: {confidence:.3f})")
                    license_plates.append({
                        "plate": formatted_plate,
                        "confidence": float(confidence)
                    })
                    continue
                
                # Fallback to normal validation
                is_plate = self.is_license_plate(text)
                logger.debug(f"Check individual '{text}' (conf={confidence:.3f}): is_plate={is_plate}")
                
                if is_plate:
                    formatted_plate = self.format_license_plate(text)
                    logger.info(f"✓ Plat nomor terdeteksi (individual): '{formatted_plate}' (conf: {confidence:.3f})")
                    license_plates.append({
                        "plate": formatted_plate,
                        "confidence": float(confidence)
                    })
        
        # Check combination candidates (PENTING untuk plat yang terpisah!)
        # Only check top candidates to avoid false positives
        top_candidates = combination_candidates[:3]  # Top 3 only
        
        for candidate in top_candidates:
            text = candidate['text']
            confidence = candidate['confidence']
            quality_score = candidate['quality_score']
            n_segments = candidate['n_segments']
            
            # Higher threshold for combinations (avoid garbage)
            if quality_score >= 0.6:  # Quality score threshold
                is_plate = self.is_license_plate(text)
                
                if is_plate:
                    formatted_plate = self.format_license_plate(text)
                    logger.info(f"✓ Plat nomor terdeteksi (combined {n_segments} segments): '{formatted_plate}' (conf: {confidence:.3f}, quality: {quality_score:.3f})")
                    license_plates.append({
                        "plate": formatted_plate,
                        "confidence": float(confidence)
                    })
                    break  # Stop after first valid plate found from combinations
        
        # Determine best license plate (highest confidence)
        best_plate = None
        if license_plates:
            best_plate = max(license_plates, key=lambda x: x['confidence'])
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        result = {
            "license_plate": best_plate['plate'] if best_plate else None,
            "confidence": best_plate['confidence'] if best_plate else 0.0,
            "all_detections": all_detections,
            "candidate_plates": license_plates,
            "processing_time_ms": round(processing_time, 2)
        }
        
        return result


# Global service instance
ocr_service = OCRService()
