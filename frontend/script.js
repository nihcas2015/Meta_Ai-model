// Meta AI System - Frontend JavaScript

let currentJsonData = null;
let uploadedFiles = [];

// Backend API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    updateStatus('Ready');
});

function initializeEventListeners() {
    // File upload handling
    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
    
    // Toggle logs visibility
    document.getElementById('toggleLogs').addEventListener('click', toggleLogs);
    
    // Enter key to send message
    document.getElementById('userInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Click outside modal to close
    window.addEventListener('click', function(e) {
        const modal = document.getElementById('jsonModal');
        if (e.target === modal) {
            closeJsonModal();
        }
    });
}

function handleFileUpload(event) {
    const files = Array.from(event.target.files);
    
    files.forEach(file => {
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            addLogEntry('warning', `File ${file.name} exceeds 10MB limit`);
            return;
        }
        
        uploadedFiles.push(file);
        addFileTag(file);
    });
    
    if (files.length > 0) {
        addLogEntry('info', `Uploaded ${files.length} file(s)`);
    }
    
    // Clear the input
    event.target.value = '';
}

function addFileTag(file) {
    const filesContainer = document.getElementById('uploadedFiles');
    const tag = document.createElement('div');
    tag.className = 'file-tag';
    tag.innerHTML = `
        📎 ${file.name} (${formatFileSize(file.size)})
        <span class="remove" onclick="removeFile('${file.name}')">&times;</span>
    `;
    filesContainer.appendChild(tag);
}

function removeFile(fileName) {
    uploadedFiles = uploadedFiles.filter(file => file.name !== fileName);
    const filesContainer = document.getElementById('uploadedFiles');
    const tags = filesContainer.querySelectorAll('.file-tag');
    tags.forEach(tag => {
        if (tag.textContent.includes(fileName)) {
            tag.remove();
        }
    });
    addLogEntry('info', `Removed file: ${fileName}`);
}

function formatFileSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

function toggleLogs() {
    const logsContent = document.getElementById('logsContent');
    const toggleBtn = document.getElementById('toggleLogs');
    
    if (logsContent.style.display === 'none') {
        logsContent.style.display = 'block';
        toggleBtn.textContent = 'Hide Logs';
    } else {
        logsContent.style.display = 'none';
        toggleBtn.textContent = 'Show Logs';
    }
}

function addLogEntry(type, message) {
    const logsContent = document.getElementById('logsContent');
    const timestamp = new Date().toLocaleTimeString();
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `<strong>[${timestamp}]</strong> ${message}`;
    
    logsContent.appendChild(logEntry);
    logsContent.scrollTop = logsContent.scrollHeight;
    
    // Auto-show logs if there's an error
    if (type === 'error') {
        document.getElementById('logsContent').style.display = 'block';
        document.getElementById('toggleLogs').textContent = 'Hide Logs';
    }
}

function updateStatus(message, showSpinner = false) {
    document.getElementById('statusText').textContent = message;
    const spinner = document.getElementById('loadingSpinner');
    spinner.style.display = showSpinner ? 'block' : 'none';
}

