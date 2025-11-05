# app.py — VIP UI (3 theme), giữ nguyên logic gọi các hàm OCR
from io import BytesIO
import audiorecorder
import streamlit as st
from image_to_text import image_to_text
from pdf_to_text import pdf_to_text
from scan_to_text import scan_to_text
from speech_to_text import speech_to_text

# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="Universal OCR App", page_icon="🧠", layout="wide")

# ===================== SIDEBAR SETTINGS =====================
st.sidebar.header("⚙️ Settings")

# Theme switcher (chỉ là CSS thay đổi — không cần lib ngoài)
ui_theme = st.sidebar.selectbox(
    "🎨 Theme",
    ["✨ Neon Cyber", "🧊 Glass Morph", "🌚 Minimal Dark"],
    index=0
)

lang = st.sidebar.radio("🌐 Language / Ngôn ngữ", ["English", "Tiếng Việt"])

if lang == "English":
    sidebar_info = {
        "📸 Image": "Upload an image (PNG/JPG/JPEG) to extract text using OCR.",
        "📄 PDF": "Upload a PDF to extract text from scanned pages.",
        "📷 Scan": "Use your webcam to scan a document.",
        "🎤 Speech": "Record or upload audio to convert speech to text."
    }
else:
    sidebar_info = {
        "📸 Ảnh": "Tải ảnh (PNG/JPG/JPEG) để nhận diện chữ.",
        "📄 PDF": "Tải file PDF để trích xuất chữ từ trang quét.",
        "📷 Scan": "Dùng webcam để quét tài liệu.",
        "🎤 Giọng nói": "Ghi âm hoặc tải file để chuyển giọng nói thành văn bản."
    }

mode = st.sidebar.radio(
    "🧩 " + ("Select Mode" if lang == "English" else "Chọn chế độ"),
    list(sidebar_info.keys())
)
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ " + ("Description" if lang == "English" else "Mô tả"))
st.sidebar.info(sidebar_info[mode])

# ===================== THEME CSS =====================
def inject_css(theme: str):
    common = """
    <style>
    /* Global */
    .stApp {
      color: #eaf3ff;
      font-family: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Apple Color Emoji","Segoe UI Emoji";
    }
    /* Hide default block gap a bit */
    .block-container { padding-top: 1.2rem; }
    /* Section Card */
    .outer-card {
      border-radius: 18px;
      padding: 20px 18px;
      border: 1px solid rgba(255,255,255,0.14);
    }
    /* Header title animation */
    .title-hero {
      text-align: center;
      font-weight: 900;
      font-size: 46px;
      letter-spacing: .6px;
      margin: 0 0 6px 0;
      background: linear-gradient(90deg, #7af5ff, #8ef6a0, #ff93e1, #7af5ff);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      animation: hue 9s linear infinite;
    }
    @keyframes hue {
      0%{filter:hue-rotate(0deg)} 100%{filter:hue-rotate(360deg)}
    }
    .title-sub {
      text-align: center;
      color: #b9dfff;
      margin-bottom: 1.0rem;
      opacity: .9;
    }
    /* Buttons */
    div.stButton > button {
      width: 100% !important;
      border-radius: 12px;
      padding: 11px 14px;
      font-size: 17px;
      font-weight: 800;
      border: 0;
      transition: transform .15s ease, box-shadow .18s ease, opacity .2s ease;
    }
    div.stButton > button:hover { transform: translateY(-1px) scale(1.02); }

    /* Sidebar aesthetic */
    [data-testid="stSidebar"] {
      border-right: 1px solid rgba(255,255,255,0.12);
      backdrop-filter: blur(8px);
    }

    /* Result box */
    .result-box {
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.18);
      border-radius: 12px;
      padding: 14px;
      white-space: pre-wrap;
      font-size: 16px;
      max-height: 320px;
      overflow-y: auto;
    }
    .badge {
      display:inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 12px;
      letter-spacing: .3px;
      margin: 0 6px 12px 0;
    }
    </style>
    """
    neon = """
    <style>
    .stApp { 
      background: radial-gradient(1200px 600px at 10% -20%, #0b1f3f77 0%, transparent 60%),
                  radial-gradient(1200px 600px at 90% 120%, #1c114fcc 0%, transparent 60%),
                  linear-gradient(135deg, #050a1b 0%, #040a18 35%, #02030a 100%);
    }
    .outer-card {
      background: rgba(0, 10, 30, 0.55);
      box-shadow: 0 12px 34px rgba(0, 255, 255, 0.16), inset 0 0 0 1px rgba(0,255,255,.08);
    }
    h1, h2, h3, label, .stRadio, .stSelectbox, .stFileUploader, textarea, input, .stAlert { color: #eaf3ff !important; }
    div.stButton > button { background: linear-gradient(90deg, #00eaff, #0077ff); color: #041121 !important; box-shadow: 0 0 14px #00eaff55; }
    div.stButton > button:hover { box-shadow: 0 0 24px #00eaffaa; }
    [data-testid="stSidebar"] { background: rgba(0,0,0,.35); }
    .badge { background: #071b35; border:1px solid #2bdcff; color:#8fe9ff; }
    </style>
    """
    glass = """
    <style>
    .stApp {
      background: linear-gradient(135deg, #0c111b 0%, #0f1626 100%);
    }
    .outer-card {
      background: rgba(255,255,255,0.08);
      backdrop-filter: blur(14px);
      box-shadow: 0 10px 30px rgba(0,0,0,0.28);
    }
    h1, h2, h3, label, .stRadio, .stSelectbox, .stFileUploader, textarea, input, .stAlert { color: #eaf3ff !important; }
    div.stButton > button { background: linear-gradient(90deg, #89f7fe 0%, #66a6ff 100%); color: #0c1020 !important; }
    [data-testid="stSidebar"] { background: rgba(255,255,255,0.06); }
    .badge { background: #ffffff12; border:1px solid #cde7ff66; color:#cfe7ff; }
    </style>
    """
    minimal = """
    <style>
    .stApp { background: #0b0d13; }
    .outer-card { background: #121521; box-shadow: 0 8px 28px rgba(0,0,0,.45); }
    h1, h2, h3, label, .stRadio, .stSelectbox, .stFileUploader, textarea, input, .stAlert { color: #e0e6f5 !important; }
    div.stButton > button { background: #2b63ff; color: #fff !important; }
    [data-testid="stSidebar"] { background: #0e111a; }
    .badge { background: #101320; border:1px solid #2b63ff66; color:#bcd1ff; }
    </style>
    """
    st.markdown(common, unsafe_allow_html=True)
    if theme.startswith("✨"): st.markdown(neon, unsafe_allow_html=True)
    elif theme.startswith("🧊"): st.markdown(glass, unsafe_allow_html=True)
    else: st.markdown(minimal, unsafe_allow_html=True)

