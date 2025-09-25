// DOM Elements
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const fileInput = document.getElementById('fileInput');
const logPopup = document.getElementById('logPopup');
const logBody = document.getElementById('logBody');

// SocketIO connection
const socket = io();

// State management
let currentConversationId = null;
let currentProcessingSteps = [];
let isProcessing = false;

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
});

// Add click event listener to send button
sendBtn.addEventListener('click', function() {
    const content = userInput.value.trim();
    if (content && !isProcessing) {
        sendMessage(content);
        userInput.value = '';
        userInput.style.height = 'auto';
    }
});

// Add enter key event listener
userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey && !isProcessing) {
        e.preventDefault();
        sendBtn.click();
    }
});

// Send message function
async function sendMessage(content) {
    if (isProcessing) {
        addMessageToChat('Please wait for the current processing to complete.', 'system');
        return;
    }

    const message = {
        content: content,
        conversation_id: currentConversationId,
        timestamp: new Date().toISOString()
    };

    // Add user message to chat
    addMessageToChat(content, 'user');

    // Show processing state
    isProcessing = true;
    sendBtn.disabled = true;
    sendBtn.textContent = 'Processing...';
    userInput.disabled = true;

    // Show real-time processing message
    const processingId = showProcessingMessage();

    try {
        // Send to backend
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(message)
        });

        const result = await response.json();

        if (result.status === 'processing') {
            currentConversationId = result.conversation_id;
            
            // Update processing message with conversation ID
            updateProcessingMessage(processingId, `Processing conversation ${result.conversation_id}...`);
            
            addMessageToChat(`🎯 Started Meta Model workflow for conversation: ${result.conversation_id}`, 'system');
            
            // Real-time updates will be handled by SocketIO events
        } else {
            throw new Error(result.error || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Error processing message:', error);
        removeProcessingMessage(processingId);
        addMessageToChat('❌ Error processing your request. Please try again. Make sure Ollama is running with llama3.2 model.', 'error');
        
        // Reset processing state
        resetProcessingState();
    }
}

// SocketIO Event Handlers
socket.on('connect', function() {
    console.log('Connected to Meta System');
    addMessageToChat('🌟 Connected to Meta Model System. Ready to process your queries!', 'system');
});

socket.on('processing_update', function(data) {
    console.log('Processing update:', data);
    
    if (data.conversation_id === currentConversationId) {
        const step = data.step;
        currentProcessingSteps.push(step);
        
        // Update processing display
        updateProcessingDisplay(step);
        
        // Update logs
        updateLogDisplay();
    }
});

socket.on('processing_complete', function(data) {
    console.log('Processing complete:', data);
    
    if (data.conversation_id === currentConversationId) {
        // Remove processing message
        removeAllProcessingMessages();
        
        // Add final response
        addMessageToChat(data.response, 'bot');
        
        // Show completion message
        addMessageToChat('✅ Meta Model workflow completed successfully!', 'system');
        
        // Reset processing state
        resetProcessingState();
        
        // Show logs button
        showProcessingLogsButton();
    }
});

socket.on('processing_error', function(data) {
    console.log('Processing error:', data);
    
    if (data.conversation_id === currentConversationId) {
        // Remove processing message
        removeAllProcessingMessages();
        
        // Add error message
        addMessageToChat(`❌ Processing error: ${data.error}`, 'error');
        
        // Reset processing state
        resetProcessingState();
    }
});

