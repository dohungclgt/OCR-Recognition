from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from io import BytesIO
import os
import math

# ⚙️ Đặt API key của bạn ở đây (đừng commit public)
os.environ["GEMINI_API_KEY"] = "Your API Key Here"

# Kích hoạt cấu hình Tesseract từ config.py
try:
    import config  # noqa: F401
except Exception:
    pass

# ============ Tích hợp Gemini ============
try:
    from google import genai
    from google.genai import types as gem_types
    _gemini_available = True
except Exception:
    _gemini_available = False


def _ensure_rgb_jpeg(pil_img: Image.Image, max_side: int = 1800, jpeg_quality: int = 85) -> bytes:
    img = pil_img.convert("RGB")
    w, h = img.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
    return buf.getvalue()


def _gemini_ocr_page(pil_img: Image.Image, model: str = "gemini-2.5-flash") -> str:
    if not _gemini_available:
        raise RuntimeError("google-genai chưa được cài. Chạy: pip install -U google-genai")
    client = genai.Client()
    jpeg_bytes = _ensure_rgb_jpeg(pil_img)
    parts = [
        gem_types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
        "Extract readable text (Vietnamese + English). Keep line breaks. Plain text only."
    ]
    resp = client.models.generate_content(model=model, contents=parts)
    return (getattr(resp, "text", "") or "").strip()


def pdf_to_text(pdf_path: str, engine: str = "tesseract", model: str = "gemini-2.5-flash"):
    """
    engine: 'tesseract' (local) | 'gemini' (Google AI Studio)
    """
    try:
        # Poppler path (sửa đúng nếu bạn không thêm vào PATH)
        poppler_path = r"C:\Program Files\poppler-25.07.0\Library\bin"

        temp_dir = "temp_pdf_images"
        os.makedirs(temp_dir, exist_ok=True)

        pages = convert_from_path(
            pdf_path,
            dpi=300 if engine == "tesseract" else 200,
            fmt="png",
            poppler_path=poppler_path
        )

        all_text = ""
        if engine == "tesseract":
            for i, page in enumerate(pages):
                image_path = os.path.join(temp_dir, f"page_{i+1}.png")
                page.save(image_path, "PNG")
                text = pytesseract.image_to_string(Image.open(image_path), lang="vie+eng")
                all_text += f"\n\n--- Trang {i+1} ---\n{text}"
        elif engine == "gemini":
            for i, page in enumerate(pages, start=1):
                text = _gemini_ocr_page(page, model)
                all_text += f"\n\n--- Trang {i} ---\n{text}"
        else:
            return {"success": False, "message": f"Engine không hợp lệ: {engine}"}

        # Dọn dẹp
        try:
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)
        except Exception:
            pass

        if not all_text.strip():
            return {"success": False, "message": "Không phát hiện được chữ trong PDF."}
        return {"success": True, "text": all_text}

    except Exception as e:
        return {"success": False, "message": f"Lỗi xử lý PDF: {e}"}
