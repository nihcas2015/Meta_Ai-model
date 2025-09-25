#!/usr/bin/env python3
"""
Backend API Server for Meta AI System
Integrates with correct_meta_system.py to provide web API

Handles:
1. Frontend requests with prompts/uploads
2. JSON storage and retrieval  
3. Domain analysis processing
4. Workflow execution
5. Process logging
"""

import os
import sys
import json
import uuid
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Flask imports
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add the parent directory to Python path to import our Meta system
sys.path.append(str(Path(__file__).parent))

# Import our corrected Meta system
from correct_meta_system import CorrectMetaSystem, DomainExpertOutput, SystemState

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Setup paths
BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"  
API_DATA_DIR = BASE_DIR / "api_data"
API_DATA_DIR.mkdir(exist_ok=True)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'backend_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# FLASK APP SETUP
# ==============================================================================

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Global Meta AI system instance
meta_system = None

def initialize_meta_system():
    """Initialize the Meta AI system"""
    global meta_system
    try:
        logger.info("🚀 Initializing Meta AI System...")
        meta_system = CorrectMetaSystem()
        logger.info("✅ Meta AI System initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Meta AI System: {e}")
        return False

# ==============================================================================
# DATA CLASSES FOR API
# ==============================================================================

@dataclass
class APIRequest:
    """API request structure"""
    user_query: str
    files: List[Dict[str, Any]] = None
    timestamp: str = None
    request_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.request_id is None:
            self.request_id = uuid.uuid4().hex[:8]

@dataclass  
class ProcessLog:
    """Process log entry"""
    timestamp: str
    level: str  # info, success, warning, error
    message: str
    component: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class APIResponse:
    """API response structure"""
    success: bool
    conversation_id: str
    request_id: str
    user_query: str
    domain_outputs: Dict[str, Dict] = None
    workflow_type: str = None
    generated_file: str = None
    summary: Dict = None
    process_logs: List[ProcessLog] = None
    error_message: str = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.process_logs is None:
            self.process_logs = []

# ==============================================================================
# JSON STORAGE SYSTEM
# ==============================================================================

class JSONStorage:
    """Handle JSON storage for all system data"""
    
    def __init__(self):
        self.storage_dir = API_DATA_DIR
    
    def save_request(self, api_request: APIRequest) -> Path:
        """Save initial request data"""
        filename = f"request_{api_request.request_id}.json"
        filepath = self.storage_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(asdict(api_request), f, indent=2)
        
        logger.info(f"📁 Saved request to: {filepath}")
        return filepath
    
    def save_domain_outputs(self, conversation_id: str, domain_outputs: Dict[str, DomainExpertOutput]) -> Path:
        """Save domain expert outputs"""
        filename = f"domain_outputs_{conversation_id}.json"
        filepath = self.storage_dir / filename
        
        # Convert domain outputs to serializable format
        serializable_outputs = {}
        for domain, output in domain_outputs.items():
            serializable_outputs[domain] = asdict(output)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_outputs, f, indent=2)
        
        logger.info(f"📁 Saved domain outputs to: {filepath}")
        return filepath
    
    def save_summary(self, conversation_id: str, summary_data: Dict) -> Path:
        """Save summarized results"""
        filename = f"summary_{conversation_id}.json"
        filepath = self.storage_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"📁 Saved summary to: {filepath}")
        return filepath
    
    def save_final_response(self, api_response: APIResponse) -> Path:
        """Save complete API response"""
        filename = f"response_{api_response.conversation_id}.json"
        filepath = self.storage_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(asdict(api_response), f, indent=2)
        
        logger.info(f"📁 Saved final response to: {filepath}")
        return filepath
    
    def load_response(self, conversation_id: str) -> Optional[Dict]:
        """Load saved response"""
        filename = f"response_{conversation_id}.json"
        filepath = self.storage_dir / filename
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

# Global storage instance
storage = JSONStorage()

# ==============================================================================
# PROCESS LOGGING SYSTEM
# ==============================================================================

