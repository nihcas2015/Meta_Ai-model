# Production Meta System

A production-ready system that combines the Meta Model architecture with attempt2 document generation capabilities, using only the llama3.2 model.

## 🎯 Overview

This system integrates:
- **Meta Model Architecture**: Domain experts (mechanical, electrical, programming) that provide specialized analysis
- **attempt2 Document Generation**: All 5 document generation agents
- **llama3.2 Only**: No mock implementations, production-ready

## 🤖 All 5 Agents from attempt2

1. **PDF Report Generator** - Creates comprehensive PDF reports using reportlab
2. **Pipeline Diagram Generator** - Creates flowchart/pipeline diagrams using matplotlib
3. **PowerPoint Presentation Generator** - Creates presentations using python-pptx
4. **Word Document Generator** - Creates Word documents using python-docx
5. **Complex Code Project Generator** - Creates complete code projects with multiple files

## 📋 Requirements

### System Requirements
- Python 3.8+
- Ollama running locally (`ollama serve`)
- llama3.2 model installed (`ollama pull llama3.2`)

### Python Dependencies
```bash
pip install -r requirements_production.txt
```

## 🚀 Quick Start

1. **Install Ollama and llama3.2**:
```bash
# Install Ollama (if not installed)
# Visit: https://ollama.ai/download

# Pull llama3.2 model
ollama pull llama3.2

# Start Ollama server
ollama serve
```

2. **Install Python Dependencies**:
```bash
pip install -r requirements_production.txt
```

3. **Run the System**:
```bash
python production_meta_system.py
```

## 💡 How It Works

### Step 1: Domain Expert Analysis
The system runs all 3 domain experts in parallel:
- **Mechanical Expert**: Analyzes mechanical engineering aspects
- **Electrical Expert**: Analyzes electrical engineering aspects  
- **Programming Expert**: Analyzes software/programming aspects

### Step 2: Document Generation
Based on your selection, one of the 5 agents generates the appropriate document:
- Each agent combines domain expert insights with specialized document generation
- All outputs are saved to the `./data` directory

### Step 3: System State Management
- Complete system state is saved for each conversation
- Domain analysis results are stored as JSON files
- Generated scripts are saved for execution

## 🎮 Interactive Menu

```
📋 Select document type to generate:
  1. PDF Report
  2. Pipeline Diagram (PNG)
  3. PowerPoint Presentation (PPTX)
  4. Word Document (DOCX)
  5. Complex Code Project
  6. Exit
```

## 📁 File Structure

```
production_meta_system.py     # Main system file
requirements_production.txt   # Python dependencies
config/
  └── production_config.json  # System configuration
data/                         # Generated outputs
  ├── mechanical_analysis_*.json
  ├── electrical_analysis_*.json  
  ├── programming_analysis_*.json
  ├── system_state_*.json
  └── *_generator_*.py        # Generated scripts
```

## ⚠️ Important Notes

### Production Requirements
- **NO MOCK IMPLEMENTATIONS**: System will exit if llama3.2 is not available
- **STRICT VALIDATION**: Only llama3.2 model is allowed
- **REAL CONNECTIONS**: Must have working Ollama connection

### Error Handling
The system will exit with clear error messages if:
- Langchain components are not installed
- Ollama is not running
- llama3.2 model is not available
- Connection to llama3.2 fails

## 🔧 Configuration

Edit `config/production_config.json` to modify:
- Model settings (base_url, temperature, timeout)
- Data directory location
- Logging level
- System validation rules

## 📊 Outputs

### Domain Analysis Files
- `mechanical_analysis_*.json`: Mechanical engineering insights
- `electrical_analysis_*.json`: Electrical engineering insights
- `programming_analysis_*.json`: Software development insights

### Generated Scripts
- `pdf_generator_*.py`: PDF report generation script
- `diagram_generator_*.py`: Diagram generation script
- `ppt_generator_*.py`: PowerPoint generation script
- `word_generator_*.py`: Word document generation script
- `project_generator_*.py`: Complete project generation script

### System State
- `system_state_*.json`: Complete conversation state and results

## 🐛 Troubleshooting

### Common Issues

1. **"ERROR: Required Langchain components not available"**
   ```bash
   pip install langchain langchain-ollama langchain-core
   ```

2. **"Cannot connect to llama3.2 model"**
   ```bash
   # Check if Ollama is running
   ollama serve
   
   # Check if model is installed
   ollama pull llama3.2
   
   # Test connection
   ollama run llama3.2 "Hello"
   ```

3. **"Only llama3.2 model is allowed"**
   - System is configured for production use only
   - Only llama3.2 is accepted, no other models

## 🚀 Advanced Usage

### Programmatic Access
```python
from production_meta_system import ProductionMetaSystem

# Initialize system
system = ProductionMetaSystem()

# Run full analysis and generation
result = system.run_full_analysis_and_generation(
    user_query="Design a smart home system",
    document_type="pdf"
)

# Access results
print(f"Generated file: {result['generated_file']}")
print(f"Domain outputs: {result['domain_outputs']}")
```

### Batch Processing
```python
queries = [
    ("IoT sensor network", "pdf"),
    ("Manufacturing pipeline", "diagram"),
    ("Software architecture", "powerpoint")
]

for query, doc_type in queries:
    result = system.run_full_analysis_and_generation(query, doc_type)
    print(f"Processed: {query} -> {result['generated_file']}")
```

## 📝 License

This is a production system combining Meta Model architecture with attempt2 document generation capabilities.

## 🤝 Contributing

This is a production-ready system. For modifications:
1. Maintain the requirement for llama3.2 only
2. Preserve all 5 agents from attempt2
3. Keep the Meta Model domain expert approach
4. No mock implementations allowed