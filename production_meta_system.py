#!/usr/bin/env python3
"""
Production Meta AI System - Combines Meta Model Architecture with attempt2 Document Generation
Requirements: Only uses llama3.2 model, no mock implementations
All 5 agents from attempt2 are included: PDF Report, Pipeline Diagram, PowerPoint, Word Document, Complex Code Project
"""

import json
import logging
import os
import sys
import subprocess
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

# Strict requirement: Langchain with Ollama must be available
try:
    from langchain_ollama import OllamaLLM
    from langchain_core.prompts import PromptTemplate
    from langchain.chains import LLMChain
    from langchain.memory import ConversationBufferMemory
    print("✅ Langchain components loaded successfully")
except ImportError as e:
    print("❌ ERROR: Required Langchain components not available.")
    print("This system requires Langchain with Ollama integration.")
    print("Please install: pip install langchain langchain-ollama")
    print(f"Import error: {e}")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data directory for storing outputs
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

@dataclass
class LLMConfig:
    """Configuration for LLM - ONLY LLAMA3.2 ALLOWED"""
    model: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    timeout: int = 60
    temperature: float = 0.7
    
    def get_ollama_llm(self) -> OllamaLLM:
        """Get Ollama LLM instance - only llama3.2"""
        if self.model != "llama3.2":
            raise ValueError(f"Only llama3.2 model is allowed. Got: {self.model}")
        
        try:
            llm = OllamaLLM(
                model=self.model,
                base_url=self.base_url,
                temperature=self.temperature
            )
            # Test the connection
            test_response = llm.invoke("Hello")
            if not test_response:
                raise ConnectionError("No response from llama3.2")
            logger.info(f"✅ Successfully connected to {self.model}")
            return llm
        except Exception as e:
            print(f"❌ ERROR: Cannot connect to llama3.2 model at {self.base_url}")
            print(f"Error: {e}")
            print("Please ensure:")
            print("1. Ollama is running: ollama serve")
            print("2. llama3.2 model is pulled: ollama pull llama3.2")
            sys.exit(1)

# ==============================================================================
# DATA STRUCTURES FROM META MODEL
# ==============================================================================

@dataclass
class DomainExpertInput:
    """Input for a domain expert"""
    user_query: str
    context: Optional[str] = None
    domain_name: str = ""
    additional_instructions: Optional[str] = None
    
@dataclass
class DomainExpertOutput:
    """Output from a domain expert"""
    domain: str
    analysis: str  
    concerns: List[str]
    recommendations: List[str]
    compatibility_notes: Optional[List[str]] = None
    timestamp: str = datetime.now().isoformat()
    
@dataclass
class WorkflowStep:
    """Represents a step in the agent workflow"""
    step_id: str
    agent_type: str
    dependencies: List[str]
    accumulated_prompt: str = ""
    executed: bool = False
    output: Optional[Any] = None

@dataclass
class SystemState:
    """Overall system state"""
    conversation_id: str
    user_query: str
    domain_outputs: Dict[str, DomainExpertOutput]
    workflow_steps: Dict[str, WorkflowStep]
    final_outputs: List[Any]
    timestamp: str = datetime.now().isoformat()

# ==============================================================================
# DOMAIN EXPERTS (FROM META MODEL)
# ==============================================================================

class DomainExpert:
    """Base domain expert class"""
    
    def __init__(self, domain_name: str, llm_config: LLMConfig):
        self.domain_name = domain_name
        self.llm_config = llm_config
        self.llm = llm_config.get_ollama_llm()
        
    def analyze(self, input_data: DomainExpertInput) -> DomainExpertOutput:
        """Analyze input and provide domain-specific insights"""
        raise NotImplementedError("Subclasses must implement analyze method")

class MechanicalDomainExpert(DomainExpert):
    """Mechanical engineering domain expert"""
    
    def __init__(self, llm_config: LLMConfig):
        super().__init__("mechanical", llm_config)
        
    def analyze(self, input_data: DomainExpertInput) -> DomainExpertOutput:
        """Analyze from mechanical engineering perspective"""
        
        prompt = f"""You are a Mechanical Engineering Domain Expert. Analyze the following request from a mechanical engineering perspective:

User Query: {input_data.user_query}
Context: {input_data.context or 'None provided'}

Provide analysis covering:
1. Mechanical design considerations
2. Material requirements and constraints
3. Manufacturing and assembly considerations
4. Performance and reliability factors
5. Safety and regulatory compliance
6. Cost and feasibility analysis

Focus on practical, actionable insights for mechanical aspects."""

        try:
            analysis = self.llm.invoke(prompt)
            
            return DomainExpertOutput(
                domain="mechanical",
                analysis=analysis,
                concerns=["Material compatibility", "Manufacturing feasibility", "Structural integrity"],
                recommendations=["Conduct stress analysis", "Review material specifications", "Consider manufacturing constraints"]
            )
        except Exception as e:
            logger.error(f"Mechanical domain expert analysis failed: {e}")
            raise