// Processing display functions
function showProcessingMessage() {
    const id = Date.now();
    const processingDiv = document.createElement('div');
    processingDiv.className = 'message bot-message processing-message fade-in';
    processingDiv.id = `processing-${id}`;
    processingDiv.innerHTML = `
        <div class="processing-content">
            <div class="processing-text">🔄 Initializing Meta Model workflow...</div>
            <div class="processing-steps" id="steps-${id}"></div>
            <button class="show-logs-btn" onclick="showLogPopup()">Show Real-time Logs</button>
        </div>
    `;
    messagesContainer.appendChild(processingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
}

function updateProcessingMessage(id, message) {
    const processingDiv = document.getElementById(`processing-${id}`);
    if (processingDiv) {
        const textDiv = processingDiv.querySelector('.processing-text');
        if (textDiv) {
            textDiv.textContent = message;
        }
    }
}

function updateProcessingDisplay(step) {
    const processingMessages = document.querySelectorAll('.processing-message');
    const latestProcessing = processingMessages[processingMessages.length - 1];
    
    if (latestProcessing) {
        const stepsContainer = latestProcessing.querySelector('.processing-steps');
        if (stepsContainer) {
            const stepDiv = document.createElement('div');
            stepDiv.className = `processing-step step-${step.status}`;
            
            let statusIcon = '⏳';
            if (step.status === 'completed') statusIcon = '✅';
            else if (step.status === 'error') statusIcon = '❌';
            
            stepDiv.innerHTML = `
                <span class="step-icon">${statusIcon}</span>
                <span class="step-name">${step.step_name}</span>
                <span class="step-domain">(${step.domain})</span>
            `;
            
            stepsContainer.appendChild(stepDiv);
        }
        
        // Update main processing text based on current step
        const textDiv = latestProcessing.querySelector('.processing-text');
        if (textDiv) {
            textDiv.textContent = `🔄 ${step.step_name}...`;
        }
    }
}

function removeProcessingMessage(id) {
    const processingDiv = document.getElementById(`processing-${id}`);
    if (processingDiv) {
        processingDiv.remove();
    }
}

function removeAllProcessingMessages() {
    const processingMessages = document.querySelectorAll('.processing-message');
    processingMessages.forEach(msg => msg.remove());
}

function resetProcessingState() {
    isProcessing = false;
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';
    userInput.disabled = false;
    userInput.focus();
}

// Add message to chat
function addMessageToChat(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message fade-in`;
    
    // Format content based on sender
    if (sender === 'bot' || sender === 'system') {
        // Convert markdown-like formatting to HTML
        content = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^• (.*$)/gim, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    }
    
    messageDiv.innerHTML = content;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Add glow animation for bot messages
    if (sender === 'bot') {
        setTimeout(() => {
            messageDiv.classList.add('active-glow');
            setTimeout(() => {
                messageDiv.classList.remove('active-glow');
            }, 2000);
        }, 100);
    }
    
    return messageDiv;
}

// Logs functionality
function showProcessingLogsButton() {
    // Remove existing button if any
    const existingBtn = document.querySelector('.main-logs-btn');
    if (existingBtn) {
        existingBtn.remove();
    }
    
    const logsBtn = document.createElement('button');
    logsBtn.className = 'main-logs-btn show-logs-btn';
    logsBtn.textContent = 'View Complete Processing Logs';
    logsBtn.onclick = showLogPopup;
    
    // Add to chat container
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.appendChild(logsBtn);
}

async function showLogPopup() {
    try {
        let logs = [];
        
        if (currentConversationId) {
            // Get logs for current conversation
            const response = await fetch(`/logs/${currentConversationId}`);
            const data = await response.json();
            logs = data.steps || [];
        } else {
            // Get all logs
            const response = await fetch('/logs');
            const data = await response.json();
            
            // Flatten all logs
            for (const [convId, steps] of Object.entries(data)) {
                logs = logs.concat(steps.map(step => ({
                    ...step,
                    conversation_id: convId
                })));
            }
        }
        
        // Sort by timestamp
        logs.sort((a, b) => a.timestamp - b.timestamp);
        
        // Display logs
        displayLogs(logs);
        
    } catch (error) {
        console.error('Error fetching logs:', error);
        alert('Error loading logs. Please try again.');
    }
}

function displayLogs(logs) {
    const logBody = document.getElementById('logBody');
    logBody.innerHTML = '';
    
    if (logs.length === 0) {
        logBody.innerHTML = '<div class="log-empty">No processing logs available yet.</div>';
    } else {
        logs.forEach(log => {
            const logDiv = document.createElement('div');
            logDiv.className = `log-entry log-${log.status}`;
            
            const timestamp = new Date(log.timestamp * 1000).toLocaleString();
            
            logDiv.innerHTML = `
                <div class="log-header">
                    <span class="log-step">${log.step_name}</span>
                    <span class="log-domain">${log.domain}</span>
                    <span class="log-status status-${log.status}">${log.status}</span>
                    <span class="log-time">${timestamp}</span>
                </div>
                <div class="log-details">${log.details}</div>
                ${log.output ? `<div class="log-output">${log.output}</div>` : ''}
                ${log.conversation_id ? `<div class="log-conv-id">Conversation: ${log.conversation_id}</div>` : ''}
            `;
            
            logBody.appendChild(logDiv);
        });
    }
    
    // Show popup
    document.getElementById('logPopup').style.display = 'flex';
}

function updateLogDisplay() {
    // Update real-time log display if popup is open
    const logPopup = document.getElementById('logPopup');
    if (logPopup.style.display === 'flex') {
        showLogPopup(); // Refresh logs
    }
}

// Close log popup
function closeLogPopup() {
    document.getElementById('logPopup').style.display = 'none';
}

// Close popup when clicking outside
document.getElementById('logPopup').addEventListener('click', function(e) {
    if (e.target === this) {
        closeLogPopup();
    }
});

// Feature buttons functionality
function clearChat() {
    messagesContainer.innerHTML = '';
    currentConversationId = null;
    currentProcessingSteps = [];
    
    // Remove logs button
    const logsBtn = document.querySelector('.main-logs-btn');
    if (logsBtn) {
        logsBtn.remove();
    }
    
    addMessageToChat('🔄 Chat cleared. Ready for new conversation!', 'system');
}

function exportChat() {
    const messages = document.querySelectorAll('.message');
    let chatText = 'Meta Model System - Chat Export\n';
    chatText += '=====================================\n\n';
    
    messages.forEach(msg => {
        const sender = msg.classList.contains('user-message') ? 'User' : 
                      msg.classList.contains('bot-message') ? 'Bot' : 'System';
        chatText += `[${sender}]: ${msg.textContent}\n\n`;
    });
    
    // Create and download file
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `meta_model_chat_${new Date().toISOString().slice(0, 19)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Focus on input
    userInput.focus();
    
    // Add welcome message
    setTimeout(() => {
        addMessageToChat('🎯 Welcome to the Integrated Meta Model System!', 'system');
        addMessageToChat('Enter your query and I will process it through our domain experts (Mechanical, Electrical, Programming), create an optimal workflow, and generate the appropriate document.', 'system');
        addMessageToChat('All prompts and processing steps are logged for transparency.', 'system');
    }, 500);
});

// Add CSS for new elements
const style = document.createElement('style');
style.textContent = `
.processing-message {
    border-left: 4px solid #00ffff;
    background: rgba(0, 255, 255, 0.1);
}

.processing-content {
    padding: 10px;
}

.processing-text {
    font-weight: 600;
    margin-bottom: 10px;
    color: #00ffff;
}

.processing-steps {
    margin: 10px 0;
}

.processing-step {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    font-size: 0.9rem;
}

.step-icon {
    font-size: 1rem;
}

.step-name {
    font-weight: 500;
}

.step-domain {
    color: #888;
    font-size: 0.8rem;
}

.step-completed {
    color: #00ff00;
}

.step-error {
    color: #ff0000;
}

.main-logs-btn {
    margin: 20px 0;
    width: 100%;
    background: linear-gradient(45deg, #ff00ff, #00ffff);
    border: none;
    color: #fff;
    padding: 15px 25px;
    border-radius: 30px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 600;
    transition: all 0.3s ease;
}

.main-logs-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.log-entry {
    margin-bottom: 15px;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid;
}

.log-completed {
    border-left-color: #00ff00;
    background: rgba(0, 255, 0, 0.1);
}

.log-started {
    border-left-color: #ffff00;
    background: rgba(255, 255, 0, 0.1);
}

.log-error {
    border-left-color: #ff0000;
    background: rgba(255, 0, 0, 0.1);
}

.log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    flex-wrap: wrap;
    gap: 10px;
}

.log-step {
    font-weight: 600;
    color: #fff;
}

.log-domain {
    background: rgba(255, 255, 255, 0.1);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
}

.log-status {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
}

.status-completed {
    background: rgba(0, 255, 0, 0.3);
    color: #00ff00;
}

.status-started {
    background: rgba(255, 255, 0, 0.3);
    color: #ffff00;
}

.status-error {
    background: rgba(255, 0, 0, 0.3);
    color: #ff0000;
}

.log-time {
    font-size: 0.8rem;
    color: #888;
}

.log-details {
    color: #ccc;
    margin-bottom: 5px;
}

.log-output {
    background: rgba(255, 255, 255, 0.05);
    padding: 8px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.85rem;
    color: #00ffff;
    margin-top: 5px;
}

.log-conv-id {
    font-size: 0.8rem;
    color: #888;
    margin-top: 5px;
}

.log-empty {
    text-align: center;
    color: #888;
    padding: 40px;
    font-style: italic;
}

.system-message {
    background: rgba(0, 255, 255, 0.1);
    border-left: 4px solid #00ffff;
    color: #00ffff;
}

.error-message {
    background: rgba(255, 0, 0, 0.1);
    border-left: 4px solid #ff0000;
    color: #ff6666;
}

.active-glow {
    animation: glow 2s ease-in-out;
}

@keyframes glow {
    0%, 100% { box-shadow: none; }
    50% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.5); }
}
`;
document.head.appendChild(style);