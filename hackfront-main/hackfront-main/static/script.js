// DOM Elements
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const fileInput = document.getElementById('fileInput');
const logPopup = document.getElementById('logPopup');
const logBody = document.getElementById('logBody');

// State management
let currentUploadedFile = null;
let currentFileContent = null;
let currentTranscription = null;
let showLogsBtn = null;

// State
let processingLogs = [];

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
});

// Add click event listener to send button
sendBtn.addEventListener('click', function() {
    const content = userInput.value.trim();
    if (content) {
        sendMessage(content);
        userInput.value = '';
        userInput.style.height = 'auto';
    }
});

// Add enter key event listener
userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

// Send message function
async function sendMessage(content, type = 'text') {
    const message = {
        type: type,
        content: content,
        timestamp: new Date().toISOString()
    };

    // If there's a file attached, add it to the message
    if (currentUploadedFile && currentFileContent) {
        message.file = {
            name: currentUploadedFile.name,
            type: currentUploadedFile.type,
            content: currentFileContent
        };
    }

    // Add user message to chat
    addMessageToChat(content, 'user');

    // Show processing message
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

        // Add processing steps to logs
        if (result.steps) {
            result.steps.forEach(step => {
                processingLogs.push({
                    timestamp: new Date().toISOString(),
                    type: step.domain,
                    status: 'completed',
                    details: step.details,
                    output: step.output
                });
            });
        }

        // Update logs display
        updateLogDisplay();

        // Remove processing message
        removeProcessingMessage(processingId);
        
        // Add bot response with animation
        const botMessage = addMessageToChat(result.response, 'bot');
        // Add glow animation
        setTimeout(() => {
            botMessage.classList.add('active-glow');
            setTimeout(() => {
                botMessage.classList.remove('active-glow');
            }, 2000);
        }, 100);

        // Show feature buttons after response
        featureButtons.style.display = 'flex';

        // Clear current file
        currentUploadedFile = null;
        currentFileContent = null;
        
    } catch (error) {
        console.error('Error processing message:', error);
        removeProcessingMessage(processingId);
        addMessageToChat('Error processing your request. Please try again.', 'error');
    }
}

// Show logs button
function showProcessingLogsButton() {
    if (!showLogsBtn) {
        showLogsBtn = document.createElement('button');
        showLogsBtn.className = 'show-logs-btn';
        showLogsBtn.textContent = 'Show Processing Logs';
        showLogsBtn.onclick = showLogPopup;
        document.querySelector('.chat-container').appendChild(showLogsBtn);
    }
}