class ElectricalDomainExpert(DomainExpert):
    """Electrical engineering domain expert"""
    
    def __init__(self, llm_config: LLMConfig):
        super().__init__("electrical", llm_config)
        
    def analyze(self, input_data: DomainExpertInput) -> DomainExpertOutput:
        """Analyze from electrical engineering perspective"""
        
        prompt = f"""You are an Electrical Engineering Domain Expert. Analyze the following request from an electrical engineering perspective:

User Query: {input_data.user_query}
Context: {input_data.context or 'None provided'}

Provide analysis covering:
1. Electrical system design and architecture
2. Power requirements and distribution
3. Signal processing and communication
4. Control systems and automation
5. Safety standards and compliance (IEC, IEEE, etc.)
6. EMC/EMI considerations
7. Component selection and reliability

Focus on practical, actionable insights for electrical aspects."""

        try:
            analysis = self.llm.invoke(prompt)
            
            return DomainExpertOutput(
                domain="electrical",
                analysis=analysis,
                concerns=["Power consumption", "Signal integrity", "EMI/EMC compliance"],
                recommendations=["Verify power calculations", "Design proper grounding", "Consider EMI shielding"]
            )
        except Exception as e:
            logger.error(f"Electrical domain expert analysis failed: {e}")
            raise

class ProgrammingDomainExpert(DomainExpert):
    """Software/Programming domain expert"""
    
    def __init__(self, llm_config: LLMConfig):
        super().__init__("programming", llm_config)
        
    def analyze(self, input_data: DomainExpertInput) -> DomainExpertOutput:
        """Analyze from software development perspective"""
        
        prompt = f"""You are a Software Development Domain Expert. Analyze the following request from a programming and software architecture perspective:

User Query: {input_data.user_query}
Context: {input_data.context or 'None provided'}

Provide analysis covering:
1. Software architecture and design patterns
2. Programming languages and frameworks
3. Database design and data management
4. API design and integration
5. Security considerations
6. Performance and scalability
7. Testing and deployment strategies
8. Code quality and maintainability

Focus on practical, actionable insights for software development aspects."""

        try:
            analysis = self.llm.invoke(prompt)
            
            return DomainExpertOutput(
                domain="programming",
                analysis=analysis,
                concerns=["Code maintainability", "Security vulnerabilities", "Performance bottlenecks"],
                recommendations=["Implement proper testing", "Follow security best practices", "Design for scalability"]
            )
        except Exception as e:
            logger.error(f"Programming domain expert analysis failed: {e}")
            raise

# ==============================================================================
# DOCUMENT GENERATION PROMPTS (ALL 5 FROM ATTEMPT2)
# ==============================================================================

def get_pdf_generation_prompt(topic: str) -> str:
    """Generate prompt for PDF Report (Agent 1 from attempt2)"""
    return f"""Create a comprehensive PDF report on "{topic}". 

Generate a complete Python script that uses reportlab to create a professional PDF document with the following structure:

1. Title page with report title, date, and author
2. Executive summary (1-2 paragraphs)
3. Table of contents
4. Main content sections (3-5 sections with detailed analysis)
5. Conclusions and recommendations
6. References/Bibliography

The script should:
- Use reportlab library for PDF generation
- Include proper formatting with headers, paragraphs, and bullet points
- Add page numbers and headers/footers
- Include charts or diagrams where relevant
- Generate a file named '{topic.replace(' ', '_')}_report.pdf'

Provide the complete, executable Python script."""

def get_diagram_generation_prompt(topic: str) -> str:
    """Generate prompt for Pipeline Diagram (Agent 2 from attempt2)"""
    return f"""Create a pipeline diagram for "{topic}".

Generate a complete Python script that uses matplotlib and/or other visualization libraries to create a professional pipeline/flowchart diagram with:

1. Clear process flow from start to finish
2. Decision points and branching logic
3. Input/output indicators
4. Process steps with descriptive labels
5. Proper color coding and styling
6. Legend and annotations

The script should:
- Use matplotlib, networkx, or similar libraries
- Create a high-quality PNG image
- Include proper titles, labels, and legends
- Generate a file named '{topic.replace(' ', '_')}_pipeline.png'
- Be visually appealing and professional

Provide the complete, executable Python script."""

