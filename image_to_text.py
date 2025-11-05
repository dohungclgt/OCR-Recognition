import cv2
import numpy as np
from PIL import Image
import pytesseract
import math
from config import pytesseract

def preprocess_image(image_path):
    """Tiền xử lý ảnh nâng cao để tăng độ chính xác OCR"""
    img = cv2.imread(image_path)

    # 1️⃣ Chuyển grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2️⃣ Loại bỏ nhiễu nhẹ bằng Gaussian
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # 3️⃣ Phát hiện cạnh bằng Canny để tìm hướng nghiêng
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    angle = 0
    if lines is not None:
        angles = []
        for rho, theta in lines[:, 0]:
            angle_deg = (theta * 180 / np.pi) - 90
            if -45 < angle_deg < 45:
                angles.append(angle_deg)
        if angles:
            angle = np.median(angles)
    # Xoay lại nếu nghiêng
    (h, w) = gray.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
    gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # 4️⃣ Dùng adaptive threshold cho vùng sáng không đều
    gray = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 11
    )

    # 5️⃣ Sharpen để làm nét chữ
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    gray = cv2.filter2D(gray, -1, kernel)

    # 6️⃣ Tăng tương phản (nếu ảnh mờ)
    gray = cv2.convertScaleAbs(gray, alpha=1.6, beta=10)

    # 7️⃣ Lưu ảnh xử lý tạm
    processed_path = "temp_processed.png"
    cv2.imwrite(processed_path, gray)
    return processed_path


def image_to_text(image_path):
    """Chuyển ảnh sang văn bản với tối ưu song ngữ"""
    try:
        processed = preprocess_image(image_path)

        # ⚙️ Cấu hình tùy chỉnh: dùng LSTM OCR engine và PSM linh hoạt
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'

        text = pytesseract.image_to_string(
            Image.open(processed),
            lang="vie+eng",
            config=custom_config
        )

        # 8️⃣ Làm sạch text đầu ra
        text = text.replace('\x0c', '').strip()

        if not text:
            return {"success": False, "message": "Không phát hiện được chữ trong ảnh."}
        return {"success": True, "text": text}

    except Exception as e:
        return {"success": False, "message": f"Lỗi xử lý ảnh: {e}"}
