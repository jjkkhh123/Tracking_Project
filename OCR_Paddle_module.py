
import cv2
from paddleocr import PaddleOCR

# OCR 초기화 (언어 설정은 상황에 맞게 조정)
ocr = PaddleOCR(use_angle_cls=False, lang='korean')

def extract_text_from_image(image):
    try:
        # 원본 컬러 이미지 사용 권장 (회색/이진화는 오히려 성능 저하)
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        results = ocr.ocr(image)

        if not results or len(results[0]) == 0:
            return "[인식된 텍스트 없음]"

        texts = []
        for line in results[0]:
            if isinstance(line, list) and len(line) >= 2:
                text = line[1][0]
                texts.append(text)

        return '\n'.join(texts) if texts else "[인식된 텍스트 없음]"

    except Exception as e:
        print("[!] OCR 내부 오류:", e)
        return f"[오류] {str(e)}"
