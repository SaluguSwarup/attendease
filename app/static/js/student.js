document.addEventListener('DOMContentLoaded', () => {
    // Common elements
    const statusMessage = document.getElementById('status-message');

    // Register Mode elements
    const registerBtn = document.getElementById('registerBtn');
    const registerRollInput = document.getElementById('registerRollInput');
    const registerDeviceInput = document.getElementById('registerDeviceInput');

    // Mark Attendance Mode elements
    const markAttendanceBtn = document.getElementById('markAttendanceBtn');
    const markRollInput = document.getElementById('markRollInput'); // Get the new input
    const markDeviceInput = document.getElementById('markDeviceInput');
    const kCodeInput = document.getElementById('kCodeInput');

    // --- REGISTER MODE LOGIC ---
    registerBtn.addEventListener('click', async () => {
        const rollNo = registerRollInput.value.trim();
        const deviceName = registerDeviceInput.value.trim();
        if (!rollNo || !deviceName) {
            statusMessage.textContent = 'Please enter both Roll Number and a Device Name.';
            statusMessage.style.color = 'red';
            return;
        }
        const response = await fetch('/api/register-device', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ roll_no: rollNo })
        });
        const result = await response.json();
        if (result.success) {
            const storageKey = `attendease-device-${deviceName}`;
            localStorage.setItem(storageKey, result.device_token);
            statusMessage.textContent = `${result.message} Your device name is '${deviceName}'. Use it to mark attendance.`;
            statusMessage.style.color = 'green';
        } else {
            statusMessage.textContent = `Error: ${result.message}`;
            statusMessage.style.color = 'red';
        }
    });

    // --- MARK ATTENDANCE MODE LOGIC (CORRECTED) ---
    markAttendanceBtn.addEventListener('click', async () => {
        const rollNo = markRollInput.value.trim(); // Read the roll number from the form
        const deviceName = markDeviceInput.value.trim();
        const kCode = kCodeInput.value.trim();

        if (!rollNo || !deviceName || !kCode) { // Add rollNo to the check
            statusMessage.textContent = 'Please enter Roll Number, Device Name, and K-CODE.';
            statusMessage.style.color = 'red';
            return;
        }
        
        const storageKey = `attendease-device-${deviceName}`;
        const deviceToken = localStorage.getItem(storageKey);
        if (!deviceToken) {
            statusMessage.textContent = 'Error: Device not found. Have you registered with this name?';
            statusMessage.style.color = 'red';
            return;
        }
        
        const response = await fetch('/attendance/mark', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                roll_no: rollNo, // Add rollNo to the data sent to the server
                device_token: deviceToken,
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