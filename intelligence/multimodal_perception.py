# intelligence/multimodal_perception.py —— 多模态感知
import cv2, numpy as np
from PIL import Image
import pytesseract

class MultimodalPerception:
    def __init__(self):
        self.ocr_available = self._check_ocr()

    def _check_ocr(self):
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            print("⚠️ Tesseract OCR 未安装，图像文字识别不可用")
            return False

    def capture_screen(self):
        img = Image.grab()
        return img

    def extract_text_from_image(self, image):
        if not self.ocr_available:
            return "OCR 不可用"
        return pytesseract.image_to_string(image, lang='chi_sim+eng')

    def analyze_image(self, image_path):
        # 简化：返回图片基本属性
        img = Image.open(image_path)
        return f"尺寸: {img.size}, 模式: {img.mode}"
