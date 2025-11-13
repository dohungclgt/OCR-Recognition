# frontend.py — Pro UI for Universal OCR App (Streamlit)
# ------------------------------------------------------
# - Cách 1: thêm khoảng đệm đáy bằng CSS (--fx-bottom-offset)
# - Theme (Neon / Glass / Minimal)
# - Hero header, breadcrumbs, animated dividers
# - Contextual help + Quick Summary theo chế độ
# - Page transition animations (fade+slide + ripple overlay)
# - Reusable UI blocks + manual key:value selector
# - An toàn với CSS: không dùng str.format cho _BASE_CSS

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import html
import tempfile
import pandas as pd
import streamlit as st
from docx import Document


# =============================== UTILS ===============================
def _esc(x) -> str:
    """Safe HTML escape."""
    return html.escape(str(x), quote=True)


def _is_en(lang: str) -> bool:
    return str(lang).strip().lower().startswith("english")


# =============================== PUBLIC API ===============================
def get_ui_prefs() -> Dict[str, str]:
    """Sidebar: Language + Theme. Return {'lang','theme'}."""
    with st.sidebar:
        st.header("⚙️ Settings")
        lang = st.radio("🌐 Language / Ngôn ngữ", ["English", "Tiếng Việt"], index=1, key="ui_lang")
        theme = st.selectbox("🎨 Theme", ["✨ Neon Cyber", "🧊 Glass Morph", "🌚 Minimal Dark"], index=0, key="ui_theme")
    return {"lang": lang, "theme": theme}


def inject_theme_css(theme_label: str) -> None:
    """Inject global CSS for selected theme without touching literal braces."""
    theme_key = theme_label.replace("✨ ", "").replace("🧊 ", "").replace("🌚 ", "").strip().lower()
    css_vars = _css_vars_by_theme(theme_key)

    css = _BASE_CSS
    # Thay thế đúng các placeholder, giữ nguyên mọi { } khác trong CSS
    for k, v in css_vars.items():
        css = css.replace("{" + k + "}", v)

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def hero_header(title: str, subtitle: str, badge: Optional[str] = None, icon: str = "🧠") -> None:
    """Top hero header."""
    st.markdown(f"""
<div class="fx-hero">
  <div class="fx-hero-icon">{_esc(icon)}</div>
  <div class="fx-hero-content">
    <div class="fx-hero-title">{_esc(title)}</div>
    <div class="fx-hero-sub">{_esc(subtitle)}</div>
    {f'<div class="fx-badge">{_esc(badge)}</div>' if badge else ''}
  </div>
</div>
""", unsafe_allow_html=True)


def breadcrumbs(items: List[str]) -> None:
    """Show navigation breadcrumbs."""
    if not items:
        return
    html_items = ' <span class="sep">/</span> '.join(
        f'<span class="crumb">{_esc(i)}</span>' for i in items
    )
    st.markdown(f'<div class="fx-breadcrumbs">{html_items}</div>', unsafe_allow_html=True)


def divider(label: Optional[str] = None) -> None:
    """Animated divider."""
    if label:
        st.markdown(f"""<div class="fx-divider"><span>{_esc(label)}</span></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="fx-divider"></div>""", unsafe_allow_html=True)


def section(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None) -> None:
    """Section title."""
    ic = icon or "🧩"
    subtitle_html = f'<div class="fx-subtitle">{_esc(subtitle)}</div>' if subtitle else ''
    st.markdown(f"""
<div class="fx-section">
  <div class="fx-title">{_esc(ic)} {_esc(title)}</div>
  {subtitle_html}
</div>
""", unsafe_allow_html=True)


def callout(kind: str, text: str) -> None:
    """Callout box: 'info' | 'success' | 'warning' | 'danger'."""
    kind = kind.lower()
    st.markdown(f'<div class="fx-callout {kind}">{text}</div>', unsafe_allow_html=True)


def checklist(title: str, steps: List[str]) -> None:
    """Step checklist in a card."""
    items = "".join([f'<li>✅ {_esc(s)}</li>' for s in steps])
    st.markdown(f"""
<div class="fx-card">
  <div class="fx-card-body">
    <div class="fx-card-title">{_esc(title)}</div>
    <ul class="fx-list">{items}</ul>
  </div>
</div>
""", unsafe_allow_html=True)


