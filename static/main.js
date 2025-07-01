async function fetchPending() {
    const res = await fetch('/get_pending_tags');
    const pendingList = await res.json();

    const previousInputs = {};
    document.querySelectorAll("form").forEach(form => {
        const faceId = form.getAttribute("data-id");
        const tagValue = form.querySelector("input[name='tag']").value;
        previousInputs[faceId] = tagValue;
    });

    let html = '';
    for (let { face_id, image } of pendingList) {
        const value = previousInputs[face_id] || '';
        html += `
            <form onsubmit="submitTag(event, '${face_id}')" data-id="${face_id}">
                <label>Face ID: ${face_id}</label>
                <img src="data:image/jpeg;base64,${image}" style="width:100px; border-radius: 5px;" />
                <input name="tag" placeholder="태그 입력" value="${value}" required>
                <button>등록</button>
            </form>`;
    }

    document.getElementById('pending').innerHTML = html;
}


async function submitTag(event, face_id) {
    event.preventDefault();
    const tag = event.target.tag.value;

    await fetch('/submit_tag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ face_id, tag })
    });

    fetchPending(); // 갱신
}

// 최초 실행 및 반복 호출
setInterval(fetchPending, 3000);
fetchPending();
