"""
smart_ai_extract.py — Gemini AI Auto Language Detection
----------------------------------------------------------
Phân tích tài liệu (ảnh hoặc PDF) và tự động phát hiện ngôn ngữ.
Trích xuất văn bản, nhận dạng các trường thông tin nếu có, và tóm tắt nội dung.
Kết quả được phản hồi cùng ngôn ngữ của tài liệu.
"""

import tempfile
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import os

# ⚙️ Load API key từ .env hoặc biến môi trường
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "AIzaSyASIDdnathRVBROZpbKMmreESjj_HzPR0E"))

# 🧠 Hàm chính
def analyze_document_ai(file_data: bytes, file_type: str = "image"):
    """
    Phân tích tài liệu bằng Google Gemini AI (tự động phát hiện ngôn ngữ).
    - file_type: "image" hoặc "pdf"
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")  # Dùng model mạnh để OCR chính xác hơn

        # ==================== PROMPT TỰ ĐỘNG NHẬN DIỆN NGÔN NGỮ ====================
        prompt = """
        You are an intelligent OCR and document analysis assistant.
        Read this image or PDF carefully.

        1️⃣ Automatically detect the document's language (English, Vietnamese, or others).
        2️⃣ Extract all readable text accurately.
        3️⃣ If the document is structured (e.g., ID, certificate, contract, invoice):
            - Identify and clearly label the following information if found:
              • Document Type
              • Full Name / Organization
              • Date of Birth / Date Issued
              • Place of Birth / Issued by
              • Reference Number / Serial Number
            - Write a short summary explaining what the document represents.
        4️⃣ If the document is unstructured (like an article, paragraph, or note):
            - Return the readable text as-is and provide a short summary.

        ⚙️ Response Rules:
        - Respond entirely in the **same language as the document**.
        - Keep it clean, human-readable (no JSON, no numbered lists).
        - Preserve natural line breaks and formatting.
        - If the text mixes English and Vietnamese, respond in the **dominant language**.
        """

        # ==================== XỬ LÝ FILE THEO LOẠI ====================
        if file_type == "image":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(file_data)
                tmp_path = tmp.name
            img = Image.open(tmp_path)
            response = model.generate_content([prompt, img])

        elif file_type == "pdf":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_data)
                tmp_path = tmp.name
            pdf_data = open(tmp_path, "rb").read()
            response = model.generate_content([
                prompt,
                {"mime_type": "application/pdf", "data": pdf_data}
            ])

        else:
            return {"success": False, "message": f"❌ Không hỗ trợ loại file: {file_type}"}

        # ==================== TRÍCH XUẤT KẾT QUẢ ====================
        result_text = getattr(response, "text", "").strip()
        if not result_text:
            return {"success": False, "message": "⚠️ Không nhận được phản hồi từ Gemini AI."}

        return {"success": True, "text": result_text}

    except Exception as e:
        return {"success": False, "message": f"⚠️ Lỗi khi xử lý AI: {e}"}


# ==================== TEST LOCAL ====================
if __name__ == "__main__":
    print("🧠 Test Gemini Auto Language OCR")
    try:
        with open("test_image.png", "rb") as f:
            res = analyze_document_ai(f.read(), file_type="image")
            if res["success"]:
                print("\n✅ Kết quả OCR:")
                print(res["text"])
            else:
                print("\n❌ Lỗi:", res["message"])
    except FileNotFoundError:
        print("⚠️ Không tìm thấy test_image.png, hãy đặt ảnh test cùng thư mục.")
