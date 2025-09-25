"""
Agent function implementations for the Multi-Domain Specialized Agent System.
These functions are called by the main system to generate different output types.
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import aiohttp

# Output class matching the one in the notebook
@dataclass
class AgentOutput:
    """Output from a specific agent"""
    agent_type: str
    content: Any
    format: str
    file_path: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = datetime.now().isoformat()

# Configuration for external APIs
API_CONFIG = {
    "diagram_api": {
        "url": "https://api.example.com/diagram",
        "api_key": os.environ.get("DIAGRAM_API_KEY", "demo_key"),
        "timeout": 30
    },
    "presentation_api": {
        "url": "https://api.example.com/presentation",
        "api_key": os.environ.get("PPT_API_KEY", "demo_key"),
        "timeout": 45
    },
    "document_api": {
        "url": "https://api.example.com/document",
        "api_key": os.environ.get("DOC_API_KEY", "demo_key"),
        "timeout": 40
    },
    "pdf_api": {
        "url": "https://api.example.com/pdf",
        "api_key": os.environ.get("PDF_API_KEY", "demo_key"),
        "timeout": 30
    },
    "code_api": {
        "url": "https://api.example.com/code",
        "api_key": os.environ.get("CODE_API_KEY", "demo_key"),
        "timeout": 60
    }
}

# Helper to make API calls
async def _make_api_call(api_config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """Make an API call to an external service"""
    start_time = datetime.now()
    
    try:
        headers = {
            "Authorization": f"Bearer {api_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        # For real implementation:
        # async with aiohttp.ClientSession() as session:
        #     timeout = aiohttp.ClientTimeout(total=api_config['timeout'])
        #     async with session.post(
        #         api_config['url'], 
        #         json=data,
        #         headers=headers,
        #         timeout=timeout
        #     ) as response:
        #         if response.status == 200:
        #             result = await response.json()
        #             return result
        #         else:
        #             error_text = await response.text()
        #             raise Exception(f"API error: {response.status} - {error_text}")
        
        # For demo/mock:
        await asyncio.sleep(1)  # Simulate API call
        mock_result = {
            "success": True,
            "file_url": f"https://example.com/files/{data.get('output_format', 'unknown')}_output.file",
            "message": f"Successfully generated {data.get('output_format', 'unknown')} content"
        }
        return mock_result
        
    except Exception as e:
        print(f"API error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        execution_time = (datetime.now() - start_time).total_seconds()
        print(f"API call took {execution_time:.2f} seconds")

# Helper to download file from URL
async def _download_file(url: str, local_path: str) -> bool:
    """Download file from URL to local path"""
    # For real implementation:
    # try:
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(url) as response:
    #             if response.status == 200:
    #                 with open(local_path, 'wb') as f:
    #                     while True:
    #                         chunk = await response.content.read(1024)
    #                         if not chunk:
    #                             break
    #                         f.write(chunk)
    #                 return True
    #             else:
    #                 print(f"Download failed: {response.status}")
    #                 return False
    # except Exception as e:
    #     print(f"Download error: {str(e)}")
    #     return False
    
    # For demo/mock:
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'w') as f:
            f.write(f"Mock content downloaded from {url}")
        return True
    except Exception as e:
        print(f"Mock download error: {str(e)}")
        return False

# Agent function implementations

async def generate_architecture_diagram(prompt: str) -> AgentOutput:
    """Generate architectural diagrams using external API"""
    start_time = datetime.now()
    print(f"🔄 Generating architecture diagram for prompt length: {len(prompt)}")
    
    # Save the prompt for reference
    os.makedirs("./data", exist_ok=True)
    prompt_file = f"./data/diagram_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    # Prepare API call
    api_data = {
        "prompt": prompt,
        "output_format": "png",
        "style": "technical",
        "include_labels": True,
        "color_scheme": "professional"
    }
    
    # Call API
    result = await _make_api_call(API_CONFIG["diagram_api"], api_data)
    
    output_file = f"./data/diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    if result.get("success", False):
        # Download the generated file
        await _download_file(result["file_url"], output_file)
        content = "Architecture diagram generated successfully"
    else:
        content = f"Error generating diagram: {result.get('error', 'Unknown error')}"
        output_file = None
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return AgentOutput(
        agent_type="diagram",
        content=content,
        format="png",
        file_path=output_file,
        execution_time=execution_time
    )

async def generate_presentation(prompt: str) -> AgentOutput:
    """Generate PowerPoint presentation using external API"""
    start_time = datetime.now()
    print(f"🔄 Generating presentation for prompt length: {len(prompt)}")
    
    # Save the prompt for reference
    os.makedirs("./data", exist_ok=True)
    prompt_file = f"./data/presentation_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    # Prepare API call
    api_data = {
        "prompt": prompt,
        "output_format": "pptx",
        "slide_count": "auto",
        "include_graphics": True,
        "style": "professional"
    }
    
    # Call API
    result = await _make_api_call(API_CONFIG["presentation_api"], api_data)
    
    output_file = f"./data/presentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
    
    if result.get("success", False):
        # Download the generated file
        await _download_file(result["file_url"], output_file)
        content = "Presentation generated successfully"
    else:
        content = f"Error generating presentation: {result.get('error', 'Unknown error')}"
        output_file = None
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return AgentOutput(
        agent_type="presentation",
        content=content,
        format="pptx",
        file_path=output_file,
        execution_time=execution_time
    )

async def generate_document(prompt: str) -> AgentOutput:
    """Generate Word document using external API"""
    start_time = datetime.now()
    print(f"🔄 Generating document for prompt length: {len(prompt)}")
    
    # Save the prompt for reference
    os.makedirs("./data", exist_ok=True)
    prompt_file = f"./data/document_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    # Prepare API call
    api_data = {
        "prompt": prompt,
        "output_format": "docx",
        "include_toc": True,
        "include_references": True,
        "style": "technical"
    }
    
    # Call API
    result = await _make_api_call(API_CONFIG["document_api"], api_data)
    
    output_file = f"./data/document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    
    if result.get("success", False):
        # Download the generated file
        await _download_file(result["file_url"], output_file)
        content = "Document generated successfully"
    else:
        content = f"Error generating document: {result.get('error', 'Unknown error')}"
        output_file = None
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return AgentOutput(
        agent_type="document",
        content=content,
        format="docx",
        file_path=output_file,
        execution_time=execution_time
    )

async def generate_pdf(prompt: str) -> AgentOutput:
    """Generate PDF report using external API"""
    start_time = datetime.now()
    print(f"🔄 Generating PDF for prompt length: {len(prompt)}")
    
    # Save the prompt for reference
    os.makedirs("./data", exist_ok=True)
    prompt_file = f"./data/pdf_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    # Prepare API call
    api_data = {
        "prompt": prompt,
        "output_format": "pdf",
        "include_charts": True,
        "include_executive_summary": True,
        "style": "professional"
    }
    
    # Call API
    result = await _make_api_call(API_CONFIG["pdf_api"], api_data)
    
    output_file = f"./data/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    if result.get("success", False):
        # Download the generated file
        await _download_file(result["file_url"], output_file)
        content = "PDF report generated successfully"
    else:
        content = f"Error generating PDF: {result.get('error', 'Unknown error')}"
        output_file = None
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return AgentOutput(
        agent_type="pdf",
        content=content,
        format="pdf",
        file_path=output_file,
        execution_time=execution_time
    )

async def generate_code(prompt: str) -> AgentOutput:
    """Generate code using external API"""
    start_time = datetime.now()
    print(f"🔄 Generating code for prompt length: {len(prompt)}")
    
    # Save the prompt for reference
    os.makedirs("./data", exist_ok=True)
    prompt_file = f"./data/code_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    # Prepare API call
    api_data = {
        "prompt": prompt,
        "output_format": "zip",
        "include_tests": True,
        "include_documentation": True,
        "language": "auto"
    }
    
    # Call API
    result = await _make_api_call(API_CONFIG["code_api"], api_data)
    
    output_file = f"./data/code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    if result.get("success", False):
        # Download the generated file
        await _download_file(result["file_url"], output_file)
        content = "Code generated successfully"
    else:
        content = f"Error generating code: {result.get('error', 'Unknown error')}"
        output_file = None
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return AgentOutput(
        agent_type="code",
        content=content,
        format="zip",
        file_path=output_file,
        execution_time=execution_time
    )

# Export a function map for easy access from the main notebook
AGENT_FUNCTIONS = {
    "diagram": generate_architecture_diagram,
    "presentation": generate_presentation,
    "document": generate_document,
    "pdf": generate_pdf,
    "code": generate_code
}