def quick_summary(mode_label: str, lang: str) -> None:
    """Hiển thị 1 ô tóm tắt ngắn gọn về chức năng đang chọn."""
    is_en = _is_en(lang)
    mode = "image" if "📸" in mode_label else "pdf" if "📄" in mode_label else "scan" if "📷" in mode_label else "speech"

    if mode == "image":
        title = "Quick Summary — Image" if is_en else "Tóm tắt nhanh — Ảnh"
        desc  = ("Upload PNG/JPG, then extract with Tesseract or Gemini. Optional post-processing: pick Full Text or key:value fields."
                 if is_en else
                 "Tải ảnh PNG/JPG, trích xuất bằng Tesseract hoặc Gemini. Có thể hậu xử lý: lấy toàn bộ hoặc chọn các cặp key:value.")
        icon  = "🖼️"
    elif mode == "pdf":
        title = "Quick Summary — PDF" if is_en else "Tóm tắt nhanh — PDF"
        desc  = ("Upload PDF (multi-page ok). Use local Tesseract OCR or Gemini AI extraction. Then post-process and download."
                 if is_en else
                 "Tải PDF (nhiều trang được). Dùng Tesseract OCR cục bộ hoặc Gemini AI. Sau đó hậu xử lý và tải xuống.")
        icon  = "📄"
    elif mode == "scan":
        title = "Quick Summary — Scan" if is_en else "Tóm tắt nhanh — Quét"
        desc  = ("Open webcam to capture a document. Choose Gemini (default) or Tesseract. Good lighting = better accuracy."
                 if is_en else
                 "Mở webcam để chụp tài liệu. Chọn Gemini (mặc định) hoặc Tesseract. Ảnh đủ sáng giúp chính xác hơn.")
        icon  = "📷"
    else:
        title = "Quick Summary — Speech" if is_en else "Tóm tắt nhanh — Giọng nói"
        desc  = ("Record or upload audio, pick language (EN/VN), then transcribe to text and download."
                 if is_en else
                 "Ghi âm hoặc tải file audio, chọn ngôn ngữ (EN/VN), nhận diện thành văn bản và tải xuống.")
        icon  = "🎧"

    st.markdown(f"""
<div class="fx-card">
  <div class="fx-card-body">
    <div class="fx-card-title">{icon} {_esc(title)}</div>
    <div class="fx-subtitle">{_esc(desc)}</div>
  </div>
</div>
""", unsafe_allow_html=True)


def two_columns(ratio_left: float = 1.25, ratio_right: float = 1.0):
    """Consistent columns with spacing."""
    return st.columns([ratio_left, ratio_right])


def manual_kv_selector_ui(
    raw_text: str,
    lang: str = "Tiếng Việt",
    session_prefix: str = "img",
    default_checked: bool = True
) -> Tuple[str, List[str]]:
    """
    Manual selection UI from 'key: value' lines.
    - Unique widget keys by enumeration.
    - Persist selection via st.session_state.
    Return: (filtered_text, selected_lines)
    """
    lines = [ln.strip() for ln in (raw_text or "").split("\n") if ln.strip()]
    kv_lines = [ln for ln in lines if ":" in ln]

    map_key = f"{session_prefix}_manual_fields"
    if map_key not in st.session_state or not isinstance(st.session_state[map_key], dict):
        st.session_state[map_key] = {ln: default_checked for ln in kv_lines}

    st.write("🔍 Select fields to include:" if _is_en(lang) else "🔍 Chọn các trường muốn giữ lại:")

    selected_map: Dict[str, bool] = {}
    for i, ln in enumerate(kv_lines):
        k, v = ln.split(":", 1)
        widget_key = f"{session_prefix}_chk_{i}"
        checked_default = st.session_state[map_key].get(ln, default_checked)
        checked = st.checkbox(f"{_esc(k.strip())}: {_esc(v.strip())}", value=checked_default, key=widget_key)
        selected_map[ln] = checked

    st.session_state[map_key] = selected_map
    selected_lines = [ln for ln, ok in selected_map.items() if ok]
    filtered = "\n".join(selected_lines) if selected_lines else ("(No field selected)" if _is_en(lang) else "(Không có trường nào được chọn)")
    return filtered, selected_lines


