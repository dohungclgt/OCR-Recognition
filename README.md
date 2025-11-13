# 🧠 OCR Multi-Module Application

Ứng dụng OCR (Optical Character Recognition) này được xây dựng bằng **Python + Streamlit**, cho phép bạn trích xuất văn bản từ nhiều nguồn khác nhau như **PDF, hình ảnh, máy scan**, và **giọng nói (speech)**.

---

## 🚀 **Tính năng**

### ✅ 1. Image to Text
- Tải lên một **ảnh chứa văn bản** (PNG, JPG, JPEG, BMP).
- Tự động nhận diện chữ bằng **Tesseract OCR**.
- Hỗ trợ cả **Tiếng Việt** và **Tiếng Anh**.
- Hiển thị kết quả trực tiếp trên giao diện web.
- Có thể download các trường hoặc 1 trường nhất định
- Có tóm tắt nội dung trong Image

### ✅ 2. PDF to Text
- Tải lên file **PDF (1 hoặc nhiều trang)**.
- Tự động chuyển đổi sang ảnh và quét toàn bộ văn bản.
- Xuất kết quả dạng text có thể sao chép.

### ⚙️ 3. Scan to Text *(đang thử nghiệm)*
- Chụp ảnh trực tiếp từ camera.
- Tự động quét chữ nếu ảnh rõ nét.
- Có thể cần cấu hình thêm về camera hoặc độ sáng ảnh.

### 🎙️ 4. Speech to Text *(đang thử nghiệm)*
- Hỗ trợ **2 lựa chọn**:
  - Upload file ghi âm (`.wav`, `.mp3`).
  - Ghi âm trực tiếp bằng micro (Streamlit mic input).
- Hỗ trợ **English & Vietnamese**.
- Độ chính xác trung bình hiện tại: **~85%+** với file âm thanh rõ.

---

## 🧩 **Công nghệ sử dụng**

| Thành phần | Mô tả |
|-------------|-------|
| `Streamlit` | Giao diện web thân thiện, chạy local nhanh. |
| `pytesseract` | Engine OCR nhận diện ký tự từ ảnh. |
| `pdf2image` | Chuyển PDF sang ảnh để OCR dễ xử lý. |
| `PIL (Pillow)` | Xử lý hình ảnh cơ bản. |
| `SpeechRecognition` | Thư viện chuyển giọng nói thành text. |
| `pydub` | Hỗ trợ đọc các định dạng âm thanh. |
| `ffmpeg` | Cần thiết để xử lý audio input/output. |

---

## 🧰 **Cách cài đặt và chạy**
### 1️⃣ Clone project từ GitHub
- git clone https://github.com/dohungclgt/OCR-recognizition
- cd ocr_app
### 2️⃣ Tạo môi trường ảo
```bash
python -m venv venv
```
### 3️⃣ Kích hoạt môi trường ảo
- Windows:
```bash
venv\Scripts\activate
```
### 4️⃣ Cài đặt thư viện cần thiết
```bash
pip install -r requirements.txt
```
### 5️⃣ Cài đặt Tesseract OCR
- Windows:
- Tải và cài đặt tại: https://github.com/UB-Mannheim/tesseract/wiki
- Ghi nhớ đường dẫn cài đặt (ví dụ: C:\Program Files\Tesseract-OCR\tesseract.exe).

### 6️⃣ Cấu hình biến môi trường (Windows)
- Tạo file .env trong thư mục gốc:
```bash
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

Hoặc thêm vào code nếu chưa có:
```python
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH")
```

### 7️⃣ Cài đặt ffmpeg (cho speech/audio)

- Tải tại: https://ffmpeg.org/download.html

- Sau khi cài đặt, thêm ffmpeg vào biến môi trường PATH.
- Kiểm tra bằng:
```cmd
ffmpeg -version
```  
- Cài đặt Poppler và thêm vào biến môi trường PATH
- https://poppler.freedesktop.org/
- Thêm đường dẫn vào PATH:
- Mở System Properties → Environment Variables
- Trong “System variables”, chọn “Path” → “Edit” → “New”
- Thêm:
- C:\poppler-24.08.0\Library\bin
- Kiểm tra: mở CMD và gõ
```cmd
pdfinfo -v
```
- Bạn cần API để có thể hoạt động chính xác
- truy cập vào: https://aistudio.google.com/api-keys để lấy key
- Sau khi lấy, vào các thư mục như là Image_to_text, pdf_to_text...
- Tìm dòng:
```python
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "Your key here")
```
- dán key API bạn lấy vào "your key here"
- lưu lại
### ▶️ Chạy ứng dụng
- mở Terminal và gõ lệnh:
```cmd
streamlit run app.py
```
- Ứng dụng sẽ tự động mở trình duyệt localhost

### ⚠️ Lưu ý:
- Các module Scan và Speech hiện đang trong giai đoạn phát triển. (còn 1 số lỗi chưa sửa được)
- Nếu gặp lỗi khi chạy phần speech, hãy đảm bảo:
- ffmpeg đã được cài và thêm vào PATH.
- File âm thanh có chất lượng rõ ràng.
- Ngôn ngữ chọn đúng (en-US hoặc vi-VN).
- Không tiết lộ API
