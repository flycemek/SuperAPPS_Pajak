"""
PUSAKO Bengkulu Web Scraping Service
Mengambil data pajak kendaraan dari website PUSAKO
"""

import requests
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from bs4 import BeautifulSoup
import re
import time
import logging
from typing import Optional, Dict, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

class TLSAdapter(HTTPAdapter):
    """
    Adapter untuk menangani SSL legacy/insecure tanpa error verify_mode
    """
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        # Allow weaker ciphers
        ctx.set_ciphers('DEFAULT@SECLEVEL=1') 
        
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx
        )

class PusakoService:
    """
    Service untuk scraping data pajak dari website PUSAKO Bengkulu
    """
    
    def __init__(self):
        self.base_url = settings.PUSAKO_BASE_URL
        self.timeout = settings.PUSAKO_TIMEOUT
        self.max_retries = settings.PUSAKO_MAX_RETRIES
        self.rate_limit_delay = settings.PUSAKO_RATE_LIMIT_DELAY
        self.last_request_time = 0
        
        # Headers dasar
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
        }
    
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _parse_plate_number(self, plate_number: str) -> Tuple[str, str, str]:
        """
        Parse plat nomor menjadi components
        Input: "BD 6397 GE" atau "BD6397GE"
        Output: ("BD", "6397", "GE")
        """
        # Remove spaces and uppercase
        cleaned = re.sub(r'\s+', '', plate_number.strip().upper())
        
        # Pattern: [1-2 huruf][angka][1-3 huruf]
        pattern = r'^([A-Z]{1,2})(\d{1,4})([A-Z]{1,3})$'
        match = re.match(pattern, cleaned)
        
        if not match:
            raise ValueError(f"Format plat nomor tidak valid: {plate_number}")
        
        kode_wilayah_prefix = match.group(1)  # BD
        nomor = match.group(2)  # 6397
        kode_wilayah_suffix = match.group(3)  # GE
        
        logger.debug(f"Parsed plate: {kode_wilayah_prefix} {nomor} {kode_wilayah_suffix}")
        
        return kode_wilayah_prefix, nomor, kode_wilayah_suffix
    
    def _get_session(self) -> requests.Session:
        """Create configured session"""
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        session.headers.update(self.headers)
        return session

    def _fetch_csrf_token(self, session: requests.Session) -> Tuple[str, str, str]:
        """
        Fetch CSRF token dan encrypted token dari homepage
        Returns: (csrf_token_name, csrf_token_value, encrypted_token)
        """
        self._rate_limit()
        
        url = f"{self.base_url}/infopajak"
        
        try:
            logger.info(f"Fetching CSRF token from {url}")
            response = session.get(url, timeout=self.timeout, verify=False)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find CSRF token in hidden input
            csrf_input = soup.find('input', {'name': re.compile(r'csrf.*')})
            if not csrf_input:
                raise ValueError("CSRF token input not found in page")
            
            csrf_token_name = csrf_input.get('name')
            csrf_token_value = csrf_input.get('value')
            
            # Find encrypted token (txt_encryptToken)
            encrypt_input = soup.find('input', {'name': 'txt_encryptToken'})
            encrypted_token = encrypt_input.get('value') if encrypt_input else ""
            
            if not encrypted_token:
                 logger.warning("Encrypted token not found, request might fail")

            logger.info(f"✓ CSRF token fetched: {csrf_token_name}")
            
            return csrf_token_name, csrf_token_value, encrypted_token
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch CSRF token: {e}")
            raise

    def _submit_form(
        self,
        session: requests.Session,
        csrf_token_name: str,
        csrf_token_value: str,
        encrypted_token: str,
        nomor_plat: str,
        kd_plat: str
    ) -> Dict:
        """
        Submit form ke endpoint getInfoPajak
        """
        self._rate_limit()
        
        url = f"{self.base_url}/infopajak/getInfoPajak"
        
        # Prepare multipart data
        # Note: requests sends multipart/form-data if 'files' is provided.
        # Format for fields: 'name': (None, 'value')
        multipart_data = {
            csrf_token_name: (None, csrf_token_value),
            'txt_encryptToken': (None, encrypted_token),
            'nomor_plat': (None, nomor_plat),
            'kd_plat': (None, kd_plat),
            'typeOfPajak': (None, 'infoPkb')  # Critical field discovered from browser inspection
        }
        
        # Headers specific to the POST request
        post_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': self.base_url,
            'Referer': f"{self.base_url}/infopajak",
            'X-APP-TOKEN': encrypted_token  # Critical header found during debugging
        }
        # Update session headers strictly for this request, or pass in post()
        
        try:
            logger.info(f"Submitting form for plate: {nomor_plat} {kd_plat}")
            
            response = session.post(
                url,
                files=multipart_data,
                headers=post_headers,
                timeout=self.timeout,
                verify=False
            )
            
            # Handle 500 explicitly (Pusako returns 500 for invalid data sometimes)
            if response.status_code == 500:
                logger.warning(f"Server returned 500. Response: {response.text[:200]}")
                return {
                    'status': False,
                    'status_pajak': '',
                    'message': 'Data tidak ditemukan (Server Error 500)',
                    'data': None
                }

            response.raise_for_status()
            
            # Parse JSON response
            result = response.json()
            
            logger.info(f"✓ Response received, status: {result.get('status')}")
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Failed to submit form: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    async def get_tax_info(self, plate_number: str) -> Dict:
        """
        Main method: Get tax information untuk plat nomor
        """
        start_time = time.time()
        
        try:
            # Parse plat nomor
            kode_prefix, nomor, kode_suffix = self._parse_plate_number(plate_number)
            
            # Retry logic
            for attempt in range(self.max_retries):
                try:
                    session = self._get_session()
                    
                    # Fetch CSRF token
                    csrf_name, csrf_value, encrypt_token = self._fetch_csrf_token(session)
                    
                    # Submit form
                    result = self._submit_form(
                        session,
                        csrf_name,
                        csrf_value,
                        encrypt_token,
                        nomor,
                        kode_suffix
                    )
                    
                    # Check status
                    if not result.get('status'):
                        msg = result.get('message') or result.get('msg', 'Data tidak ditemukan')
                        logger.warning(f"Status false from API: {result}")
                        return {
                            'status': False,
                            'status_pajak': '',
                            'message': msg,
                            'data': None
                        }
                    
                    # Extract data
                    data = result.get('data', {})
                    status_pajak = result.get('status_pajak', 'tahunan')
                    
                    elapsed = (time.time() - start_time) * 1000
                    logger.info(f"✓ Tax data fetched successfully in {elapsed:.2f}ms")
                    
                    return {
                        'status': True,
                        'status_pajak': status_pajak,
                        'message': 'Data pajak berhasil diambil',
                        'data': data
                    }
                    
                except requests.RequestException as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        raise
            
        except ValueError as e:
            logger.error(f"Invalid plate number format: {e}")
            return {
                'status': False,
                'status_pajak': '',
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_tax_info: {e}")
            return {
                'status': False,
                'status_pajak': '',
                'message': f'Terjadi kesalahan: {str(e)}',
                'data': None
            }

# Singleton instance
pusako_service = PusakoService()
