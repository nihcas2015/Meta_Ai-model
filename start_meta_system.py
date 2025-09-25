#!/usr/bin/env python3
"""
Startup Script for Integrated Meta System
"""

import sys
import subprocess
import os
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    print("🔍 Checking requirements...")
    
    try:
        import flask
        import flask_socketio
        import langchain
        import langchain_community
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements: pip install -r integrated_requirements.txt")
        return False

def check_ollama():
    """Check if Ollama is running"""
    print("🔍 Checking Ollama connection...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            tags = response.json()
            models = [model['name'] for model in tags.get('models', [])]
            
            if any('llama3.2' in model for model in models):
                print("✅ Ollama is running and llama3.2 is available")
                return True
            else:
                print("⚠️ Ollama is running but llama3.2 model not found")
                print("Available models:", models)
                print("Please install llama3.2: ollama pull llama3.2")
                return False
        else:
            print("❌ Ollama is not responding properly")
            return False
            
    except Exception as e:
        print("❌ Cannot connect to Ollama")
        print("Please make sure:")
        print("1. Ollama is installed and running")
        print("2. llama3.2 model is installed: ollama pull llama3.2")
        print("3. Ollama is accessible at http://localhost:11434")
        return False

def main():
    """Main startup function"""
    print("🎯 INTEGRATED META SYSTEM STARTUP")
    print("="*50)
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Check Ollama
    if not check_ollama():
        return 1
    
    print("\n🚀 Starting Integrated Meta System...")
    print("="*50)
    
    # Import and run the system
    try:
        from integrated_web_meta_system import app, socketio, initialize_system
        
        # Initialize system
        print("🔧 Initializing system...")
        if not initialize_system():
            print("❌ Failed to initialize system")
            return 1
        
        print("✅ System initialized successfully!")
        print("\n🌐 Starting web server...")
        print("📍 Open your browser and go to: http://localhost:5000")
        print("📋 Processing logs will be saved to: logs/")
        print("📁 Generated files will be saved to: data/")
        print("⚡ Real-time updates via WebSocket")
        print("\n🎮 READY! Enter your queries in the web interface!")
        print("="*50)
        
        # Run the Flask app with SocketIO
        socketio.run(app, debug=False, port=5000, host='0.0.0.0')
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())