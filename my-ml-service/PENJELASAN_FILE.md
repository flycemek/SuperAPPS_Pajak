# 📚 Penjelasan Fungsi Setiap File
## OCR Microservice - DISKOMINFOTIK Bengkulu

---

## 🗂️ Struktur Project

```
my-ml-service/
├─ app/                          # Aplikasi utama
│  ├─ __init__.py               # Package marker
│  ├─ main.py                   # Entry point aplikasi
│  ├─ api/                      # Layer HTTP/API
│  │  ├─ __init__.py
│  │  ├─ routes.py              # Endpoint umum (health check, root)
│  │  └─ predict.py             # Endpoint OCR predict
│  ├─ core/                     # Konfigurasi & security
│  │  ├─ __init__.py
│  │  ├─ config.py              # Konfigurasi aplikasi
│  │  └─ security.py            # API Key authentication
│  ├─ schemas/                  # Request/Response models
│  │  ├─ __init__.py
│  │  └─ prediction.py          # Pydantic models untuk validation
│  └─ services/                 # Business logic
│     ├─ __init__.py
│     └─ model_service.py       # OCR service logic
├─ assets/                       # File pendukung (gambar test, dll)
├─ tests/                        # Unit tests
│  ├─ __init__.py
│  └─ test_ocr.py               # Test untuk OCR service
├─ .env                          # Environment variables (konfigurasi)
├─ .gitignore                    # Git ignore patterns
├─ requirements.txt              # Python dependencies
├─ README.md                     # Dokumentasi utama
├─ PANDUAN_INSTALASI.md         # Panduan instalasi detail
├─ POSTMAN_GUIDE.md             # Panduan testing dengan Postman
├─ TROUBLESHOOTING.md           # Troubleshooting guide
├─ start.bat                     # Script untuk menjalankan service
├─ install.bat                   # Script untuk instalasi
└─ start-service.bat            # Script untuk start service
```

---

## 📄 Penjelasan Detail Setiap File

### 🔹 **Root Directory**

#### `.env`
**Fungsi:** File konfigurasi environment variables
**Isi:**
- Konfigurasi aplikasi (nama, version, debug mode)
- Server settings (host, port)
- API Key untuk authentication
- OCR settings (bahasa, GPU, confidence threshold)
- Upload settings (max file size, allowed extensions)

**Contoh:**
```env
API_KEY=your_secure_api_key_here
OCR_CONFIDENCE_THRESHOLD=0.3
DEBUG=True
```

**Kenapa Penting:** Memisahkan konfigurasi dari code, mudah diubah tanpa edit code

---

#### `requirements.txt`
**Fungsi:** Daftar semua Python packages yang dibutuhkan
**Isi:**
- FastAPI (web framework)
- Uvicorn (ASGI server)
- EasyOCR (OCR engine)
- Pillow, OpenCV (image processing)
- PyTorch (deep learning framework)
- Pydantic (data validation)

**Cara Pakai:**
```bash
pip install -r requirements.txt
```

**Kenapa Penting:** Memastikan semua dependencies terinstall dengan versi yang benar

---

#### `README.md`
**Fungsi:** Dokumentasi utama project
**Isi:**
- Deskripsi project
- Arsitektur dan struktur
- Cara instalasi
- Cara menjalankan
- Endpoint API
- Testing guide
- Fitur-fitur

**Kenapa Penting:** First point of contact untuk siapa saja yang buka project

---

#### `start.bat`, `install.bat`, `start-service.bat`
**Fungsi:** Script otomatis untuk Windows
- **install.bat**: Instalasi dependencies
- **start.bat**: Install + run sekaligus
- **start-service.bat**: Jalankan service (setelah install)

**Kenapa Penting:** Memudahkan user yang tidak familiar dengan command line

---

### 🔹 **app/** - Aplikasi Utama

#### `app/__init__.py`
**Fungsi:** Menandai folder `app` sebagai Python package
**Isi:** Minimal, hanya version info
**Kenapa Penting:** Memungkinkan import dari folder app

