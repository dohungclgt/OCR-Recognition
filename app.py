# app.py — Universal OCR App (Pro UI + Hướng dẫn + Page Transition + Quick Summary)
from io import BytesIO
import os
import tempfile
import streamlit as st
import audiorecorder

# ====== Logic modules (theo dự án của bạn) ======
from image_to_text import image_to_text
from pdf_to_text import pdf_to_text
from speech_to_text import speech_to_text
from smart_ai_extract import analyze_document_ai
from scan_to_text import scan_to_text  # bản của bạn (có/không có engine tuỳ phiên bản)

# ====== UI layer (từ frontend.py) ======
from frontend import (
    get_ui_prefs, inject_theme_css, hero_header, breadcrumbs, divider,
    section, callout, checklist, manual_kv_selector_ui, download_block, two_columns, contextual_help,
    begin_route_transition, transition_container_start, transition_container_end, transition_overlay,
    quick_summary
)

# ====================== PAGE CONFIG & GLOBALS ======================
st.set_page_config(page_title="Universal OCR App", page_icon="🧠", layout="wide")
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "Your API Key Here")

# Sidebar: Language + Theme
ui = get_ui_prefs()
st.session_state.setdefault("ui_lang", ui["lang"])  # tránh xung đột key widget
inject_theme_css(ui["theme"])

# Sidebar: Engine / Model / Mode
st.sidebar.subheader("🧠 OCR Engine")
engine_choice = st.sidebar.radio("Engine", ["Tesseract (Local)", "Google AI Studio (Gemini)"], index=1, key="global_engine")
gem_model = st.sidebar.selectbox("🤖 Gemini Model", ["gemini-2.5-flash", "gemini-2.5-pro"], index=0, key="global_model")

modes = ["📸 Image", "📄 PDF", "📷 Scan", "🎤 Speech"] if ui["lang"] == "English" else ["📸 Ảnh", "📄 PDF", "📷 Quét", "🎤 Giọng nói"]
mode = st.sidebar.radio("🧩 " + ("Select Mode" if ui["lang"] == "English" else "Chọn chế độ"), modes, index=0, key="global_mode")

# Header & contextual help + quick summary
hero_header(
    "Universal OCR App",
    "Tesseract OCR + Google Gemini AI · Image · PDF · Scan · Speech" if ui["lang"]=="English"
    else "Tesseract OCR + Google Gemini AI · Ảnh · PDF · Quét · Giọng nói",
    badge="v2025.11",
    icon="🧠"
)
breadcrumbs(["Home", mode])
quick_summary(mode, ui["lang"])   # Ô tóm tắt nhanh ngay theo chế độ
contextual_help(mode, ui["lang"])
divider()

def _is_en() -> bool:
    return ui["lang"] == "English"

# ====== KÍCH HOẠT ANIMATION CHUYỂN TRANG ======
begin_route_transition(mode)
transition_container_start()

# =============================== IMAGE MODE ===============================
if mode in ["📸 Image", "📸 Ảnh"]:
    section("📸 Image" if _is_en() else "📸 Ảnh",
            "Upload an image and extract its text." if _is_en() else "Tải một ảnh và nhận diện văn bản.",
            icon="🖼️")

    uploaded_img = st.file_uploader("📤 Upload image" if _is_en() else "📤 Tải lên ảnh",
                                    type=["png", "jpg", "jpeg"], key="img_uploader")

    if uploaded_img:
        img_bytes = uploaded_img.read()
        left, right = two_columns(1.3, 1.0)

        with right:
            st.image(img_bytes, caption="🖼️ Uploaded Image" if _is_en() else "🖼️ Ảnh đã tải",
                     use_container_width=True)

        with left:
            st.subheader("📄 Text Extraction" if _is_en() else "📄 Nhận diện văn bản")
            c1, c2 = st.columns(2)
            with c1:
                run_tess = st.button("🧠 Tesseract OCR", key="img_btn_tess")
            with c2:
                run_ai = st.button("🤖 Gemini AI Analysis", key="img_btn_ai")

            # Tesseract branch
            if run_tess:
                with st.spinner("🔍 Extracting..." if _is_en() else "🔍 Đang nhận diện..."):
                    tmp_path = "temp_image.png"
                    with open(tmp_path, "wb") as f:
                        f.write(img_bytes)
                    result = image_to_text(tmp_path)
                    if result.get("success"):
                        st.text_area("📜 Result" if _is_en() else "📜 Kết quả",
                                     result["text"], height=350, key="img_tess_result")
                        st.download_button("💾 TXT", result["text"], file_name="ocr_image.txt", key="img_tess_dl")
                    else:
                        st.error(result.get("message", "Error"))

            # Gemini branch
            if run_ai:
                with st.spinner("🔮 Analyzing with Gemini..." if _is_en() else "🔮 Đang phân tích bằng Gemini..."):
                    ai_result = analyze_document_ai(img_bytes, file_type="image")
                    if ai_result.get("success"):
                        st.session_state["img_ai_text"] = ai_result["text"]
                        st.success("✅ Done!" if _is_en() else "✅ Hoàn tất!")
                    else:
                        st.error(ai_result.get("message", "AI error"))

        # Hậu xử lý/phân loại (Image)
        if "img_ai_text" in st.session_state:
            divider("Post-processing" if _is_en() else "Hậu xử lý")
            extract_mode = st.radio(
                "🧠 Select extraction mode:" if _is_en() else "🧠 Chọn cách trích xuất:",
                ["📄 Full Text", "✅ Manual Field Selection"] if _is_en() else ["📄 Lấy toàn bộ văn bản", "✅ Chọn thủ công các trường"],
                horizontal=True,
                key="img_extract_mode"
            )

            lines = [ln.strip() for ln in st.session_state["img_ai_text"].split("\n") if ln.strip()]
            if extract_mode.startswith("📄") or extract_mode.startswith("Full"):
                filtered_text = "\n".join(lines)
            else:
                filtered_text, _ = manual_kv_selector_ui(st.session_state["img_ai_text"], ui["lang"], session_prefix="img")

            st.text_area("📜 Processed Result" if _is_en() else "📜 Kết quả sau xử lý",
                         filtered_text, height=350, key="img_processed")
            download_block(filtered_text, "ai_result", "img_dl")

