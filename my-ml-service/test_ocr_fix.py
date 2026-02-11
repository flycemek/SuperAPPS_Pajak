import requests

# Test OCR dengan gambar yang bermasalah
url = "http://127.0.0.1:6677/api/v1/ocr-and-check-tax"
headers = {"X-API-Key": "tps2025"}
image_path = r"C:\Users\Rafly\.gemini\antigravity\brain\eb2e24d9-78bb-40bd-a011-860932cb5821\uploaded_media_1770093021820.png"

with open(image_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)

print("Status Code:", response.status_code)
print("\nResponse JSON:")
print(response.json())
