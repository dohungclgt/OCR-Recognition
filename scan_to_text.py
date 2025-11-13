# scan_to_text.py — Scan OCR: Gemini AI (mặc định) + Tesseract (tuỳ chọn)
from typing import Dict, Any
from io import BytesIO
import numpy as np
import cv2
import pytesseract

# ===== Optional: tesseract path trên Windows =====
try:
    import config  # noqa
except:
    pass

# ===== Gemini SDK (google.generativeai) =====
import os
from PIL import Image
import google.generativeai as genai

# Lấy API key từ ENV (ưu tiên .env nếu bạn dùng dotenv ở smart_ai_extract)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "Your API Key Here")
genai.configure(api_key=GEMINI_API_KEY)
_GEM_MODEL_DEFAULT = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ----------------- Helpers (Tesseract pipeline) -----------------
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
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = gray.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def _preprocess(gray):
    gray = cv2.medianBlur(gray, 3)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    thr = cv2.adaptiveThreshold(gray, 255,
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                31, 10)
    thr = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8), 1)
    return thr

def _text_ratio(s):
    if not s:
        return 0.0
    valid = sum(ch.isalnum() or ch.isspace() for ch in s)
    return valid / max(1, len(s))

def _ocr_tesseract(proc, lang_ui):
    tess_lang = "eng" if "eng" in lang_ui.lower() else "vie+eng"
    def _try(img, psm):
        cfg = f"--oem 1 --psm {psm}"
        return pytesseract.image_to_string(img, lang=tess_lang, config=cfg).strip()

    text = _try(proc, 6)
    if _text_ratio(text) < 0.6:
        inv = cv2.bitwise_not(proc)
        t2 = _try(inv, 6)
        if _text_ratio(t2) > _text_ratio(text):
            text = t2
    if _text_ratio(text) < 0.6:
        t3 = _try(proc, 4)
        if _text_ratio(t3) > _text_ratio(text):
            text = t3
    return text

# ----------------- Gemini OCR for image -----------------
_GEM_PROMPT = (
    "Extract all readable text from this photo. "
    "Preserve natural line breaks. Plain text only. "
    "Vietnamese + English supported. Do NOT translate or summarize."
)

def _ocr_gemini_image(image_bytes: bytes, model_name: str = _GEM_MODEL_DEFAULT) -> str:
    try:
        model = genai.GenerativeModel(model_name)
        img = Image.open(BytesIO(image_bytes))
        resp = model.generate_content([_GEM_PROMPT, img])
        text = getattr(resp, "text", "") or ""
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini OCR error: {e}")

# ----------------- Public API -----------------
def scan_to_text(image_bytes: bytes, lang="Tiếng Việt", engine: str = "gemini", gem_model: str = None) -> Dict[str, Any]:
    """
    Scan OCR:
      - engine='gemini' (mặc định): dùng Google Gemini AI để nhận dạng chữ, không dịch/không tóm tắt.
      - engine='tesseract': pipeline tiền xử lý + Tesseract fallback.
    """
    try:
        if engine.lower() == "gemini":
            model = gem_model or _GEM_MODEL_DEFAULT
            text = _ocr_gemini_image(image_bytes, model_name=model)
            if not text.strip():
                return {"success": False, "message": "Gemini không trả về nội dung văn bản."}
            return {"success": True, "text": text}

        # ---- Tesseract branch (giữ nguyên để bạn có thể so sánh) ----
        np_img = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if bgr is None:
            return {"success": False, "message": "Không đọc được ảnh camera"}
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray = _resize(gray)
        gray = _deskew(gray)
        proc = _preprocess(gray)

        text = _ocr_tesseract(proc, lang)
        # tuỳ bạn có muốn giữ quality gate 80% nữa hay không
        # ở đây mình bỏ cổng 80% để không chặn kết quả hợp lệ
        if not text.strip():
            return {"success": False, "message": "Không nhận diện được văn bản (Tesseract)."}
        return {"success": True, "text": text}

    except Exception as e:
        return {"success": False, "message": f"Lỗi Scan OCR: {e}"}
