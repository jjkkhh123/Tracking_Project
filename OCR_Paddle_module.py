import cv2
from paddleocr import PaddleOCR

# OCR 엔진 초기화 (한글 전용, 회전 미사용)
ocr = PaddleOCR(use_angle_cls=False, lang='korean')


def extract_text_from_image(image):
    """이미지에서 텍스트를 추출해 문자열로 반환"""
    try:
        # 🔧 입력 유효성 검사 추가
        if image is None or image.size == 0:
            return "[입력 이미지 오류]"

        # 🔧 흑백 이미지를 BGR로 변환 (필수: OCR 정확도 유지)
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # 💡 OCR 실행
        results = ocr.ocr(image)
        print("🔍 OCR raw 결과:", results)

        texts = []

        # 🔧 DocVQA 스타일 처리
        if isinstance(results, list) and isinstance(results[0], dict):
            rec_texts = results[0].get('rec_texts', [])
            if isinstance(rec_texts, list):
                texts.extend(rec_texts)  # 💡 extend로 한꺼번에 추가

        # 🔧 일반 리스트 결과 처리
        elif isinstance(results, list):
            for line_group in results:
                if not isinstance(line_group, list):
                    continue
                for line in line_group:
                    if isinstance(line, list) and len(line) >= 2:
                        text = line[1][0]
                        texts.append(text)

        # 결과 반환
        return '\n'.join(texts) if texts else "[인식된 텍스트 없음]"

    except Exception as e:
        # 💡 에러 로그를 명확하게 출력
        print("[!] OCR 내부 오류:", e)
        return f"[오류] {str(e)}"