class ProcessLogger:
    """Collect and manage process logs for frontend display"""
    
    def __init__(self):
        self.logs = []
    
    def add_log(self, level: str, message: str, component: str = None):
        """Add a process log entry"""
        log_entry = ProcessLog(
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            component=component
        )
        self.logs.append(log_entry)
        logger.info(f"[{level.upper()}] {component or 'SYSTEM'}: {message}")
    
    def get_logs(self) -> List[ProcessLog]:
        """Get all logged entries"""
        return self.logs.copy()
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs.clear()

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'meta_system_ready': meta_system is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/process', methods=['POST'])
def process_request():
    """Main processing endpoint - handles the complete Meta AI workflow"""
    
    process_logger = ProcessLogger()
    start_time = time.time()
    
    try:
        # Parse request data
        request_data = request.get_json()
        if not request_data or not request_data.get('user_query'):
            return jsonify({
                'success': False,
                'error': 'Missing user_query in request'
            }), 400
        
        # Create API request object
        api_request = APIRequest(
            user_query=request_data['user_query'],
            files=request_data.get('files', []),
            timestamp=request_data.get('timestamp')
        )
        
        process_logger.add_log('info', f'Received request: "{api_request.user_query}"', 'API')
        
        # Save initial request
        storage.save_request(api_request)
        process_logger.add_log('success', 'Request data saved', 'STORAGE')
        
        # Check if Meta system is initialized
        if meta_system is None:
            process_logger.add_log('error', 'Meta AI System not initialized', 'SYSTEM')
            return create_error_response(api_request.request_id, 'Meta AI System not initialized', process_logger)
        
        # Process files if any
        processed_context = None
        if api_request.files:
            processed_context = process_uploaded_files(api_request.files, process_logger)
        
        process_logger.add_log('info', 'Starting Meta AI workflow execution', 'WORKFLOW')
        
        # Execute the Meta AI workflow
        meta_result = meta_system.run_correct_workflow(api_request.user_query)
        
        process_logger.add_log('success', f'Meta AI workflow completed. Conversation ID: {meta_result["conversation_id"]}', 'WORKFLOW')
        
        # Save domain outputs
        domain_outputs_file = storage.save_domain_outputs(
            meta_result['conversation_id'], 
            meta_result['domain_outputs']
        )
        process_logger.add_log('success', 'Domain outputs saved', 'STORAGE')
        
        # Create comprehensive summary
        summary = create_comprehensive_summary(meta_result, api_request, process_logger)
        
        # Save summary
        summary_file = storage.save_summary(meta_result['conversation_id'], summary)
        process_logger.add_log('success', 'Summary data saved', 'STORAGE')
        
        # Create API response
        api_response = APIResponse(
            success=True,
            conversation_id=meta_result['conversation_id'],
            request_id=api_request.request_id,
            user_query=api_request.user_query,
            domain_outputs={k: asdict(v) for k, v in meta_result['domain_outputs'].items()},
            workflow_type=meta_result.get('workflow_type', 'auto-determined'),
            generated_file=meta_result.get('generated_file'),
            summary=summary,
            process_logs=process_logger.get_logs()
        )
        
        # Save final response
        response_file = storage.save_final_response(api_response)
        
        processing_time = round(time.time() - start_time, 2)
        process_logger.add_log('success', f'Complete workflow finished in {processing_time}s', 'SYSTEM')
        
        # Update response with final logs
        api_response.process_logs = process_logger.get_logs()
        
        logger.info(f"✅ Request {api_request.request_id} processed successfully in {processing_time}s")
        
        return jsonify(asdict(api_response))
        
    except Exception as e:
        process_logger.add_log('error', f'Fatal error: {str(e)}', 'SYSTEM')
        logger.error(f"❌ Error processing request: {e}")
        return create_error_response(
            getattr(api_request, 'request_id', 'unknown'), 
            str(e), 
            process_logger
        ), 500

def process_uploaded_files(files: List[Dict], process_logger: ProcessLogger) -> Dict[str, Any]:
    """Process uploaded files and extract content"""
    
    processed_files = []
    
    for file_data in files:
        try:
            file_name = file_data.get('name', 'unknown')
            file_type = file_data.get('type', 'unknown')
            content = file_data.get('content', {})
            
            if content.get('type') == 'text':
                text_content = content.get('data', '')
                processed_files.append({
                    'name': file_name,
                    'type': 'text',
                    'content': text_content[:5000]  # Limit to 5000 chars
                })
                process_logger.add_log('success', f'Processed text file: {file_name}', 'FILE_PROCESSOR')
                
            elif content.get('type') == 'base64':
                # For PDF files, we'll note them but not process content yet
                processed_files.append({
                    'name': file_name,
                    'type': 'pdf',
                    'content': '[PDF content - processing not implemented yet]'
                })
                process_logger.add_log('info', f'Received PDF file: {file_name} (processing limited)', 'FILE_PROCESSOR')
            
        except Exception as e:
            process_logger.add_log('error', f'Failed to process file {file_data.get("name", "unknown")}: {str(e)}', 'FILE_PROCESSOR')
    
    return {
        'files': processed_files,
        'file_count': len(processed_files)
    }

