document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startSessionBtn');
    const kCodeDisplay = document.getElementById('k-code-display');

    startBtn.addEventListener('click', async () => {
        const response = await fetch('/session/start', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            kCodeDisplay.textContent = data.k_code;
            startBtn.disabled = true;
            startBtn.textContent = 'Session Active';
        }
    });
});