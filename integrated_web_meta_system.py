#!/usr/bin/env python3
"""
INTEGRATED WEB META SYSTEM
Combines the correct Meta Model workflow with a modern web frontend
"""

import os
import sys
import json
import uuid
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import threading

# Flask imports
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit

# LangChain imports  
from langchain_community.llms import Ollama
from langchain.schema import BaseOutputParser
from langchain.prompts import PromptTemplate

# ==============================================================================
# CONFIGURATION & SETUP
# ==============================================================================

# Setup paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
STATIC_DIR = BASE_DIR / "hackfront-main" / "static"
TEMPLATES_DIR = BASE_DIR / "hackfront-main" / "templates"

# Create directories
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Flask app setup
app = Flask(__name__, 
           static_folder=str(STATIC_DIR),
           template_folder=str(TEMPLATES_DIR))
app.config['SECRET_KEY'] = 'meta_ai_secret_key_2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'meta_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global storage for conversation logs
conversation_logs = {}
processing_steps = {}

# ==============================================================================
# LLM CONFIGURATION (LLAMA3.2 ONLY)
# ==============================================================================

@dataclass
class LLMConfig:
    """LLM configuration for the system"""
    model: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.1

def create_llm(config: LLMConfig) -> Ollama:
    """Create and test LLM connection"""
    try:
        llm = Ollama(
            model=config.model,
            base_url=config.base_url,
            temperature=config.temperature
        )
        
        # Test connection
        logger.info(f"Testing connection to {config.model}...")
        test_response = llm.invoke("Test connection")
        if not test_response:
            raise ValueError(f"No response from {config.model}")
        
        logger.info(f"✅ Successfully connected to {config.model}")
        return llm
        
    except Exception as e:
        error_msg = f"❌ ERROR: Could not connect to {config.model}. Make sure Ollama is running and llama3.2 is installed."
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

# ==============================================================================
# DATA CLASSES (FROM META MODEL)
# ==============================================================================

@dataclass
class DomainExpertInput:
    """Input data for domain expert analysis"""
    user_query: str
    context: Optional[Dict[str, Any]] = None

@dataclass 
class DomainExpertOutput:
    """Output from domain expert analysis"""
    domain: str
    analysis: str
    recommendations: List[str]
    key_findings: List[str]
    next_steps: List[str]

@dataclass
class ProcessingStep:
    """Individual processing step for logging"""
    step_id: str
    step_name: str
    domain: str
    status: str  # 'started', 'completed', 'error'
    details: str
    output: str
    timestamp: float

@dataclass
class SystemState:
    """Complete system state tracking"""
    conversation_id: str
    user_query: str
    domain_outputs: Dict[str, DomainExpertOutput]
    workflow_type: str
    final_outputs: List[str]
    processing_steps: List[ProcessingStep]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

# ==============================================================================
# DOMAIN EXPERTS (FROM META MODEL)
# ==============================================================================

class DomainExpert:
    """Base domain expert class"""
    
    def __init__(self, llm: Ollama, domain: str):
        self.llm = llm
        self.domain = domain
    
    def analyze(self, input_data: DomainExpertInput, conversation_id: str) -> DomainExpertOutput:
        """Analyze input from domain perspective"""
        raise NotImplementedError("Subclasses must implement analyze method")

