document.addEventListener('DOMContentLoaded', () => {
    // Session elements
    const startBtn = document.getElementById('startSessionBtn');
    const endBtn = document.getElementById('endSessionBtn');
    const kCodeDisplay = document.getElementById('k-code-display');
    const profIdInput = document.getElementById('profIdInput');
    const classCodeInput = document.getElementById('classCodeInput');
    let activeKCode = null; // We still store the token here, just don't show it

    // Manual Mark elements
    const manualMarkBtn = document.getElementById('manualMarkBtn');
    const manualRollInput = document.getElementById('manualRollInput');
    const manualStatus = document.getElementById('manual-status');

    // Override Code elements
    const generateOverrideBtn = document.getElementById('generateOverrideBtn');
    const overrideCodeDisplay = document.getElementById('override-code-display');

    // Helper function to read a cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    // Event listener for starting a session
    startBtn.addEventListener('click', async () => {
        const profId = profIdInput.value;
        const classCode = classCodeInput.value;

        if (!profId || !classCode) {
            alert('Please enter both Professor ID and Class Code.');
            return;
        }

        const gatewayToken = getCookie('gateway_token');
        if (!gatewayToken) {
            alert('Error: Not connected to the Attendance Wi-Fi. Please connect to the ESP32 hotspot and try again.');
            return;
        }

        const response = await fetch('/session/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prof_id: profId, class_code: classCode})
        });
        
        const data = await response.json();
        if (data.success) {
            activeKCode = data.k_code; // Save the token internally
            kCodeDisplay.textContent = "Active"; // Display "Active" to the user
            kCodeDisplay.style.color = 'green';
            startBtn.disabled = true;
            endBtn.style.display = 'inline-block'; // Show the end button
        } else {
            alert(`Error: ${data.message}`);
        }
    });

    // Event listener for ending a session
    endBtn.addEventListener('click', async () => {
        if (!activeKCode) {
            alert('No active session to end.');
            return;
        }

        const response = await fetch('/session/end', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ k_code: activeKCode }) // Send the stored token
        });

        const result = await response.json();
        if (result.success) {
            alert(result.message);
            // Reset the UI
            kCodeDisplay.textContent = "Inactive";
            kCodeDisplay.style.color = '#555';
            overrideCodeDisplay.textContent = "None"; // Clear override code
            startBtn.disabled = false;
            endBtn.style.display = 'none';
            activeKCode = null;
            manualStatus.textContent = '';
        } else {
            alert(`Error: ${result.message}`);
        }
    });

    // Event listener for manual marking
    manualMarkBtn.addEventListener('click', async () => {
        const rollNo = manualRollInput.value.trim();
        if (!rollNo) {
            manualStatus.textContent = 'Please enter a roll number.';
            manualStatus.style.color = 'red';
            return;
        }
        if (!activeKCode) {
            manualStatus.textContent = 'You must start a session first.';
            manualStatus.style.color = 'red';
            return;
        }

        const response = await fetch('/attendance/manual-mark', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({roll_no: rollNo, k_code: activeKCode})
        });

        const result = await response.json();
        if (result.success) {
            manualStatus.textContent = result.message;
            manualStatus.style.color = 'green';
            manualRollInput.value = '';
        } else {
            manualStatus.textContent = `Error: ${result.message}`;
            manualStatus.style.color = 'red';
        }
    });

    // Event listener for generating override code
    generateOverrideBtn.addEventListener('click', async () => {
        if (!activeKCode) {
            alert('You must start a session first.');
            return;
        }

        // The gateway_token is sent via cookie, so we just POST
        const response = await fetch('/session/generate-override', {
            method: 'POST'
        });

        const result = await response.json();
        if (result.success) {
            overrideCodeDisplay.textContent = result.override_code;
        } else {
            alert(`Error: ${result.message}`);
        }
    });
});