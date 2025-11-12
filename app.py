# app.py — Universal OCR App (final polished version with 2-column layout)
from io import BytesIO
import os
import io
import tempfile
import pandas as pd
import streamlit as st
import audiorecorder
from PIL import Image
from docx import Document

# ====== MODULES ======
from image_to_text import image_to_text
from pdf_to_text import pdf_to_text
from scan_to_text import scan_to_text
from speech_to_text import speech_to_text
from smart_ai_extract import analyze_document_ai

# ====== GOOGLE GENAI SDK ======
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "AIzaSyASIDdnathRVBROZpbKMmreESjj_HzPR0E")

try:
    from google import genai
    from google.genai import types as gem_types
    _gemini_available = True
    _gem_client = genai.Client()
except Exception:
    _gemini_available = False
    _gem_client = None

# ====== GEMINI HELPER ======
def _extract_text_from_resp(resp) -> str:
    try:
        if getattr(resp, "text", None):
            return resp.text.strip()
        if getattr(resp, "candidates", None):
            for c in resp.candidates:
                if getattr(c, "content", None) and getattr(c.content, "parts", None):
                    chunks = []
                    for p in c.content.parts:
                        if getattr(p, "text", None):
                            chunks.append(p.text)
                    if chunks:
                        return "\n".join(chunks).strip()
        return ""
    except Exception:
        return ""

# ====== PAGE CONFIG ======
st.set_page_config(page_title="Universal OCR App", page_icon="🧠", layout="wide")
st.title("🧠 Universal OCR App (Tesseract + Google Gemini AI)")

# ====== SIDEBAR ======
st.sidebar.header("⚙️ Settings")
lang = st.sidebar.radio("🌐 Language / Ngôn ngữ", ["English", "Tiếng Việt"], index=1)
engine = st.sidebar.radio("🧠 OCR Engine", ["Tesseract (Local)", "Google AI Studio (Gemini)"], index=1)
gem_model = st.sidebar.selectbox("🤖 Gemini Model", ["gemini-2.5-flash", "gemini-2.5-pro"], index=0)

modes = ["📸 Image", "📄 PDF", "📷 Scan", "🎤 Speech"] if lang == "English" else ["📸 Ảnh", "📄 PDF", "📷 Scan", "🎤 Giọng nói"]
mode = st.sidebar.radio("🧩 " + ("Select Mode" if lang == "English" else "Chọn chế độ"), modes)

# ====== Sidebar Descriptions ======
if "📸" in mode:
    st.sidebar.info("📸 " + ("Upload an image to extract or analyze text." if lang == "English" else "Tải lên ảnh để nhận diện hoặc phân tích văn bản."))
elif "📄" in mode:
    st.sidebar.info("📄 " + ("Upload a PDF file for OCR or AI extraction." if lang == "English" else "Tải lên file PDF để nhận diện hoặc phân tích."))
elif "📷" in mode:
    st.sidebar.info("📷 " + ("Use your camera to scan and extract text." if lang == "English" else "Dùng webcam để quét và nhận diện chữ."))
elif "🎤" in mode:
    st.sidebar.info("🎤 " + ("Record or upload audio to transcribe speech." if lang == "English" else "Ghi âm hoặc tải lên file giọng nói để nhận diện."))