// Add message to chat
function addMessageToChat(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message fade-in`;
    messageDiv.textContent = content;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return messageDiv; // Return the message div for animation
}

// Show processing message
function showProcessingMessage() {
    const id = Date.now();
    const processingDiv = document.createElement('div');
    processingDiv.className = 'message bot-message processing-message fade-in';
    processingDiv.id = `processing-${id}`;
    processingDiv.innerHTML = `
        Processing...
        <button class="show-logs-btn" onclick="showLogPopup()">Show logs</button>
    `;
    messagesContainer.appendChild(processingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
}

// Remove processing message
function removeProcessingMessage(id) {
    const processingDiv = document.getElementById(`processing-${id}`);
    if (processingDiv) {
        processingDiv.remove();
    }
}

// Simulate processing (replace with actual API call)
async function simulateProcessing(message) {
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Add dummy processing logs
    processingLogs.push({
        timestamp: new Date().toISOString(),
        type: message.type,
        status: 'processing',
        details: `Processing ${message.type} input...`
    });

    processingLogs.push({
        timestamp: new Date().toISOString(),
        type: message.type,
        status: 'complete',
        details: 'Processing complete'
    });

    // Return dummy response
    return {
        content: `I received your ${message.type} input and processed it. You can now use the feature buttons below.`
    };
}

// File upload handling
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async function(e) {
        currentUploadedFile = file;
        currentFileContent = e.target.result;
        
        // Process the file but don't send yet
        try {
            const processedData = await processFile(file, e.target.result);
            
            // Show file preview and extracted text in input
            userInput.value = `[File: ${file.name}]\n${processedData.extractedText || ''}\n\nAdd your prompt here:`;
            userInput.style.height = userInput.scrollHeight + 'px';
            
            // Add to processing logs
            processingLogs.push({
                timestamp: new Date().toISOString(),
                type: processedData.type,
                status: 'processed',
                details: `${file.name} processed`,
                preview: processedData.preview,
                extractedText: processedData.extractedText
            });
            
            // Show logs button if not already visible
            showProcessingLogsButton();
            updateLogDisplay();
            
        } catch (error) {
            console.error('Error processing file:', error);
            addMessageToChat(`Error processing file: ${error.message}`, 'error');
        }
    };

    if (file.type.includes('image')) {
        reader.readAsDataURL(file);
    } else {
        reader.readAsText(file);
    }
});

// File processing function
async function processFile(file, content) {
    const processedData = {
        type: '',
        extractedText: '',
        preview: null
    };

    if (file.type.includes('image')) {
        processedData.type = 'image';
        processedData.preview = content;
        // Send to backend for OCR
        const formData = new FormData();
        formData.append('image', file);
        
        try {
            const response = await fetch('/process_image', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            processedData.extractedText = result.text;
        } catch (error) {
            console.error('OCR processing error:', error);
            processedData.extractedText = 'Error processing image text';
        }
    } else if (file.name.endsWith('.pdf')) {
        processedData.type = 'pdf';
        // Send to backend for PDF processing
        const formData = new FormData();
        formData.append('pdf', file);
        
        try {
            const response = await fetch('/process_pdf', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            processedData.extractedText = result.text;
        } catch (error) {
            console.error('PDF processing error:', error);
            processedData.extractedText = 'Error processing PDF';
        }
    } else if (file.name.endsWith('.doc') || file.name.endsWith('.docx')) {
        processedData.type = 'document';
        // Send to backend for document processing
        const formData = new FormData();
        formData.append('document', file);
        
        try {
            const response = await fetch('/process_document', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            processedData.extractedText = result.text;
        } catch (error) {
            console.error('Document processing error:', error);
            processedData.extractedText = 'Error processing document';
        }
    }

    return processedData;
}



// Log popup handling
function showLogPopup() {
    logPopup.style.display = 'block';
    updateLogDisplay();
}

function closeLogPopup() {
    logPopup.style.display = 'none';
}

function updateLogDisplay() {
    logBody.innerHTML = processingLogs.map(log => {
        let logContent = `
            <div class="log-entry step">
                <div class="log-header">
                    <div><strong>Time:</strong> ${new Date(log.timestamp).toLocaleTimeString()}</div>
                    <div><strong>Type:</strong> ${log.type}</div>
                    <div><strong>Status:</strong> ${log.status}</div>
                    <div><strong>Details:</strong> ${log.details}</div>
                </div>
        `;

        // Add extracted text if available
        if (log.extractedText) {
            logContent += `
                <div class="extracted-text">
                    <strong>Extracted Text:</strong><br>
                    ${log.extractedText}
                </div>
            `;
        }

        // Add image preview if available
        if (log.preview && log.type === 'image') {
            logContent += `
                <img src="${log.preview}" alt="Processed Image" class="image-preview">
            `;
        }

        // Add code preview if available
        if (log.code) {
            logContent += `
                <div class="code-preview">
                    <pre><code>${log.code}</code></pre>
                </div>
            `;
        }

        // Add directory structure if available
        if (log.directory) {
            logContent += `
                <div class="directory-structure">
                    ${renderDirectoryStructure(log.directory)}
                </div>
            `;
        }

        // Add domain processing steps if available
        if (log.steps) {
            logContent += `
                <div class="processing-steps">
                    ${renderProcessingSteps(log.steps)}
                </div>
            `;
        }

        logContent += '</div>';
        return logContent;
    }).join('');
}

function renderDirectoryStructure(directory, indent = 0) {
    let html = '';
    for (const item of directory) {
        const padding = indent * 20;
        if (item.type === 'directory') {
            html += `
                <div class="directory-item" style="padding-left: ${padding}px">
                    ${item.name}/
                </div>
                ${renderDirectoryStructure(item.children, indent + 1)}
            `;
        } else {
            html += `
                <div class="directory-item file" style="padding-left: ${padding}px">
                    ${item.name}
                </div>
            `;
        }
    }
    return html;
}

function renderProcessingSteps(steps) {
    return steps.map(step => `
        <div class="log-entry">
            <strong>${step.domain}</strong>
            <div class="log-step-content">${step.output}</div>
        </div>
    `).join('');
}

// Simulation functions for different file types
async function simulateImageProcessing(imageData) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return "Simulated OCR text from image: This is extracted text from the uploaded image...";
}

async function simulatePDFProcessing(pdfData) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return "Simulated PDF text: Extracted content from PDF document...";
}

async function simulateDocProcessing(docData) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return "Simulated DOC text: Extracted content from document...";
}

// Automatic feature detection and generation
async function detectAndGenerateFeatures(content) {
    const features = [];
    
    // Detect potential features from content
    if (content.toLowerCase().includes('code') || content.toLowerCase().includes('program')) {
        features.push('code');
    }
    if (content.toLowerCase().includes('diagram') || content.toLowerCase().includes('pipeline')) {
        features.push('pipeline');
    }
    if (content.toLowerCase().includes('presentation') || content.toLowerCase().includes('ppt')) {
        features.push('ppt');
    }
    if (content.toLowerCase().includes('document') || content.toLowerCase().includes('doc')) {
        features.push('doc');
    }
    if (content.toLowerCase().includes('pdf')) {
        features.push('pdf');
    }
    
    // Generate each detected feature
    for (const feature of features) {
        const result = await simulateFeatureGeneration(feature);
        
        // Add to processing logs
        processingLogs.push({
            timestamp: new Date().toISOString(),
            type: feature,
            status: 'generated',
            details: `${feature.toUpperCase()} generation complete`,
            ...result
        });
        
        // Show result in chat
        const resultMessage = document.createElement('div');
        resultMessage.className = 'message bot-message fade-in';
        
        if (feature === 'code') {
            resultMessage.innerHTML = `
                <div>Code generated successfully! Directory structure:</div>
                <div class="directory-structure">${renderDirectoryStructure(result.directory)}</div>
                <div class="code-preview"><pre><code>${result.code}</code></pre></div>
                <a href="#" class="download-link">Download Code</a>
            `;
        } else if (feature === 'pipeline') {
            resultMessage.innerHTML = `
                <div>Pipeline diagram generated:</div>
                <img src="${result.preview}" alt="Pipeline Diagram" class="image-preview">
                <a href="#" class="download-link">Download Diagram</a>
            `;
        } else {
            resultMessage.innerHTML = `
                <div>${feature.toUpperCase()} generated successfully!</div>
                <a href="#" class="download-link">Download ${feature.toUpperCase()}</a>
            `;
        }
        
        messagesContainer.appendChild(resultMessage);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    updateLogDisplay();
    return features;
}

// Simulate feature generation
async function simulateFeatureGeneration(feature) {
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    switch (feature) {
        case 'code':
            return {
                directory: [
                    {
                        type: 'directory',
                        name: 'src',
                        children: [
                            { type: 'file', name: 'index.js' },
                            { type: 'file', name: 'config.js' }
                        ]
                    },
                    {
                        type: 'directory',
                        name: 'lib',
                        children: [
                            { type: 'file', name: 'utils.js' }
                        ]
                    },
                    { type: 'file', name: 'README.md' }
                ],
                code: 'console.log("Generated code example");\n// More code here...',
                steps: [
                    { domain: 'Code Analysis', output: 'Analyzing requirements...' },
                    { domain: 'Structure Generation', output: 'Creating project structure...' },
                    { domain: 'Code Generation', output: 'Generating code files...' }
                ]
            };
        case 'pipeline':
            return {
                preview: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMAAAADAAQMAAABoEv5EAAAABlBMVEX///8AAABVwtN+AAABNElEQVRYw+2WvQ6DIBSFKa/AsHZ18A2Y+gL1/R+DxhBvQaGtxGa4X0LCwXA4/ADB/1K7znX2W4Uu5mso1NvL4zq3w3XOhwmvueYVGwI7jkM5oPA+dCGfioCHUhxYe0ADeoVqwBQCQAHQQgDEAObEOsHXAEQzIDcD0UhlgGb0HmowkA4EFgON/RrBJYCwAIAD5QRQIhyBQzaBmYHADMAKGEABQA7YBxYBDEJAHfBQAmYGRgI2YJQZGKQXFAFAtQAhVIDIQAiAFahBAIQBIEUCigEEApkcgGwAwhFIDADrQXYDZFJARYC8H6AL2G3ASADwDhABTiKgzYBeBKQB5AXYEZgQwDIEGAWAfQCmDwz0/mzAQm9UBk70zGVgo/dAAwT9MzQQbN1L+FX6Ad3Zv9YX1gNdRmJ2GfgAAAAASUVORK5CYII=',
                steps: [
                    { domain: 'Diagram Planning', output: 'Planning pipeline structure...' },
                    { domain: 'Visual Generation', output: 'Creating visual elements...' },
                    { domain: 'Export', output: 'Preparing final diagram...' }
                ]
            };
        default:
            return {
                steps: [
                    { domain: 'Content Analysis', output: 'Analyzing input...' },
                    { domain: 'Content Generation', output: 'Generating content...' },
                    { domain: 'Format Conversion', output: 'Converting to final format...' }
                ]
            };
    }
}

// Send button handler
sendBtn.addEventListener('click', () => {
    const text = userInput.value.trim();
    if (text) {
        sendMessage(text, 'text');
        userInput.value = '';
        userInput.style.height = 'auto';
    }
});

// Enter key handler
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});
