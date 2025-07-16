from paddleocr import PaddleOCR
import numpy as np
import cv2

# PaddleOCR 초기화 (한글 + 회전 보정)
ocr = PaddleOCR(use_angle_cls=True, lang='korean')

def extract_text_from_image(image):
    if image is None or not isinstance(image, np.ndarray):
        return "이미지 오류"

    resized = cv2.resize(image, (0, 0), fx=2, fy=2)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    result = ocr.ocr(rgb)  # ❗ cls 제거
    if not result or not result[0]:
        return "텍스트를 인식하지 못했습니다."

    texts = [line[1][0] for line in result[0]]
    return "\n".join(texts)