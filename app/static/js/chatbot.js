document.addEventListener('DOMContentLoaded', function() {
    // --- Key for sessionStorage ---
    const CHAT_HISTORY_KEY = 'chatbot_history';

    // --- DOM Element Selectors ---
    const openBtn = document.getElementById('open-chatbot-btn');
    const closeBtn = document.getElementById('close-chatbot-btn');
    const modalOverlay = document.getElementById('chatbot-modal-overlay');
    
    const chatForm = document.getElementById('chatbot-form');
    const chatInput = document.getElementById('chatbot-input');
    const sendBtn = document.getElementById('chatbot-send-btn');
    const messagesContainer = document.getElementById('chatbot-messages');

    // Security Configuration for Marked.js - This tells the parser to sanitize the output, preventing XSS attacks.
    marked.setOptions({
      sanitize: true
    });

    // --- Modal Open/Close Logic ---
    function openChatbot() {
        if (modalOverlay) {
            modalOverlay.classList.add('visible');
            chatInput.focus();
        }
    }

    function closeChatbot() {
        if (modalOverlay) {
            modalOverlay.classList.remove('visible');
        }
    }

    // --- Event Listeners for Modal ---
    if (openBtn) {
        openBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openChatbot();
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeChatbot);
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(event) {
            if (event.target === modalOverlay) {
                closeChatbot();
            }
        });
    }
    
    // --- Chat Functionality ---
    if (chatForm) {
        // The event listener is now an 'async' function to allow for 'await'
        chatForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const userMessage = chatInput.value.trim();

            if (userMessage) {
                // Display user message and save history
                addMessage(userMessage, 'user');
                saveHistory();
                
                // Clear input and disable the form while waiting for a response
                chatInput.value = '';
                sendBtn.disabled = true;
                showTypingIndicator();

                // --- BEST PRACTICE: Use a try...catch...finally block for API calls ---
                try {
                    // Get the CSRF token from the hidden input in your HTML
                    const csrfToken = document.getElementById('csrf_token')?.value;

                    // Await the response from the fetch call to your Flask backend
                    const response = await fetch('/api/chatbot', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            // Include the CSRF token if the element exists
                            'X-CSRFToken': csrfToken 
                        },
                        body: JSON.stringify({
                            message: userMessage
                        })
                    });
                    
                    // Check if the server responded with an error status
                    if (!response.ok) {
                        const errorData = await response.json();
                        // Throw an error to be caught by the 'catch' block
                        throw new Error(errorData.error || 'An unknown server error occurred.');
                    }
                    
                    // If the response is successful, parse the JSON
                    const data = await response.json();
                    
                    // Display the bot's response and save history
                    addMessage(data.response, 'bot');
                    saveHistory();

                } catch (error) {
                    // If any error occurs, display it in the chat window
                    console.error("Chatbot fetch error:", error);
                    addMessage(`Error: ${error.message}`, 'bot');
                    saveHistory();
                } finally {
                    // This block runs whether the API call succeeded or failed
                    removeTypingIndicator();
                    sendBtn.disabled = false; // Re-enable the send button
                    chatInput.focus(); // Re-focus the input field
                }
            }
        });
    }

    /**
     * Creates and appends a complete message structure (avatar + bubble) to the chat.
     * @param {string} text - The message text to display.
     * @param {string} type - The type of message ('user' or 'bot').
     */
    function addMessage(text, type) {
             const messageElement = document.createElement('div');
             messageElement.classList.add('chat-message', type);
             messageElement.dataset.type = type; 
     
             const avatar = document.createElement('div');
             avatar.classList.add('chat-avatar');
             const icon = document.createElement('i');
             icon.classList.add('bi');
             icon.classList.add(type === 'user' ? 'bi-person-fill' : 'bi-shield-check');
             avatar.appendChild(icon);
     
             const bubble = document.createElement('div');
             bubble.classList.add('chat-bubble');
             
             // --- THIS IS THE KEY CHANGE ---
             if (type === 'bot') {
                 // For bot messages, parse the Markdown text into HTML
                 bubble.innerHTML = marked.parse(text);
             } else {
                 // For user messages, just use plain text
                 bubble.textContent = text;
             }
             // Keep the original text in a data attribute for history
             bubble.dataset.text = text;
             // -----------------------------
         
             messageElement.appendChild(avatar);
             messageElement.appendChild(bubble);
             messagesContainer.appendChild(messageElement);
             messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }


    /**
     * Shows a "typing" indicator with the avatar structure.
     */
    function showTypingIndicator() {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', 'bot', 'typing-indicator-container');

        const avatar = document.createElement('div');
        avatar.classList.add('chat-avatar');
        const icon = document.createElement('i');
        icon.classList.add('bi', 'bi-shield-check');
        avatar.appendChild(icon);
        
        const indicatorElement = document.createElement('div');
        indicatorElement.classList.add('typing-indicator');
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            indicatorElement.appendChild(dot);
        }
        
        messageElement.appendChild(avatar);
        messageElement.appendChild(indicatorElement);
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Removes the "typing" indicator from the chat.
     */
    function removeTypingIndicator() {
        const indicator = document.querySelector('.typing-indicator-container');
        if (indicator) {
            indicator.remove();
        }
    }
    
    // --- History Management Functions ---
    function saveHistory() {
        const messagesToSave = [];
        const messageElements = messagesContainer.querySelectorAll('.chat-message:not(.typing-indicator-container)');
        messageElements.forEach(el => {
            const bubble = el.querySelector('.chat-bubble');
            if (bubble) {
                messagesToSave.push({ type: el.dataset.type, text: bubble.dataset.text });
            }
        });
        sessionStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messagesToSave));
    }

    function loadHistory() {
        const savedHistory = sessionStorage.getItem(CHAT_HISTORY_KEY);
        const history = savedHistory ? JSON.parse(savedHistory) : [];

        if (history.length > 0) {
            history.forEach(msg => addMessage(msg.text, msg.type));
        } else {
            const welcomeText = `
Welcome to My Disaster Planner! I am your AI assistant, here to guide you and offer helpful information and advice for an emergency or disaster preparedness.

To get started, you can ask me things like:
- **"What should I put in a emergency go-kit?"**
- **"How do I find my evacuation zone in Florida?"**
- **"What are some tips for making a plan for an older adult with dementia?"**

How can I assist you today?
            `;

            addMessage(welcomeText, 'bot');
        }
    }

    // --- Initialize the Chat ---
    loadHistory();
});
