#!/bin/bash
# Startup script for Meta AI System (Windows PowerShell version)

Write-Host "🚀 Starting Meta AI System - Frontend-Backend Integration" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan

# Check if Python is available
Write-Host "🐍 Checking Python installation..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "✅ $pythonVersion found" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check if pip requirements are installed
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
if (Test-Path "backend_requirements.txt") {
    Write-Host "📋 Installing/checking requirements..." -ForegroundColor Yellow
    pip install -r backend_requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  backend_requirements.txt not found. Assuming dependencies are installed." -ForegroundColor Yellow
}

# Check if Ollama is running
Write-Host "🤖 Checking Ollama service..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 5
    Write-Host "✅ Ollama is running" -ForegroundColor Green
    
    # Check if llama3.2 is available
    $models = $ollamaCheck.models
    $llama32Available = $models | Where-Object { $_.name -like "*llama3.2*" }
    
    if ($llama32Available) {
        Write-Host "✅ llama3.2 model found" -ForegroundColor Green
    } else {
        Write-Host "⚠️  llama3.2 model not found. You may need to run: ollama pull llama3.2" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Ollama is not running or not accessible" -ForegroundColor Red
    Write-Host "   Please start Ollama first: ollama serve" -ForegroundColor Yellow
    Write-Host "   And pull the model: ollama pull llama3.2" -ForegroundColor Yellow
    exit 1
}

# Create necessary directories
Write-Host "📁 Setting up directories..." -ForegroundColor Yellow
if (!(Test-Path "frontend")) {
    Write-Host "❌ Frontend directory not found" -ForegroundColor Red
    exit 1
}
if (!(Test-Path "data")) { New-Item -ItemType Directory -Path "data" | Out-Null }
if (!(Test-Path "api_data")) { New-Item -ItemType Directory -Path "api_data" | Out-Null }
Write-Host "✅ Directories ready" -ForegroundColor Green

# Start the backend server
Write-Host "🌐 Starting backend server..." -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "🔗 Frontend will be available at: http://localhost:5000" -ForegroundColor Yellow
Write-Host "🔗 API endpoints available at: http://localhost:5000/api" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

try {
    python backend_api.py
} catch {
    Write-Host "❌ Failed to start backend server" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "👋 Server stopped" -ForegroundColor Gray