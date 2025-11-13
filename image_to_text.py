from PIL import Image
import pytesseract
import cv2
import numpy as np
from io import BytesIO
import os

# ⚙️ Đặt API key Google AI Studio tại đây (đừng public)
os.environ["GEMINI_API_KEY"] = "Your API Key Here"

# Kích hoạt cấu hình tesseract_cmd từ config.py (Windows)
try:
    import config  # noqa
except Exception:
    pass

# ============ Gemini ============
try:
    from google import genai
    from google.genai import types as gem_types
    _gemini_available = True
    _gem_client = genai.Client()
except Exception:
    _gemini_available = False
    _gem_client = None


def _text_ratio(s: str) -> float:
    if not s:
        return 0.0
    valid = sum(ch.isalnum() or ch.isspace() for ch in s)
    return valid / max(1, len(s))


def _preprocess_for_ocr(image_path: str) -> str:
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        return image_path
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    gray = cv2.medianBlur(gray, 3)
    processed_path = "temp_processed.png"
    cv2.imwrite(processed_path, gray)
    return processed_path


def _tesseract_try_all(pil_img: Image.Image, lang: str = "vie+eng") -> str:
    def _ocr(img, cfg):
        try:
            return pytesseract.image_to_string(img, lang=lang, config=cfg).strip()
        except Exception:
            return ""
    best_text, best_score = "", 0.0
    cfgs = ["--oem 1 --psm 6", "--oem 1 --psm 4"]
    variants = [pil_img]
    # đảo màu
    try:
        inv = Image.fromarray(255 - np.array(pil_img.convert("L"))).convert("RGB")
        variants.append(inv)
    except Exception:
        pass
    for v in variants:
        for cfg in cfgs:
            t = _ocr(v, cfg)
            score = _text_ratio(t)
            if score > best_score:
                best_text, best_score = t, score
    return best_text


def _ensure_rgb_jpeg_bytes(pil_img: Image.Image, max_side: int = 2400, quality: int = 88) -> bytes:
    img = pil_img.convert("RGB")
    w, h = img.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def _extract_text_from_resp(resp) -> str:
    try:
        if getattr(resp, "text", None):
            return resp.text.strip()
        if getattr(resp, "candidates", None):
            for c in resp.candidates:
                if getattr(c, "content", None) and getattr(c.content, "parts", None):
                    chunks = []
                    for p in c.content.parts:
                        t = getattr(p, "text", None)
                        if t:
                            chunks.append(t)
                    if chunks:
                        return "\n".join(chunks).strip()
        return ""
    except Exception:
        return ""


def _gemini_ocr_pil(pil_img: Image.Image, model: str = "gemini-2.5-flash") -> str:
    if not _gemini_available or _gem_client is None:
        raise RuntimeError("Gemini chưa sẵn (cài `google-genai` & cấu hình GEMINI_API_KEY).")
    jpeg = _ensure_rgb_jpeg_bytes(pil_img)
    contents = [
        gem_types.Part.from_bytes(data=jpeg, mime_type="image/jpeg"),
        "Extract all readable text (Vietnamese + English). Keep line breaks. Plain text only."
    ]
    resp = _gem_client.models.generate_content(model=model, contents=contents)
    text = _extract_text_from_resp(resp)
    if text:
        return text

    # Nếu rỗng: đẩy lí do cho dev/debug
    reason = getattr(resp, "candidates", [None])[0]
    finish = getattr(reason, "finish_reason", None) if reason else None
    safety = getattr(reason, "safety_ratings", None) if reason else None
    raise RuntimeError(f"Gemini trả rỗng. finish_reason={finish}; safety={safety}")


def image_to_text(image_path: str):
    """
    1) Tesseract trên ảnh đã tiền xử lý
    2) Nếu yếu/rỗng -> gọi Gemini (Google AI Studio)
    """
    try:
        processed_path = _preprocess_for_ocr(image_path)
        pil_proc = Image.open(processed_path)

        tess_text = _tesseract_try_all(pil_proc, lang="vie+eng")
        if _text_ratio(tess_text) >= 0.55 and tess_text.strip():
            return {"success": True, "text": tess_text}

        # Fallback sang Gemini
        pil_orig = Image.open(image_path) if os.path.exists(image_path) else pil_proc
        gem_text = _gemini_ocr_pil(pil_orig, model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
        return {"success": True, "text": gem_text}

    except Exception as e:
        # Trả lỗi rõ ràng để bạn biết đúng điểm nghẽn (SDK/key/model/safety/…)
        return {"success": False, "message": f"Lỗi Image OCR: {e}"}
