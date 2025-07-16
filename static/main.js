let previousPending = [];

async function fetchPending(forceUpdate = false) {
    const res = await fetch('/get_pending_tags');
    const pendingList = await res.json();

    const pendingIds = pendingList.map(p => p.face_id);
    const prevIds = previousPending.map(p => p.face_id);
    const isDifferent = forceUpdate || pendingIds.join() !== prevIds.join();

    if (!isDifferent) return;
    previousPending = pendingList;

    const previousInputs = {};
    document.querySelectorAll("form").forEach(form => {
        const faceId = form.getAttribute("data-id");
        const tagInput = form.querySelector("input[name='tag']");
        const categorySelect = form.querySelector("select[name='category']");
        previousInputs[faceId] = {
            tag: tagInput?.value || '',
            category: categorySelect?.value || '기타'
        };
    });

    let html = '';
    for (let { face_id, image } of pendingList) {
        const values = previousInputs[face_id] || { tag: '', category: '기타' };
        html += `
            <form onsubmit="submitTag(event, '${face_id}')" data-id="${face_id}">
                <label>Face ID: ${face_id}</label>
                <img src="data:image/jpeg;base64,${image}" style="width:100px; border-radius: 5px;" />
                <input name="tag" placeholder="태그 입력" value="${values.tag}" required>
                <select name="category" required>
                    <option value="가족" ${values.category === '가족' ? 'selected' : ''}>가족</option>
                    <option value="친구" ${values.category === '친구' ? 'selected' : ''}>친구</option>
                    <option value="동료" ${values.category === '동료' ? 'selected' : ''}>동료</option>
                    <option value="기타" ${values.category === '기타' ? 'selected' : ''}>기타</option>
                </select>
                <button>등록</button>
            </form>`;
    }
    document.getElementById('pending').innerHTML = html;
}

async function submitTag(event, face_id) {
    event.preventDefault();
    const tag = event.target.tag.value;
    const category = event.target.category.value;

    await fetch('/submit_tag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ face_id, tag, category })
    });

    fetchPending(true);
}

// OCR + TTS 기능
document.addEventListener('DOMContentLoaded', () => {
    const ocrBtn = document.getElementById("ocrBtn");
    if (ocrBtn) {
        ocrBtn.addEventListener("click", async () => {
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

setInterval(() => fetchPending(false), 3000);
fetchPending(true);