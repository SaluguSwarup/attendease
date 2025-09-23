document.addEventListener('DOMContentLoaded', () => {
    const kCodeDisplay = document.getElementById('k-code-display');
    const attendanceList = document.getElementById('attendance-list');

    async function updateAttendanceList() {
        const response = await fetch('/session/attendance');
        const data = await response.json();
        
        kCodeDisplay.textContent = data.k_code || 'None';
        attendanceList.innerHTML = '';
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

    // Poll for updates every 3 seconds
    setInterval(updateAttendanceList, 3000);
    // Run it once immediately on page load
    updateAttendanceList();
});