def get_ppt_generation_prompt(topic: str) -> str:
    """Generate prompt for PowerPoint Presentation (Agent 3 from attempt2)"""
    return f"""Create a PowerPoint presentation on "{topic}".

Generate a complete Python script that uses python-pptx to create a professional presentation with:

1. Title slide with presentation title and author
2. Agenda/Overview slide
3. 8-12 content slides covering key aspects of the topic
4. Each slide should have:
   - Clear title
   - Bullet points or structured content
   - Relevant information and insights
5. Conclusion/Summary slide
6. Thank you/Questions slide

The script should:
- Use python-pptx library
- Apply consistent formatting and design
- Include proper slide transitions
- Generate a file named '{topic.replace(' ', '_')}_presentation.pptx'
- Create visually appealing slides with good information hierarchy

Provide the complete, executable Python script."""

def get_word_generation_prompt(topic: str) -> str:
    """Generate prompt for Word Document (Agent 4 from attempt2)"""
    return f"""Create a Word document on "{topic}".

Generate a complete Python script that uses python-docx to create a professional Word document with:

1. Cover page with title, author, and date
2. Table of contents (automatically generated)
3. Executive summary
4. Main content organized in sections:
   - Introduction
   - Background/Context
   - Analysis and Discussion
   - Findings and Insights
   - Recommendations
   - Conclusion
5. Proper formatting with:
   - Headers and styles
   - Bullet points and numbering
   - Tables where appropriate
   - Page breaks and sections

The script should:
- Use python-docx library
- Apply professional document formatting
- Include headers, footers, and page numbers
- Generate a file named '{topic.replace(' ', '_')}_document.docx'
- Create a well-structured, readable document

Provide the complete, executable Python script."""

def get_project_generation_prompt(topic: str) -> str:
    """Generate prompt for Complex Code Project (Agent 5 from attempt2)"""
    return f"""Create a complex code project for "{topic}".

Generate a complete Python project structure with multiple files and comprehensive functionality:

Project Structure:
```
{topic.replace(' ', '_')}_project/
├── main.py (entry point)
├── requirements.txt
├── README.md
├── config/
│   └── settings.py
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── engine.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── models/
│       ├── __init__.py
│       └── data_models.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
└── docs/
    └── documentation.md
```

Generate complete code for each file with:
1. Main.py - Entry point with CLI interface
2. Core engine with main functionality
3. Utility functions and helpers
4. Data models and structures
5. Configuration management
6. Comprehensive tests
7. Full documentation
8. Requirements file with dependencies

The project should be:
- Production-ready and executable
- Well-documented with docstrings
- Follow Python best practices
- Include error handling
- Have a clear API and interfaces

Provide the complete code for each file in the project structure."""

# ==============================================================================
# WORKFLOW MANAGER (FROM META MODEL)
# ==============================================================================

