# Meta AI System - Frontend-Backend Integration

## 🎯 Complete System Overview

This integration combines the Meta Model domain analysis with attempt2 agents through a web-based chat interface.

### **Architecture:**
```
Frontend (HTML/CSS/JS) ←→ Backend API (Flask) ←→ Meta System (correct_meta_system.py)
         ↓                        ↓                        ↓
    Chat Interface          JSON Storage           Domain Analysis → Workflow → Agents
```

## 🔧 Setup Instructions

### **1. Install Dependencies**

```bash
pip install -r backend_requirements.txt
```

### **2. Ensure Ollama & llama3.2 are Ready**

```bash
# Check if Ollama is running
ollama serve

# Pull llama3.2 if not available
ollama pull llama3.2
```

### **3. Start the Backend Server**

```bash
python backend_api.py
```

The server will start at: `http://localhost:5000`

### **4. Access the Frontend**

Open your browser and go to: `http://localhost:5000`

## 📋 Features Implemented

### **Frontend Chat Interface:**
- ✅ Clean chat UI with message history
- ✅ File upload support (PDF, TXT, DOCX)
- ✅ Real-time process logging display
- ✅ JSON viewer modal for results
- ✅ Responsive design

### **Backend API System:**
- ✅ `/api/process` - Main workflow endpoint
- ✅ `/api/health` - Health check
- ✅ `/api/conversations` - List all conversations
- ✅ `/api/conversation/<id>` - Get specific result
- ✅ CORS enabled for frontend requests

### **JSON Data Flow (As Requested):**

1. **User Input → JSON Storage**
   ```json
   {
     "user_query": "Design a smart home system",
     "files": [...],
     "timestamp": "2024-09-25T10:30:00",
     "request_id": "abc123def"
   }
   ```

2. **Domain Outputs → JSON Storage**
   ```json
   {
     "mechanical": {
       "domain": "mechanical",
       "analysis": "...",
       "recommendations": [...],
       "key_findings": [...]
     },
     "electrical": {...},
     "programming": {...}
   }
   ```

3. **Summarized Results → JSON Storage (Shown in Chat)**
   ```json
   {
     "conversation_id": "xyz789abc",
     "workflow_type": "pdf",
     "domain_analysis": {
       "mechanical": {"findings_count": 5, "recommendations_count": 3},
       "electrical": {...},
       "programming": {...}
     },
     "statistics": {...},
     "generated_file": "path/to/result.txt"
   }
   ```

### **Process Logging (As Requested):**
- ✅ Real-time logging in sidebar
- ✅ Color-coded log levels (info, success, warning, error)
- ✅ Component-specific logging (API, STORAGE, WORKFLOW, etc.)
- ✅ Detailed process tracking from request to completion

## 🔄 Workflow Process

### **Exact Flow (Following Your Specification):**

1. **User enters prompt in chat interface**
2. **Frontend sends JSON to backend API**
3. **Backend processes with Meta Model:**
   - Runs 3 domain experts (Mechanical, Electrical, Programming)
   - Creates workflow based on domain analysis 
   - Determines appropriate agent (PDF, Diagram, PowerPoint, Word, Project)
   - Executes the chosen agent
4. **JSON storage at each step**
5. **Final summarized JSON shown in chat response**
6. **Full process logs displayed in sidebar**

## 📁 File Structure

```
Meta_Ai model/
├── frontend/
│   ├── index.html          # Chat interface
│   ├── styles.css          # UI styling
│   └── script.js           # Frontend logic
├── backend_api.py          # Flask API server
├── correct_meta_system.py  # Meta Model system
├── data/                   # Meta system data
├── api_data/              # API JSON storage
│   ├── request_*.json     # User requests
│   ├── domain_outputs_*.json  # Domain analysis
│   ├── summary_*.json     # Summarized results
│   └── response_*.json    # Complete responses
└── backend_requirements.txt
```

## 🚀 Usage

1. **Start the system:** `python backend_api.py`
2. **Open browser:** `http://localhost:5000`
3. **Enter your query** in the chat input
4. **Optional:** Upload files using the file upload area
5. **Click Send** and watch the process logs
6. **View results** in the chat with JSON data
7. **Click "View Full JSON"** to see complete response data
8. **Download JSON** files for later analysis

## 🎯 Integration Points

### **Frontend → Backend:**
- POST requests to `/api/process` with user queries and files
- Real-time status updates and error handling
- JSON response parsing and display

### **Backend → Meta System:**
- Direct integration with `CorrectMetaSystem`
- Proper error handling and logging
- JSON serialization of all data structures

### **JSON Storage System:**
- Automatic saving of all workflow stages
- Retrievable conversation history
- Complete audit trail of processing

## 🔍 Monitoring & Logs

- **Backend logs:** `backend_api.log`
- **Meta system logs:** `correct_meta_system.log`
- **Process logs:** Real-time in frontend sidebar
- **JSON data:** Stored in `api_data/` directory

This complete integration provides the exact workflow you specified with full JSON storage, process logging, and chat interface! 🎉