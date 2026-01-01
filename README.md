# Meta AI System - Simplified

A clean, minimal multi-domain analysis system with document generation using Ollama and llama3.2.

## Quick Start

### 1. Install Ollama
- Download from [ollama.ai](https://ollama.ai)
- Pull the model: `ollama pull llama3.2`
- Start server: `ollama serve`

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the System

**CLI Mode:**
```bash
python meta_system.py "Your query here"
```

**Interactive Mode:**
```bash
python meta_system.py
```

## Project Structure

```
meta_system.py          # Main unified system
meta_system_api.py      # Optional Flask API
requirements.txt        # All dependencies
config.json            # Configuration
frontend/              # Web UI (optional)
  ├── index.html
  ├── script.js
  └── styles.css
data/                  # Output storage
```

## Features

- **Multi-Domain Analysis**: Mechanical, Electrical, Software domains
- **Automated Workflow**: Query → Analysis → Workflow Plan
- **Document Generation**: PDF and JSON outputs
- **Clean & Simple**: Minimal dependencies, easy to understand
- **Ollama Integration**: Uses local llama3.2 model

## Configuration

Edit `config.json`:
```json
{
  "system": {
    "model": "llama3.2",
    "base_url": "http://localhost:11434",
    "temperature": 0.7
  }
}
```

## API (Optional)

If using the Flask API:
```bash
python meta_system_api.py
```

Then POST to `http://localhost:5000/api/analyze`:
```json
{
  "query": "Your engineering question"
}
```

## Output

Results are saved to `./data/`:
- `analysis_[session_id].json` - Structured analysis
- `report_[session_id].pdf` - PDF report

## Removed Files

The following duplicate/unnecessary files were removed:
- `attempt2.py`, `Codeee.py`
- `combined_meta_system.py`, `correct_meta_system.py`
- `integrated_web_meta_system.py`, `production_meta_system.py`
- `start_meta_system.py`, `run.py`
- Multiple requirements files
- Duplicate README files
- Nested hackfront-main folder
- Test files (test_deliverables.py, test_visuals.py)
- Unnecessary config files
- Backup scripts

This project is now simplified to its essential components.