class WorkflowManager:
    """Manages the execution workflow of domain experts and agents"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.domain_experts = {
            "mechanical": MechanicalDomainExpert(llm_config),
            "electrical": ElectricalDomainExpert(llm_config),
            "programming": ProgrammingDomainExpert(llm_config)
        }
        
    def execute_domain_analysis(self, user_query: str, context: str = None) -> Dict[str, DomainExpertOutput]:
        """Execute analysis by all domain experts"""
        logger.info("Starting domain expert analysis...")
        
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

# ==============================================================================
# DOCUMENT GENERATOR (ALL 5 AGENTS FROM ATTEMPT2)
# ==============================================================================

class DocumentGenerator:
    """Generates different types of documents using llama3.2"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.llm = llm_config.get_ollama_llm()
        
    def generate_pdf_report(self, topic: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Generate PDF report (Agent 1)"""
        logger.info(f"Generating PDF report for: {topic}")
        
        # Combine domain insights
        combined_analysis = self._combine_domain_insights(domain_outputs)
        enhanced_topic = f"{topic} - incorporating {combined_analysis}"
        
        prompt = get_pdf_generation_prompt(enhanced_topic)
        
        try:
            script_content = self.llm.invoke(prompt)
            
            # Save the generated script
            script_file = DATA_DIR / f"pdf_generator_{uuid.uuid4().hex[:8]}.py"
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            logger.info(f"PDF generation script saved to: {script_file}")
            return str(script_file)
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    def generate_pipeline_diagram(self, topic: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Generate pipeline diagram (Agent 2)"""
        logger.info(f"Generating pipeline diagram for: {topic}")
        
        combined_analysis = self._combine_domain_insights(domain_outputs)
        enhanced_topic = f"{topic} - incorporating {combined_analysis}"
        
        prompt = get_diagram_generation_prompt(enhanced_topic)
        
        try:
            script_content = self.llm.invoke(prompt)
            
            script_file = DATA_DIR / f"diagram_generator_{uuid.uuid4().hex[:8]}.py"
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            logger.info(f"Diagram generation script saved to: {script_file}")
            return str(script_file)
            
        except Exception as e:
            logger.error(f"Error generating pipeline diagram: {e}")
            raise
    
    def generate_powerpoint_presentation(self, topic: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Generate PowerPoint presentation (Agent 3)"""
        logger.info(f"Generating PowerPoint presentation for: {topic}")
        
        combined_analysis = self._combine_domain_insights(domain_outputs)
        enhanced_topic = f"{topic} - incorporating {combined_analysis}"
        
        prompt = get_ppt_generation_prompt(enhanced_topic)
        
        try:
            script_content = self.llm.invoke(prompt)
            
            script_file = DATA_DIR / f"ppt_generator_{uuid.uuid4().hex[:8]}.py"
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            logger.info(f"PowerPoint generation script saved to: {script_file}")
            return str(script_file)
            
        except Exception as e:
            logger.error(f"Error generating PowerPoint presentation: {e}")
            raise
    
    def generate_word_document(self, topic: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Generate Word document (Agent 4)"""
        logger.info(f"Generating Word document for: {topic}")
        
        combined_analysis = self._combine_domain_insights(domain_outputs)
        enhanced_topic = f"{topic} - incorporating {combined_analysis}"
        
        prompt = get_word_generation_prompt(enhanced_topic)
        
        try:
            script_content = self.llm.invoke(prompt)
            
            script_file = DATA_DIR / f"word_generator_{uuid.uuid4().hex[:8]}.py"
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            logger.info(f"Word generation script saved to: {script_file}")
            return str(script_file)
            
        except Exception as e:
            logger.error(f"Error generating Word document: {e}")
            raise
    
    def generate_complex_project(self, topic: str, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Generate complex code project (Agent 5)"""
        logger.info(f"Generating complex code project for: {topic}")
        
        combined_analysis = self._combine_domain_insights(domain_outputs)
        enhanced_topic = f"{topic} - incorporating {combined_analysis}"
        
        prompt = get_project_generation_prompt(enhanced_topic)
        
        try:
            project_content = self.llm.invoke(prompt)
            
            project_file = DATA_DIR / f"project_generator_{uuid.uuid4().hex[:8]}.py"
            with open(project_file, 'w') as f:
                f.write(project_content)
            
            logger.info(f"Project generation script saved to: {project_file}")
            return str(project_file)
            
        except Exception as e:
            logger.error(f"Error generating complex project: {e}")
            raise
    
    def _combine_domain_insights(self, domain_outputs: Dict[str, DomainExpertOutput]) -> str:
        """Combine insights from all domain experts"""
        insights = []
        for domain, output in domain_outputs.items():
            insights.append(f"{domain.title()}: {output.analysis[:200]}...")
        return " | ".join(insights)

# ==============================================================================
# MAIN SYSTEM CLASS
# ==============================================================================

class ProductionMetaSystem:
    """Main system combining Meta Model approach with attempt2 document generation"""
    
    def __init__(self):
        """Initialize the production system with llama3.2 only"""
        print("🚀 Initializing Production Meta System...")
        print("📋 Requirements: llama3.2 model only, no mocks allowed")
        
        # Initialize LLM configuration - ONLY LLAMA3.2
        self.llm_config = LLMConfig(model="llama3.2")
        
        # Initialize components
        self.workflow_manager = WorkflowManager(self.llm_config)
        self.document_generator = DocumentGenerator(self.llm_config)
        
        print("✅ Production Meta System initialized successfully!")
        print("🤖 All 5 agents from attempt2 are available:")
        print("   1. PDF Report Generator")
        print("   2. Pipeline Diagram Generator") 
        print("   3. PowerPoint Presentation Generator")
        print("   4. Word Document Generator")
        print("   5. Complex Code Project Generator")
    
    def run_full_analysis_and_generation(self, user_query: str, document_type: str) -> Dict[str, Any]:
        """Run complete workflow: domain analysis + document generation"""
        
        conversation_id = uuid.uuid4().hex[:8]
        logger.info(f"Starting full analysis for conversation {conversation_id}")
        
        try:
            # Step 1: Domain expert analysis (Meta Model approach)
            print("\n🔍 Step 1: Running domain expert analysis...")
            domain_outputs = self.workflow_manager.execute_domain_analysis(user_query)
            
            # Step 2: Generate document based on type (attempt2 agents)
            print(f"\n📄 Step 2: Generating {document_type}...")
            generated_file = None
            
            if document_type == "pdf":
                generated_file = self.document_generator.generate_pdf_report(user_query, domain_outputs)
            elif document_type == "diagram":
                generated_file = self.document_generator.generate_pipeline_diagram(user_query, domain_outputs)
            elif document_type == "powerpoint":
                generated_file = self.document_generator.generate_powerpoint_presentation(user_query, domain_outputs)
            elif document_type == "word":
                generated_file = self.document_generator.generate_word_document(user_query, domain_outputs)
            elif document_type == "project":
                generated_file = self.document_generator.generate_complex_project(user_query, domain_outputs)
            else:
                raise ValueError(f"Unknown document type: {document_type}")
            
            # Step 3: Save complete system state
            system_state = SystemState(
                conversation_id=conversation_id,
                user_query=user_query,
                domain_outputs=domain_outputs,
                workflow_steps={},
                final_outputs=[generated_file]
            )
            
            state_file = DATA_DIR / f"system_state_{conversation_id}.json"
            with open(state_file, 'w') as f:
                # Convert to serializable format
                state_dict = {
                    "conversation_id": system_state.conversation_id,
                    "user_query": system_state.user_query,
                    "domain_outputs": {k: asdict(v) for k, v in system_state.domain_outputs.items()},
                    "final_outputs": system_state.final_outputs,
                    "timestamp": system_state.timestamp
                }
                json.dump(state_dict, f, indent=2)
            
            print(f"\n✅ Complete workflow finished!")
            print(f"💾 System state saved to: {state_file}")
            print(f"📁 Generated file: {generated_file}")
            
            return {
                "conversation_id": conversation_id,
                "domain_outputs": domain_outputs,
                "generated_file": generated_file,
                "system_state_file": str(state_file)
            }
            
        except Exception as e:
            logger.error(f"Error in full analysis and generation: {e}")
            raise
    
    def interactive_menu(self):
        """Interactive menu system (like attempt2)"""
        print("\n" + "="*60)
        print("🤖 PRODUCTION META SYSTEM - INTERACTIVE MENU")
        print("="*60)
        print("This system combines Meta Model domain analysis with document generation")
        print("Using llama3.2 model only - no mock implementations")
        
        while True:
            print("\n📋 Select document type to generate:")
            print("  1. PDF Report")
            print("  2. Pipeline Diagram (PNG)")
            print("  3. PowerPoint Presentation (PPTX)")
            print("  4. Word Document (DOCX)")
            print("  5. Complex Code Project")
            print("  6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '6':
                print("👋 Goodbye!")
                break
            
            if choice not in ['1', '2', '3', '4', '5']:
                print("❌ Invalid choice. Please select 1-6.")
                continue
            
            # Get user query
            user_query = input("\n📝 Enter your query/topic: ").strip()
            if not user_query:
                print("❌ Query cannot be empty.")
                continue
            
            # Map choice to document type
            doc_type_map = {
                '1': 'pdf',
                '2': 'diagram', 
                '3': 'powerpoint',
                '4': 'word',
                '5': 'project'
            }
            
            document_type = doc_type_map[choice]
            
            try:
                print(f"\n🚀 Processing: {user_query}")
                print(f"📄 Generating: {document_type}")
                
                result = self.run_full_analysis_and_generation(user_query, document_type)
                
                print(f"\n🎉 SUCCESS!")
                print(f"🆔 Conversation ID: {result['conversation_id']}")
                print(f"📁 Generated file: {result['generated_file']}")
                print(f"💾 System state: {result['system_state_file']}")
                
                print(f"\n📊 Domain Analysis Summary:")
                for domain, output in result['domain_outputs'].items():
                    print(f"  • {domain.title()}: {len(output.analysis)} characters of analysis")
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                logger.error(f"Error processing request: {e}")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """Main function to run the production meta system"""
    try:
        # Initialize system
        system = ProductionMetaSystem()
        
        # Run interactive menu
        system.interactive_menu()
        
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()