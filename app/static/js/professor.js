document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startSessionBtn');
    const kCodeDisplay = document.getElementById('k-code-display');
    const profIdInput = document.getElementById('profIdInput');
    const classCodeInput = document.getElementById('classCodeInput');

    startBtn.addEventListener('click', async () => {
        const profId = profIdInput.value;
        const classCode = classCodeInput.value;

        if (!profId || !classCode) {
            alert('Please enter both Professor ID and Class Code.');
            return;
        }

        const response = await fetch('/session/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prof_id: profId,
                class_code: classCode
            })
        });
        
        const data = await response.json();
        if (data.success) {
            kCodeDisplay.textContent = data.k_code;
            startBtn.disabled = true;
        } else {
            alert(`Error: ${data.message}`);
        }
    });
});