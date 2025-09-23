// // app/static/js/student.js
// document.addEventListener('DOMContentLoaded', () => {
//     const loginBtn = document.getElementById('loginBtn');
//     const rollNumberInput = document.getElementById('rollNumberInput');
//     const uidDisplay = document.getElementById('uid-display');
//     const attendanceSection = document.getElementById('attendance-section');
//     const markAttendanceBtn = document.getElementById('markAttendanceBtn');
//     const kCodeInput = document.getElementById('kCodeInput');
//     const statusMessage = document.getElementById('status-message');

//     // Sample mapping for PoC. In a real app, this would be an API call.
//     const studentData = {
//         '2301001': 'uid_student_alpha',
//         '2301002': 'uid_student_beta',
//         '2301003': 'uid_student_gamma',
//         '2301004': 'uid_student_delta',
//         '2301005': 'uid_student_epsilon'
//     };
    
//     // Check if UID is already in localStorage
//     if (localStorage.getItem('student_uid')) {
//         const uid = localStorage.getItem('student_uid');
//         uidDisplay.textContent = uid;
//         attendanceSection.style.display = 'block';
//     }

//     loginBtn.addEventListener('click', () => {
//         const rollNo = rollNumberInput.value.trim();
//         const uid = studentData[rollNo];

//         if (uid) {
//             localStorage.setItem('student_uid', uid);
//             uidDisplay.textContent = uid;
//             attendanceSection.style.display = 'block';
//             statusMessage.textContent = 'Device registered successfully!';
//             statusMessage.style.color = 'green';
//         } else {
//             statusMessage.textContent = 'Roll Number not found.';
//             statusMessage.style.color = 'red';
//         }
//     });

//    // app/static/js/student.js

// // ... (previous code)

//     markAttendanceBtn.addEventListener('click', async () => {
//         const uid = localStorage.getItem('student_uid');
//         const kCode = kCodeInput.value.trim();

//         if (!uid || !kCode) {
//             statusMessage.textContent = 'UID not set or K-CODE is missing.';
//             statusMessage.style.color = 'red';
//             return;
//         }

//         // Generate X-CODE = hash(UID + K-CODE)
//         const dataToHash = uid + kCode;
//         const xCode = CryptoJS.SHA256(dataToHash).toString(CryptoJS.enc.Hex);

//         // Send to backend for validation
//         const response = await fetch('/attendance/mark', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify({ uid: uid, x_code: xCode })
//         });

//         const result = await response.json();
        
//         // ---- THIS IS THE SECTION TO CHECK (around line 53) ----
//         if (result.success) {
//             statusMessage.textContent = result.message;
//             statusMessage.style.color = 'green';
//         } else {
//             statusMessage.textContent = `Error: ${result.message}`;
//             statusMessage.style.color = 'red';
//         }
//     });
// });

// app/static/js/student.js

document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('loginBtn');
    const rollNumberInput = document.getElementById('rollNumberInput');
    // We no longer need the uidDisplay element, but we can keep it for user feedback
    const uidDisplay = document.getElementById('uid-display'); 
    const attendanceSection = document.getElementById('attendance-section');
    const markAttendanceBtn = document.getElementById('markAttendanceBtn');
    const kCodeInput = document.getElementById('kCodeInput');
    const statusMessage = document.getElementById('status-message');

    // This checks if the cookie exists by a simple flag, not its value
    // In a real app, you might have an API endpoint to verify the session
    if (document.cookie.includes('student_uid')) {
        uidDisplay.textContent = 'Device Previously Registered';
        attendanceSection.style.display = 'block';
    }

    loginBtn.addEventListener('click', async () => {
        const rollNo = rollNumberInput.value.trim();
        if (!rollNo) {
            statusMessage.textContent = 'Please enter a Roll Number.';
            statusMessage.style.color = 'red';
            return;
        }
    
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ roll_no: rollNo })
        });
    
        const result = await response.json();
    
        // --- CHECK THIS SECTION CAREFULLY ---
        if (result.success) {
            // This line takes the UID from the response and displays it.
            uidDisplay.textContent = result.uid;
            
            attendanceSection.style.display = 'block';
            statusMessage.textContent = result.message;
            statusMessage.style.color = 'green';
        } else {
            statusMessage.textContent = `Error: ${result.message}`;
            statusMessage.style.color = 'red';
        }
    });
    


    markAttendanceBtn.addEventListener('click', async () => {
        const kCode = kCodeInput.value.trim();

        if (!kCode) {
            statusMessage.textContent = 'K-CODE is missing.';
            statusMessage.style.color = 'red';
            return;
        }

        // The UID is no longer stored in localStorage. The browser handles the cookie.
        const dataToHash = "dummy_data_since_uid_is_on_server" + kCode; // We still need to create a hash.
        // A better approach would be to have the server expect a hash of just the K-Code + a salt.
        // For now, let's keep the X-CODE generation but remove the UID from it client-side.
        // NOTE: The backend logic for X-CODE validation would need to be updated.
        // Let's adjust for a simpler flow: The backend handles the UID, the frontend just sends K-Code.

        // Let's RE-ADJUST for simplicity and security. The X-CODE's purpose is to bind the UID and K-CODE.
        // We will send a hash of the K-CODE and the server will combine it with the cookie UID.
        // This is a more complex change, so for your PoC, we will simply REMOVE UID from the request body.

        // The browser AUTOMATICALLY sends the HttpOnly cookie. We don't need to do anything.
        // We just need to send the X-CODE as before, but the JS can't know the UID.
        // This reveals a challenge in your original architecture.
        // Let's adjust the X-CODE to be something the frontend CAN create.
        
        // --- Let's revert to the original X-CODE logic for now, with the understanding that this is a conceptual PoC ---
        // A more secure system might use a different challenge-response mechanism.
        // The most direct way forward without redesigning the hashing is to actually fetch the UID client-side,
        // use it, and then discard it. But that defeats the purpose of HttpOnly.
        
        // --- NEW SIMPLIFIED AND SECURE FLOW ---
        // Let's modify the X-CODE to just be a hash of the K-CODE.
        // The security now comes from the server validating the (K-CODE hash + the secure UID cookie).

        const xCode = CryptoJS.SHA256(kCode).toString(CryptoJS.enc.Hex);

        const response = await fetch('/attendance/mark', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            // We NO LONGER send the UID. The server gets it from the cookie.
            body: JSON.stringify({ x_code: xCode })
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

// app/static/js/student.js

// ... (other code)

// loginBtn.addEventListener('click', async () => {
//     const rollNo = rollNumberInput.value.trim();
//     if (!rollNo) {
//         statusMessage.textContent = 'Please enter a Roll Number.';
//         statusMessage.style.color = 'red';
//         return;
//     }

//     const response = await fetch('/api/login', {
//         method: 'POST',
//         headers: {'Content-Type': 'application/json'},
//         body: JSON.stringify({ roll_no: rollNo })
//     });

//     const result = await response.json();

//     // --- CHECK THIS SECTION CAREFULLY ---
//     if (result.success) {
//         // This line takes the UID from the response and displays it.
//         uidDisplay.textContent = result.uid;
        
//         attendanceSection.style.display = 'block';
//         statusMessage.textContent = result.message;
//         statusMessage.style.color = 'green';
//     } else {
//         statusMessage.textContent = `Error: ${result.message}`;
//         statusMessage.style.color = 'red';
//     }
// });

// ... (rest of the file)