---

#### `app/main.py` ⭐ ENTRY POINT
**Fungsi:** File utama aplikasi, starting point
**Tanggung Jawab:**
1. Inisialisasi FastAPI application
2. Setup CORS middleware
3. Include routers dari api/routes.py dan api/predict.py
4. Setup logging
5. Lifecycle events (startup, shutdown)

**Flow:**
```
User run uvicorn → Load main.py → Initialize FastAPI → 
Load routers → Start server → Listen di port 8000
```

**Kenapa Penting:** Ini adalah "pintu masuk" aplikasi, koordinasi semua komponen

---

### 🔹 **app/api/** - HTTP Layer

#### `app/api/__init__.py`
**Fungsi:** Package marker untuk folder api
**Kenapa Penting:** Memungkinkan import: `from app.api import routes, predict`

---

#### `app/api/routes.py`
**Fungsi:** Endpoint HTTP umum (non-OCR)
**Endpoints:**
- `GET /api/v1/` - Info aplikasi
- `GET /api/v1/health` - Health check untuk monitoring

**Tanggung Jawab:**
- Response informasi service
- Status kesehatan aplikasi

**Kenapa Dipisah:** Endpoint general vs business logic (OCR) terpisah untuk clarity

**Contoh Response:**
```json
{
  "status": "healthy",
  "service": "OCR Microservice",
  "timestamp": "2026-01-26T08:58:14"
}
```

---

#### `app/api/predict.py` ⭐ CORE ENDPOINT
**Fungsi:** Endpoint untuk OCR prediction
**Endpoints:**
- `POST /api/v1/predict` - Upload gambar, get hasil OCR

**Tanggung Jawab:**
1. Terima request upload file
2. Validasi API Key (via dependency)
3. Validasi file (type, size)
4. Call OCR service untuk proses gambar
5. Format response sesuai schema
6. Error handling

**Flow Request:**
```
User POST gambar → Validasi API Key → Validasi file → 
Call OCR service → Format response → Return JSON
```

**Kenapa Penting:** Ini adalah endpoint utama yang digunakan user untuk OCR

**Contoh Response:**
```json
{
  "success": true,
  "message": "Plat nomor berhasil dideteksi",
  "data": {
    "plat": "B 1234 XYZ",
    "confidence": 0.95
  }
}
```

---

### 🔹 **app/core/** - Konfigurasi & Security

#### `app/core/__init__.py`
**Fungsi:** Package marker untuk folder core
**Kenapa Penting:** Memungkinkan import konfigurasi dan security

---

#### `app/core/config.py` ⭐ KONFIGURASI
**Fungsi:** Centralized configuration management
**Tanggung Jawab:**
1. Load environment variables dari .env
2. Validasi tipe data dengan Pydantic
3. Provide default values
4. Create directories (assets) jika belum ada

**Class:** `Settings` - Pydantic BaseSettings
**Fields:**
- APP_NAME, APP_VERSION
- HOST, PORT
- API_KEY
- OCR_LANGUAGES, OCR_GPU, OCR_CONFIDENCE_THRESHOLD
- MAX_FILE_SIZE, ALLOWED_EXTENSIONS
- ASSETS_DIR (path)

**Pattern:** Singleton - `settings` object diimport di semua file

**Kenapa Penting:** 
- Single source of truth untuk konfigurasi
- Type-safe dengan Pydantic validation
- Easy to change tanpa edit code

---

#### `app/core/security.py`
**Fungsi:** API Key authentication
**Tanggung Jawab:**
1. Verify API Key dari header `X-API-Key`
2. Raise HTTPException jika invalid/missing

**Function:** `verify_api_key(api_key: str)`
- Dipanggil sebagai FastAPI Dependency
- Return api_key jika valid
- Raise 401/403 jika invalid

**Flow:**
```
Request → Check header X-API-Key → 
Compare dengan settings.API_KEY → 
✅ Valid: Continue | ❌ Invalid: Raise 403
```