inject_css(ui_theme)

# ===================== TITLE =====================
st.markdown("<div class='title-hero'>Universal OCR AI Suite</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='title-sub'>Advanced AI-powered Extraction from <b>Image · PDF · Camera · Voice</b></div>",
    unsafe_allow_html=True
)
st.markdown(
    "<span class='badge'>⚡ Real-time</span><span class='badge'>🧪 Pro Scan</span><span class='badge'>🎙 Speech</span><span class='badge'>🧊 Multi-theme</span>",
    unsafe_allow_html=True
)

# =============== Helper: pretty result box ===============
def show_result_box(text: str, height: int = 320, filename: str = "ocr_result.txt"):
    st.success("✅ " + ("Done! Detected text:" if lang == "English" else "Hoàn tất! Văn bản nhận được:"))
    st.markdown(f"<div class='result-box' style='max-height:{height}px'>{text}</div>", unsafe_allow_html=True)
    st.download_button(
        "💾 " + ("Download text" if lang == "English" else "Tải kết quả"),
        text, file_name=filename
    )

# ===================== MODES =====================

# === IMAGE MODE ===
if mode in ["📸 Ảnh", "📸 Image"]:
    st.markdown("<div class='outer-card'>", unsafe_allow_html=True)
    st.subheader("🖼️ " + ("Image to Text" if lang == "English" else "Chuyển Ảnh thành Văn bản"))
    col1, col2, col3 = st.columns([1, 1, 1.2], vertical_alignment="top")

    with col1:
        uploaded_file = st.file_uploader(
            "📤 " + ("Upload Image" if lang == "English" else "Tải lên ảnh"),
            type=["png", "jpg", "jpeg"]
        )
        if uploaded_file:
            temp_path = "uploaded_image.png"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            if st.button("🧠 " + ("Recognize Text" if lang == "English" else "Nhận diện chữ"), use_container_width=True):
                with st.spinner("🚀 " + ("AI is reading your image..." if lang == "English" else "AI đang xử lý ảnh...")):
                    result = image_to_text(temp_path)
                if result.get("success"):
                    st.session_state["img_result"] = result.get("text", "")
                else:
                    st.error(result.get("message", "Error"))

    with col2:
        if uploaded_file:
            st.image(temp_path, caption="Preview", use_column_width=True)

    with col3:
        if "img_result" in st.session_state:
            show_result_box(st.session_state["img_result"], height=320, filename="image_result.txt")
    st.markdown("</div>", unsafe_allow_html=True)

# === PDF MODE ===
elif mode in ["📄 PDF", "📄 Pdf"]:
    st.markdown("<div class='outer-card'>", unsafe_allow_html=True)
    st.subheader("📄 " + ("PDF to Text" if lang == "English" else "Chuyển PDF thành Văn bản"))
    uploaded_pdf = st.file_uploader(
        "📁 " + ("Upload PDF file" if lang == "English" else "Tải lên file PDF"),
        type=["pdf"]
    )
    if uploaded_pdf:
        temp_path = "uploaded_file.pdf"
        with open(temp_path, "wb") as f:
            f.write(uploaded_pdf.read())
        if st.button("🧠 " + ("Extract Text" if lang == "English" else "Nhận diện chữ từ PDF")):
            with st.spinner("🚀 " + ("AI is reading your PDF..." if lang == "English" else "AI đang xử lý PDF...")):
                result = pdf_to_text(temp_path)
            if result.get("success"):
                show_result_box(result.get("text", ""), height=360, filename="pdf_result.txt")
            else:
                st.error(result.get("message", "Error"))
    st.markdown("</div>", unsafe_allow_html=True)