def download_block(filtered_text: str, base_filename: str, key_prefix: str) -> None:
    """Unified download block (TXT / DOCX / Excel)."""
    fmt_label = "📥 Download format:" if _is_en(st.session_state.get("ui_lang", "Tiếng Việt")) else "📥 Chọn định dạng tải xuống:"
    fmt = st.radio(fmt_label, ["TXT", "DOCX", "Excel"], horizontal=True, key=f"{key_prefix}_fmt")

    if fmt == "TXT":
        st.download_button("💾 TXT", filtered_text, file_name=f"{base_filename}.txt", key=f"{key_prefix}_txt")

    elif fmt == "DOCX":
        doc = Document()
        doc.add_paragraph(filtered_text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_doc:
            doc.save(tmp_doc.name)
            tmp_doc.seek(0)
            st.download_button(
                "💾 DOCX", tmp_doc.read(),
                file_name=f"{base_filename}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"{key_prefix}_docx"
            )

    elif fmt == "Excel":
        rows = []
        for ln in filtered_text.split("\n"):
            if ":" in ln:
                k, v = ln.split(":", 1)
                rows.append({"Field": k.strip(), "Value": v.strip()})
        if rows:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_xlsx:
                pd.DataFrame(rows).to_excel(tmp_xlsx.name, index=False)
                tmp_xlsx.seek(0)
                st.download_button(
                    "💾 Excel", tmp_xlsx.read(),
                    file_name=f"{base_filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"{key_prefix}_xlsx"
                )
        else:
            callout("info", "ℹ️ Không có dòng dạng <code>key: value</code> để xuất Excel.")


def contextual_help(mode_label: str, lang: str) -> None:
    """Contextual help per current mode."""
    is_en = _is_en(lang)
    mode = "image" if "📸" in mode_label else "pdf" if "📄" in mode_label else "scan" if "📷" in mode_label else "speech"

    if mode == "image":
        title = "How to use Image mode" if is_en else "Cách dùng chế độ Ảnh"
        steps = [
            "Upload PNG/JPG.",
            "Choose: Tesseract or Gemini.",
            "If Gemini → Post-processing: Full Text / Manual Fields.",
            "Download as TXT / DOCX / Excel.",
        ] if is_en else [
            "Tải ảnh PNG/JPG.",
            "Chọn: Tesseract hoặc Gemini.",
            "Nếu Gemini → Hậu xử lý: Toàn bộ / Chọn key:value.",
            "Tải xuống: TXT / DOCX / Excel.",
        ]
        checklist(title, steps)
        callout("info", "💡 " + ("Tip: sharp, high-contrast images improve OCR." if is_en else "Mẹo: ảnh rõ, tương phản cao giúp OCR chính xác."))

    elif mode == "pdf":
        title = "How to use PDF mode" if is_en else "Cách dùng chế độ PDF"
        steps = [
            "Upload PDF.",
            "Tesseract: local OCR (per page).",
            "Gemini: AI extraction (keeps layout reasonably).",
            "Post-process: Full Text or Manual Fields → download.",
        ] if is_en else [
            "Tải PDF.",
            "Tesseract: OCR cục bộ (theo trang).",
            "Gemini: trích xuất AI (giữ bố cục tương đối).",
            "Hậu xử lý: Toàn bộ hoặc Chọn key:value → tải xuống.",
        ]
        checklist(title, steps)
        callout("warning", "📎 " + ("If PDF is scanned, Poppler must be installed for pdf2image." if is_en else "Nếu PDF dạng scan, cần cài Poppler để pdf2image hoạt động."))

    elif mode == "scan":
        title = "How to use Scan mode" if is_en else "Cách dùng chế độ Quét"
        steps = [
            "Open camera and take a photo.",
            "Pick engine: Gemini (default) or Tesseract.",
            "Confirm text result → download.",
        ] if is_en else [
            "Mở camera và chụp ảnh.",
            "Chọn engine: Gemini (mặc định) hoặc Tesseract.",
            "Xem kết quả → tải xuống.",
        ]
        checklist(title, steps)
        callout("success", "📸 " + ("Ensure bright lighting and flat paper. Avoid shadows." if is_en else "Nên đủ sáng, giấy phẳng, tránh bóng đổ."))

    elif mode == "speech":
        title = "How to use Speech mode" if is_en else "Cách dùng chế độ Giọng nói"
        steps = [
            "Record or upload audio.",
            "Pick language (EN/VN in sidebar).",
            "Transcribe and download as TXT.",
        ] if is_en else [
            "Ghi âm hoặc tải file audio.",
            "Chọn ngôn ngữ (EN/VN ở sidebar).",
            "Nhận diện và tải TXT.",
        ]
        checklist(title, steps)
        callout("info", "🎙️ " + ("For best results: clear speech, minimal noise." if is_en else "Để chính xác hơn: giọng rõ, ít tạp âm."))


# ====================== PAGE TRANSITION HELPERS ======================
def begin_route_transition(current_mode_label: str) -> None:
    """
    Call early in app.py, right after 'mode' is chosen.
    Track change to trigger animation.
    """
    last = st.session_state.get("_fx_last_mode")
    st.session_state["_fx_just_changed"] = (last is not None and last != current_mode_label)
    st.session_state["_fx_last_mode"] = current_mode_label


def transition_container_start() -> None:
    """
    Wrap main content within an animated container.
    Call RIGHT BEFORE rendering per-mode content.
    """
    just_changed = st.session_state.get("_fx_just_changed", True)
    klass = "fx-page enter" if just_changed else "fx-page"
    st.markdown(f'<div class="{klass}">', unsafe_allow_html=True)


def transition_container_end() -> None:
    """Close container."""
    st.markdown("</div>", unsafe_allow_html=True)


def transition_overlay() -> None:
    """
    Draw overlay ripple/fade when page (mode) just changed.
    Call RIGHT AFTER container end.
    """
    if not st.session_state.get("_fx_just_changed", False):
        return
    st.markdown('<div class="fx-overlay"></div>', unsafe_allow_html=True)


# =============================== THEME & CSS ===============================
def _css_vars_by_theme(theme: str) -> Dict[str, str]:
    """Return CSS vars for: 'neon cyber', 'glass morph', 'minimal dark'."""
    t = theme.lower().strip()
    if t.startswith("neon"):
        return dict(
            bg="radial-gradient(1200px 800px at 10% 0%, #0a0f1f 0%, #04070d 45%, #02040a 100%)",
            card_bg="linear-gradient(180deg, rgba(14,23,43,0.75), rgba(8,14,30,0.75))",
            border="1px solid rgba(0, 255, 188, 0.25)",
            glow="0 0 22px rgba(0,255,188,.14), inset 0 0 18px rgba(0,255,188,.06)",
            accent="#00ffbc",
            accent_soft="rgba(0,255,188,.10)",
            text="#d9e7ff",
            sub="#90a9cc"
        )
    if t.startswith("glass"):
        return dict(
            bg="linear-gradient(135deg, #0f1420 0%, #0b1220 50%, #0a0f1f 100%)",
            card_bg="linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03))",
            border="1px solid rgba(255,255,255,0.12)",
            glow="0 14px 30px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.06)",
            accent="#a1c4fd",
            accent_soft="rgba(161,196,253,.12)",
            text="#e6f1ff",
            sub="#a3b5cc"
        )
    # minimal dark default
    return dict(
        bg="linear-gradient(180deg, #0b0f14, #0a0e13)",
        card_bg="linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.03))",
        border="1px solid rgba(255,255,255,0.08)",
        glow="0 10px 24px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.04)",
        accent="#6ea8fe",
        accent_soft="rgba(110,168,254,.12)",
        text="#e8eef7",
        sub="#9aa9be"
    )


# ===== CSS FIX + STYLE BASE =====
_BASE_CSS = """
/* ===== Fix header overlap ===== */
:root {
  --fx-top-offset: 3.4rem;
  /* Cách 1: thêm khoảng đệm đáy toàn trang để tránh bị thanh hệ điều hành che */
  --fx-bottom-offset: 72px;
}
header[data-testid="stHeader"] {
  position: sticky;
  top: 0;
  z-index: 1000;
  backdrop-filter: blur(6px);
  background: rgba(6,10,20,0.35);
}
/* block container: thêm khoảng đệm đáy */
[data-testid="stAppViewContainer"] .main .block-container {
  padding-top: calc(1rem + var(--fx-top-offset)) !important;
  padding-bottom: calc(2.25rem + var(--fx-bottom-offset)) !important;
}

/* ===== Theme Base ===== */
:root {
  --fx-bg: {bg};
  --fx-card-bg: {card_bg};
  --fx-border: {border};
  --fx-glow: {glow};
  --fx-accent: {accent};
  --fx-accent-soft: {accent_soft};
  --fx-text: {text};
  --fx-sub: {sub};
}
html, body, [data-testid="stAppViewContainer"] { background: var(--fx-bg) !important; }
.block-container { /* giữ để có khoảng cách mặc định, đã cộng thêm bottom ở trên */ }
h1,h2,h3,h4,h5,h6,p,span,div,label,code { color: var(--fx-text) !important; }
.stMarkdown, .stText, .stTextInput, .stTextArea textarea, .stSelectbox div, .stFileUploader, .stRadio {
  font-family: Inter, ui-sans-serif, Segoe UI, system-ui, -apple-system, sans-serif !important;
}

/* Hero */
.fx-hero { display:grid; grid-template-columns:64px 1fr; gap:14px; align-items:center; margin:.25rem 0 1rem 0; }
.fx-hero-icon { font-size:38px; }
.fx-hero-title { font-size:1.6rem; font-weight:800; letter-spacing:.2px; }
.fx-hero-sub { color:var(--fx-sub); margin-top:4px; }
.fx-badge { display:inline-block; margin-top:8px; padding:4px 10px; border-radius:999px; color:var(--fx-accent); background:var(--fx-accent-soft); border:1px solid rgba(255,255,255,.08); }

/* Breadcrumbs & Divider */
.fx-breadcrumbs { color:var(--fx-sub); margin:.25rem 0 .5rem 0; font-size:.92rem; }
.fx-breadcrumbs .sep { opacity:.55; margin:0 .35rem; }
.fx-divider { position:relative; height:1px; margin:1rem 0 1.25rem 0; background:linear-gradient(90deg,transparent,var(--fx-accent),transparent); opacity:.7; }
.fx-divider>span { position:absolute; left:50%; transform:translateX(-50%) translateY(-45%); padding:0 .55rem; font-size:.8rem; color:var(--fx-sub); background:linear-gradient(180deg,rgba(0,0,0,.35),rgba(0,0,0,0)); border-radius:8px; }

/* Card & Callouts */
.fx-card { background:var(--fx-card-bg); border-radius:18px; border:var(--fx-border); box-shadow:var(--fx-glow); overflow:hidden; backdrop-filter:blur(10px); margin:.25rem 0 1rem 0; animation:fxCardIn .4s ease-out both; }
@keyframes fxCardIn { from{opacity:0;transform:translateY(6px);} to{opacity:1;transform:none;} }
.fx-card-body{padding:.95rem .95rem;}
.fx-card-title{font-weight:700;margin-bottom:.4rem;}
.fx-callout{border-radius:14px;padding:.75rem .9rem;margin:.35rem 0 .9rem 0;border:1px solid rgba(255,255,255,.08);background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.02));}
.fx-callout.info{border-color:rgba(161,196,253,.25);} .fx-callout.success{border-color:rgba(0,255,188,.25);}
.fx-callout.warning{border-color:rgba(255,214,102,.25);} .fx-callout.danger{border-color:rgba(255,105,97,.25);}
.fx-list{margin:.25rem 0 0 .25rem;} .fx-list li{margin:.28rem 0;}

/* Buttons & Inputs */
.stButton>button,.stDownloadButton>button{border-radius:12px!important;border:1px solid rgba(255,255,255,.08)!important;background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.03))!important;transition:all .16s ease;}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-1px);box-shadow:0 10px 24px rgba(0,0,0,.35);border-color:var(--fx-accent);}
.stButton>button:active,.stDownloadButton>button:active{transform:translateY(0) scale(.995);}
.stTextArea textarea, .stFileUploader, .stSelectbox div[data-baseweb="select"] { border-radius:12px!important; box-shadow: inset 0 1px 0 rgba(255,255,255,.04); }

/* Page Transitions */
.fx-page{position:relative;animation:none;}
.fx-page.enter{animation:fxFadeSlideIn .55s ease-out both;}
@keyframes fxFadeSlideIn{0%{opacity:0;transform:translateY(14px) scale(0.992);filter:blur(2px);}60%{opacity:1;transform:translateY(0) scale(1.0);filter:blur(0);}100%{opacity:1;transform:none;}}
/* Overlay ripple on route change */
.fx-overlay{pointer-events:none;position:fixed;inset:0;background:radial-gradient(1200px 800px at 20% 10%, rgba(0,255,188,.12), transparent 60%);opacity:0;animation:fxRipple 700ms ease-out forwards;mix-blend-mode:screen;}
@keyframes fxRipple{0%{opacity:0;}20%{opacity:.7;}100%{opacity:0;}}
/* Flowing divider */
.fx-divider{background-size:200% 100%;animation:fxDividerFlow 2.2s linear infinite;}
@keyframes fxDividerFlow{0%{background-position:0% 50%;}100%{background-position:200% 50%;}}
"""
# =========================== END CSS ===========================


# ========== Demo (optional) ==========
if __name__ == "__main__":
    prefs = get_ui_prefs()
    inject_theme_css(prefs["theme"])
    hero_header("Universal OCR App", "Tesseract + Google Gemini · Image · PDF · Scan · Speech", badge="UI Preview", icon="🎨")
    breadcrumbs(["Home", "Preview"])
    quick_summary("📸 Image", prefs["lang"])
    divider("Contextual Help")
    contextual_help("📸 Image", prefs["lang"])
