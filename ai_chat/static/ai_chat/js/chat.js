// AI Chat Interface JavaScript

class AIChat {
    constructor() {
        this.messages = [];
        this.isWaitingForResponse = false;
        this.conversationHistory = [];
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        this.initializeElements();
        this.bindEvents();
        this.loadConversationHistory();
        this.connectWebSocket();
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
            if (this.websocket) {
                this.websocket.close();
            }
        });
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();

        if (!message || this.isWaitingForResponse || !this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
                this.addMessage('assistant', 'Connection lost. Trying to reconnect...');
                this.connectWebSocket();
            }
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
            // Send message via WebSocket
            this.websocket.send(JSON.stringify({
                type: 'chat',
                message: message
            }));

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            this.setWaitingState(false);
            // Reset WebSocket connection if needed
            if (this.websocket && this.websocket.readyState !== WebSocket.OPEN) {
                this.connectWebSocket();
            }
        }
    }

    connectWebSocket() {
        // Use configured WebSocket URL from Django settings if available
        const wsUrl = window.AI_CHAT_WEBSOCKET_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat/`;

        console.log('Connecting to WebSocket:', wsUrl);

        try {
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = (event) => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('Connected', 'connected');
            };

            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };

            this.websocket.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.updateConnectionStatus('Disconnected', 'disconnected');
                this.attemptReconnect();
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('Error', 'error');
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateConnectionStatus('Failed to connect', 'error');
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            this.updateConnectionStatus('Connection failed', 'error');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connectWebSocket();
        }, delay);
    }

    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('Received WebSocket message:', data.type);

            switch (data.type) {
                case 'welcome':
                    this.addMessage('assistant', data.message);
                    break;

                case 'stream_chunk':
                    this.handleStreamChunk(data.chunk);
                    break;

                case 'response_complete':
                    this.handleResponseComplete(data.full_response);
                    break;

                case 'error':
                    this.handleWebSocketError(data.message);
                    break;

                case 'history_cleared':
                    this.addMessage('assistant', data.message);
                    break;

                default:
                    console.warn('Unknown message type:', data.type);
            }

        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    handleStreamChunk(chunk) {
        // For streaming, we'll accumulate chunks and display them progressively
        if (!this.currentStreamingMessage) {
            // Start a new streaming message
            this.currentStreamingMessage = this.addStreamingMessage('assistant', '');
        }

        // Append chunk to current message
        this.appendToStreamingMessage(chunk);
    }

    handleResponseComplete(fullResponse) {
        this.hideTypingIndicator();
        this.setWaitingState(false);

        if (this.currentStreamingMessage) {
            // Update with final response
            this.finalizeStreamingMessage(fullResponse);
            this.currentStreamingMessage = null;
        } else {
            // Fallback: add complete message
            this.addMessage('assistant', fullResponse);
        }
    }

    handleWebSocketError(message) {
        this.hideTypingIndicator();
        this.setWaitingState(false);
        this.addMessage('assistant', `Error: ${message}`);
    }

    addStreamingMessage(role, initialContent) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message streaming`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.textContent = role === 'user' ? 'You' : 'AI';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const messageContent = document.createElement('p');
        messageContent.textContent = initialContent;
        messageContent.className = 'streaming-content';
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

        return {
            element: messageDiv,
            contentElement: messageContent,
            currentContent: initialContent
        };
    }

    appendToStreamingMessage(chunk) {
        if (this.currentStreamingMessage) {
            this.currentStreamingMessage.currentContent += chunk;
            this.currentStreamingMessage.contentElement.textContent = this.currentStreamingMessage.currentContent;
            this.scrollToBottom();
        }
    }

    finalizeStreamingMessage(finalContent) {
        if (this.currentStreamingMessage) {
            this.currentStreamingMessage.contentElement.textContent = finalContent;
            this.currentStreamingMessage.element.classList.remove('streaming');
            this.scrollToBottom();
        }
    }

    updateConnectionStatus(status, statusClass) {
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.status-text');

        if (statusIndicator && statusText) {
            statusIndicator.className = `status-indicator ${statusClass}`;
            statusText.textContent = status;
        }
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

            // Send clear history command via WebSocket
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({
                    type: 'clear_history'
                }));
            }

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