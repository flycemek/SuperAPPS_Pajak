# Dokumentasi API Microservice OCR & Cek Pajak

Berikut adalah dokumentasi API lengkap dari Microservice OCR dan Super App Pajak (PUSAKO) yang bisa diberikan langsung ke rekan Backend (BE).

Semua endpoint berjalan dengan `prefix` di `/api/v1` (contoh: `http://<domain-atau-ip-server-ml>:8000/api/v1/...`).

---

## 1. Endpoint OCR Saja
Digunakan jika Backend hanya butuh ekstraksi nomor plat kendaraan dari sebuah foto tanpa mengecek pajak (hanya memproses gambar menggunakan AI).

* **Route**: `POST /api/v1/predict`
* **Headers**: 
  * `X-API-Key` : `(disesuaikan dengan di env)`
* **Body**: `multipart/form-data`
  * `file`: (tipe **File**, gambar JPG/PNG maksimal 10MB)

**Contoh Request (cURL):**
```bash
curl --location 'http://localhost:8000/api/v1/predict' \
--header 'X-API-Key: SUPER_SECRET_KEY_123' \
--form 'file=@"/path/ke/foto/plat.jpg"'
```

**Contoh Response Sukses (200 OK):**
```json
{
  "success": true,
  "message": "Plat nomor berhasil dideteksi",
  "timestamp": "2026-04-22T06:30:00.000",
  "data": {
    "plat": "BD 1234 AB",
    "confidence": 0.89
  }
}
```

---

## 2. Endpoint Cek Pajak Saja (via PUSAKO)
Digunakan jika Backend sudah memiliki teks "Plat Nomor" (tanpa gambar) dan hanya butuh mengecek data pajaknya ke server PUSAKO Bengkulu.

* **Route**: `POST /api/v1/check-tax`
* **Headers**: 
  * `Content-Type`: `application/json`
* **Body**: `RAW JSON`
  ```json
  {
      "plate_number": "BD 1234 AB"
  }
  ```

**Contoh Request (cURL):**
```bash
curl --location 'http://localhost:8000/api/v1/check-tax' \
--header 'Content-Type: application/json' \
--data '{
    "plate_number": "BD 1234 AB"
}'
```

**Contoh Response Sukses (200 OK):**
```json
{
  "tax_data": {
    "status": true,
    "status_pajak": "tahunan",
    "message": "Data pajak berhasil diambil",
    "data": {
      "nopol": "BD 1234 AB",
      "nama": "NAMA PEMILIK",
      "merek": "HONDA",
      "model": "SEPEDA MOTOR",
      "warna": "HITAM",
      "warna_plat": "HITAM",
      "th_buatan": "2019",
      "jumlah_cc": "150",
      "bbm": "BENSIN",
      "akhir_pkb": "10-10-2026",
      "akhir_stnkb": "10-10-2029",
      "jumlah_total": "250000"
    }
  }
}
```

---

## 3. Gabungan Keduanya: Upload Foto Kendaraan Langsung Cek Pajak
Digunakan jika Backend mengirimkan **Foto Kendaraan** dan ingin langsung menerima **Data Pajak** sebagai hasil (AI secara internal membaca foto, kemudian di-backend otomatis menembak API PUSAKO & mengembalikan output pajaknya). Ini adalah endpoint yang paling praktis.

* **Route**: `POST /api/v1/ocr-and-check-tax`
* **Headers**: *(Cukup Form Data)*
* **Body**: `multipart/form-data`
  * `file`: (tipe **File**, gambar JPG/PNG maksimal 10MB)

**Contoh Request (cURL):**
```bash
curl --location 'http://localhost:8000/api/v1/ocr-and-check-tax' \
--form 'file=@"/path/ke/foto/plat.jpg"'
```

**Contoh Response Sukses:**
*(Response sama persis dengan endpoint nomor 2 jika plat ditemukan dan valid di database PUSAKO)*
```json
{
  "tax_data": {
    "status": true,
    "status_pajak": "tahunan",
    "message": "Data pajak berhasil diambil",
    "data": {
       "nopol": "BD 1234 AB",
       "nama": "NAMA PEMILIK",
       "merek": "HONDA",
       "jumlah_total": "250000"
    }
  }
}
```

**Contoh Response Gagal (Jika plat bukan BD / AI Salah mendeteksi / Tidak ada kendaraan di foto):**
```json
{
  "tax_data": {
    "status": false,
    "status_pajak": "",
    "message": "Plat yang terdeteksi bukan plat Bengkulu",
    "data": null
  }
}
```

---

## 🔥 Catatan Penting untuk Integrasi:
1. Pastikan mengarahkan/menyambungkan endpoint diatas ke **Host / IP server AI** tempat microservice ini di-deploy beserta port-nya (misalnya server AI ada di `http://192.168.1.50:8000`).
2. Jika menggunakan alat seperti Postman untuk testing upload foto mobil, pastikan ganti tabs Request `Body` ke tipe **`form-data`**, pada kolom *Key* ketikkan `file`, dan ubah tipe inputannya disebelah kanan dari *Text* menjadi *File*, barulah upload gambarnya.
3. FastAPI microservice ini menyediakan Swagger UI secara default, rekan Backend bisa juga mencoba API secara interaktif dengan membuka `http://localhost:8000/docs` di browser.
