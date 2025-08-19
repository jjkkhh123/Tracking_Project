function openRegisterModal() {
    document.getElementById('registerModal').style.display = 'block';
}

function closeRegisterModal() {
    const modal = document.getElementById('registerModal');
    modal.style.display = 'none';

    // 🔄 폼 초기화
    const form = modal.querySelector('form');
    if (form) {
        form.reset();
    }
}

// 외부 클릭 시 닫기 + 초기화
window.onclick = function(event) {
    const modal = document.getElementById('registerModal');
    if (event.target == modal) {
        closeRegisterModal();
    }
}
