import cv2
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=False, lang='korean')

def extract_text_from_image(image):
    try:
        if image is None or image.size == 0:
            return "[입력 이미지 오류]"

        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        results = ocr.ocr(image)

        print("🔍 OCR raw 결과:", results)

        texts = []

        # ✅ DocVQA 스타일로 반환된 경우 (딕셔너리 포함)
        if isinstance(results, list) and isinstance(results[0], dict) and 'rec_texts' in results[0]:
            texts = results[0].get('rec_texts', [])

        # ✅ 일반 OCR 스타일로 반환된 경우 (리스트 구조)
        elif isinstance(results, list):
            for line_group in results:
                for line in line_group:
                    if isinstance(line, list) and len(line) >= 2:
                        text = line[1][0]
                        texts.append(text)

        return '\n'.join(texts) if texts else "[인식된 텍스트 없음]"

    except Exception as e:
        print("[!] OCR 내부 오류:", e)
        return f"[오류] {str(e)}"