**Kenapa Penting:** Melindungi endpoint dari unauthorized access

---

### 🔹 **app/schemas/** - Data Validation

#### `app/schemas/__init__.py`
**Fungsi:** Package marker untuk folder schemas

---

#### `app/schemas/prediction.py` ⭐ VALIDATION MODELS
**Fungsi:** Pydantic models untuk request/response validation
**Models:**

1. **PlateData**
   - Fields: `plat`, `confidence`
   - Digunakan di response success

2. **PredictionResponse**
   - Fields: `success`, `message`, `timestamp`, `data`
   - Response format untuk predict endpoint
   - `data` bisa PlateData object atau empty list

3. **ErrorResponse**
   - Fields: `success`, `message`, `timestamp`, `error`
   - Response format untuk error cases

**Tanggung Jawab:**
- Type validation (string, float, bool, etc)
- Field validation (required, optional)
- Auto-generate OpenAPI schema untuk Swagger
- Serialize/Deserialize JSON

**Kenapa Penting:**
- Type safety
- Auto-validation
- Auto-documentation di Swagger
- Consistent response format

---

### 🔹 **app/services/** - Business Logic

#### `app/services/__init__.py`
**Fungsi:** Package marker untuk folder services

---

#### `app/services/model_service.py` ⭐ OCR LOGIC
**Fungsi:** Core business logic untuk OCR
**Class:** `OCRService` (Singleton pattern)

**Methods:**

1. **`__init__()` & `_ensure_reader()`**
   - Inisialisasi EasyOCR Reader (lazy loading)
   - Download model jika belum ada
   - Setup GPU/CPU mode

2. **`validate_image(image_bytes)`**
   - Validasi file size
   - Validasi format (JPG/PNG)
   - Check if valid image

3. **`preprocess_image(image_bytes)`**
   - Enhance contrast (1.5x)
   - Enhance sharpness (2x)
   - Convert to numpy array
   - Optional: grayscale conversion

4. **`is_license_plate(text)`**
   - Heuristic untuk detect plat nomor
   - Pattern matching: huruf-angka-huruf
   - Support dengan/tanpa spasi
   - Validasi panjang (5-10 chars)

5. **`format_license_plate(text)`**
   - Standardize format plat nomor
   - Uppercase, normalize spaces

6. **`perform_ocr(image_bytes)` ⭐ MAIN METHOD**
   - Orchestrate semua proses OCR
   - Validasi → Preprocess → OCR → Filter → Format
   - Return dict dengan license_plate, confidence, dll

**Flow OCR:**
```
Image bytes → Validate → Preprocess (enhance) → 
EasyOCR readtext → Filter by confidence → 
Check pattern plat nomor → Return best match
```

**Kenapa Penting:** 
- Ini adalah "otak" aplikasi
- Semua logic OCR ada di sini
- Dipisah dari HTTP layer untuk reusability

---

### 🔹 **tests/** - Testing

#### `tests/__init__.py`
**Fungsi:** Package marker untuk folder tests

---

#### `tests/test_ocr.py`
**Fungsi:** Unit tests untuk OCR service
**Tests:**
- `test_is_license_plate_valid()` - Test pattern matching valid
- `test_is_license_plate_invalid()` - Test pattern matching invalid
- `test_format_license_plate()` - Test formatting

**Cara Run:**
```bash
pytest tests/test_ocr.py -v
```

**Kenapa Penting:** 
- Quality assurance
- Prevent regression bugs
- Documentation of expected behavior

---

### 🔹 **assets/** - Supporting Files

**Fungsi:** Folder untuk file pendukung
**Isi (optional):**
- Gambar test plat nomor
- Model weights (jika ada)
- Other static files

**Kenapa Ada:** Centralized storage untuk file-file pendukung

---

## 🎯 Arsitektur Layered (Clean Architecture)

