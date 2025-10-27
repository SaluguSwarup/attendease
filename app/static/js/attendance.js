document.addEventListener('DOMContentLoaded', () => {
    const sessionsContainer = document.getElementById('sessions-container');

    async function updateAttendanceTables() {
        const response = await fetch('/session/attendance');
        const sessions = await response.json();
        
        sessionsContainer.innerHTML = ''; // Clear previous content

        const kCodes = Object.keys(sessions);

        if (kCodes.length === 0) {
            sessionsContainer.innerHTML = '<p>No active sessions.</p>';
            return;
        }

        kCodes.forEach(kCode => {
            const session = sessions[kCode];
            
            // Create a container for each session table
            const tableContainer = document.createElement('div');
            tableContainer.className = 'session-table';

            let attendeeListHtml = '<tr><td>No students yet.</td></tr>';
            if (session.attendees.length > 0) {
                attendeeListHtml = session.attendees.map(roll_no => `<tr><td>${roll_no}</td></tr>`).join('');
            }
            
            // This is the updated HTML: The K-CODE line is removed.
            tableContainer.innerHTML = `
                <h3>Class: ${session.class_code} (Prof: ${session.prof_id})</h3>
                <table>
                    <thead>
                        <tr><th>Attended Roll Numbers</th></tr>
                    </thead>
                    <tbody>
                        ${attendeeListHtml}
                    </tbody>
                </table>
            `;
            sessionsContainer.appendChild(tableContainer);
        });
    }

    // Poll for updates every 3 seconds
    setInterval(updateAttendanceTables, 3000);
    // Run it once immediately on page load
    updateAttendanceTables();
});