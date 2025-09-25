# 🎯 Integrated Meta Model System

A comprehensive web-based AI system that combines the Meta Model domain expert workflow with a modern chatbot interface. This system follows your exact specification: **User prompt → Domain experts → Workflow creation → Execute workflow with attempt2 agents**.

## 🌟 Features

### 🔬 Meta Model Workflow
- **3 Domain Experts**: Mechanical, Electrical, Programming analysis
- **Intelligent Workflow Creation**: AI determines optimal document type
- **5 Document Generators**: PDF, Diagram, PowerPoint, Word, Code Projects
- **No Mock Implementations**: Uses only llama3.2 model

### 🌐 Modern Web Interface
- **Real-time Updates**: Live processing steps via WebSocket
- **Chat Interface**: Natural conversation with the AI system
- **Processing Logs**: Complete transparency of all operations
- **File Logging**: All prompts saved to individual log files

### 📋 Comprehensive Logging
- **Prompt Logging**: Every LLM prompt saved to `/logs/` directory
- **Processing Steps**: Real-time step tracking and status
- **System State**: Complete conversation history and results
- **File Outputs**: Generated documents saved to `/data/` directory

## 🚀 Quick Start

### Prerequisites

1. **Ollama** installed and running:
   ```bash
   # Install Ollama (if not already installed)
   # Then install llama3.2 model
   ollama pull llama3.2
   
   # Start Ollama
   ollama serve
   ```

2. **Python Requirements**:
   ```bash
   pip install -r integrated_requirements.txt
   ```

### Run the System

**Option 1: Use the startup script (Recommended)**
```bash
python start_meta_system.py
```

**Option 2: Run directly**
```bash
python integrated_web_meta_system.py
```

### Access the Interface

Open your browser and go to: **http://localhost:5000**

## 🔧 How It Works

### Exact Meta Model Flow

1. **User Input**: Enter your query in the web chat interface
2. **Domain Analysis**: 3 expert agents analyze your query:
   - 🔧 **Mechanical Expert**: Engineering, materials, constraints
   - ⚡ **Electrical Expert**: Systems, circuits, components
   - 💻 **Programming Expert**: Architecture, frameworks, APIs
3. **Workflow Creation**: AI analyzes domain outputs and selects optimal document type
4. **Agent Execution**: Appropriate attempt2 agent generates the document:
   - 📄 **PDF Report**: Comprehensive analysis document
   - 📊 **Pipeline Diagram**: Visual workflow diagrams
   - 📽️ **PowerPoint**: Executive presentation
   - 📝 **Word Document**: Detailed technical documentation
   - 💻 **Code Project**: Complete software implementation

### Real-time Features

- **Live Processing Updates**: See each step as it happens
- **Connection Status**: Real-time connection indicator
- **Processing Indicator**: Shows current operation
- **Step-by-Step Logging**: Complete transparency

## 📁 File Structure

```
/
├── integrated_web_meta_system.py    # Main system file
├── start_meta_system.py            # Startup script
├── integrated_requirements.txt      # Python dependencies
├── hackfront-main/                 # Frontend assets
│   ├── templates/
│   │   └── integrated_index.html   # Web interface
│   └── static/
│       ├── integrated_script.js    # Frontend JavaScript
│       ├── style.css              # Styling
│       ├── background.mp4         # Background video
│       └── background.jpg         # Fallback background
├── data/                          # Generated documents
│   ├── *_analysis_*.json         # Domain analyses
│   ├── *_report_*.txt            # Generated documents
│   └── system_state_*.json       # System states
└── logs/                         # Processing logs
    ├── meta_system.log           # Main system log
    ├── *_prompt_*.txt           # Individual prompts
    └── *_analysis_*.json        # Domain analysis files
```

## 🎮 Using the System

### Web Interface

1. **Connect**: The interface shows connection status
2. **Enter Query**: Type your request in the chat input
3. **Watch Processing**: Real-time updates show each step:
   - ⏳ Domain expert analysis
   - 🔧 Workflow creation
   - 📄 Document generation