### Layer 1: HTTP/API (`app/api/`)
**Tanggung Jawab:**
- Handle HTTP requests
- Route ke service layer
- Format responses
- Error handling HTTP errors

**Files:** `routes.py`, `predict.py`

---

### Layer 2: Business Logic (`app/services/`)
**Tanggung Jawab:**
- Core OCR logic
- Image processing
- Pattern matching
- Pure Python logic (tidak tahu HTTP)

**Files:** `model_service.py`

---

### Layer 3: Data/Schema (`app/schemas/`)
**Tanggung Jawab:**
- Data validation
- Type checking
- Serialization/Deserialization

**Files:** `prediction.py`

---

### Layer 4: Core/Infrastructure (`app/core/`)
**Tanggung Jawab:**
- Configuration management
- Security/Authentication
- Utilities

**Files:** `config.py`, `security.py`

---

## 🔄 Request Flow (End-to-End)

```
1. User kirim POST /api/v1/predict dengan gambar
   ↓
2. uvicorn terima request → main.py
   ↓
3. FastAPI routing → api/predict.py → predict_license_plate()
   ↓
4. Dependency injection → core/security.py → verify_api_key()
   ↓
5. Validasi file di predict.py
   ↓
6. Call services/model_service.py → perform_ocr()
   ↓
7. Image preprocessing → EasyOCR → Pattern matching
   ↓
8. Return result ke predict.py
   ↓
9. Format response pakai schemas/prediction.py
   ↓
10. Return JSON ke user
```

---

## 📊 Dependency Graph

```
main.py
  ├─ api/routes.py
  │    └─ core/config.py
  │
  ├─ api/predict.py
  │    ├─ schemas/prediction.py
  │    ├─ services/model_service.py
  │    │    └─ core/config.py
  │    └─ core/security.py
  │         └─ core/config.py
  │
  └─ core/config.py (root dependency)
```

**Catatan:** `core/config.py` adalah root dependency yang diimport hampir semua file

---

## 💡 Best Practices yang Diterapkan

### ✅ Separation of Concerns
- HTTP logic terpisah dari business logic
- Business logic terpisah dari data models
- Configuration terpisah dari code

### ✅ Dependency Injection
- API key verification via FastAPI Depends
- Easy to mock untuk testing

### ✅ Singleton Pattern
- OCRService hanya diinisialisasi sekali
- Memory efficient
- Model EasyOCR di-load sekali saja

### ✅ Type Safety
- Pydantic untuk validation
- Python type hints di semua function

### ✅ Error Handling
- Try-catch di endpoint
- Consistent error response format
- Logging untuk debugging

### ✅ Configuration Management
- Environment variables via .env
- Centralized di config.py
- Type-safe dengan Pydantic

---

## 📚 Untuk Laporan KP

File-file yang penting untuk dijelaskan di laporan:

### ⭐ Must Explain (Core):
1. **app/main.py** - Entry point & orchestration
2. **app/api/predict.py** - Main endpoint
3. **app/services/model_service.py** - OCR logic
4. **app/core/config.py** - Configuration management
5. **app/schemas/prediction.py** - Data models

### ✅ Should Explain (Supporting):
6. **app/core/security.py** - Authentication
7. **app/api/routes.py** - Health check endpoints
8. **.env** - Configuration file
9. **requirements.txt** - Dependencies

### 📝 Nice to Mention:
10. **tests/test_ocr.py** - Testing
11. Script files (.bat) - Deployment automation

---

## 🎓 Kesimpulan

Project ini menggunakan **Clean Architecture** dengan pemisahan layer yang jelas:

- **API Layer**: Handle HTTP (routes.py, predict.py)
- **Service Layer**: Business logic (model_service.py)
- **Schema Layer**: Data validation (prediction.py)
- **Core Layer**: Infrastructure (config.py, security.py)

Setiap file punya tanggung jawab yang spesifik dan tidak overlap, memudahkan maintenance dan scalability.

---

**Semoga penjelasan ini membantu untuk laporan KP! 🎉**
