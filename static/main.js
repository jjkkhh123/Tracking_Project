async function fetchPending() {
    const res = await fetch('/get_pending_tags');
    const pendingList = await res.json();

    const previousInputs = {};
    document.querySelectorAll("form").forEach(form => {
        const faceId = form.getAttribute("data-id");
        previousInputs[faceId] = {
            tag: form.querySelector("input[name='tag']").value,
            category: form.querySelector("select[name='category']").value
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

    fetchPending(); // 갱신
}

// 최초 실행 및 반복 호출
setInterval(fetchPending, 3000);
fetchPending();
