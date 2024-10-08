// Toggle between sign in and sign up forms
document.getElementById('showSignup').addEventListener('click', function() {
    document.getElementById('signinContainer').classList.add('hidden');
    document.getElementById('signupContainer').classList.remove('hidden');
});

document.getElementById('showSignin').addEventListener('click', function() {
    document.getElementById('signupContainer').classList.add('hidden');
    document.getElementById('signinContainer').classList.remove('hidden');
});

// Sign In form submission
document.getElementById('signinForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const email = document.getElementById('signinEmail').value;
    const password = document.getElementById('signinPassword').value;
    console.log('Sign In submitted:', { email, password });

    // After successful login, show the chat interface
    document.querySelector('.container').style.display = 'none'; // Hide the login container
    document.getElementById('chat-container').style.display = 'flex'; // Show chat container
});

// Sign Up form submission
document.getElementById('signupForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const firstName = document.getElementById('signupFirstName').value;
    const lastName = document.getElementById('signupLastName').value;
    const email = document.getElementById('signupEmail').value;
    const countryCode = document.getElementById('countryCode').value;
    const phone = document.getElementById('signupPhone').value;
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('signupConfirmPassword').value;

    if (password !== confirmPassword) {
        alert("Passwords don't match!");
        return;
    }

    console.log('Sign Up submitted:', { firstName, lastName, email, countryCode, phone, password });

    // Optionally, after successful sign-up, you can auto log the user in and show the chat interface
    document.querySelector('.container').style.display = 'none'; // Hide the login container
    document.getElementById('chat-container').style.display = 'flex'; // Show chat container
});

// Google Sign-In
function handleCredentialResponse(response) {
    console.log("Encoded JWT ID token: " + response.credential);

    // After successful Google login, show the chat interface
    document.querySelector('.container').style.display = 'none'; // Hide the login container
    document.getElementById('chat-container').style.display = 'flex'; // Show chat container
}
window.onload = function () {
    google.accounts.id.initialize({
        client_id: 'YOUR_GOOGLE_CLIENT_ID',
        callback: handleCredentialResponse
    });
    google.accounts.id.renderButton(
        document.getElementById("googleAuth"),
        { theme: "outline", size: "large" }
    );
};

// LinkedIn Sign-In
document.getElementById('linkedinAuth').addEventListener('click', function() {
    window.open('https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_LINKEDIN_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&state=foobar&scope=r_liteprofile%20r_emailaddress', '_blank');

    // Optionally, you can show the chat interface after successful LinkedIn login
    document.querySelector('.container').style.display = 'none'; // Hide the login container
    document.getElementById('chat-container').style.display = 'flex'; // Show chat container
});

// Chat Interface
document.getElementById('send-btn').addEventListener('click', async function() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();

    if (!message) return;  // Prevent empty messages

    // Display the user's message in the chat
    const userMessage = document.createElement('div');
    userMessage.textContent = 'You: ' + message;
    document.getElementById('message-box').appendChild(userMessage);

    // Clear the input field after retrieving the message
    messageInput.value = '';

    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.textContent = 'ChatGPT is typing...';
    document.getElementById('message-box').appendChild(typingIndicator);

    // Scroll to bottom after typing indicator is added
    document.getElementById('message-box').scrollTop = document.getElementById('message-box').scrollHeight;

    try {
        // Make an API call to OpenAI
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer sk-svcacct-Xq9VEzBiFKrmY_xUhnLReE4Id0pj4CTSPxaPBZP5jfvc1d7BvC6t4XTKPQVELT3BlbkFJIa0tTuWo86KuvPfbQ5v4y1zR9x9MKMJRmHCk7lOo8aUPVBveXsQQVZBqmtKAA`,  // Replace with your OpenAI API key
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: "gpt-3.5-turbo",  // You can replace with "gpt-4" if you want
                messages: [{ role: "user", content: message }]
            })
        });

        const data = await response.json();
        const botReply = data.choices[0].message.content;

        // Remove typing indicator
        typingIndicator.remove();

        // Display the bot's reply with a typing effect
        const botMessage = document.createElement('div');
        botMessage.textContent = 'ChatGPT: ';
        document.getElementById('message-box').appendChild(botMessage);

        // Call function to simulate typing out the response character by character
        simulateTypingEffect(botReply, botMessage);

    } catch (error) {
        console.error('Error:', error);

        // Remove typing indicator
        typingIndicator.remove();

        // Display an error message
        const errorMessage = document.createElement('div');
        errorMessage.textContent = 'Error: Unable to fetch response from server.';
        document.getElementById('message-box').appendChild(errorMessage);
    }

    // Scroll to the bottom of the message box after new messages
    document.getElementById('message-box').scrollTop = document.getElementById('message-box').scrollHeight;
});

// Function to simulate typing effect
function simulateTypingEffect(text, element) {
    let index = 0;
    
    function typeCharacter() {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            index++;
            setTimeout(typeCharacter, 10);  // Adjust typing speed (50ms per character)
        }
    }

    typeCharacter();  // Start typing effect
}



// Log Out and return to the login page
document.getElementById('logout-btn').addEventListener('click', function() {
    document.getElementById('chat-container').style.display = 'none'; // Hide chat container
    document.querySelector('.container').style.display = 'block'; // Show login container
    document.getElementById('message-box').innerHTML = ''; // Clear chat history
});