4. **View Results**: Complete response with file links
5. **Access Logs**: Click "View Logs" to see detailed processing

### Processing Flow Example

```
User Query: "Design a smart irrigation system"

🔍 Step 1: Domain Expert Analysis
  ✅ Mechanical: Pump systems, sensors, materials
  ✅ Electrical: Control circuits, power systems
  ✅ Programming: IoT integration, data processing

🔧 Step 2: Workflow Creation
  🤖 AI Decision: "PDF Report best serves comprehensive analysis needs"

📄 Step 3: Document Generation
  ✅ PDF Report: Complete 50-page technical analysis generated

💾 Step 4: Results
  📁 Files: pdf_report_abc12345.txt
  📋 Logs: 15 processing steps logged
  💽 State: system_state_abc12345.json
```

### Log Files

The system creates detailed logs for complete transparency:

- **Prompt Files**: Each LLM interaction saved separately
  - `mechanical_domain_prompt_abc12345.txt`
  - `electrical_domain_prompt_abc12345.txt` 
  - `programming_domain_prompt_abc12345.txt`
  - `workflow_prompt_abc12345.txt`
  - `pdf_generation_prompt_abc12345.txt`

- **Analysis Files**: Structured domain expert outputs
- **System State**: Complete conversation tracking

## 🔍 Troubleshooting

### Common Issues

**"Could not connect to llama3.2"**
- Ensure Ollama is running: `ollama serve`
- Check model is installed: `ollama list`
- Install if missing: `ollama pull llama3.2`

**"Failed to initialize system"**
- Check all requirements installed: `pip install -r integrated_requirements.txt`
- Verify Ollama is accessible at `http://localhost:11434`

**Web interface not loading**
- Check port 5000 is not in use
- Try different port in code: `socketio.run(app, port=5001)`

### Debug Mode

For detailed debugging, modify the startup:
```python
socketio.run(app, debug=True, port=5000)
```

## 🎯 Key Differences from Previous Versions

### ✅ Correct Implementation
- **Follows exact Meta Model flow**: Domain experts → Workflow creation → Agent execution
- **No menu options**: Simple text input interface
- **Real workflow decision**: AI actually chooses document type based on analysis
- **Complete integration**: Frontend shows all processing steps

### ❌ What Was Wrong Before
- Previous versions skipped workflow creation step
- Had confusing menu options instead of natural input
- Didn't show processing transparency
- Missing real-time updates

## 📊 System Monitoring

The web interface provides real-time monitoring:

- **Connection Status**: Green = connected, Red = disconnected
- **Processing Indicator**: Shows current operation
- **Step Progress**: Live updates for each processing step
- **Log Viewer**: Complete processing history
- **File Access**: Direct links to generated documents

## 🔐 Security Notes

- System runs on localhost by default
- No authentication implemented (add as needed)
- All files stored locally
- No external API calls except to local Ollama

## 🚀 Performance

- **Concurrent Processing**: Non-blocking architecture
- **Real-time Updates**: WebSocket communication
- **File Caching**: Generated files persist across sessions
- **Memory Efficient**: Streaming responses

## 📈 Extending the System

### Adding New Domain Experts
1. Create new expert class inheriting from `DomainExpert`
2. Add to `WorkflowManager.domain_experts`
3. Update workflow prompts to include new domain

### Adding New Document Types
1. Add new generator method to `Attempt2AgentExecutor`
2. Update workflow decision logic
3. Add frontend display support

### Custom Frontend
- Replace `hackfront-main` folder with your design
- Keep same JavaScript API calls
- Maintain SocketIO event handlers

---

## 🎉 Success!

You now have a fully integrated Meta Model system with:
- ✅ Exact workflow specification followed
- ✅ Modern web interface
- ✅ Real-time processing visibility  
- ✅ Complete prompt logging
- ✅ Professional document generation
- ✅ No mock implementations

The system demonstrates the power of combining sophisticated AI workflows with modern web technology! 🚀