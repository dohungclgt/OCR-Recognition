# scan_to_text.py — Tesseract Scan + Quality >= 80%
from typing import Dict, Any
import numpy as np
import cv2
import pytesseract

try:
    import config  # noqa
except: 
    pass

# ---------- Helpers ----------
def _resize(gray):
    h, w = gray.shape[:2]
    max_side = max(h, w)
    if max_side > 2200:
        s = 2200 / max_side
        return cv2.resize(gray, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    if max_side < 900:
        s = 1300 / max(1, max_side)
        return cv2.resize(gray, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    return gray

def _deskew(gray):
    coords = np.column_stack(np.where(gray < 200))
    if len(coords) < 100: 
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45: angle = -(90 + angle)
    else: angle = -angle
    (h, w) = gray.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def _preprocess(gray):
    gray = cv2.medianBlur(gray, 3)
    # CLAHE tăng tương phản mạnh với ảnh tối
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    # Adaptive threshold
    thr = cv2.adaptiveThreshold(gray,255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,31,10)
    thr = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, np.ones((2,2),np.uint8),1)
    return thr

def _text_ratio(s):
    if not s: return 0.0
    valid = sum(ch.isalnum() or ch.isspace() for ch in s)
    return valid / max(1,len(s))

def _ocr(img, lang, psm):
    cfg = f"--oem 1 --psm {psm}"
    return pytesseract.image_to_string(img, lang=lang, config=cfg)

# ---------- API ----------
def scan_to_text(image_bytes: bytes, lang="Tiếng Việt") -> Dict[str,Any]:
    try:
        np_img = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if bgr is None:
            return {"success":False,"message":"Không đọc được ảnh camera"}

        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray = _resize(gray)
        gray = _deskew(gray)
        proc = _preprocess(gray)

        tess_lang = "eng" if "eng" in lang.lower() else "vie+eng"

        # attempt 1
        text = _ocr(proc, tess_lang, 6).strip()

        # fallback invert
        if _text_ratio(text) < 0.6:
            inv = cv2.bitwise_not(proc)
            t2 = _ocr(inv, tess_lang, 6).strip()
            if _text_ratio(t2) > _text_ratio(text):
                text = t2

        # fallback PSM 4 (multi block)
        if _text_ratio(text) < 0.6:
            t3 = _ocr(proc, tess_lang, 4).strip()
            if _text_ratio(t3) > _text_ratio(text):
                text = t3

        # QUALITY GATE
        quality = _text_ratio(text)
        if quality < 0.80:
            return {
                "success": False,
                "message": f"Ảnh chưa đủ rõ (độ chuẩn {quality*100:.1f}%). "
                           f"Hãy chụp gần hơn, đủ sáng & thẳng giấy."
            }

        return {"success":True,"text":text}

    except Exception as e:
        return {"success":False,"message":f"Lỗi Scan OCR: {e}"}
