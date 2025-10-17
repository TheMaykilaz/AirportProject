// AI Chat Interface JavaScript

class AIChat {
    constructor() {
        this.messages = [];
        this.isWaitingForResponse = false;
        this.conversationHistory = [];

        this.initializeElements();
        this.bindEvents();
        this.loadConversationHistory();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearChatBtn = document.getElementById('clearChat');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.settingsModal = document.getElementById('settingsModal');
        this.closeSettingsBtn = document.getElementById('closeSettings');
        this.typingIndicator = document.getElementById('typingIndicator');
    }

    bindEvents() {
        // Send message events
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResizeTextarea());

        // Control buttons
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
        this.settingsBtn.addEventListener('click', () => this.openSettings());
        this.closeSettingsBtn.addEventListener('click', () => this.closeSettings());

        // Modal close on outside click
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.closeSettings();
            }
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.saveConversationHistory();
            }
        });

        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.saveConversationHistory();
        });
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();

        if (!message || this.isWaitingForResponse) {
            return;
        }

        // Add user message to chat
        this.addMessage('user', message);
        this.messageInput.value = '';
        this.autoResizeTextarea();

        // Show typing indicator
        this.showTypingIndicator();

        // Disable send button
        this.setWaitingState(true);

        try {
            // Send message to API
            const response = await this.callChatAPI(message);

            // Hide typing indicator
            this.hideTypingIndicator();

            // Add AI response to chat
            this.addMessage('assistant', response);

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        } finally {
            this.setWaitingState(false);
        }
    }

    async callChatAPI(message) {
        const response = await fetch('/api/ai-chat/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify({
                message: message,
                conversation_history: this.conversationHistory.slice(-10) // Keep last 10 messages
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Update conversation history
        this.conversationHistory.push(
            { role: 'user', content: message },
            { role: 'assistant', content: data.response }
        );

        return data.response;
    }

    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.textContent = role === 'user' ? 'You' : 'AI';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const messageContent = document.createElement('p');
        messageContent.textContent = content;
        contentDiv.appendChild(messageContent);

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (role === 'user') {
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(avatarDiv);
            messageDiv.appendChild(timeDiv);
        } else {
            messageDiv.appendChild(avatarDiv);
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timeDiv);
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Save to local storage periodically
        if (this.messages.length % 5 === 0) {
            this.saveConversationHistory();
        }
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    setWaitingState(waiting) {
        this.isWaitingForResponse = waiting;
        this.sendButton.disabled = waiting;

        if (waiting) {
            this.sendButton.style.background = '#d1d5db';
            this.sendButton.style.cursor = 'not-allowed';
        } else {
            this.sendButton.style.background = '';
            this.sendButton.style.cursor = '';
        }
    }

    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            this.chatMessages.innerHTML = '';
            this.messages = [];
            this.conversationHistory = [];
            this.saveConversationHistory();

            // Add welcome message back
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'message assistant-message';
            welcomeDiv.innerHTML = `
                <div class="message-avatar">AI</div>
                <div class="message-content">
                    <p>Hello! I'm your AI assistant powered by Llama. How can I help you today?</p>
                </div>
                <div class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
            `;
            this.chatMessages.appendChild(welcomeDiv);
            this.scrollToBottom();
        }
    }

    openSettings() {
        this.settingsModal.style.display = 'flex';
    }

    closeSettings() {
        this.settingsModal.style.display = 'none';
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    saveConversationHistory() {
        try {
            localStorage.setItem('ai_chat_history', JSON.stringify(this.conversationHistory.slice(-50))); // Keep last 50 messages
        } catch (error) {
            console.warn('Could not save conversation history:', error);
        }
    }

    loadConversationHistory() {
        try {
            const saved = localStorage.getItem('ai_chat_history');
            if (saved) {
                this.conversationHistory = JSON.parse(saved);
                this.displayConversationHistory();
            }
        } catch (error) {
            console.warn('Could not load conversation history:', error);
        }
    }

    displayConversationHistory() {
        if (this.conversationHistory.length === 0) {
            return;
        }

        // Clear current messages
        this.chatMessages.innerHTML = '';

        // Add conversation history messages
        this.conversationHistory.forEach(msg => {
            this.addMessage(msg.role, msg.content);
        });

        // Scroll to bottom to show latest messages
        setTimeout(() => {
            this.scrollToBottom();
        }, 100);
    }

    // Method to handle file uploads (for future enhancement)
    async handleFileUpload(file) {
        // This could be extended to handle file uploads for analysis
        this.addMessage('user', `[File uploaded: ${file.name}]`);
        this.addMessage('assistant', 'I can see you uploaded a file. Currently, I can help analyze text-based content. What would you like me to help you with regarding this file?');
    }

    // Method to handle voice input (for future enhancement)
    async handleVoiceInput() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            // Speech recognition implementation could go here
            console.log('Voice input feature not yet implemented');
        } else {
            alert('Speech recognition is not supported in this browser.');
        }
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.aiChat = new AIChat();
});

// Add some utility functions for enhanced UX
function formatMessage(text) {
    // Basic formatting for URLs, mentions, etc.
    return text
        .replace(/\bhttps?:\/\/\S+/gi, '<a href="$&" target="_blank">$&</a>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// Add smooth scrolling for better UX
function smoothScrollToBottom(element) {
    element.scrollTo({
        top: element.scrollHeight,
        behavior: 'smooth'
    });
}

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIChat;
}