async function sendMessage() {
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const userQuery = userInput.value.trim();
    
    if (!userQuery) {
        addLogEntry('warning', 'Please enter a query');
        return;
    }
    
    // Disable input while processing
    userInput.disabled = true;
    sendButton.disabled = true;
    sendButton.innerHTML = '<span>🔄</span><span>Processing...</span>';
    
    // Add user message to chat
    addMessage('user', userQuery);
    
    // Clear input
    userInput.value = '';
    
    try {
        // Update status and logs
        updateStatus('Processing request...', true);
        addLogEntry('info', `Starting Meta AI workflow for: "${userQuery}"`);
        
        // Prepare request data
        const requestData = {
            user_query: userQuery,
            files: await processUploadedFiles(),
            timestamp: new Date().toISOString()
        };
        
        addLogEntry('info', 'Sending request to backend...');
        
        // Send request to backend
        const response = await fetch(`${API_BASE_URL}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        addLogEntry('success', 'Backend response received');
        
        // Process response
        const result = await response.json();
        handleBackendResponse(result);
        
    } catch (error) {
        addLogEntry('error', `Error: ${error.message}`);
        addMessage('system', `❌ Error: ${error.message}`, 'error');
        updateStatus('Error occurred', false);
    } finally {
        // Re-enable input
        userInput.disabled = false;
        sendButton.disabled = false;
        sendButton.innerHTML = '<span>🚀</span><span>Send</span>';
        updateStatus('Ready', false);
    }
}

async function processUploadedFiles() {
    const fileData = [];
    
    for (const file of uploadedFiles) {
        try {
            const content = await readFileContent(file);
            fileData.push({
                name: file.name,
                size: file.size,
                type: file.type,
                content: content
            });
            addLogEntry('info', `Processed file: ${file.name}`);
        } catch (error) {
            addLogEntry('error', `Failed to read file ${file.name}: ${error.message}`);
        }
    }
    
    return fileData;
}

function readFileContent(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            if (file.type === 'application/pdf') {
                // For PDF files, we'll send the base64 data
                resolve({
                    type: 'base64',
                    data: e.target.result.split(',')[1]
                });
            } else {
                // For text files
                resolve({
                    type: 'text',
                    data: e.target.result
                });
            }
        };
        reader.onerror = reject;
        
        if (file.type === 'application/pdf') {
            reader.readAsDataURL(file);
        } else {
            reader.readAsText(file);
        }
    });
}

function handleBackendResponse(result) {
    addLogEntry('success', `Workflow completed. Conversation ID: ${result.conversation_id}`);
    
    // Store data for modal viewing (but prioritize visual display)
    currentJsonData = result;
    
    // Create response message with visual content
    let responseHtml = `
        <strong>🎉 Meta AI Analysis Complete</strong>
        <p><strong>Conversation ID:</strong> ${result.conversation_id}</p>
        <p><strong>Workflow Type:</strong> ${result.workflow_type || 'Auto-determined'}</p>
    `;
    
    // Add domain analysis summary
    if (result.domain_outputs) {
        responseHtml += '<br><strong>📊 Domain Analysis Summary:</strong><ul>';
        Object.entries(result.domain_outputs).forEach(([domain, output]) => {
            responseHtml += `<li><strong>${domain.charAt(0).toUpperCase() + domain.slice(1)}:</strong> ${output.key_findings?.length || 0} findings, ${output.recommendations?.length || 0} recommendations</li>`;
        });
        responseHtml += '</ul>';
    }
    
    // Display workflow diagram (always shown)
    if (result.visual_content?.workflow_diagram_base64) {
        responseHtml += `
            <div class="visual-content">
                <h3>� Workflow Process</h3>
                <img src="${result.visual_content.workflow_diagram_base64}" alt="Workflow Diagram" class="workflow-image">
            </div>
        `;
    }
    
    // Display content based on workflow type
    if (result.visual_content) {
        responseHtml += displayVisualContent(result.visual_content, result.workflow_type);
    }
    
    // Add option to view technical details
    responseHtml += `
        <div class="json-preview">
            <button class="expand-btn" onclick="showJsonModal()">🔍 View Technical Details</button>
        </div>
    `;
    
    addMessage('system', responseHtml);
    
    // Log the process steps
    if (result.process_logs) {
        result.process_logs.forEach(log => {
            addLogEntry(log.level || 'info', log.message);
        });
    }
    
    // Clear uploaded files after successful processing
    uploadedFiles = [];
    document.getElementById('uploadedFiles').innerHTML = '';
}

function displayVisualContent(visualContent, workflowType) {
    let contentHtml = '';
    
    switch(workflowType) {
        case 'pdf':
        case 'word':
            if (visualContent.document_preview_base64) {
                contentHtml += `
                    <div class="visual-content">
                        <h3>📄 Document Preview</h3>
                        <img src="${visualContent.document_preview_base64}" alt="Document Preview" class="document-image">
                    </div>
                `;
            }
            break;
            
        case 'diagram':
            if (visualContent.pipeline_diagram_base64) {
                contentHtml += `
                    <div class="visual-content">
                        <h3>📊 System Pipeline Diagram</h3>
                        <img src="${visualContent.pipeline_diagram_base64}" alt="Pipeline Diagram" class="diagram-image">
                    </div>
                `;
            }
            break;
            
        case 'powerpoint':
            if (visualContent.powerpoint_slides_base64) {
                contentHtml += `
                    <div class="visual-content">
                        <h3>📽️ PowerPoint Presentation Preview</h3>
                        <div class="slides-container">
                `;
                
                visualContent.powerpoint_slides_base64.forEach((slide, index) => {
                    contentHtml += `
                        <div class="slide-preview">
                            <p class="slide-title">Slide ${index + 1}</p>
                            <img src="${slide.base64}" alt="Slide ${index + 1}" class="slide-image" onclick="showSlideModal('${slide.base64}', ${index + 1})">
                        </div>
                    `;
                });
                
                contentHtml += `
                        </div>
                    </div>
                `;
            }
            break;
            
        case 'project':
            if (visualContent.project_structure_base64) {
                contentHtml += `
                    <div class="visual-content">
                        <h3>💻 Project Structure</h3>
                        <img src="${visualContent.project_structure_base64}" alt="Project Structure" class="project-image">
                    </div>
                `;
            }
            break;
    }
    
    return contentHtml;
}

function addMessage(sender, content, type = 'normal') {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (type === 'error') {
        contentDiv.style.backgroundColor = '#fed7d7';
        contentDiv.style.color = '#c53030';
        contentDiv.style.borderColor = '#feb2b2';
    }
    
    contentDiv.innerHTML = content;
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showSlideModal(slideBase64, slideNumber) {
    const modal = document.getElementById('jsonModal');
    const jsonContent = document.getElementById('jsonContent');
    
    // Replace JSON content with slide image
    jsonContent.innerHTML = `
        <h2>📽️ Slide ${slideNumber} Preview</h2>
        <img src="${slideBase64}" alt="Slide ${slideNumber}" style="max-width: 100%; height: auto;">
    `;
    
    modal.style.display = 'block';
    addLogEntry('info', `Opened slide ${slideNumber} preview`);
}

function showJsonModal() {
    if (!currentJsonData) return;
    
    const modal = document.getElementById('jsonModal');
    const jsonContent = document.getElementById('jsonContent');
    
    jsonContent.innerHTML = `
        <h2>📄 Technical Details</h2>
        <pre>${JSON.stringify(currentJsonData, null, 2)}</pre>
    `;
    modal.style.display = 'block';
    
    addLogEntry('info', 'Opened technical details viewer');
}

function closeJsonModal() {
    document.getElementById('jsonModal').style.display = 'none';
}

function downloadJson() {
    if (!currentJsonData) return;
    
    const dataStr = JSON.stringify(currentJsonData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `meta_ai_result_${currentJsonData.conversation_id || Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
    addLogEntry('success', 'JSON file downloaded');
}

// Utility function for error handling
function handleError(error, context) {
    console.error(`Error in ${context}:`, error);
    addLogEntry('error', `${context}: ${error.message}`);
    updateStatus('Error occurred', false);
}

// Connection test function
async function testBackendConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            addLogEntry('success', 'Backend connection established');
            return true;
        } else {
            throw new Error(`Backend health check failed: ${response.status}`);
        }
    } catch (error) {
        addLogEntry('error', `Backend connection failed: ${error.message}`);
        return false;
    }
}

// Test connection on page load
setTimeout(testBackendConnection, 1000);