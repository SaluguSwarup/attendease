document.addEventListener('DOMContentLoaded', () => {
    const statusMessage = document.getElementById('status-message');

    // --- Section 1: Registration Logic ---
    const registerBtn = document.getElementById('registerBtn');
    const registerRollInput = document.getElementById('registerRollInput');

    registerBtn.addEventListener('click', async () => {
        const rollNo = registerRollInput.value.trim();
        if (!rollNo) {
            statusMessage.textContent = 'Please enter your Roll Number to register.';
            statusMessage.style.color = 'red';
            return;
        }

        // This endpoint's only job is to set the permanent cookie.
        const response = await fetch('/api/register-browser', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ roll_no: rollNo })
        });

        const result = await response.json();
        if (result.success) {
            statusMessage.textContent = 'Browser registered successfully! You can now mark attendance.';
            statusMessage.style.color = 'green';
        } else {
            statusMessage.textContent = `Error: ${result.message}`;
            statusMessage.style.color = 'red';
        }
    });

    // --- Section 2: Mark Attendance Logic ---
    const markAttendanceBtn = document.getElementById('markAttendanceBtn');
    const markRollInput = document.getElementById('markRollInput');
    const kCodeInput = document.getElementById('kCodeInput');

    markAttendanceBtn.addEventListener('click', async () => {
        const rollNo = markRollInput.value.trim();
        const kCode = kCodeInput.value.trim();

        if (!rollNo || !kCode) {
            statusMessage.textContent = 'Please enter your Roll Number and the K-CODE.';
            statusMessage.style.color = 'red';
            return;
        }

        // This endpoint verifies the cookie and marks attendance.
        const response = await fetch('/attendance/mark', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                roll_no: rollNo,
                k_code: kCode
            })
        });

        const result = await response.json();
        if (result.success) {
            statusMessage.textContent = result.message;
            statusMessage.style.color = 'green';
        } else {
            statusMessage.textContent = `Error: ${result.message}`;
            statusMessage.style.color = 'red';
        }
    });
});