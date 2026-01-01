#!/usr/bin/env python3
"""
CORRECT META SYSTEM - Following exact Meta Model workflow
Combines Meta_model.ipynb and attempt2.py correctly

Flow: User prompt → Domain experts → Workflow creation → Execute workflow with attempt2 agents
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
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR.mkdir(exist_ok=True)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'correct_meta_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
@dataclass
class DomainExpertOutput:
    """Output from domain expert analysis"""
    domain: str
    analysis: str
    recommendations: List[str]
    key_findings: List[str]
    next_steps: List[str]
    confidence_score: float = 0.85  # Default confidence score

@dataclass
class WorkflowStep:
    """Individual workflow step"""
    step_id: str
    step_name: str
    description: str
    agent_type: str
    dependencies: List[str]
    estimated_time: str

@dataclass
class SystemState:
    """Complete system state tracking"""
    conversation_id: str
    user_query: str
    domain_outputs: Dict[str, DomainExpertOutput]
    workflow_steps: Dict[str, WorkflowStep]
    final_outputs: List[str]
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
    
    def analyze(self, input_data: DomainExpertInput) -> DomainExpertOutput:
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
    
    def analyze(self, input_data: DomainExpertInput) -> DomainExpertOutput:
        try:
            logger.info("Running mechanical domain analysis...")
            
            prompt = self.analysis_prompt.format(user_query=input_data.user_query)
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
            
            return DomainExpertOutput(
                domain="mechanical",
                analysis=analysis_text,
                recommendations=recommendations,
                key_findings=key_findings,
                next_steps=next_steps,
                confidence_score=0.88
            )
            
        except Exception as e:
            logger.error(f"Error in mechanical analysis: {e}")
            raise

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
    
    def analyze(self, input_data: DomainExpertInput) -> DomainExpertOutput:
        try:
            logger.info("Running electrical domain analysis...")
            
            prompt = self.analysis_prompt.format(user_query=input_data.user_query)
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
            
            return DomainExpertOutput(
                domain="electrical",
                analysis=analysis_text,
                recommendations=recommendations,
                key_findings=key_findings,
                next_steps=next_steps,
                confidence_score=0.90
            )
            
        except Exception as e:
            logger.error(f"Error in electrical analysis: {e}")
            raise

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
    
    def analyze(self, input_data: DomainExpertInput) -> DomainExpertOutput:
        try:
            logger.info("Running programming domain analysis...")
            
            prompt = self.analysis_prompt.format(user_query=input_data.user_query)
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
            
            return DomainExpertOutput(
                domain="programming",
                analysis=analysis_text,
                recommendations=recommendations,
                key_findings=key_findings,
                next_steps=next_steps,
                confidence_score=0.87
            )
            
        except Exception as e:
            logger.error(f"Error in programming analysis: {e}")
            raise

# ==============================================================================
# WORKFLOW MANAGER (FROM META MODEL - CRITICAL COMPONENT!)
# ==============================================================================

class WorkflowManager:
    """
    CRITICAL: This is the missing piece! 
    The Meta Model's WorkflowManager creates the workflow based on domain analysis
    """
    
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
    
    def execute_domain_analysis(self, user_query: str, context: Optional[Dict] = None) -> Dict[str, DomainExpertOutput]:
        """Execute all domain expert analyses - FROM META MODEL"""
        logger.info("🔍 Starting domain expert analysis workflow...")
        
        domain_outputs = {}
        
        input_data = DomainExpertInput(
            user_query=user_query,
            context=context
        )
        
        for domain_name, expert in self.domain_experts.items():
            try:
                logger.info(f"Running {domain_name} domain analysis...")
                output = expert.analyze(input_data)
                domain_outputs[domain_name] = output
                
                # Save domain analysis to file
                output_file = DATA_DIR / f"{domain_name}_analysis_{uuid.uuid4().hex[:8]}.json"
                with open(output_file, 'w') as f:
                    json.dump(asdict(output), f, indent=2)
                logger.info(f"Saved {domain_name} analysis to {output_file}")
                
            except Exception as e:
                logger.error(f"Error in {domain_name} domain analysis: {e}")
                raise
        
        return domain_outputs
    
    def create_workflow(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """
        CRITICAL: Create workflow based on domain analysis - THIS WAS MISSING!
        This determines which attempt2 agent to call
        """
        logger.info("🔧 Creating workflow based on domain analysis...")
        
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
            
            print("🤖 Analyzing domain expert outputs to determine best workflow...")
            workflow_decision = self.llm.invoke(prompt)
            
            print(f"💭 LLM Decision Reasoning:\n{workflow_decision[:300]}...")
            
            # Parse the decision to extract document type
            decision_lower = workflow_decision.lower()
            
            if "pdf report" in decision_lower or "pdf" in decision_lower:
                return "pdf"
            elif "diagram" in decision_lower or "pipeline" in decision_lower:
                return "diagram"
            elif "powerpoint" in decision_lower or "presentation" in decision_lower:
                return "powerpoint"  
            elif "word" in decision_lower or "document" in decision_lower:
                return "word"
            elif "code" in decision_lower or "project" in decision_lower:
                return "project"
            else:
                # Default to PDF if unclear
                logger.warning("Could not determine document type from workflow decision, defaulting to PDF")
                print("⚠️ Could not determine specific workflow type, defaulting to PDF Report")
                return "pdf"
                
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            print(f"⚠️ Error in workflow creation: {e}, defaulting to PDF Report")
            # Default fallback
            return "pdf"

# ==============================================================================
# ATTEMPT2 AGENTS INTEGRATION
# ==============================================================================

class Attempt2AgentExecutor:
    """
    Execute the 5 agents from attempt2.py based on workflow decision
    This is the integration point between Meta Model and attempt2
    """
    
    def __init__(self, llm: Ollama):
        self.llm = llm
        
    def generate_pdf_report(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Agent 1: PDF Pipeline Report Generation"""
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
            report_content = self.llm.invoke(prompt)
            
            # Save to file
            filename = f"pdf_report_{uuid.uuid4().hex[:8]}.txt"
            output_file = DATA_DIR / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"PDF REPORT: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(report_content)
            
            logger.info(f"✅ PDF report saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    def generate_pipeline_diagram(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Agent 2: Generate and Execute Diagram Script"""
        logger.info("📊 Executing Pipeline Diagram Agent...")
        
        context = self._create_context_from_domains(user_query, domain_outputs)
        
        prompt = f"""Generate a pipeline diagram description for: {user_query}

Context from Domain Analysis:
{context}

Create a detailed description of a visual pipeline/workflow diagram that shows the process flow, 
components, and relationships based on the domain expert analysis.

Diagram Description:"""
        
        try:
            diagram_description = self.llm.invoke(prompt)
            
            # Save diagram description
            filename = f"diagram_script_{uuid.uuid4().hex[:8]}.txt"
            output_file = DATA_DIR / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"PIPELINE DIAGRAM: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(diagram_description)
            
            logger.info(f"✅ Diagram description saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            raise
    
    def generate_powerpoint_presentation(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Agent 3: Generate PowerPoint Presentation"""
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
            presentation_content = self.llm.invoke(prompt)
            
            # Save presentation outline
            filename = f"powerpoint_{uuid.uuid4().hex[:8]}.txt"
            output_file = DATA_DIR / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"POWERPOINT PRESENTATION: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(presentation_content)
            
            logger.info(f"✅ PowerPoint outline saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error generating PowerPoint: {e}")
            raise
    
    def generate_word_document(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Agent 4: Generate Word Document"""
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
            document_content = self.llm.invoke(prompt)
            
            # Save document
            filename = f"word_document_{uuid.uuid4().hex[:8]}.txt"
            output_file = DATA_DIR / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"WORD DOCUMENT: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(document_content)
            
            logger.info(f"✅ Word document saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error generating Word document: {e}")
            raise
    
    def generate_complex_project(self, user_query: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Agent 5: Generate Project/Code Files"""
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
            project_content = self.llm.invoke(prompt)
            
            # Save project description
            filename = f"complex_project_{uuid.uuid4().hex[:8]}.txt"
            output_file = DATA_DIR / filename  
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"COMPLEX PROJECT: {user_query}\n")
                f.write("="*50 + "\n\n")
                f.write(project_content)
            
            logger.info(f"✅ Complex project saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
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

# ==============================================================================
# MAIN SYSTEM CLASS - CORRECT IMPLEMENTATION
# ==============================================================================

class CorrectMetaSystem:
    """
    CORRECT implementation following user's exact specification:
    User prompt → Domain experts → Workflow creation → Execute workflow with attempt2 agents
    """
    
    def __init__(self):
        """Initialize the correct meta system"""
        logger.info("🚀 Initializing Correct Meta System...")
        
        # Initialize LLM (llama3.2 only)
        self.llm_config = LLMConfig()
        self.llm = create_llm(self.llm_config)
        
        # Initialize Meta Model components
        self.workflow_manager = WorkflowManager(self.llm)
        
        # Initialize attempt2 agents
        self.agent_executor = Attempt2AgentExecutor(self.llm)
        
        logger.info("✅ Correct Meta System initialized successfully")
    
    def run_correct_workflow(self, user_query: str) -> Dict[str, Any]:
        """
        CORRECT WORKFLOW following user's exact specification:
        1. User types prompt
        2. Follow Meta model - run domain experts  
        3. Till finding workflow - create workflow based on analysis
        4. Then workflow should be called - execute attempt2 agents
        """
        
        conversation_id = uuid.uuid4().hex[:8]
        logger.info(f"🎯 Starting CORRECT workflow for conversation {conversation_id}")
        
        print(f"\n🎯 PROCESSING: {user_query}")
        print(f"🆔 Conversation ID: {conversation_id}")
        
        try:
            # STEP 1: Follow Meta model - Domain expert analysis
            print(f"\n{'='*60}")
            print("🔍 STEP 1: RUNNING 3 DOMAIN EXPERT ANALYSES")
            print(f"{'='*60}")
            
            domain_outputs = self.workflow_manager.execute_domain_analysis(user_query)
            
            print("\n✅ DOMAIN EXPERT ANALYSIS COMPLETED:")
            for domain, output in domain_outputs.items():
                print(f"\n📋 {domain.upper()} DOMAIN EXPERT:")
                print(f"   • Analysis: {len(output.analysis)} characters")
                print(f"   • Key findings: {len(output.key_findings)} items")
                print(f"   • Recommendations: {len(output.recommendations)} items")
                # Show first few key findings
                if output.key_findings:
                    print(f"   • Sample finding: {output.key_findings[0][:100]}...")
            
            # STEP 2: Till finding workflow - Create workflow
            print(f"\n{'='*60}")
            print("🔧 STEP 2: CREATING WORKFLOW BASED ON DOMAIN ANALYSIS")
            print(f"{'='*60}")
            
            workflow_type = self.workflow_manager.create_workflow(user_query, domain_outputs)
            
            print(f"✅ WORKFLOW DECISION MADE: {workflow_type.upper()}")
            
            # Show reasoning
            workflow_descriptions = {
                "pdf": "📄 PDF Report - Comprehensive documentation with all domain insights",
                "diagram": "📊 Pipeline Diagram - Visual workflow representation",
                "powerpoint": "📽️ PowerPoint Presentation - Executive summary format",
                "word": "📝 Word Document - Detailed technical documentation", 
                "project": "💻 Complex Project - Full software implementation"
            }
            print(f"   {workflow_descriptions.get(workflow_type, 'Unknown workflow type')}")
            
            # STEP 3: Execute workflow - Call attempt2 agents
            print(f"\n{'='*60}")
            print(f"🚀 STEP 3: EXECUTING WORKFLOW - CALLING ATTEMPT2 {workflow_type.upper()} AGENT")
            print(f"{'='*60}")
            
            generated_file = None
            if workflow_type == "pdf":
                generated_file = self.agent_executor.generate_pdf_report(user_query, domain_outputs)
            elif workflow_type == "diagram": 
                generated_file = self.agent_executor.generate_pipeline_diagram(user_query, domain_outputs)
            elif workflow_type == "powerpoint":
                generated_file = self.agent_executor.generate_powerpoint_presentation(user_query, domain_outputs)
            elif workflow_type == "word":
                generated_file = self.agent_executor.generate_word_document(user_query, domain_outputs)
            elif workflow_type == "project":
                generated_file = self.agent_executor.generate_complex_project(user_query, domain_outputs)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            # STEP 4: Save complete system state
            system_state = SystemState(
                conversation_id=conversation_id,
                user_query=user_query,
                domain_outputs=domain_outputs,
                workflow_steps={},  # Could expand this later
                final_outputs=[generated_file]
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
                    "timestamp": system_state.timestamp
                }
                json.dump(state_dict, f, indent=2)
            
            print(f"\n{'='*60}")
            print("🎉 META MODEL WORKFLOW COMPLETED SUCCESSFULLY!")
            print(f"{'='*60}")
            
            return {
                "conversation_id": conversation_id,
                "domain_outputs": domain_outputs,
                "workflow_type": workflow_type,
                "generated_file": generated_file,
                "system_state_file": str(state_file)
            }
            
        except Exception as e:pyth
            logger.error(f"Error in correct workflow: {e}")
            raise
    
    def interactive_prompt(self):
        """Simple text prompt interface - NO MENU OPTIONS"""
        print("\n" + "="*70)
        print("🎯 CORRECT META SYSTEM")
        print("="*70)
        print("Meta Model Workflow:")
        print("  User Input → Domain Analysis → Workflow Decision → Agent Execution")
        print()
        print("Using llama3.2 model only - no mock implementations")
        
        while True:
            print("\n" + "="*50)
            user_query = input("📝 Enter your query (or 'quit' to exit): ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not user_query:
                print("❌ Query cannot be empty.")
                continue
            
            try:
                result = self.run_correct_workflow(user_query)
                
                print(f"\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
                print(f"📁 Generated File: {result['generated_file']}")
                print(f"🔧 Workflow Type: {result['workflow_type']}")
                print(f"🆔 Conversation ID: {result['conversation_id']}")
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                logger.error(f"Error processing query: {e}")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """Main function - run the CORRECT meta system"""
    try:
        print("🎯 Starting CORRECT Meta System...")
        print("This follows the exact Meta Model workflow as specified")
        
        # Initialize system  
        system = CorrectMetaSystem()
        
        # Run interactive prompt (NO MENU)
        system.interactive_prompt()
        
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()