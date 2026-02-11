"""
Main Application
Entry point untuk FastAPI microservice OCR
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes, predict, pusako
from app.core.config import settings
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Initialize FastAPI application
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        Microservice OCR untuk pemindaian plat nomor kendaraan
        
        Dikembangkan untuk DISKOMINFOTIK Provinsi Bengkulu sebagai bagian dari Super App.
        
        ## Fitur:
        * OCR plat nomor kendaraan menggunakan EasyOCR
        * Validasi format plat nomor Indonesia
        * Integrasi dengan PUSAKO untuk data pajak kendaraan
        * API Key authentication
        * Response terstruktur dengan confidence score
        
        ## Endpoints:
        * `/api/v1/predict` - OCR plat nomor dari foto
        * `/api/v1/check-tax` - Cek data pajak dengan plat nomor
        * `/api/v1/ocr-and-check-tax` - Upload foto → OCR + Data pajak
        
        ---
        **Kerja Praktik (KP) - DISKOMINFOTIK Provinsi Bengkulu**
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        routes.router,
        prefix="/api/v1",
        tags=["General"]
    )
    
    app.include_router(
        predict.router,
        prefix="/api/v1",
        tags=["OCR Prediction"]
    )
    
    app.include_router(
        pusako.router,
        prefix="/api/v1",
        tags=["Tax Check (PUSAKO)"]
    )
    
    return app


# Create the FastAPI app instance
app = create_app()


@app.on_event("startup")
async def startup_event():
    """
    Event yang dijalankan saat aplikasi startup
    """
    logger.info("="*60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"OCR GPU Enabled: {settings.OCR_GPU}")
    logger.info(f"Confidence Threshold: {settings.OCR_CONFIDENCE_THRESHOLD}")
    logger.info(f"PUSAKO Integration: Enabled")
    logger.info("="*60)
    logger.info("Aplikasi siap menerima request!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Event yang dijalankan saat aplikasi shutdown
    """
    logger.info("Shutting down application...")


if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