def create_comprehensive_summary(meta_result: Dict, api_request: APIRequest, process_logger: ProcessLogger) -> Dict:
    """Create a comprehensive summary of the entire process"""
    
    summary = {
        'conversation_id': meta_result['conversation_id'],
        'request_id': api_request.request_id,
        'user_query': api_request.user_query,
        'timestamp': datetime.now().isoformat(),
        'workflow_type': meta_result.get('workflow_type', 'auto-determined'),
        'generated_file': meta_result.get('generated_file'),
        
        # Domain analysis summary
        'domain_analysis': {},
        
        # Overall statistics
        'statistics': {
            'total_domains_analyzed': len(meta_result.get('domain_outputs', {})),
            'total_recommendations': 0,
            'total_findings': 0,
            'files_processed': len(api_request.files) if api_request.files else 0
        },
        
        # Process summary
        'process_summary': {
            'steps_completed': [
                'Request received and validated',
                'Domain expert analysis executed',
                'Workflow type determined',
                'Appropriate agent executed',
                'Results generated and saved'
            ],
            'total_process_logs': len(process_logger.get_logs())
        }
    }
    
    # Analyze domain outputs
    for domain, output in meta_result.get('domain_outputs', {}).items():
        summary['domain_analysis'][domain] = {
            'analysis_length': len(output.analysis),
            'key_findings_count': len(output.key_findings),
            'recommendations_count': len(output.recommendations),
            'next_steps_count': len(output.next_steps),
            'key_findings': output.key_findings[:3],  # Top 3 findings
            'top_recommendations': output.recommendations[:3]  # Top 3 recommendations
        }
        
        # Update statistics
        summary['statistics']['total_recommendations'] += len(output.recommendations)
        summary['statistics']['total_findings'] += len(output.key_findings)
    
    process_logger.add_log('success', 'Comprehensive summary created', 'SUMMARY')
    return summary

def create_error_response(request_id: str, error_message: str, process_logger: ProcessLogger) -> Dict:
    """Create standardized error response"""
    
    return {
        'success': False,
        'request_id': request_id,
        'error_message': error_message,
        'process_logs': [asdict(log) for log in process_logger.get_logs()],
        'timestamp': datetime.now().isoformat()
    }

@app.route('/api/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id: str):
    """Retrieve a specific conversation result"""
    
    result = storage.load_response(conversation_id)
    if result:
        return jsonify(result)
    else:
        return jsonify({
            'success': False,
            'error': f'Conversation {conversation_id} not found'
        }), 404

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    """List all available conversations"""
    
    try:
        response_files = list(API_DATA_DIR.glob('response_*.json'))
        conversations = []
        
        for file in response_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    conversations.append({
                        'conversation_id': data.get('conversation_id'),
                        'user_query': data.get('user_query', '')[:100] + '...' if len(data.get('user_query', '')) > 100 else data.get('user_query', ''),
                        'timestamp': data.get('timestamp'),
                        'success': data.get('success', False),
                        'workflow_type': data.get('workflow_type')
                    })
            except Exception as e:
                logger.error(f"Error reading conversation file {file}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'conversations': sorted(conversations, key=lambda x: x.get('timestamp', ''), reverse=True),
            'total': len(conversations)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Static file serving for frontend
@app.route('/')
def serve_frontend():
    """Serve the frontend HTML"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serve static frontend files"""
    return send_from_directory(FRONTEND_DIR, filename)

# ==============================================================================
# MAIN APPLICATION STARTUP
# ==============================================================================

def main():
    """Main function to start the backend API server"""
    
    print("🚀 Starting Meta AI Backend API Server...")
    
    # Initialize Meta AI system
    if not initialize_meta_system():
        print("❌ Failed to initialize Meta AI system. Exiting.")
        sys.exit(1)
    
    print("✅ Meta AI system initialized successfully")
    print(f"📁 Data directory: {API_DATA_DIR}")
    print(f"🌐 Frontend directory: {FRONTEND_DIR}")
    
    # Start Flask server
    print("\n🌐 Starting Flask server...")
    print("📋 Available endpoints:")
    print("   GET  /                     - Frontend interface")
    print("   GET  /api/health           - Health check")
    print("   POST /api/process          - Main processing endpoint")
    print("   GET  /api/conversations    - List all conversations") 
    print("   GET  /api/conversation/<id> - Get specific conversation")
    print("\n🔗 Access the application at: http://localhost:5000")
    print("🔗 API base URL: http://localhost:5000/api")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # Set to False for production
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server shutdown by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()