# =============================== PDF MODE ===============================
elif mode in ["📄 PDF"]:
    section("📄 PDF",
            "Upload a PDF and choose OCR engine." if _is_en() else "Tải một file PDF và chọn engine OCR.",
            icon="📄")

    uploaded_pdf = st.file_uploader("📁 Upload PDF file" if _is_en() else "📁 Tải lên file PDF",
                                    type=["pdf"], key="pdf_uploader")

    if uploaded_pdf:
        pdf_bytes = uploaded_pdf.read()
        left, right = two_columns(1.2, 1.0)

        with right:
            st.info("📄 PDF uploaded successfully." if _is_en() else "📄 Đã tải PDF.")

        with left:
            st.subheader("⚙️ Process PDF" if _is_en() else "⚙️ Xử lý PDF")
            c1, c2 = st.columns(2)
            with c1:
                run_tess = st.button("🧠 OCR PDF (Tesseract)", key="pdf_btn_tess")
            with c2:
                run_ai = st.button("🤖 Gemini AI (PDF)", key="pdf_btn_ai")

            # Tesseract OCR for PDF: ghi file tạm
            if run_tess:
                with st.spinner("📄 Processing PDF..." if _is_en() else "📄 Đang xử lý PDF..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                        tmp_pdf.write(pdf_bytes)
                        tmp_pdf_path = tmp_pdf.name
                    result = pdf_to_text(tmp_pdf_path, engine="tesseract")
                    try:
                        os.remove(tmp_pdf_path)
                    except Exception:
                        pass

                    if result.get("success"):
                        st.text_area("📜 Result" if _is_en() else "📜 Kết quả",
                                     result["text"], height=350, key="pdf_tess_result")
                        st.download_button("💾 TXT", result["text"], file_name="pdf_result.txt", key="pdf_tess_dl")
                    else:
                        st.error(result.get("message", "Error"))

            # Gemini AI for PDF: dùng bytes trực tiếp
            if run_ai:
                with st.spinner("🔮 Analyzing PDF with Gemini..." if _is_en() else "🔮 Đang phân tích PDF bằng Gemini..."):
                    ai_result = analyze_document_ai(pdf_bytes, file_type="pdf")
                    if ai_result.get("success"):
                        st.session_state["pdf_ai_text"] = ai_result["text"]
                        st.success("✅ Done!" if _is_en() else "✅ Hoàn tất!")
                    else:
                        st.error(ai_result.get("message", "AI error"))

        # Hậu xử lý/phân loại (PDF)
        if "pdf_ai_text" in st.session_state:
            divider("Post-processing" if _is_en() else "Hậu xử lý")
            extract_mode = st.radio(
                "🧠 Select extraction mode:" if _is_en() else "🧠 Chọn cách trích xuất:",
                ["📄 Full Text", "✅ Manual Field Selection"] if _is_en() else ["📄 Lấy toàn bộ văn bản", "✅ Chọn thủ công các trường"],
                horizontal=True,
                key="pdf_extract_mode"
            )

            lines = [ln.strip() for ln in st.session_state["pdf_ai_text"].split("\n") if ln.strip()]
            if extract_mode.startswith("📄") or extract_mode.startswith("Full"):
                filtered_text = "\n".join(lines)
            else:
                filtered_text, _ = manual_kv_selector_ui(st.session_state["pdf_ai_text"], ui["lang"], session_prefix="pdf")

            st.text_area("📜 Processed Result" if _is_en() else "📜 Kết quả sau xử lý",
                         filtered_text, height=350, key="pdf_processed")
            download_block(filtered_text, "ai_pdf_result", "pdf_dl")

# =============================== SCAN MODE ===============================
elif mode in ["📷 Scan", "📷 Quét"]:
    section("📷 Scan" if _is_en() else "📷 Quét",
            "Capture with webcam, then OCR." if _is_en() else "Chụp bằng webcam rồi OCR.",
            icon="📷")

    # Một số bạn đã nâng cấp scan_to_text(engine="gemini"); ta gọi an toàn:
    scan_engine = st.radio("🧠 Engine", ["Gemini", "Tesseract"], horizontal=True, index=0, key="scan_engine")
    cam = st.camera_input("📸 Take a photo" if _is_en() else "📸 Chụp ảnh", key="scan_cam")

    if cam:
        img_bytes = cam.getvalue()
        left, right = two_columns(1.2, 1.0)

        with right:
            st.image(img_bytes, caption="📷 Captured Image" if _is_en() else "📷 Ảnh đã chụp",
                     width='stretch')

        with left:
            st.subheader("📄 Scan Result" if _is_en() else "📄 Kết quả quét")

            # Gọi linh hoạt tuỳ phiên bản scan_to_text (có/không có engine)
            try:
                if scan_engine == "Gemini":
                    result = scan_to_text(img_bytes, lang=ui["lang"], engine="gemini", gem_model=gem_model)
                else:
                    result = scan_to_text(img_bytes, lang=ui["lang"], engine="tesseract")
            except TypeError:
                # Fall back: phiên bản cũ chỉ nhận (image_bytes, lang)
                result = scan_to_text(img_bytes, lang=ui["lang"])

            if result.get("success"):
                st.text_area("📜 Result" if _is_en() else "📜 Kết quả",
                             result["text"], height=350, key="scan_result")
                st.download_button("💾 TXT", result["text"], file_name="scan_result.txt", key="scan_dl")
            else:
                st.error(result.get("message", "Scan error"))

# =============================== SPEECH MODE ===============================
elif mode in ["🎤 Speech", "🎤 Giọng nói"]:
    section("🎤 Speech" if _is_en() else "🎤 Giọng nói",
            "Record or upload audio, then transcribe." if _is_en() else "Ghi âm hoặc tải file âm thanh để nhận diện.",
            icon="🎧")

    choice = st.radio(
        "🎧 Choose method:" if _is_en() else "🎧 Chọn phương thức:",
        ["🎙️ Record" if _is_en() else "🎙️ Ghi âm",
         "📁 Upload file" if _is_en() else "📁 Tải file âm thanh"],
        key="sp_mode"
    )
    left, right = two_columns(1.2, 1.0)

    with left:
        if "Record" in choice or "Ghi" in choice:
            audio = audiorecorder.audiorecorder(
                "🎙️ Start Recording" if _is_en() else "🎙️ Bắt đầu ghi âm",
                "🛑 Stop" if _is_en() else "🛑 Dừng",
                key="sp_rec"
            )
            if len(audio) > 0:
                buf = BytesIO()
                audio.export(buf, format="wav")
                wav_bytes = buf.getvalue()
                st.audio(wav_bytes, format="audio/wav")
                if st.button("🧠 Transcribe" if _is_en() else "🧠 Nhận diện", key="sp_btn_recognize"):
                    result = speech_to_text(audio_bytes=wav_bytes, lang=ui["lang"])
                    if result.get("success"):
                        st.text_area("📜 Result" if _is_en() else "📜 Kết quả",
                                     result["text"], height=350, key="sp_text_res")
                        st.download_button("💾 TXT", result["text"], file_name="speech_result.txt", key="sp_txt_dl")
                    else:
                        st.error(result.get("message", "Speech error"))
        else:
            up = st.file_uploader("📁 Upload audio" if _is_en() else "📁 Chọn file âm thanh",
                                  type=["wav", "mp3", "m4a", "aac", "ogg", "flac"],
                                  key="sp_uploader")
            if up:
                st.audio(up)
                if st.button("🧠 Recognize file" if _is_en() else "🧠 Nhận diện file", key="sp_btn_file"):
                    result = speech_to_text(uploaded_file=up, lang=ui["lang"])
                    if result.get("success"):
                        st.text_area("📜 Result" if _is_en() else "📜 Kết quả",
                                     result["text"], height=350, key="sp_file_res")
                        st.download_button("💾 TXT", result["text"], file_name="audio_result.txt", key="sp_file_dl")
                    else:
                        st.error(result.get("message", "Speech error"))

    with right:
        tip = "Upload or record audio to convert speech to text." if _is_en() else "Ghi âm hoặc tải file giọng nói để nhận diện."
        callout("info", "🎤 " + tip)

# ====== KẾT THÚC VÙNG NỘI DUNG + OVERLAY CHUYỂN TRANG ======
transition_container_end()
transition_overlay()
