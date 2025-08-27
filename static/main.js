let previousPending = [];

// 🔹 태그 대기중 얼굴 목록 가져오기
async function fetchPending(forceUpdate = false) {
    const res = await fetch('/get_pending_tags');
    const pendingList = await res.json();

    const pendingIds = pendingList.map(p => p.face_id);
    const prevIds = previousPending.map(p => p.face_id);
    const isDifferent = forceUpdate || pendingIds.join() !== prevIds.join();

    if (!isDifferent) return;
    previousPending = pendingList;

    // 이전 입력값 복구
    const previousInputs = {};
    document.querySelectorAll("tr[data-id]").forEach(row => {
        const faceId = row.getAttribute("data-id");
        const tagInput = row.querySelector("input[name='tag']");
        const categorySelect = row.querySelector("select[name='category']");
        previousInputs[faceId] = {
            tag: tagInput?.value || '',
            category: categorySelect?.value || '기타'
        };
    });

    const pendingContainer = document.getElementById('pending');
    const noDataMessage = document.getElementById('noDataMessage');
    pendingContainer.innerHTML = '';
    noDataMessage.style.display = pendingList.length === 0 ? 'block' : 'none';

    // 새로운 대기중 목록 렌더링
    for (let { face_id, image } of pendingList) {
        const values = previousInputs[face_id] || { tag: '', category: '기타' };

        const row = document.createElement('tr');
        row.setAttribute("data-id", face_id);
        row.innerHTML = `
            <td><img src="data:image/jpeg;base64,${image}" class="face-image" /></td>
            <td class="face-id">${face_id}</td>
            <td>
                <input name="tag" class="name-input" placeholder="태그 입력" value="${values.tag}" required />
            </td>
            <td>
                <select name="category" class="category-select" required>
                    <option value="가족" ${values.category === '가족' ? 'selected' : ''}>가족</option>
                    <option value="친구" ${values.category === '친구' ? 'selected' : ''}>친구</option>
                    <option value="동료" ${values.category === '동료' ? 'selected' : ''}>동료</option>
                    <option value="기타" ${values.category === '기타' ? 'selected' : ''}>기타</option>
                </select>
            </td>
            <td>
                <button type="button" class="ocr-btn">등록</button>
            </td>
        `;

        // ✅ 버튼 클릭 이벤트 직접 바인딩
        const button = row.querySelector("button");
        button.addEventListener("click", () => {
            const tag = row.querySelector("input[name='tag']").value;
            const category = row.querySelector("select[name='category']").value;
            submitTag(face_id, tag, category);
        });

        pendingContainer.appendChild(row);
        console.log("👉 등록 버튼 생성됨:", face_id);
    }
}

// 🔹 태그 등록 요청
async function submitTag(face_id, tag, category) {
    console.log("✅ submitTag 실행됨:", face_id, tag, category);

    try {
        const res = await fetch('/submit_tag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ face_id, tag, category })
        });
        const text = await res.text();
        console.log("서버 응답:", text);

        fetchPending(true);
    } catch (err) {
        console.error("submitTag 오류:", err);
    }
}

// 🔹 OCR + TTS 기능
document.addEventListener('DOMContentLoaded', () => {
    const ocrBtn = document.getElementById("ocrBtn");
    if (ocrBtn) {
        ocrBtn.addEventListener("click", async () => {
            alert("실행중...");  // OCR 시작 알림
            const res = await fetch('/ocr_capture', { method: 'POST' });
            const data = await res.json();
            if (!data.success) {
                alert("OCR 실패: " + data.message);
                return;
            }
            const text = data.text || "텍스트를 인식하지 못했습니다.";
            if (confirm(`다음 텍스트가 추출되었습니다:\n\n"${text}"\n\n읽어드릴까요?`)) {
                fetch('/speak_text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
            }
        });
    }
});

// 🔹 3초마다 대기 목록 갱신
setInterval(() => fetchPending(false), 3000);
fetchPending(true);