class MechanicalDomainExpert(DomainExpert):
    """Mechanical engineering domain expert"""
    
    def __init__(self, llm: Ollama):
        super().__init__(llm, "mechanical")
        
        self.analysis_prompt = PromptTemplate(
            input_variables=["user_query"],
            template="""You are a senior mechanical engineering expert analyzing a project request.

User Query: {user_query}

As a mechanical engineering expert, analyze this query and provide:
1. Mechanical engineering aspects and considerations
2. Structural, thermal, fluid mechanics, or materials considerations
3. Physical constraints and requirements
4. Manufacturing and assembly considerations
5. Safety and reliability factors

Provide detailed analysis focusing specifically on mechanical engineering aspects.

Analysis:"""
        )
    
    def analyze(self, input_data: DomainExpertInput, conversation_id: str) -> DomainExpertOutput:
        try:
            # Log processing step
            step = ProcessingStep(
                step_id=f"mech_{uuid.uuid4().hex[:8]}",
                step_name="Mechanical Domain Analysis",
                domain="mechanical",
                status="started",
                details=f"Analyzing query: {input_data.user_query[:100]}...",
                output="",
                timestamp=time.time()
            )
            self._log_step(conversation_id, step)
            
            logger.info("Running mechanical domain analysis...")
            
            prompt = self.analysis_prompt.format(user_query=input_data.user_query)
            
            # Save prompt to log file
            self._save_prompt_to_log("mechanical_domain_prompt", prompt, conversation_id)
            
            analysis_text = self.llm.invoke(prompt)
            
            # Parse analysis into structured format
            recommendations = []
            key_findings = []
            next_steps = []
            
            # Extract key information (simplified parsing)
            lines = analysis_text.split('\n')
            for line in lines:
                if 'recommend' in line.lower():
                    recommendations.append(line.strip())
                elif 'finding' in line.lower() or 'important' in line.lower():
                    key_findings.append(line.strip())
                elif 'next' in line.lower() or 'step' in line.lower():
                    next_steps.append(line.strip())
            
            # Ensure we have at least some content
            if not recommendations:
                recommendations = ["Consider mechanical design constraints"]
            if not key_findings:
                key_findings = ["Mechanical analysis completed"]
            if not next_steps:
                next_steps = ["Proceed to electrical analysis"]
            
            result = DomainExpertOutput(
                domain="mechanical",
                analysis=analysis_text,
                recommendations=recommendations,
                key_findings=key_findings,
                next_steps=next_steps
            )
            
            # Update processing step
            step.status = "completed"
            step.output = f"Analysis: {len(analysis_text)} chars, {len(recommendations)} recommendations"
            self._log_step(conversation_id, step)
            
            # Save analysis to file
            self._save_analysis_to_file(result, conversation_id)
            
            return result
            
        except Exception as e:
            # Log error step
            step.status = "error"
            step.output = f"Error: {str(e)}"
            self._log_step(conversation_id, step)
            
            logger.error(f"Error in mechanical analysis: {e}")
            raise
    
    def _log_step(self, conversation_id: str, step: ProcessingStep):
        """Log processing step"""
        if conversation_id not in processing_steps:
            processing_steps[conversation_id] = []
        processing_steps[conversation_id].append(step)
        
        # Emit to frontend via SocketIO
        socketio.emit('processing_update', {
            'conversation_id': conversation_id,
            'step': asdict(step)
        })
    
    def _save_prompt_to_log(self, prompt_type: str, prompt: str, conversation_id: str):
        """Save prompt to log file"""
        log_file = LOGS_DIR / f"{prompt_type}_{conversation_id}.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Prompt Type: {prompt_type}\n")
            f.write(f"Conversation ID: {conversation_id}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("="*50 + "\n")
            f.write(prompt)
    
    def _save_analysis_to_file(self, result: DomainExpertOutput, conversation_id: str):
        """Save analysis to file"""
        analysis_file = DATA_DIR / f"{result.domain}_analysis_{conversation_id}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2)

class ElectricalDomainExpert(DomainExpert):
    """Electrical engineering domain expert"""
    
    def __init__(self, llm: Ollama):
        super().__init__(llm, "electrical")
        
        self.analysis_prompt = PromptTemplate(
            input_variables=["user_query"],
            template="""You are a senior electrical engineering expert analyzing a project request.

User Query: {user_query}

As an electrical engineering expert, analyze this query and provide:
1. Electrical system requirements and specifications
2. Power systems, circuits, and control considerations
3. Electronic components and integration needs
4. Signal processing and communication aspects
5. Safety standards and compliance requirements

Provide detailed analysis focusing specifically on electrical engineering aspects.

Analysis:"""
        )
    
    def analyze(self, input_data: DomainExpertInput, conversation_id: str) -> DomainExpertOutput:
        try:
            # Log processing step
            step = ProcessingStep(
                step_id=f"elec_{uuid.uuid4().hex[:8]}",
                step_name="Electrical Domain Analysis",
                domain="electrical",
                status="started",
                details=f"Analyzing query: {input_data.user_query[:100]}...",
                output="",
                timestamp=time.time()
            )
            self._log_step(conversation_id, step)
            
            logger.info("Running electrical domain analysis...")
            
            prompt = self.analysis_prompt.format(user_query=input_data.user_query)
            
            # Save prompt to log file
            self._save_prompt_to_log("electrical_domain_prompt", prompt, conversation_id)
            
            analysis_text = self.llm.invoke(prompt)
            
            # Parse analysis into structured format
            recommendations = []
            key_findings = []
            next_steps = []
            
            # Extract key information (simplified parsing)
            lines = analysis_text.split('\n')
            for line in lines:
                if 'recommend' in line.lower():
                    recommendations.append(line.strip())
                elif 'finding' in line.lower() or 'important' in line.lower():
                    key_findings.append(line.strip())
                elif 'next' in line.lower() or 'step' in line.lower():
                    next_steps.append(line.strip())
            
            # Ensure we have at least some content
            if not recommendations:
                recommendations = ["Consider electrical system requirements"]
            if not key_findings:
                key_findings = ["Electrical analysis completed"]
            if not next_steps:
                next_steps = ["Proceed to programming analysis"]
            
            result = DomainExpertOutput(
                domain="electrical",
                analysis=analysis_text,
                recommendations=recommendations,
                key_findings=key_findings,
                next_steps=next_steps
            )
            
            # Update processing step
            step.status = "completed"
            step.output = f"Analysis: {len(analysis_text)} chars, {len(recommendations)} recommendations"
            self._log_step(conversation_id, step)
            
            # Save analysis to file
            self._save_analysis_to_file(result, conversation_id)
            
            return result
            
        except Exception as e:
            # Log error step
            step.status = "error"
            step.output = f"Error: {str(e)}"
            self._log_step(conversation_id, step)
            
            logger.error(f"Error in electrical analysis: {e}")
            raise
    
    def _log_step(self, conversation_id: str, step: ProcessingStep):
        """Log processing step"""
        if conversation_id not in processing_steps:
            processing_steps[conversation_id] = []
        processing_steps[conversation_id].append(step)
        
        # Emit to frontend via SocketIO
        socketio.emit('processing_update', {
            'conversation_id': conversation_id,
            'step': asdict(step)
        })
    
    def _save_prompt_to_log(self, prompt_type: str, prompt: str, conversation_id: str):
        """Save prompt to log file"""
        log_file = LOGS_DIR / f"{prompt_type}_{conversation_id}.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Prompt Type: {prompt_type}\n")
            f.write(f"Conversation ID: {conversation_id}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("="*50 + "\n")
            f.write(prompt)
    
    def _save_analysis_to_file(self, result: DomainExpertOutput, conversation_id: str):
        """Save analysis to file"""
        analysis_file = DATA_DIR / f"{result.domain}_analysis_{conversation_id}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2)

class ProgrammingDomainExpert(DomainExpert):
    """Programming/software domain expert"""
    
    def __init__(self, llm: Ollama):
        super().__init__(llm, "programming")
        
        self.analysis_prompt = PromptTemplate(
            input_variables=["user_query"], 
            template="""You are a senior software engineering expert analyzing a project request.

User Query: {user_query}

As a programming/software expert, analyze this query and provide:
1. Software architecture and design patterns
2. Programming languages and frameworks to consider
3. Data structures and algorithms requirements
4. Integration and API considerations
5. Testing, deployment, and maintenance aspects

Provide detailed analysis focusing specifically on software/programming aspects.

Analysis:"""
        )
    
    def analyze(self, input_data: DomainExpertInput, conversation_id: str) -> DomainExpertOutput:
        try:
            # Log processing step
            step = ProcessingStep(
                step_id=f"prog_{uuid.uuid4().hex[:8]}",
                step_name="Programming Domain Analysis",
                domain="programming",
                status="started",
                details=f"Analyzing query: {input_data.user_query[:100]}...",
                output="",
                timestamp=time.time()
            )
            self._log_step(conversation_id, step)
            
            logger.info("Running programming domain analysis...")
            
            prompt = self.analysis_prompt.format(user_query=input_data.user_query)
            
            # Save prompt to log file
            self._save_prompt_to_log("programming_domain_prompt", prompt, conversation_id)
            
            analysis_text = self.llm.invoke(prompt)
            
            # Parse analysis into structured format
            recommendations = []
            key_findings = []
            next_steps = []
            
            # Extract key information (simplified parsing)
            lines = analysis_text.split('\n')
            for line in lines:
                if 'recommend' in line.lower():
                    recommendations.append(line.strip())
                elif 'finding' in line.lower() or 'important' in line.lower():
                    key_findings.append(line.strip())
                elif 'next' in line.lower() or 'step' in line.lower():
                    next_steps.append(line.strip())
            
            # Ensure we have at least some content
            if not recommendations:
                recommendations = ["Consider software design patterns"]
            if not key_findings:
                key_findings = ["Programming analysis completed"]
            if not next_steps:
                next_steps = ["Proceed to workflow integration"]
            
            result = DomainExpertOutput(
                domain="programming",
                analysis=analysis_text,
                recommendations=recommendations,
                key_findings=key_findings,
                next_steps=next_steps
            )
            
            # Update processing step
            step.status = "completed"
            step.output = f"Analysis: {len(analysis_text)} chars, {len(recommendations)} recommendations"
            self._log_step(conversation_id, step)
            
            # Save analysis to file
            self._save_analysis_to_file(result, conversation_id)
            
            return result
            
        except Exception as e:
            # Log error step
            step.status = "error"
            step.output = f"Error: {str(e)}"
            self._log_step(conversation_id, step)
            
            logger.error(f"Error in programming analysis: {e}")
            raise
    
    def _log_step(self, conversation_id: str, step: ProcessingStep):
        """Log processing step"""
        if conversation_id not in processing_steps:
            processing_steps[conversation_id] = []
        processing_steps[conversation_id].append(step)
        
        # Emit to frontend via SocketIO
        socketio.emit('processing_update', {
            'conversation_id': conversation_id,
            'step': asdict(step)
        })
    
    def _save_prompt_to_log(self, prompt_type: str, prompt: str, conversation_id: str):
        """Save prompt to log file"""
        log_file = LOGS_DIR / f"{prompt_type}_{conversation_id}.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Prompt Type: {prompt_type}\n")
            f.write(f"Conversation ID: {conversation_id}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("="*50 + "\n")
            f.write(prompt)
    
    def _save_analysis_to_file(self, result: DomainExpertOutput, conversation_id: str):
        """Save analysis to file"""
        analysis_file = DATA_DIR / f"{result.domain}_analysis_{conversation_id}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2)

# ==============================================================================
# WORKFLOW MANAGER (FROM META MODEL)
# ==============================================================================

class WorkflowManager:
    """Meta Model's WorkflowManager creates the workflow based on domain analysis"""
    
    def __init__(self, llm: Ollama):
        self.llm = llm
        self.domain_experts = {
            'mechanical': MechanicalDomainExpert(llm),
            'electrical': ElectricalDomainExpert(llm), 
            'programming': ProgrammingDomainExpert(llm)
        }
        
        self.workflow_prompt = PromptTemplate(
            input_variables=["user_query", "domain_analyses"],
            template="""You are a workflow orchestration expert. Based on the user query and domain expert analyses, create an optimal workflow.

User Query: {user_query}

Domain Expert Analyses:
{domain_analyses}

Based on this analysis, determine the best workflow by selecting the most appropriate document type(s) to generate:

Available document types:
1. PDF Report - Comprehensive analysis and documentation
2. Pipeline Diagram - Visual workflow and process diagrams  
3. PowerPoint Presentation - Executive summary and presentation
4. Word Document - Detailed technical documentation
5. Complex Code Project - Full software implementation

Consider:
- Which document type best serves the user's needs?
- What is the primary goal of the user's query?
- Which deliverable would be most valuable?

Recommend the SINGLE most appropriate document type and explain why.

Workflow Decision:"""
        )
    
    def execute_domain_analysis(self, user_query: str, conversation_id: str, context: Optional[Dict] = None) -> Dict[str, DomainExpertOutput]:
        """Execute all domain expert analyses"""
        logger.info("🔍 Starting domain expert analysis workflow...")
        
        domain_outputs = {}
        
        input_data = DomainExpertInput(
            user_query=user_query,
            context=context
        )
        
        for domain_name, expert in self.domain_experts.items():
            try:
                logger.info(f"Running {domain_name} domain analysis...")
                output = expert.analyze(input_data, conversation_id)
                domain_outputs[domain_name] = output
                
            except Exception as e:
                logger.error(f"Error in {domain_name} domain analysis: {e}")
                raise
        
        return domain_outputs
    
    def create_workflow(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput], conversation_id: str) -> str:
        """Create workflow based on domain analysis"""
        logger.info("🔧 Creating workflow based on domain analysis...")
        
        # Log workflow creation step
        step = ProcessingStep(
            step_id=f"workflow_{uuid.uuid4().hex[:8]}",
            step_name="Workflow Creation",
            domain="workflow",
            status="started",
            details="Analyzing domain outputs to determine optimal workflow",
            output="",
            timestamp=time.time()
        )
        self._log_step(conversation_id, step)
        
        # Prepare domain analyses text
        domain_analyses = ""
        for domain, output in domain_outputs.items():
            domain_analyses += f"\n{domain.upper()} ANALYSIS:\n"
            domain_analyses += f"Key Findings: {', '.join(output.key_findings)}\n"
            domain_analyses += f"Recommendations: {', '.join(output.recommendations)}\n"
            domain_analyses += f"Analysis Summary: {output.analysis[:200]}...\n"
        
        try:
            # Use LLM to determine optimal workflow
            prompt = self.workflow_prompt.format(
                user_query=user_query,
                domain_analyses=domain_analyses
            )
            
            # Save workflow prompt to log
            self._save_prompt_to_log("workflow_prompt", prompt, conversation_id)
            
            workflow_decision = self.llm.invoke(prompt)
            
            # Parse the decision to extract document type
            decision_lower = workflow_decision.lower()
            
            workflow_type = None
            if "pdf report" in decision_lower or "pdf" in decision_lower:
                workflow_type = "pdf"
            elif "diagram" in decision_lower or "pipeline" in decision_lower:
                workflow_type = "diagram"
            elif "powerpoint" in decision_lower or "presentation" in decision_lower:
                workflow_type = "powerpoint"  
            elif "word" in decision_lower or "document" in decision_lower:
                workflow_type = "word"
            elif "code" in decision_lower or "project" in decision_lower:
                workflow_type = "project"
            else:
                logger.warning("Could not determine document type from workflow decision, defaulting to PDF")
                workflow_type = "pdf"
            
            # Update processing step
            step.status = "completed"
            step.output = f"Selected workflow: {workflow_type}. Reasoning: {workflow_decision[:200]}..."
            self._log_step(conversation_id, step)
            
            return workflow_type
                
        except Exception as e:
            # Log error step
            step.status = "error"
            step.output = f"Error: {str(e)}"
            self._log_step(conversation_id, step)
            
            logger.error(f"Error creating workflow: {e}")
            return "pdf"
    
    def _log_step(self, conversation_id: str, step: ProcessingStep):
        """Log processing step"""
        if conversation_id not in processing_steps:
            processing_steps[conversation_id] = []
        processing_steps[conversation_id].append(step)
        
        # Emit to frontend via SocketIO
        socketio.emit('processing_update', {
            'conversation_id': conversation_id,
            'step': asdict(step)
        })
    
    def _save_prompt_to_log(self, prompt_type: str, prompt: str, conversation_id: str):
        """Save prompt to log file"""
        log_file = LOGS_DIR / f"{prompt_type}_{conversation_id}.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Prompt Type: {prompt_type}\n")
            f.write(f"Conversation ID: {conversation_id}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("="*50 + "\n")
            f.write(prompt)

# ==============================================================================
# ATTEMPT2 AGENTS INTEGRATION
# ==============================================================================

class Attempt2AgentExecutor:
    """Execute the 5 agents from attempt2.py based on workflow decision"""
    
    def __init__(self, llm: Ollama):
        self.llm = llm
        
    def generate_pdf_report(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput], conversation_id: str) -> str:
        """Agent 1: PDF Pipeline Report Generation"""
        step = ProcessingStep(
            step_id=f"pdf_{uuid.uuid4().hex[:8]}",
            step_name="PDF Report Generation",
            domain="document_generation",
            status="started",
            details="Generating comprehensive PDF report",
            output="",
            timestamp=time.time()
        )
        self._log_step(conversation_id, step)
        
        logger.info("📄 Executing PDF Report Agent...")
        
        # Create comprehensive context from domain analyses
        context = self._create_context_from_domains(user_query, domain_outputs)
        
        prompt = f"""Generate a comprehensive PDF report for: {user_query}

Context from Domain Analysis:
{context}

Create a detailed professional report covering all aspects analyzed by the domain experts.
Include executive summary, technical details, recommendations, and next steps.

Report Content:"""
        
        try:
            # Save prompt to log
            self._save_prompt_to_log("pdf_generation_prompt", prompt, conversation_id)
            
            report_content = self.llm.invoke(prompt)
            
            # Save to file
            filename = f"pdf_report_{conversation_id}.txt"
            output_file = DATA_DIR / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"PDF REPORT: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(report_content)
            
            # Update processing step
            step.status = "completed"
            step.output = f"PDF report generated: {filename}"
            self._log_step(conversation_id, step)
            
            logger.info(f"✅ PDF report saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            # Log error step
            step.status = "error"
            step.output = f"Error: {str(e)}"
            self._log_step(conversation_id, step)
            
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    def generate_pipeline_diagram(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput], conversation_id: str) -> str:
        """Agent 2: Generate and Execute Diagram Script"""
        step = ProcessingStep(
            step_id=f"diagram_{uuid.uuid4().hex[:8]}",
            step_name="Pipeline Diagram Generation",
            domain="document_generation",
            status="started",
            details="Generating visual pipeline diagram",
            output="",
            timestamp=time.time()
        )
        self._log_step(conversation_id, step)
        
        logger.info("📊 Executing Pipeline Diagram Agent...")
        
        context = self._create_context_from_domains(user_query, domain_outputs)
        
        prompt = f"""Generate a pipeline diagram description for: {user_query}

Context from Domain Analysis:
{context}

Create a detailed description of a visual pipeline/workflow diagram that shows the process flow, 
components, and relationships based on the domain expert analysis.

Diagram Description:"""
        
        try:
            # Save prompt to log
            self._save_prompt_to_log("diagram_generation_prompt", prompt, conversation_id)
            
            diagram_description = self.llm.invoke(prompt)
            
            # Save diagram description
            filename = f"diagram_script_{conversation_id}.txt"
            output_file = DATA_DIR / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"PIPELINE DIAGRAM: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(diagram_description)
            
            # Update processing step
            step.status = "completed"
            step.output = f"Diagram description generated: {filename}"
            self._log_step(conversation_id, step)
            
            logger.info(f"✅ Diagram description saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            # Log error step
            step.status = "error"
            step.output = f"Error: {str(e)}"
            self._log_step(conversation_id, step)
            
            logger.error(f"Error generating diagram: {e}")
            raise
    
    def generate_powerpoint_presentation(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput], conversation_id: str) -> str:
        """Agent 3: Generate PowerPoint Presentation"""
        step = ProcessingStep(
            step_id=f"ppt_{uuid.uuid4().hex[:8]}",
            step_name="PowerPoint Presentation Generation",
            domain="document_generation",
            status="started",
            details="Generating PowerPoint presentation",
            output="",
            timestamp=time.time()
        )
        self._log_step(conversation_id, step)
        
        logger.info("📽️ Executing PowerPoint Agent...")
        
        context = self._create_context_from_domains(user_query, domain_outputs)
        
        prompt = f"""Generate a PowerPoint presentation outline for: {user_query}

Context from Domain Analysis:
{context}

Create a professional presentation structure with slides covering:
- Executive Summary
- Domain Expert Findings (Mechanical, Electrical, Programming)  
- Recommendations
- Implementation Plan
- Conclusion

Presentation Outline:"""
        
        try:
            # Save prompt to log
            self._save_prompt_to_log("powerpoint_generation_prompt", prompt, conversation_id)
            
            presentation_content = self.llm.invoke(prompt)
            
            # Save presentation outline
            filename = f"powerpoint_{conversation_id}.txt"
            output_file = DATA_DIR / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"POWERPOINT PRESENTATION: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(presentation_content)
            
            # Update processing step
            step.status = "completed"
            step.output = f"PowerPoint presentation generated: {filename}"
            self._log_step(conversation_id, step)
            
            logger.info(f"✅ PowerPoint outline saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            # Log error step
            step.status = "error"
            step.output = f"Error: {str(e)}"
            self._log_step(conversation_id, step)
            
            logger.error(f"Error generating PowerPoint: {e}")
            raise
    
    def generate_word_document(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput], conversation_id: str) -> str:
        """Agent 4: Generate Word Document"""
        step = ProcessingStep(
            step_id=f"word_{uuid.uuid4().hex[:8]}",
            step_name="Word Document Generation",
            domain="document_generation",
            status="started",
            details="Generating comprehensive Word document",
            output="",
            timestamp=time.time()
        )
        self._log_step(conversation_id, step)
        
        logger.info("📝 Executing Word Document Agent...")
        
        context = self._create_context_from_domains(user_query, domain_outputs)
        
        prompt = f"""Generate a detailed Word document for: {user_query}

Context from Domain Analysis:
{context}

Create a comprehensive technical document with:
- Introduction and scope
- Detailed technical analysis from each domain
- Cross-domain integration considerations
- Implementation guidelines
- Risk assessment and mitigation
- Appendices with supporting data

Document Content:"""
        
        try:
            # Save prompt to log
            self._save_prompt_to_log("word_generation_prompt", prompt, conversation_id)
            
            document_content = self.llm.invoke(prompt)
            
            # Save document
            filename = f"word_document_{conversation_id}.txt"
            output_file = DATA_DIR / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"WORD DOCUMENT: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(document_content)
            
            # Update processing step
            step.status = "completed"
            step.output = f"Word document generated: {filename}"
            self._log_step(conversation_id, step)
            
            logger.info(f"✅ Word document saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            # Log error step
            step.status = "error"
            step.output = f"Error: {str(e)}"
            self._log_step(conversation_id, step)
            
            logger.error(f"Error generating Word document: {e}")
            raise
    
    def generate_complex_project(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput], conversation_id: str) -> str:
        """Agent 5: Generate Project/Code Files"""
        step = ProcessingStep(
            step_id=f"project_{uuid.uuid4().hex[:8]}",
            step_name="Complex Project Generation",
            domain="document_generation",
            status="started",
            details="Generating complex code project structure",
            output="",
            timestamp=time.time()
        )
        self._log_step(conversation_id, step)
        
        logger.info("💻 Executing Complex Project Agent...")
        
        context = self._create_context_from_domains(user_query, domain_outputs)
        
        prompt = f"""Generate a complex code project structure for: {user_query}

Context from Domain Analysis:
{context}

Create a detailed software project including:
- Project architecture and file structure
- Core implementation files
- Configuration files
- Documentation
- Testing strategy
- Deployment instructions

Project Structure and Code:"""
        
        try:
            # Save prompt to log
            self._save_prompt_to_log("project_generation_prompt", prompt, conversation_id)
            
            project_content = self.llm.invoke(prompt)
            
            # Save project description
            filename = f"complex_project_{conversation_id}.txt"
            output_file = DATA_DIR / filename  
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"COMPLEX PROJECT: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(project_content)
            
            # Update processing step
            step.status = "completed"
            step.output = f"Complex project generated: {filename}"
            self._log_step(conversation_id, step)
            
            logger.info(f"✅ Complex project saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            # Log error step
            step.status = "error"
            step.output = f"Error: {str(e)}"
            self._log_step(conversation_id, step)
            
            logger.error(f"Error generating complex project: {e}")
            raise
    
    def _create_context_from_domains(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Create rich context from domain expert outputs"""
        context = f"User Query: {user_query}\n\n"
        
        for domain, output in domain_outputs.items():
            context += f"{domain.upper()} DOMAIN ANALYSIS:\n"
            context += f"Analysis: {output.analysis[:300]}...\n"
            context += f"Key Findings: {', '.join(output.key_findings)}\n"
            context += f"Recommendations: {', '.join(output.recommendations)}\n"
            context += f"Next Steps: {', '.join(output.next_steps)}\n\n"
        
        return context
    
    def _log_step(self, conversation_id: str, step: ProcessingStep):
        """Log processing step"""
        if conversation_id not in processing_steps:
            processing_steps[conversation_id] = []
        processing_steps[conversation_id].append(step)
        
        # Emit to frontend via SocketIO
        socketio.emit('processing_update', {
            'conversation_id': conversation_id,
            'step': asdict(step)
        })
    
    def _save_prompt_to_log(self, prompt_type: str, prompt: str, conversation_id: str):
        """Save prompt to log file"""
        log_file = LOGS_DIR / f"{prompt_type}_{conversation_id}.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Prompt Type: {prompt_type}\n")
            f.write(f"Conversation ID: {conversation_id}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("="*50 + "\n")
            f.write(prompt)

# ==============================================================================
# INTEGRATED META SYSTEM CLASS
# ==============================================================================

class IntegratedMetaSystem:
    """Integrated system combining Meta Model workflow with web interface"""
    
    def __init__(self):
        """Initialize the integrated meta system"""
        logger.info("🚀 Initializing Integrated Meta System...")
        
        # Initialize LLM (llama3.2 only)
        self.llm_config = LLMConfig()
        self.llm = create_llm(self.llm_config)
        
        # Initialize Meta Model components
        self.workflow_manager = WorkflowManager(self.llm)
        
        # Initialize attempt2 agents
        self.agent_executor = Attempt2AgentExecutor(self.llm)
        
        logger.info("✅ Integrated Meta System initialized successfully")
    
    def process_user_query(self, user_query: str, conversation_id: str = None) -> Dict[str, Any]:
        """Process user query through the complete Meta Model workflow"""
        
        if not conversation_id:
            conversation_id = uuid.uuid4().hex[:8]
            
        logger.info(f"🎯 Starting workflow for conversation {conversation_id}")
        
        try:
            # STEP 1: Domain expert analysis (Meta Model approach)
            domain_outputs = self.workflow_manager.execute_domain_analysis(user_query, conversation_id)
            
            # STEP 2: Create workflow based on analysis
            workflow_type = self.workflow_manager.create_workflow(user_query, domain_outputs, conversation_id)
            
            # STEP 3: Execute workflow with attempt2 agents
            generated_file = None
            if workflow_type == "pdf":
                generated_file = self.agent_executor.generate_pdf_report(user_query, domain_outputs, conversation_id)
            elif workflow_type == "diagram": 
                generated_file = self.agent_executor.generate_pipeline_diagram(user_query, domain_outputs, conversation_id)
            elif workflow_type == "powerpoint":
                generated_file = self.agent_executor.generate_powerpoint_presentation(user_query, domain_outputs, conversation_id)
            elif workflow_type == "word":
                generated_file = self.agent_executor.generate_word_document(user_query, domain_outputs, conversation_id)
            elif workflow_type == "project":
                generated_file = self.agent_executor.generate_complex_project(user_query, domain_outputs, conversation_id)
            
            # STEP 4: Save complete system state
            system_state = SystemState(
                conversation_id=conversation_id,
                user_query=user_query,
                domain_outputs=domain_outputs,
                workflow_type=workflow_type,
                final_outputs=[generated_file],
                processing_steps=processing_steps.get(conversation_id, [])
            )
            
            state_file = DATA_DIR / f"system_state_{conversation_id}.json"
            with open(state_file, 'w') as f:
                # Convert to serializable format
                state_dict = {
                    "conversation_id": system_state.conversation_id,
                    "user_query": system_state.user_query,
                    "domain_outputs": {k: asdict(v) for k, v in system_state.domain_outputs.items()},
                    "workflow_type": workflow_type,
                    "final_outputs": system_state.final_outputs,
                    "processing_steps": [asdict(step) for step in system_state.processing_steps],
                    "timestamp": system_state.timestamp
                }
                json.dump(state_dict, f, indent=2)
            
            # Store in global conversation logs
            conversation_logs[conversation_id] = system_state
            
            return {
                "conversation_id": conversation_id,
                "domain_outputs": domain_outputs,
                "workflow_type": workflow_type,
                "generated_file": generated_file,
                "system_state_file": str(state_file),
                "processing_steps": processing_steps.get(conversation_id, [])
            }
            
        except Exception as e:
            logger.error(f"Error in workflow: {e}")
            raise

# Initialize global system instance
meta_system = None

def initialize_system():
    """Initialize the global system instance"""
    global meta_system
    try:
        meta_system = IntegratedMetaSystem()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        return False

# ==============================================================================
# FLASK ROUTES
# ==============================================================================

@app.route('/')
def home():
    """Home page"""
    return render_template('integrated_index.html')

@app.route('/process', methods=['POST'])
def process():
    """Process user query through Meta Model workflow"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_query = data.get('content', '').strip()
        if not user_query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        conversation_id = data.get('conversation_id', uuid.uuid4().hex[:8])
        
        # Initialize system if not already done
        if not meta_system:
            init_success = initialize_system()
            if not init_success:
                return jsonify({'error': 'Failed to initialize Meta System. Please check if Ollama is running with llama3.2.'}), 500
        
        # Process query in background thread to avoid blocking
        def process_in_background():
            try:
                result = meta_system.process_user_query(user_query, conversation_id)
                
                # Generate response summary
                response_text = f"""🎯 Meta Model Analysis Complete!

**Conversation ID:** {result['conversation_id']}
**Workflow Selected:** {result['workflow_type'].title()}

**Domain Expert Analysis:**
"""
                for domain, output in result['domain_outputs'].items():
                    response_text += f"• **{domain.title()}:** {len(output.key_findings)} findings, {len(output.recommendations)} recommendations\n"
                
                response_text += f"\n**Generated Output:** {Path(result['generated_file']).name}"
                response_text += f"\n**Processing Steps:** {len(result['processing_steps'])} steps completed"
                
                # Emit completion to frontend
                socketio.emit('processing_complete', {
                    'conversation_id': conversation_id,
                    'response': response_text,
                    'result': {
                        'conversation_id': result['conversation_id'],
                        'workflow_type': result['workflow_type'],
                        'generated_file': result['generated_file'],
                        'processing_steps': [asdict(step) for step in result['processing_steps']]
                    }
                })
                
            except Exception as e:
                logger.error(f"Error in background processing: {e}")
                socketio.emit('processing_error', {
                    'conversation_id': conversation_id,
                    'error': str(e)
                })
        
        # Start background processing
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'processing',
            'conversation_id': conversation_id,
            'message': 'Processing started. You will see real-time updates.'
        })
        
    except Exception as e:
        logger.error(f"Error in process route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs/<conversation_id>')
def get_logs(conversation_id):
    """Get processing logs for a conversation"""
    try:
        steps = processing_steps.get(conversation_id, [])
        return jsonify({
            'conversation_id': conversation_id,
            'steps': [asdict(step) for step in steps]
        })
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs')
def get_all_logs():
    """Get all processing logs"""
    try:
        all_logs = {}
        for conv_id, steps in processing_steps.items():
            all_logs[conv_id] = [asdict(step) for step in steps]
        return jsonify(all_logs)
    except Exception as e:
        logger.error(f"Error getting all logs: {e}")
        return jsonify({'error': str(e)}), 500

# ==============================================================================
# SOCKETIO EVENTS
# ==============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('connected', {'message': 'Connected to Meta System'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    print("🎯 Starting Integrated Meta System Web Application...")
    print("This combines Meta Model workflow with modern web interface")
    print("="*70)
    
    # Initialize system
    print("🚀 Initializing system...")
    init_success = initialize_system()
    
    if init_success:
        print("✅ System initialized successfully!")
        print(f"📁 Data directory: {DATA_DIR}")
        print(f"📄 Logs directory: {LOGS_DIR}")
        print(f"🌐 Web interface will be available at: http://localhost:5000")
        print("="*70)
        
        # Run Flask app with SocketIO
        socketio.run(app, debug=True, port=5000, host='0.0.0.0')
    else:
        print("❌ Failed to initialize system. Please check:")
        print("1. Ollama is running")
        print("2. llama3.2 model is installed")
        print("3. All required dependencies are installed")
        sys.exit(1)