/**
 * Chatbot Widget - Client-side JavaScript
 * Handles UI interactions and API communication
 */

(function() {
    'use strict';

    // DOM Elements
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotBadge = document.getElementById('chatbot-badge');

    // State
    let isOpen = false;
    let unreadCount = 1;
    let userId = generateUserId();

    /**
     * Generate or retrieve user ID from localStorage
     */
    function generateUserId() {
        let id = localStorage.getItem('chatbot_user_id');
        if (!id) {
            id = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chatbot_user_id', id);
        }
        return id;
    }

    /**
     * Toggle chatbot window open/closed
     */
    function toggleChatbot() {
        isOpen = !isOpen;
        
        if (isOpen) {
            chatbotWindow.classList.remove('hidden');
            chatbotToggle.style.display = 'none';
            chatbotInput.focus();
            
            // Clear unread badge
            unreadCount = 0;
            updateBadge();
            
            // Send initial message if first open
            const messages = chatbotMessages.querySelectorAll('.chatbot-message');
            if (messages.length === 1) {
                setTimeout(() => sendMessage('start'), 500);
            }
        } else {
            chatbotWindow.classList.add('hidden');
            chatbotToggle.style.display = 'flex';
        }
    }

    /**
     * Update unread message badge
     */
    function updateBadge() {
        if (unreadCount > 0) {
            chatbotBadge.textContent = unreadCount > 9 ? '9+' : unreadCount;
            chatbotBadge.classList.remove('hidden');
        } else {
            chatbotBadge.classList.add('hidden');
        }
    }

    /**
     * Add message to chat window
     */
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Convert markdown-style formatting to HTML
        let formattedContent = content
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/```([\s\S]+?)```/g, '<code style="display: block; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; margin: 4px 0;">$1</code>')
            .replace(/`(.+?)`/g, '<code style="background: rgba(0,0,0,0.3); padding: 2px 4px; border-radius: 3px;">$1</code>')
            .replace(/• /g, '&nbsp;&nbsp;• ');
        
        contentDiv.innerHTML = formattedContent;
        messageDiv.appendChild(contentDiv);
        chatbotMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        
        // Increment unread count if window is closed and it's a bot message
        if (!isOpen && !isUser) {
            unreadCount++;
            updateBadge();
        }
    }

    /**
     * Show typing indicator
     */
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message bot-message';
        typingDiv.id = 'typing-indicator';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        
        contentDiv.appendChild(indicator);
        typingDiv.appendChild(contentDiv);
        chatbotMessages.appendChild(typingDiv);
        
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    /**
     * Hide typing indicator
     */
    function hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Send message to API
     */
    async function sendMessage(messageText) {
        if (!messageText.trim()) return;
        
        // Add user message to UI (except for 'start' command)
        if (messageText !== 'start') {
            addMessage(messageText, true);
        }
        
        // Clear input
        chatbotInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Disable send button
        chatbotSend.disabled = true;
        chatbotInput.disabled = true;
        
        try {
            const response = await fetch('/api/v1/chatbot/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    message: messageText
                })
            });
            
            const data = await response.json();
            
            // Simulate slight delay for more natural feel
            await new Promise(resolve => setTimeout(resolve, 500));
            
            hideTypingIndicator();
            
            if (response.ok) {
                addMessage(data.message, false);
            } else {
                addMessage('❌ Error: ' + (data.message || 'Failed to send message'), false);
            }
            
        } catch (error) {
            hideTypingIndicator();
            addMessage('❌ Connection error. Please check your internet connection.', false);
            console.error('Chatbot error:', error);
        } finally {
            // Re-enable send button
            chatbotSend.disabled = false;
            chatbotInput.disabled = false;
            chatbotInput.focus();
        }
    }

    /**
     * Handle send button click
     */
    function handleSend() {
        const message = chatbotInput.value.trim();
        if (message) {
            sendMessage(message);
        }
    }

    /**
     * Handle Enter key in input
     */
    function handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }

    // Event Listeners
    chatbotToggle.addEventListener('click', toggleChatbot);
    chatbotClose.addEventListener('click', toggleChatbot);
    chatbotSend.addEventListener('click', handleSend);
    chatbotInput.addEventListener('keypress', handleKeyPress);

    // Initialize badge
    updateBadge();

    // Auto-focus input when opened
    chatbotInput.addEventListener('focus', function() {
        this.setAttribute('autocomplete', 'off');
    });

})();
