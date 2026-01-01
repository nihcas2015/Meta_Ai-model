// Meta AI System - Simplified Frontend

const API_BASE_URL = 'http://localhost:5000/api';

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('sendButton').addEventListener('click', sendMessage);
    document.getElementById('userInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) sendMessage();
    });
});

async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessage('user', message);
    input.value = '';
    updateStatus('Processing...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message })
        });
        
        if (!response.ok) throw new Error(`Error: ${response.status}`);
        const data = await response.json();
        
        addMessage('assistant', data.summary || 'Analysis complete');
        updateStatus('Ready');
        
    } catch (error) {
        addMessage('system', `Error: ${error.message}`);
        updateStatus('Error');
    }
}

function addMessage(type, content) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = content;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function updateStatus(status) {
    document.getElementById('status').textContent = status;
}
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
    
    // Store data for modal viewing
    currentJsonData = result;
    
    // Create response message with file paths instead of visual content
    let responseHtml = `
        <strong>🎉 Meta AI Analysis Complete</strong>
        <p><strong>Conversation ID:</strong> ${result.conversation_id}</p>
        <p><strong>Workflow Type:</strong> ${result.workflow_type || 'Auto-determined'}</p>
    `;
    
    // Show file paths instead of trying to display images/documents
    if (result.visual_content) {
        responseHtml += displayVisualContent(result.visual_content, result.workflow_type);
    } else {
        // Show default paths even if no visual content is returned
        responseHtml += `
            <div class="file-paths-section">
                <h3>📁 Default File Locations</h3>
                <div class="file-paths-container">
                    <div class="file-path-item">
                        <span class="file-icon">📄</span>
                        <div class="file-info">
                            <strong>Analysis Report:</strong>
                            <p class="file-path">${DEFAULT_FILE_PATHS.PDF_DOCUMENTS}${DEFAULT_FILE_PATHS.DEFAULT_DOCUMENT_NAME}</p>
                            <small>Generated analysis document</small>
                        </div>
                    </div>
                    <div class="file-path-item">
                        <span class="file-icon">📊</span>
                        <div class="file-info">
                            <strong>Data Output:</strong>
                            <p class="file-path">${DEFAULT_FILE_PATHS.CSV_FILES}${DEFAULT_FILE_PATHS.DEFAULT_CSV_NAME}</p>
                            <small>Analysis data and metrics</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
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
    
    // Display file paths instead of actual images/documents
    contentHtml += `
        <div class="file-paths-section">
            <h3>📁 Generated Files Locations</h3>
            <div class="file-paths-container">
    `;
    
    // Show document file paths
    if (workflowType === 'pdf' || workflowType === 'word' || visualContent.deliverable_preview_base64) {
        const docPath = workflowType === 'pdf' ? 
            DEFAULT_FILE_PATHS.PDF_DOCUMENTS + DEFAULT_FILE_PATHS.DEFAULT_DOCUMENT_NAME :
            DEFAULT_FILE_PATHS.WORD_DOCUMENTS + DEFAULT_FILE_PATHS.DEFAULT_DOCUMENT_NAME;
        
        contentHtml += `
            <div class="file-path-item">
                <span class="file-icon">📄</span>
                <div class="file-info">
                    <strong>Document Generated:</strong>
                    <p class="file-path">${docPath}</p>
                    <small>Analysis report and findings</small>
                </div>
            </div>
        `;
    }
    
    // Show presentation file paths
    if (workflowType === 'powerpoint' || visualContent.deliverable_previews_base64 || visualContent.powerpoint_slides_base64) {
        const presentationPath = DEFAULT_FILE_PATHS.POWERPOINT_PRESENTATIONS + DEFAULT_FILE_PATHS.DEFAULT_PRESENTATION_NAME;
        
        contentHtml += `
            <div class="file-path-item">
                <span class="file-icon">📽️</span>
                <div class="file-info">
                    <strong>Presentation Generated:</strong>
                    <p class="file-path">${presentationPath}</p>
                    <small>PowerPoint presentation with analysis slides</small>
                </div>
            </div>
        `;
    }
    
    // Show workflow diagram path
    if (visualContent.workflow_diagram_base64) {
        const diagramPath = DEFAULT_FILE_PATHS.WORKFLOW_DIAGRAMS + DEFAULT_FILE_PATHS.DEFAULT_DIAGRAM_NAME;
        
        contentHtml += `
            <div class="file-path-item">
                <span class="file-icon">🔄</span>
                <div class="file-info">
                    <strong>Workflow Diagram:</strong>
                    <p class="file-path">${diagramPath}</p>
                    <small>Process flow visualization</small>
                </div>
            </div>
        `;
    }
    
    // Show pipeline diagram path
    if (visualContent.pipeline_diagram_base64) {
        const pipelinePath = DEFAULT_FILE_PATHS.PIPELINE_DIAGRAMS + 'system_pipeline.png';
        
        contentHtml += `
            <div class="file-path-item">
                <span class="file-icon">📊</span>
                <div class="file-info">
                    <strong>Pipeline Diagram:</strong>
                    <p class="file-path">${pipelinePath}</p>
                    <small>System architecture visualization</small>
                </div>
            </div>
        `;
    }
    
    // Show project structure path
    if (visualContent.project_structure_base64) {
        const projectPath = DEFAULT_FILE_PATHS.SYSTEM_DIAGRAMS + 'project_structure.png';
        
        contentHtml += `
            <div class="file-path-item">
                <span class="file-icon">💻</span>
                <div class="file-info">
                    <strong>Project Structure:</strong>
                    <p class="file-path">${projectPath}</p>
                    <small>Project architecture diagram</small>
                </div>
            </div>
        `;
    }
    
    // Show analysis data path
    contentHtml += `
        <div class="file-path-item">
            <span class="file-icon">📊</span>
            <div class="file-info">
                <strong>Analysis Data (CSV):</strong>
                <p class="file-path">${DEFAULT_FILE_PATHS.CSV_FILES}${DEFAULT_FILE_PATHS.DEFAULT_CSV_NAME}</p>
                <small>Raw analysis data and metrics</small>
            </div>
        </div>
    `;
    
    // Show JSON data path
    contentHtml += `
        <div class="file-path-item">
            <span class="file-icon">⚙️</span>
            <div class="file-info">
                <strong>System State (JSON):</strong>
                <p class="file-path">${DEFAULT_FILE_PATHS.JSON_FILES}${DEFAULT_FILE_PATHS.DEFAULT_JSON_NAME}</p>
                <small>Complete system analysis state</small>
            </div>
        </div>
    `;
    
    contentHtml += `
            </div>
        </div>
    `;
    
    // Add copy path buttons
    contentHtml += `
        <div class="path-actions">
            <button class="copy-all-paths-btn" onclick="copyAllPaths()">📋 Copy All Paths</button>
            <button class="open-folder-btn" onclick="openOutputFolder()">📁 Open Output Folder</button>
        </div>
    `;
    
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

function showJsonModal() {
    if (!currentJsonData) return;
    
    const modal = document.getElementById('jsonModal');
    const jsonContent = document.getElementById('jsonContent');
    
    // Show file paths information alongside technical details
    const filePathsSection = `
        <div class="technical-details-section">
            <h3>📁 Generated Files Summary</h3>
            <div class="file-summary">
                <p><strong>Total Files Generated:</strong> ${getTotalFilesCount()}</p>
                <p><strong>Main Output Directory:</strong></p>
                <p class="file-path">C:\\Users\\nihca\\OneDrive\\Documents\\vscode\\Meta_Ai model\\outputs\\</p>
            </div>
        </div>
        <hr>
    `;
    
    jsonContent.innerHTML = filePathsSection + `
        <h2>📄 Technical Details</h2>
        <pre>${JSON.stringify(currentJsonData, null, 2)}</pre>
    `;
    modal.style.display = 'block';
    
    addLogEntry('info', 'Opened technical details with file paths');
}

function getTotalFilesCount() {
    // Count based on what was generated
    let count = 0;
    if (currentJsonData) {
        if (currentJsonData.visual_content?.deliverable_preview_base64) count++;
        if (currentJsonData.visual_content?.workflow_diagram_base64) count++;
        if (currentJsonData.visual_content?.pipeline_diagram_base64) count++;
        if (currentJsonData.visual_content?.deliverable_previews_base64) {
            count += currentJsonData.visual_content.deliverable_previews_base64.length;
        }
        // Always add CSV and JSON
        count += 2;
    }
    return count || 'Multiple';
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

// Utility function for copying all file paths
function copyAllPaths() {
    const allPaths = [
        `Documents: ${DEFAULT_FILE_PATHS.PDF_DOCUMENTS}${DEFAULT_FILE_PATHS.DEFAULT_DOCUMENT_NAME}`,
        `Presentations: ${DEFAULT_FILE_PATHS.POWERPOINT_PRESENTATIONS}${DEFAULT_FILE_PATHS.DEFAULT_PRESENTATION_NAME}`,
        `Workflow Diagrams: ${DEFAULT_FILE_PATHS.WORKFLOW_DIAGRAMS}${DEFAULT_FILE_PATHS.DEFAULT_DIAGRAM_NAME}`,
        `Pipeline Diagrams: ${DEFAULT_FILE_PATHS.PIPELINE_DIAGRAMS}system_pipeline.png`,
        `System Diagrams: ${DEFAULT_FILE_PATHS.SYSTEM_DIAGRAMS}project_structure.png`,
        `CSV Data: ${DEFAULT_FILE_PATHS.CSV_FILES}${DEFAULT_FILE_PATHS.DEFAULT_CSV_NAME}`,
        `JSON Data: ${DEFAULT_FILE_PATHS.JSON_FILES}${DEFAULT_FILE_PATHS.DEFAULT_JSON_NAME}`
    ].join('\n');
    
    navigator.clipboard.writeText(allPaths).then(() => {
        addLogEntry('success', 'All file paths copied to clipboard');
    }).catch(err => {
        addLogEntry('error', 'Failed to copy paths: ' + err.message);
    });
}

// Function to open output folder (will show path since we can't actually open folders from web)
function openOutputFolder() {
    const outputPath = 'C:\\Users\\nihca\\OneDrive\\Documents\\vscode\\Meta_Ai model\\outputs\\';
    
    // Create a modal or alert showing the path
    const pathInfo = `
        <div class="folder-path-info">
            <h3>📁 Output Directory Location</h3>
            <p><strong>Main Output Folder:</strong></p>
            <p class="file-path">${outputPath}</p>
            <br>
            <p><strong>Subdirectories:</strong></p>
            <ul class="folder-list">
                <li>📄 Documents: ${DEFAULT_FILE_PATHS.PDF_DOCUMENTS}</li>
                <li>📽️ Presentations: ${DEFAULT_FILE_PATHS.POWERPOINT_PRESENTATIONS}</li>
                <li>🔄 Diagrams: ${DEFAULT_FILE_PATHS.WORKFLOW_DIAGRAMS}</li>
                <li>📊 Data: ${DEFAULT_FILE_PATHS.CSV_FILES}</li>
            </ul>
        </div>
    `;
    
    const modal = document.getElementById('jsonModal');
    const jsonContent = document.getElementById('jsonContent');
    jsonContent.innerHTML = pathInfo;
    modal.style.display = 'block';
    
    addLogEntry('info', `Output folder path: ${outputPath}`);
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