# speech_to_text.py
from io import BytesIO
from typing import Optional, Any, Dict
from pydub import AudioSegment
import speech_recognition as sr

# Nếu bạn có config.py set tesseract/ffmpeg path thì không cần dùng ở đây.
# Chỉ cần chắc chắn ffmpeg đã ở PATH để pydub đọc định dạng.

def _to_wav_bytes(data: bytes) -> bytes:
    seg = AudioSegment.from_file(BytesIO(data))  # auto-detect
    buf = BytesIO()
    seg.export(buf, format="wav")  # normalize to WAV
    return buf.getvalue()

def _lang_to_bcp47(lang_ui: str) -> str:
    return "en-US" if lang_ui.strip().lower().startswith("english") else "vi-VN"

def speech_to_text(
    audio_bytes: Optional[bytes] = None,
    uploaded_file: Optional[Any] = None,
    lang: str = "Tiếng Việt"
) -> Dict[str, Any]:
    try:
        if audio_bytes:
            wav_bytes = _to_wav_bytes(audio_bytes)
        elif uploaded_file is not None:
            file_bytes = uploaded_file.read()
            if not file_bytes:
                return {"success": False, "message": "File rỗng hoặc không đọc được."}
            wav_bytes = _to_wav_bytes(file_bytes)
        else:
            return {"success": False, "message": "Chưa có nguồn âm thanh."}

        recog_lang = _lang_to_bcp47(lang)
        r = sr.Recognizer()
        with sr.AudioFile(BytesIO(wav_bytes)) as source:
            audio_data = r.record(source)
        text = r.recognize_google(audio_data, language=recog_lang)
        return {"success": True, "text": text}

    except sr.UnknownValueError:
        return {"success": False, "message": "Không hiểu được âm thanh (UnknownValueError)."}
    except sr.RequestError as e:
        return {"success": False, "message": f"Lỗi kết nối Speech API: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi: {e}"}
