"""
Security Module
Menangani autentikasi dan otorisasi API
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

# API Key Header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Memverifikasi API Key dari header request
    
    Args:
        api_key: API key dari header X-API-Key
        
    Returns:
        str: API key yang valid
        
    Raises:
        HTTPException: Jika API key tidak valid atau tidak ada
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key tidak ditemukan. Sertakan X-API-Key di header."
        )
    
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key tidak valid"
        )
    
    return api_key
