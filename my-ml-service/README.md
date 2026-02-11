# 🤖 OCR Microservice - DISKOMINFOTIK Bengkulu

> **FastAPI-based OCR Microservice for Indonesian License Plate Recognition**

[![FastAPI](https://img.shields.io/badge/fastapi-0.109.0-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![EasyOCR](https://img.shields.io/badge/easyocr-1.7.0-orange)](https://github.com/JaidedAI/EasyOCR)

---

## 📋 Overview

Microservice OCR untuk deteksi otomatis plat nomor kendaraan dari gambar. Dioptimasi khusus untuk plat nomor wilayah Bengkulu (BD) dengan fitur koreksi OCR errors yang canggih.

### ✨ Key Features

- 🎯 **High Accuracy OCR** - EasyOCR dengan PyTorch backend
- 🔍 **Smart Pattern Matching** - Validasi format plat Indonesia
- ⚡ **Auto Error Correction** - Koreksi otomatis kesalahan OCR umum
- 🖼️ **Image Preprocessing** - Adaptive enhancement untuk gambar berkualitas rendah
- 🔐 **Secure API** - API Key authentication
- 📊 **Confidence Scoring** - Skor kepercayaan untuk setiap deteksi
- 🌐 **PUSAKO Integration** - Web scraping data pajak kendaraan

---

## 🚀 Quick Start

### Windows (Recommended)

```bash
# Install dependencies
install.bat

# Start service
start.bat
```

### Manual Installation

```bash
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start service
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Access Documentation

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

---

## 📡 API Endpoints

### 1. Health Check

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "OCR Microservice - DISKOMINFOTIK Bengkulu",
  "version": "1.0.0"
}
```

---

### 2. OCR Prediction

```http
POST /api/v1/predict
Content-Type: multipart/form-data
X-API-Key: your_api_key_here
```

**Request:**
- `file`: Image file (JPG/PNG, max 10MB)

**Response Success:**
```json
{
  "success": true,
  "message": "Plat nomor berhasil dideteksi",
  "timestamp": "2026-02-11T14:10:00",
  "data": {
    "plat": "BD 6781 IJ",
    "confidence": 0.92
  }
}
```

**Response No Plate:**
```json
{
  "success": true,
  "message": "Tidak ditemukan plat nomor yang valid",
  "timestamp": "2026-02-11T14:10:00",
  "data": []
}
```

**Response Error:**
```json
{
  "success": false,
  "message": "Validation error",
  "timestamp": "2026-02-11T14:10:00",
  "error": {
    "file": ["Ukuran file terlalu besar. Maksimal 10MB"]
  }
}
```

---

### 3. Check Tax (PUSAKO)

```http
GET /api/v1/check-tax/{plate_number}
X-API-Key: your_api_key_here
```

**Example:**
```http
GET /api/v1/check-tax/BD6781IJ
```

---

### 4. OCR + Check Tax (Combined)

```http
POST /api/v1/ocr-and-check-tax
Content-Type: multipart/form-data
X-API-Key: your_api_key_here
```

Upload gambar dan langsung dapatkan data pajak.

---

## 🔧 Configuration

Edit file `.env`:

```env
# Application
APP_NAME="OCR Microservice - DISKOMINFOTIK Bengkulu"
APP_VERSION="1.0.0"
DEBUG=True

# Server
HOST=127.0.0.1
PORT=8000

# Security
API_KEY=your_secure_api_key_here

# OCR Settings
OCR_LANGUAGES=["en"]
OCR_GPU=False
OCR_CONFIDENCE_THRESHOLD=0.2

# Upload Settings
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=["jpg", "jpeg", "png"]

# PUSAKO Integration
PUSAKO_BASE_URL=https://pusako.bengkuluprov.go.id
PUSAKO_TIMEOUT=30
PUSAKO_MAX_RETRIES=3
```

---

## 🧠 OCR Features

### 1. Character Correction

| OCR Error | Actual | Context |
|-----------|--------|---------|
| `IBD 6781 IJ` | `BD 6781 IJ` | Remove leading 'I' noise |
| `BD 6701 IJ` | `BD 6781 IJ` | 0→8 in number context |
| `BD 67I1 IJ` | `BD 6711 IJ` | I→1 in number context |
| `BD 67O1 IJ` | `BD 6701 IJ` | O→0 in number context |

### 2. Prefix Validation

Mendukung prefix plat Indonesia:
- **Bengkulu:** BD
- **Sumatra:** BB, BG, BK, BL, BM, BN, BE, BA
- **Jakarta:** B
- **Dan lainnya...**

### 3. Pattern Matching

Format yang didukung:
```
[1-2 Huruf] [1-4 Angka] [1-3 Huruf]
```

Contoh:
- ✅ `BD 6781 IJ`
- ✅ `B 1234 ABC`
- ✅ `BD3587TE` (tanpa spasi)
- ❌ `123 ABC` (missing prefix)
- ❌ `BD ABC 123` (wrong order)

### 4. Image Preprocessing

Pipeline preprocessing:
1. **Brightness Analysis** - Deteksi kondisi pencahayaan
2. **Adaptive Contrast** - Enhancement sesuai brightness
3. **Sharpness Enhancement** - Perbaikan ketajaman (1.8x)
4. **Denoising** - Non-local Means Denoising
5. **Grayscale Conversion** - Untuk akurasi OCR lebih baik

---

## 📁 Project Structure

```
my-ml-service/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── routes.py       # General routes
│   │   ├── predict.py      # OCR endpoint
│   │   └── pusako.py       # Tax check endpoint
│   ├── core/               # Core configuration
│   │   ├── config.py       # Settings management
│   │   └── security.py     # API authentication
│   ├── schemas/            # Pydantic models
│   │   └── prediction.py   # Request/response schemas
│   ├── services/           # Business logic
│   │   ├── model_service.py    # OCR service
│   │   └── pusako_service.py   # PUSAKO scraper
│   └── main.py             # FastAPI app
├── tests/                  # Unit tests
├── assets/                 # Test images
├── .env                    # Environment config
├── requirements.txt        # Python dependencies
├── install.bat            # Installation script
├── start.bat              # Start service script
└── README.md              # This file
```

---

## 🧪 Testing

### Using cURL

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/predict" \
  -H "X-API-Key: your_api_key_here" \
  -F "file=@assets/test-plate.jpg"
```

### Using Python

```python
import requests

url = "http://127.0.0.1:8000/api/v1/predict"
headers = {"X-API-Key": "your_api_key_here"}
files = {"file": open("test-plate.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

### Unit Tests

```bash
pytest tests/ -v
```

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Processing Time** | 2-5 seconds (CPU) |
| **Accuracy** | 85-95% (clear images) |
| **Max Image Size** | 10MB |
| **Confidence Threshold** | 0.2 (adjustable) |
| **Supported Formats** | JPG, JPEG, PNG |

---

## 🐛 Troubleshooting

### Error: "SSL Certificate Error"
**Solution:** SSL verification sudah di-bypass otomatis untuk download model

### Error: "API Key tidak valid"
```bash
# Check .env file
API_KEY=your_secure_api_key_here

# Make sure header matches
X-API-Key: your_secure_api_key_here
```

### Error: "Plat tidak terdeteksi"
**Tips:**
- ✅ Gunakan gambar yang jelas dan fokus
- ✅ Pastikan plat nomor terlihat penuh
- ✅ Pencahayaan cukup
- ✅ Resolusi minimal 640x480
- ❌ Hindari gambar blur/buram
- ❌ Hindari refleksi/pantulan cahaya

### Error: "Module not found"
```bash
venv\Scripts\activate
pip install -r requirements.txt --force-reinstall
```

### Error: "Port already in use"
```bash
# Change port in .env
PORT=8001

# Or kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 🔒 Security

### API Key Authentication

Semua endpoint (kecuali health check) memerlukan API Key:

```http
X-API-Key: your_secure_api_key_here
```

**Response jika API Key salah:**
```json
{
  "detail": "API Key tidak valid"
}
```

### Production Security Checklist

- [ ] Ganti default API_KEY di `.env`
- [ ] Set `DEBUG=False` di production
- [ ] Configure CORS untuk domain spesifik
- [ ] Use HTTPS (SSL/TLS)
- [ ] Rate limiting (jika perlu)
- [ ] Log monitoring

---

## 🚀 Deployment

### Windows Server

```bash
# Install dependencies
install.bat

# Start as service (using NSSM)
nssm install OCRService "C:\path\to\venv\Scripts\uvicorn.exe"
nssm set OCRService AppParameters "app.main:app --host 0.0.0.0 --port 8000"
nssm set OCRService AppDirectory "C:\path\to\my-ml-service"
nssm start OCRService
```

### Linux Server (Systemd)

```bash
# Create service file
sudo nano /etc/systemd/system/ocr-service.service
```

```ini
[Unit]
Description=OCR Microservice
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/my-ml-service
Environment="PATH=/var/www/my-ml-service/venv/bin"
ExecStart=/var/www/my-ml-service/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable ocr-service
sudo systemctl start ocr-service
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t ocr-service .
docker run -p 8000:8000 --env-file .env ocr-service
```

---

## 📚 Documentation

- [PENJELASAN_FILE.md](PENJELASAN_FILE.md) - Penjelasan detail setiap file
- [API Documentation](http://127.0.0.1:8000/docs) - Interactive Swagger UI
- [ReDoc](http://127.0.0.1:8000/redoc) - Alternative API docs

---

## 🤝 Contributing

Contributions welcome! Please follow:

1. Fork repository
2. Create feature branch
3. Make changes dengan tests
4. Submit pull request

---

## 📄 License

MIT License - See [LICENSE](../LICENSE) for details

---

## 👥 Credits

**Developed by DISKOMINFOTIK Bengkulu**

### Technologies Used

- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - OCR Engine
- [FastAPI](https://fastapi.tiangolo.com/) - Web Framework
- [PyTorch](https://pytorch.org/) - Deep Learning
- [OpenCV](https://opencv.org/) - Image Processing
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data Validation

---

<div align="center">
  <strong>Made with ❤️ for Bengkulu</strong>
  <br>
  <sub>© 2026 DISKOMINFOTIK Bengkulu</sub>
</div>