# ====== IMAGE MODE ======
if mode in ["📸 Image", "📸 Ảnh"]:
    uploaded_file = st.file_uploader("📤 " + ("Upload image" if lang == "English" else "Tải lên ảnh"),
                                     type=["png", "jpg", "jpeg"])

    if uploaded_file:
        img_bytes = uploaded_file.read()
        col_left, col_right = st.columns([1.3, 1])  # chia layout: trái - phải

        # --- CỘT PHẢI: ẢNH XEM TRƯỚC ---
        with col_right:
            st.image(img_bytes, caption="🖼️ " + ("Uploaded Image" if lang == "English" else "Ảnh đã tải lên"), width=500)

        # --- CỘT TRÁI: KẾT QUẢ VÀ XỬ LÝ ---
        with col_left:
            st.subheader("📄 " + ("Text Extraction" if lang == "English" else "Nhận diện văn bản"))
            col1, col2 = st.columns(2)
            with col1:
                run_ocr = st.button("🧠 " + ("Tesseract OCR" if lang == "English" else "Nhận diện (Tesseract)"))
            with col2:
                run_ai = st.button("🤖 " + ("Gemini AI Analysis" if lang == "English" else "Phân tích bằng Gemini AI"))

            # --- TESSERACT ---
            if run_ocr:
                with st.spinner("🔍 " + ("Extracting text..." if lang == "English" else "Đang nhận diện...")):
                    temp_path = "temp_image.png"
                    with open(temp_path, "wb") as f:
                        f.write(img_bytes)
                    result = image_to_text(temp_path)
                    if result["success"]:
                        st.text_area("📜 " + ("Result" if lang == "English" else "Kết quả"),
                                     result["text"], height=350)
                        st.download_button("💾 TXT", result["text"], file_name="ocr_image.txt")
                    else:
                        st.error(result["message"])

            # --- GEMINI AI ---
            elif run_ai:
                with st.spinner("🔮 " + ("Analyzing with Gemini AI..." if lang == "English" else "Đang phân tích bằng Gemini AI...")):
                    ai_result = analyze_document_ai(img_bytes, file_type="image")
                    if ai_result["success"]:
                        st.session_state["ai_text"] = ai_result["text"]
                        st.session_state["manual_fields"] = {}  # reset selections
                        st.success("✅ " + ("AI Analysis Complete!" if lang == "English" else "Phân tích thành công!"))
                    else:
                        st.error(ai_result["message"])

        # --- KHI ĐÃ CÓ KẾT QUẢ AI ---
        if "ai_text" in st.session_state:
            ai_text = st.session_state["ai_text"]
            st.markdown("---")

            st.subheader("📑 " + ("Text Post-Processing" if lang == "English" else "Xử lý sau khi nhận diện"))

            # 2 chế độ trích xuất
            extract_mode = st.radio(
                "🧠 " + ("Select text extraction mode:" if lang == "English" else "Chọn cách trích xuất văn bản:"),
                ["📄 Full Text", "✅ Manual Field Selection"]
                if lang == "English"
                else ["📄 Lấy toàn bộ văn bản", "✅ Chọn thủ công các trường"],
                index=0
            )

            lines = [line.strip() for line in ai_text.split("\n") if line.strip()]
            filtered_text = ""

            # --- LẤY TOÀN BỘ ---
            if extract_mode.startswith("📄") or extract_mode.startswith("Full"):
                filtered_text = "\n".join(lines)

            # --- CHỌN THỦ CÔNG ---
            else:
                key_value_lines = [line for line in lines if ":" in line]

                # Nếu chưa có session state -> tạo mặc định
                if "manual_fields" not in st.session_state or not st.session_state["manual_fields"]:
                    st.session_state["manual_fields"] = {line: True for line in key_value_lines}

                st.write("🔍 " + ("Select fields to include:" if lang == "English" else "Chọn các trường muốn giữ lại:"))

                for line in key_value_lines:
                    k, v = line.split(":", 1)
                    key_name = f"chk_{line}"
                    if key_name not in st.session_state:
                        st.session_state[key_name] = st.session_state["manual_fields"].get(line, True)

                    # hiển thị checkbox (vẫn giữ trạng thái)
                    checked = st.checkbox(f"{k.strip()}: {v.strip()}", value=st.session_state[key_name], key=key_name)
                    st.session_state["manual_fields"][line] = checked

                selected_fields = [line for line, checked in st.session_state["manual_fields"].items() if checked]
                filtered_text = "\n".join(selected_fields) if selected_fields else "(Không có trường nào được chọn)"

            # --- HIỂN THỊ KẾT QUẢ ---
            st.text_area("📜 " + ("Processed Result" if lang == "English" else "Kết quả sau xử lý"),
                         filtered_text, height=350)

            # --- TẢI XUỐNG ---
            format_choice = st.radio("📥 " + ("Download format:" if lang == "English" else "Chọn định dạng tải xuống:"),
                                     ["TXT", "DOCX", "Excel"], horizontal=True)

            if format_choice == "TXT":
                st.download_button("💾 TXT", filtered_text, file_name="ai_result.txt")

            elif format_choice == "DOCX":
                doc = Document()
                doc.add_paragraph(filtered_text)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_doc:
                    doc.save(tmp_doc.name)
                    tmp_doc.seek(0)
                    st.download_button(
                        "💾 DOCX",
                        tmp_doc.read(),
                        file_name="ai_result.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

            elif format_choice == "Excel":
                lines_excel = [l for l in filtered_text.split("\n") if ":" in l]
                rows = [{"Field": k.strip(), "Value": v.strip()} for k, v in (line.split(":", 1) for line in lines_excel)]
                if rows:
                    df = pd.DataFrame(rows)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_xlsx:
                        df.to_excel(tmp_xlsx.name, index=False)
                        tmp_xlsx.seek(0)
                        st.download_button(
                            "💾 Excel",
                            tmp_xlsx.read(),
                            file_name="ai_result.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

# ====== PDF MODE ======
elif mode in ["📄 PDF"]:
    uploaded_pdf = st.file_uploader("📁 " + ("Upload PDF file" if lang == "English" else "Tải lên file PDF"), type=["pdf"])
    if uploaded_pdf:
        pdf_bytes = uploaded_pdf.read()
        col_left, col_right = st.columns([1.2, 1])

        with col_right:
            st.info("📄 " + ("PDF uploaded successfully." if lang == "English" else "Đã tải lên file PDF."))

        with col_left:
            st.subheader("📄 " + ("Process PDF" if lang == "English" else "Xử lý PDF"))
            col1, col2 = st.columns(2)
            with col1:
                run_ocr = st.button("🧠 OCR PDF")
            with col2:
                run_ai = st.button("🤖 Gemini AI")

            if run_ocr:
                with st.spinner("📄 Processing PDF..."):
                    result = pdf_to_text("temp_pdf.pdf")
                    if result["success"]:
                        st.text_area("📜 Result", result["text"], height=350)
                        st.download_button("💾 Download TXT", result["text"], file_name="pdf_result.txt")
                    else:
                        st.error(result["message"])

            elif run_ai:
                with st.spinner("🔮 Analyzing PDF..."):
                    ai_result = analyze_document_ai(pdf_bytes, file_type="pdf")
                    if ai_result["success"]:
                        st.text_area("📜 AI Result", ai_result["text"], height=350)
                        st.download_button("💾 TXT", ai_result["text"], file_name="ai_pdf_result.txt")
                    else:
                        st.error(ai_result["message"])

# ====== SCAN MODE ======
elif mode in ["📷 Scan"]:
    st.caption("💡 " + ("Tip: Ensure good lighting and flat paper." if lang == "English" else "Mẹo: Đặt giấy phẳng, đủ sáng."))
    cam = st.camera_input("📸 " + ("Take a photo" if lang == "English" else "Chụp ảnh"))
    if cam:
        img_bytes = cam.getvalue()
        col_left, col_right = st.columns([1.2, 1])

        with col_right:
            st.image(img_bytes, caption="📷 " + ("Captured Image" if lang == "English" else "Ảnh đã chụp"), width=500)

        with col_left:
            st.subheader("📄 " + ("Scan Result" if lang == "English" else "Kết quả quét"))
            result = scan_to_text(img_bytes, lang=lang)
            if result["success"]:
                st.text_area("📜 Result", result["text"], height=350)
                st.download_button("💾 TXT", result["text"], file_name="scan_result.txt")
            else:
                st.error(result["message"])

# ====== SPEECH MODE ======
elif mode in ["🎤 Speech", "🎤 Giọng nói"]:
    choice = st.radio("🎧 " + ("Choose method:" if lang == "English" else "Chọn phương thức:"),
                      ["🎙️ " + ("Record" if lang == "English" else "Ghi âm"),
                       "📁 " + ("Upload file" if lang == "English" else "Tải file âm thanh")])
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        if "Record" in choice or "Ghi" in choice:
            audio = audiorecorder.audiorecorder(
                "🎙️ " + ("Start Recording" if lang == "English" else "Bắt đầu ghi âm"),
                "🛑 " + ("Stop" if lang == "English" else "Dừng")
            )
            if len(audio) > 0:
                buf = BytesIO()
                audio.export(buf, format="wav")
                wav_bytes = buf.getvalue()
                st.audio(wav_bytes, format="audio/wav")
                if st.button("🧠 " + ("Transcribe" if lang == "English" else "Nhận diện")):
                    result = speech_to_text(audio_bytes=wav_bytes, lang=lang)
                    if result["success"]:
                        st.text_area("📜 Result", result["text"], height=350)
                        st.download_button("💾 TXT", result["text"], file_name="speech_result.txt")
                    else:
                        st.error(result["message"])
        else:
            up = st.file_uploader("📁 " + ("Upload audio" if lang == "English" else "Chọn file âm thanh"),
                                  type=["wav", "mp3", "m4a", "aac", "ogg", "flac"])
            if up:
                st.audio(up)
                if st.button("🧠 " + ("Recognize" if lang == "English" else "Nhận diện file")):
                    result = speech_to_text(uploaded_file=up, lang=lang)
                    if result["success"]:
                        st.text_area("📜 Result", result["text"], height=350)
                        st.download_button("💾 TXT", result["text"], file_name="audio_result.txt")
                    else:
                        st.error(result["message"])

    with col_right:
        st.info("🎤 " + ("Upload or record audio to convert speech to text." if lang == "English" else "Ghi âm hoặc tải file giọng nói để nhận diện."))
