// app/static/js/professor.js
document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startSessionBtn');
    const kCodeDisplay = document.getElementById('k-code-display');
    const attendanceList = document.getElementById('attendance-list');
    let attendanceInterval;

    startBtn.addEventListener('click', async () => {
        const response = await fetch('/session/start', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            kCodeDisplay.textContent = data.k_code;
            startBtn.disabled = true;
            startBtn.textContent = 'Session Active';
            // Start polling for live attendance
            if (attendanceInterval) clearInterval(attendanceInterval);
            attendanceInterval = setInterval(updateAttendanceList, 3000); // Poll every 3 seconds
        }
    });

    async function updateAttendanceList() {
        const response = await fetch('/session/attendance');
        const data = await response.json();

        attendanceList.innerHTML = ''; // Clear the list
        if (data.attendees.length === 0) {
            attendanceList.innerHTML = '<li>No students yet.</li>';
        } else {
            data.attendees.forEach(roll_no => {
                const li = document.createElement('li');
                li.textContent = roll_no;
                attendanceList.appendChild(li);
            });
        }
    }
});
