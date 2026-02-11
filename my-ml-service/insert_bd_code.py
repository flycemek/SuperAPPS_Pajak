import re

# Read file
with open('app/services/model_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find insertion point after "# Debug: Log semua hasil OCR mentah"
search_text = "# Debug: Log semua hasil OCR mentah"
insertion_code = '''
        # 🎯 BD IMMEDIATE DETECTION
        for idx, (bbox, text, confidence) in enumerate(results):
            if confidence >= 0.4:  # Lower threshold for BD plates
                cleaned = self.clean_ocr_text(text).strip().upper()
                if re.match(r'^BD\\s+\\d{3,4}\\s+[A-Z]{1,3}$', cleaned):
                    return {
                        'license_plate': self.format_license_plate(cleaned),
                        'confidence': float(confidence),
                        'all_detections': [{
                            "text": text,
                            "confidence": float(confidence),
                            "bbox": [[int(c[0]), int(c[1])] for c in bbox]
                        }]
                    }
'''

if search_text in content:
    # Find the line after # Debug comment
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if search_text in line:
            # Insert after this line
            lines.insert(i + 1, insertion_code)
            break
    
    # Write back
    with open('app/services/model_service.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ BD detection code inserted successfully!")
else:
    print("❌ Could not find insertion point")