# === SCAN MODE ===
elif mode in ["📷 Scan", "📷 Scan"]:
    st.markdown("<div class='outer-card'>", unsafe_allow_html=True)
    st.subheader("📷 Smart Document Scanner")
    st.caption("Tip: " + ("Place paper flat, bright lighting, fill the frame."
                           if lang == "English"
                           else "Đặt giấy phẳng, đủ sáng, lấp đầy khung."))

    # Tuỳ chọn hiển thị nhanh/chất lượng (không đổi pipeline gọi, chỉ hiển thị)
    colq, colp = st.columns(2)
    with colq:
        quick = st.toggle("⚡ " + ("Quick preview" if lang == "English" else "Xem nhanh"), value=False)
    with colp:
        st.caption("🧪 " + ("Pro pipeline is auto-selected under the hood." if lang == "English" else "Pipeline Pro tự động thử nhiều cách."))

    enable_cam = st.toggle("📷 " + ("Enable Camera" if lang == "English" else "Bật/Tắt Camera"))
    if enable_cam:
        camera_image = st.camera_input("📸 " + ("Take a picture" if lang == "English" else "Chụp ảnh"))
        if camera_image is not None:
            if st.button("🧠 " + ("Scan Text" if lang == "English" else "Nhận diện chữ từ ảnh đã chụp")):
                with st.spinner("🚀 " + ("Enhancing & reading..." if lang == "English" else "Đang làm sạch & đọc...")):
                    result = scan_to_text(camera_image.getvalue(), lang=lang)
                if result.get("success"):
                    show_result_box(result.get("text", ""), height=300, filename="scan_result.txt")
                else:
                    st.error(result.get("message", "Error"))
    st.markdown("</div>", unsafe_allow_html=True)

# === SPEECH MODE ===
elif mode in ["🎤 Giọng nói", "🎤 Speech"]:
    st.markdown("<div class='outer-card'>", unsafe_allow_html=True)
    st.subheader("🎙️ " + ("Speech to Text" if lang == "English" else "Chuyển Giọng nói thành Văn bản"))
    choice = st.radio(
        "🎧 " + ("Select method:" if lang == "English" else "Lựa chọn:"),
        ["🎙️ " + ("Record directly" if lang == "English" else "Ghi âm trực tiếp"),
         "📁 " + ("Upload audio file" if lang == "English" else "Tải lên file giọng nói")]
    )

    # --- Record directly ---
    if "Record" in choice or "Ghi âm" in choice:
        audio = audiorecorder.audiorecorder(
            "🎙️ " + ("Start recording" if lang == "English" else "Bắt đầu ghi âm"),
            "🛑 " + ("Stop recording" if lang == "English" else "Dừng ghi âm")
        )
        if len(audio) > 0:
            buf = BytesIO()
            audio.export(buf, format="wav")
            wav_bytes = buf.getvalue()
            st.audio(wav_bytes, format="audio/wav")

            if st.button("🧠 " + ("Recognize Speech" if lang == "English" else "Nhận diện giọng nói")):
                with st.spinner("🚀 " + ("Transcribing..." if lang == "English" else "Đang nhận diện...")):
                    result = speech_to_text(audio_bytes=wav_bytes, lang=lang)
                if result.get("success"):
                    show_result_box(result.get("text", ""), height=280, filename="speech_result.txt")
                else:
                    st.error(result.get("message", "Error"))

    # --- Upload audio file ---
    elif "Upload" in choice or "Tải lên" in choice:
        uploaded_audio = st.file_uploader(
            "📁 " + ("Upload audio file" if lang == "English" else "Chọn file âm thanh"),
            type=["wav", "mp3", "m4a", "aac", "ogg", "flac"]
        )
        if uploaded_audio:
            st.audio(uploaded_audio)
            if st.button("🧠 " + ("Recognize Speech" if lang == "English" else "Nhận diện file giọng nói")):
                with st.spinner("🚀 " + ("Transcribing..." if lang == "English" else "Đang nhận diện...")):
                    result = speech_to_text(uploaded_file=uploaded_audio, lang=lang)
                if result.get("success"):
                    show_result_box(result.get("text", ""), height=280, filename="uploaded_audio_result.txt")
                else:
                    st.error(result.get("message", "Error"))
    st.markdown("</div>", unsafe_allow_html=True)

# ===================== FOOTER =====================
st.markdown(
    "<div style='text-align:center; opacity:.6; font-size:12px; margin-top:10px;'>"
    "UI ⚡ by Nhóm 1 — Powered by Streamlit"
    "</div>",
    unsafe_allow_html=True
)
