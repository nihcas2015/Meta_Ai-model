# Combined Meta AI System - Integrating Meta Model and Document Generator
# This combines the advanced meta-model architecture with document generation capabilities

import os
import sys
import subprocess
import json
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

# Document generation imports
from openai import OpenAI
from dotenv import load_dotenv

# Langchain imports
try:
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
    from langchain.schema import SystemMessage, HumanMessage, AIMessage
    from langchain.chains import LLMChain
    from langchain.memory import ConversationBufferMemory
    from langchain.llms import Ollama
    LANGCHAIN_AVAILABLE = True
    print("✅ Langchain available for agent coordination")
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ Langchain not installed. Install with: pip install langchain")

# HTTP client for API interactions  
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
    print("✅ aiohttp available for API interactions")
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️ aiohttp not installed. Install with: pip install aiohttp")

# Constants
MAX_RETRIES = 3
USE_REAL_OLLAMA = False  # Set to True if you have Ollama running locally

# Create storage directory for outputs if it doesn't exist
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)
print("✅ Basic imports loaded successfully!")

# ==============================================================================
# --- CONFIGURATION CLASSES ---
# ==============================================================================

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    base_url: str
    timeout: int = 60
    temperature: float = 0.7
    
@dataclass 
class LLMConfig:
    """Configuration for LLM usage"""
    model: str = "llama3.1"
    base_url: str = "http://localhost:11434"
    timeout: int = 60
    temperature: float = 0.7
    use_real_ollama: bool = USE_REAL_OLLAMA
    
    def get_langchain_llm(self):
        """Get Langchain LLM instance"""
        if not LANGCHAIN_AVAILABLE:
            return MockOllamaLLM()
        
        if self.use_real_ollama:
            return Ollama(
                model=self.model,
                base_url=self.base_url,
                temperature=self.temperature
            )
        else:
            return MockOllamaLLM()

# ==============================================================================
# --- CORE DATA STRUCTURES (Exact copy from Meta_model.ipynb) ---
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
class GeneratedPrompt:
    """Container for generated prompts"""
    prompt_type: str  # 'domain' or 'agent'
    agent_name: str
    prompt_content: str
    timestamp: str = datetime.now().isoformat()
    file_path: Optional[str] = None
    
@dataclass
class WorkflowStep:
    """Represents a step in the agent workflow"""
    step_id: str
    agent_type: str
    dependencies: List[str]  # List of step_ids this step depends on
    accumulated_prompt: str = ""  # Combined prompt from all previous steps
    generated_prompt: Optional[GeneratedPrompt] = None
    executed: bool = False
    output: Optional[Any] = None

@dataclass
class AgentExecutionRequest:
    """Request to execute a specific agent"""
    agent_type: str
    user_query: str
    domain_outputs: Dict[str, DomainExpertOutput]
    workflow_context: Dict[str, WorkflowStep] = None
    specific_instructions: Optional[str] = None
    
@dataclass
class AgentOutput:
    """Output from a specific agent"""
    agent_type: str
    content: Any
    format: str
    file_path: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = datetime.now().isoformat()
    
@dataclass
class SystemState:
    """Overall system state"""
    conversation_id: str
    user_query: str
    domain_outputs: Dict[str, DomainExpertOutput]
    agent_outputs: Dict[str, AgentOutput] 
    conversation_history: List[Dict[str, str]]
    generated_prompts: Dict[str, GeneratedPrompt] = None
    workflow_steps: Dict[str, WorkflowStep] = None
    last_updated: str = datetime.now().isoformat()
    
    def __post_init__(self):
        """Initialize default values"""
        if self.generated_prompts is None:
            self.generated_prompts = {}
        if self.workflow_steps is None:
            self.workflow_steps = {}
    
    def save_to_json(self, file_path: Optional[str] = None) -> str:
        """Save system state to JSON file"""
        if file_path is None:
            file_path = f"./data/system_state_{self.conversation_id[:8]}.json"
        
        # Convert to dictionary with proper serialization
        state_dict = {
            "conversation_id": self.conversation_id,
            "user_query": self.user_query,
            "domain_outputs": {k: asdict(v) for k, v in self.domain_outputs.items()},
            "agent_outputs": {k: asdict(v) for k, v in self.agent_outputs.items()},
            "conversation_history": self.conversation_history,
            "generated_prompts": {k: asdict(v) for k, v in self.generated_prompts.items()},
            "workflow_steps": {k: asdict(v) for k, v in self.workflow_steps.items()},
            "last_updated": self.last_updated
        }
        
        with open(file_path, 'w') as f:
            json.dump(state_dict, f, indent=2)
        
        return file_path
    
    @classmethod
    def load_from_json(cls, file_path: str) -> 'SystemState':
        """Load system state from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert dictionaries back to dataclasses
        domain_outputs = {k: DomainExpertOutput(**v) for k, v in data['domain_outputs'].items()}
        agent_outputs = {k: AgentOutput(**v) for k, v in data['agent_outputs'].items()}
        generated_prompts = {k: GeneratedPrompt(**v) for k, v in data.get('generated_prompts', {}).items()}
        workflow_steps = {k: WorkflowStep(**v) for k, v in data.get('workflow_steps', {}).items()}
        
        return cls(
            conversation_id=data['conversation_id'],
            user_query=data['user_query'],
            domain_outputs=domain_outputs,
            agent_outputs=agent_outputs,
            conversation_history=data['conversation_history'],
            generated_prompts=generated_prompts,
            workflow_steps=workflow_steps,
            last_updated=data['last_updated']
        )

# Define domain expert types
class DomainType(Enum):
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PROGRAMMING = "programming"
    
# Define agent types
class AgentType(Enum):
    DIAGRAM = "diagram"
    PRESENTATION = "presentation"
    DOCUMENT = "document"
    PDF = "pdf"
    CODE = "code"

# ==============================================================================
# --- MOCK IMPLEMENTATIONS ---
# ==============================================================================

class MockOllamaLLM:
    """Mock implementation for testing without Ollama"""
    def __init__(self):
        self.model = "mock-llama"
    
    async def ainvoke(self, prompt, **kwargs):
        """Mock async invocation"""
        await asyncio.sleep(0.1)  # Simulate processing time
        return {"text": "Mock response from domain expert LLM"}
    
    def invoke(self, prompt, **kwargs):
        """Mock sync invocation"""
        return "Mock response from LLM"

# ==============================================================================
# --- OPENAI CLIENT SETUP (from attempt2.py) ---
# ==============================================================================

def setup_openai_client():
    """Setup OpenAI client for document generation"""
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY", "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")
    
    if not api_key or api_key == "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":
        print("WARNING: Using default API key for demo purposes.")
        print("Please create a .env file with OPENROUTER_API_KEY='your-key' for production use.")
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    return client

# ==============================================================================
# --- WORKFLOW MANAGER (Exact copy from Meta_model.ipynb) ---
# ==============================================================================

class WorkflowManager:
    """Manages sequential workflow execution with prompt chaining"""
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.workflow_steps = {}
        self.execution_order = []
        
    def create_workflow(self, agent_types: List[str]) -> Dict[str, WorkflowStep]:
        """Create a sequential workflow for the given agent types"""
        self.workflow_steps = {}
        self.execution_order = agent_types.copy()
        
        for i, agent_type in enumerate(agent_types):
            step_id = f"step_{i+1}_{agent_type}"
            dependencies = [f"step_{i}_{agent_types[i-1]}"] if i > 0 else []
            
            self.workflow_steps[step_id] = WorkflowStep(
                step_id=step_id,
                agent_type=agent_type,
                dependencies=dependencies
            )
        
        return self.workflow_steps
    
    def get_accumulated_prompt(self, step_id: str, domain_prompts: Dict[str, str]) -> str:
        """Get accumulated prompt for a specific step"""
        step = self.workflow_steps[step_id]
        accumulated_prompt = ""
        
        # Add domain expert prompts first
        domain_section = "DOMAIN EXPERT ANALYSES:\\n\\n"
        for domain, prompt in domain_prompts.items():
            domain_section += f"=== {domain.upper()} DOMAIN ANALYSIS ===\\n{prompt}\\n\\n"
        
        accumulated_prompt += domain_section
        
        # Add previous agent prompts
        current_step_index = self.execution_order.index(step.agent_type)
        if current_step_index > 0:
            agent_section = "PREVIOUS AGENT PROMPTS:\\n\\n"
            for i in range(current_step_index):
                prev_agent_type = self.execution_order[i]
                prev_step_id = f"step_{i+1}_{prev_agent_type}"
                prev_step = self.workflow_steps[prev_step_id]
                
                if prev_step.generated_prompt:
                    agent_section += f"=== {prev_agent_type.upper()} AGENT PROMPT ===\\n"
                    agent_section += f"{prev_step.generated_prompt.prompt_content}\\n\\n"
            
            accumulated_prompt += agent_section
        
        return accumulated_prompt
    
    def update_step_prompt(self, step_id: str, generated_prompt: GeneratedPrompt):
        """Update a workflow step with generated prompt"""
        if step_id in self.workflow_steps:
            self.workflow_steps[step_id].generated_prompt = generated_prompt
            self.workflow_steps[step_id].accumulated_prompt = generated_prompt.prompt_content
    
    def mark_step_executed(self, step_id: str, output: Any):
        """Mark a step as executed with output"""
        if step_id in self.workflow_steps:
            self.workflow_steps[step_id].executed = True
            self.workflow_steps[step_id].output = output
    
    def get_steps_to_redo(self, changed_step_id: str) -> List[str]:
        """Get list of steps that need to be redone after a change"""
        changed_step_index = None
        for i, agent_type in enumerate(self.execution_order):
            step_id = f"step_{i+1}_{agent_type}"
            if step_id == changed_step_id:
                changed_step_index = i
                break
        
        if changed_step_index is None:
            return []
        
        # Return all steps from the changed step onwards
        steps_to_redo = []
        for i in range(changed_step_index, len(self.execution_order)):
            agent_type = self.execution_order[i]
            step_id = f"step_{i+1}_{agent_type}"
            steps_to_redo.append(step_id)
        
        return steps_to_redo
    
    def reset_steps(self, step_ids: List[str]):
        """Reset specified steps to unexecuted state"""
        for step_id in step_ids:
            if step_id in self.workflow_steps:
                self.workflow_steps[step_id].executed = False
                self.workflow_steps[step_id].output = None

print("✅ Workflow manager implemented!")

# ==============================================================================
# --- DOMAIN EXPERTS (Exact copy from Meta_model.ipynb) ---
# ==============================================================================

class DomainExpert:
    """Base class for domain experts"""
    
    def __init__(self, domain_type: DomainType, llm_config: LLMConfig):
        self.domain_type = domain_type
        self.llm = llm_config.get_langchain_llm()
        self.system_prompt = self._get_domain_system_prompt()
        
    def _get_domain_system_prompt(self) -> str:
        """Get domain-specific system prompt"""
        if self.domain_type == DomainType.MECHANICAL:
            return """You are an expert Mechanical Engineer with extensive experience in designing physical systems, 
mechanisms, structures, and manufacturing processes. Think exclusively from a mechanical engineering perspective.

When analyzing problems:
1. Focus on physical principles, materials, structural integrity, and mechanical systems.
2. Consider forces, stresses, thermal effects, vibration, and material properties.
3. Evaluate manufacturability, assembly, maintenance, and mechanical reliability.
4. Identify potential mechanical failure points and physical constraints.
5. Always prioritize safety, durability, and mechanical efficiency.

Provide specific mechanical engineering insights with technical depth. Don't discuss electrical or software aspects 
unless they directly impact the mechanical design. Use precise mechanical engineering terminology.

Your analysis should include:
- Core mechanical principles that apply
- Material recommendations
- Structural considerations
- Thermal and vibration management
- Manufacturing approach
- Mechanical limitations and concerns"""

        elif self.domain_type == DomainType.ELECTRICAL:
            return """You are an expert Electrical Engineer with extensive experience in designing circuits, power systems, 
and electronic components. Think exclusively from an electrical engineering perspective.

When analyzing problems:
1. Focus on electrical principles, circuit design, power distribution, and signal integrity.
2. Consider voltage levels, current requirements, power management, and EMI/EMC concerns.
3. Evaluate electrical components, PCB design, wiring, and electrical safety.
4. Identify potential electrical failure modes and constraints.
5. Always prioritize electrical safety, reliability, and efficiency.

Provide specific electrical engineering insights with technical depth. Don't discuss mechanical or software aspects 
unless they directly impact the electrical design. Use precise electrical engineering terminology.

Your analysis should include:
- Power requirements and distribution
- Circuit design considerations
- Component selection guidelines
- Signal integrity and noise concerns
- Electrical safety measures
- Testing and validation approaches"""

        elif self.domain_type == DomainType.PROGRAMMING:
            return """You are an expert Software Engineer with extensive experience in designing software architectures, 
algorithms, and embedded systems. Think exclusively from a software engineering perspective.

When analyzing problems:
1. Focus on software architecture, data structures, algorithms, and system design.
2. Consider execution efficiency, memory usage, maintainability, and scalability.
3. Evaluate appropriate programming languages, frameworks, and development methodologies.
4. Identify potential software failure modes and technical debt.
5. Always prioritize code quality, maintainability, and performance.

Provide specific software engineering insights with technical depth. Don't discuss mechanical or electrical aspects 
unless they directly impact the software design. Use precise software engineering terminology.

Your analysis should include:
- Software architecture recommendations
- Data structure and algorithm considerations
- Language and framework selection
- Testing strategies
- Error handling approaches
- Performance optimization opportunities"""
        
        else:
            return "You are an engineering expert. Analyze the problem and provide technical insights."

    async def analyze(self, input_data: DomainExpertInput, conversation_id: str) -> tuple[DomainExpertOutput, GeneratedPrompt]:
        """Analyze the input from domain perspective and return both output and generated prompt"""
        
        # Create the prompt for this domain analysis
        context_section = f"ADDITIONAL CONTEXT:\\n{input_data.context}" if input_data.context else ""
        instructions_section = f"SPECIFIC INSTRUCTIONS:\\n{input_data.additional_instructions}" if input_data.additional_instructions else ""
        
        analysis_prompt = f"""
Analyze this requirement from your {self.domain_type.value} engineering perspective:

USER REQUIREMENT:
{input_data.user_query}

{context_section}

{instructions_section}

Provide your analysis in this format:
1. Core principles and considerations from your domain
2. Key concerns and potential issues
3. Specific recommendations and approaches

Be thorough, technical, and focus exclusively on {self.domain_type.value} engineering aspects.
"""

        # Save the generated prompt
        generated_prompt = GeneratedPrompt(
            prompt_type="domain",
            agent_name=f"{self.domain_type.value}_expert",
            prompt_content=analysis_prompt,
            timestamp=datetime.now().isoformat()
        )
        
        # Save prompt to file
        prompt_filename = f"{self.domain_type.value}_domain_prompt_{conversation_id[:8]}.txt"
        prompt_file_path = f"./data/{prompt_filename}"
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.domain_type.value.upper()} DOMAIN EXPERT PROMPT\\n")
            f.write(f"# Generated: {generated_prompt.timestamp}\\n\\n")
            f.write(analysis_prompt)
        
        generated_prompt.file_path = prompt_file_path
        
        # Create the actual LLM prompt template
        if LANGCHAIN_AVAILABLE:
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ])
            
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            
            # Time the execution
            start_time = datetime.now()
            result = await chain.ainvoke({"input": input_data})
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Process the output
            analysis = result['text'] if isinstance(result, dict) and 'text' in result else str(result)
        else:
            # Mock analysis when Langchain not available
            analysis = f"""Mock {self.domain_type.value} engineering analysis:

1. Core Principles:
- Technical assessment from {self.domain_type.value} perspective
- Key engineering considerations identified
- Domain-specific approach outlined

2. Key Concerns:
- Primary technical challenges in {self.domain_type.value} domain
- Potential failure modes and risks
- Performance and reliability considerations

3. Recommendations:
- Best practices for {self.domain_type.value} implementation
- Suggested approaches and methodologies
- Integration considerations with other domains

Analysis for: {input_data.user_query[:200]}{'...' if len(input_data.user_query) > 200 else ''}
"""
        
        # Extract key points
        concerns = self._extract_concerns(analysis)
        recommendations = self._extract_recommendations(analysis)
        
        domain_output = DomainExpertOutput(
            domain=self.domain_type.value,
            analysis=analysis,
            concerns=concerns,
            recommendations=recommendations
        )
        
        return domain_output, generated_prompt
    
    def _extract_concerns(self, analysis: str) -> List[str]:
        """Extract key concerns from analysis"""
        concerns = []
        lines = analysis.split('\\n')
        in_concerns_section = False
        
        for line in lines:
            if "concerns" in line.lower() or "issues" in line.lower():
                in_concerns_section = True
                continue
                
            if in_concerns_section and (line.strip() == "" or "recommendations" in line.lower()):
                in_concerns_section = False
                continue
                
            if in_concerns_section and line.strip():
                # Clean up bullet points and numbering
                clean_line = line.strip()
                for prefix in ['-', '•', '*', '○', '➢', '→']:
                    if clean_line.startswith(prefix):
                        clean_line = clean_line[1:].strip()
                        
                # Remove numbering like "1." or "1)"
                if clean_line and clean_line[0].isdigit() and clean_line[1:3] in ['. ', ') ']:
                    clean_line = clean_line[3:].strip()
                    
                if clean_line:
                    concerns.append(clean_line)
        
        # If we couldn't extract structured concerns, do a simpler extraction
        if not concerns:
            concerns = [line.strip() for line in analysis.split('\\n') 
                     if "concern" in line.lower() or "issue" in line.lower()]
        
        return concerns[:5]  # Limit to top 5 concerns
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract recommendations from analysis"""
        recommendations = []
        lines = analysis.split('\\n')
        in_recommendations_section = False
        
        for line in lines:
            if "recommendation" in line.lower() or "approach" in line.lower() or "suggest" in line.lower():
                in_recommendations_section = True
                continue
                
            if in_recommendations_section and line.strip() == "":
                in_recommendations_section = False
                continue
                
            if in_recommendations_section and line.strip():
                # Clean up bullet points and numbering
                clean_line = line.strip()
                for prefix in ['-', '•', '*', '○', '➢', '→']:
                    if clean_line.startswith(prefix):
                        clean_line = clean_line[1:].strip()
                        
                # Remove numbering like "1." or "1)"
                if clean_line and clean_line[0].isdigit() and clean_line[1:3] in ['. ', ') ']:
                    clean_line = clean_line[3:].strip()
                    
                if clean_line:
                    recommendations.append(clean_line)
        
        # If we couldn't extract structured recommendations, do a simpler extraction
        if not recommendations:
            recommendations = [line.strip() for line in analysis.split('\\n') 
                           if "recommend" in line.lower() or "should" in line.lower() or "must" in line.lower()]
        
        return recommendations[:5]  # Limit to top 5 recommendations

# Create domain experts
async def setup_domain_experts(llm_config: LLMConfig) -> Dict[str, DomainExpert]:
    """Setup all domain experts"""
    mechanical_expert = DomainExpert(DomainType.MECHANICAL, llm_config)
    electrical_expert = DomainExpert(DomainType.ELECTRICAL, llm_config) 
    programming_expert = DomainExpert(DomainType.PROGRAMMING, llm_config)
    
    return {
        "mechanical": mechanical_expert,
        "electrical": electrical_expert,
        "programming": programming_expert
    }

print("✅ Domain experts implementation with prompt saving ready!")

# ==============================================================================
# --- DOMAIN INTEGRATION SYSTEM (Exact copy from Meta_model.ipynb) ---
# ==============================================================================

class DomainIntegrator:
    """System for integrating analyses across domains"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_langchain_llm()
    
    async def integrate_domain_analyses(
        self, 
        user_query: str,
        domain_outputs: Dict[str, DomainExpertOutput]
    ) -> Dict[str, Any]:
        """Integrate analyses from different domains"""
        
        if LANGCHAIN_AVAILABLE:
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert engineering integration specialist who understands 
                mechanical, electrical, and software engineering deeply.
                
                Your task is to analyze separate domain-specific assessments and identify:
                1. Areas of compatibility and alignment between domains
                2. Potential conflicts or contradictions between domains
                3. Integration challenges that must be addressed
                4. Cross-domain risks and dependencies
                5. Unified recommendations that satisfy all domains
                
                Provide a balanced perspective that respects the expertise of each domain
                while finding optimal integration solutions."""),
                
                HumanMessage(content=f"""
                Analyze these domain-specific assessments for the following project:
                
                USER REQUIREMENT:
                {user_query}
                
                MECHANICAL ENGINEERING ASSESSMENT:
                {domain_outputs["mechanical"].analysis if "mechanical" in domain_outputs else "No mechanical assessment provided"}
                
                ELECTRICAL ENGINEERING ASSESSMENT:
                {domain_outputs["electrical"].analysis if "electrical" in domain_outputs else "No electrical assessment provided"}
                
                SOFTWARE ENGINEERING ASSESSMENT:
                {domain_outputs["programming"].analysis if "programming" in domain_outputs else "No software assessment provided"}
                
                Create a comprehensive integration analysis that:
                1. Identifies cross-domain compatibility issues
                2. Highlights contradictions between domain recommendations
                3. Provides a unified set of recommendations that satisfies requirements from all domains
                4. Suggests any necessary trade-offs or compromises
                
                Format your response to clearly address cross-domain integration.
                """)
            ])
            
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            
            result = await chain.ainvoke({})
            integration_analysis = result['text'] if isinstance(result, dict) and 'text' in result else str(result)
        else:
            # Mock integration analysis when Langchain not available
            integration_analysis = f"""Mock Integration Analysis:

            Cross-Domain Compatibility Assessment:
            - Mechanical, electrical, and software requirements have been analyzed
            - Key integration points identified between domains
            - Compatibility matrix developed for system components

            Identified Conflicts:
            - No major contradictions found between domain requirements
            - Minor alignment needed between power requirements and mechanical constraints
            - Software architecture should accommodate hardware limitations

            Unified Recommendations:
            - Integrated design approach recommended
            - Cross-domain testing protocols needed
            - Collaborative development methodology suggested
            
            Analysis for: {user_query[:200]}{'...' if len(user_query) > 200 else ''}
            """
        
        # Build integration report
        integration_report = {
            "integration_analysis": integration_analysis,
            "cross_domain_issues": self._extract_cross_domain_issues(integration_analysis),
            "unified_recommendations": self._extract_unified_recommendations(integration_analysis),
            "timestamp": datetime.now().isoformat()
        }
        
        return integration_report
    
    def _extract_cross_domain_issues(self, analysis: str) -> List[str]:
        """Extract cross-domain issues from integration analysis"""
        issues = []
        lines = analysis.split('\\n')
        in_issues_section = False
        
        for line in lines:
            if any(phrase in line.lower() for phrase in ["cross-domain issue", "conflict", "contradiction", "integration challenge"]):
                in_issues_section = True
                continue
                
            if in_issues_section and (line.strip() == "" or any(phrase in line.lower() for phrase in ["recommendation", "conclusion"])):
                in_issues_section = False
                continue
                
            if in_issues_section and line.strip():
                clean_line = self._clean_bullet_point(line)
                if clean_line:
                    issues.append(clean_line)
        
        # If we couldn't extract structured issues, do a simpler extraction
        if not issues:
            issues = [line.strip() for line in analysis.split('\\n')
                      if any(phrase in line.lower() for phrase in ["conflict", "contradiction", "issue"])]
        
        return issues[:7]  # Limit to top 7 issues
    
    def _extract_unified_recommendations(self, analysis: str) -> List[str]:
        """Extract unified recommendations from integration analysis"""
        recommendations = []
        lines = analysis.split('\\n')
        in_recommendations_section = False
        
        for line in lines:
            if any(phrase in line.lower() for phrase in ["unified recommendation", "integrated approach"]):
                in_recommendations_section = True
                continue
                
            if in_recommendations_section and line.strip() == "":
                in_recommendations_section = False
                continue
                
            if in_recommendations_section and line.strip():
                clean_line = self._clean_bullet_point(line)
                if clean_line:
                    recommendations.append(clean_line)
        
        # If we couldn't extract structured recommendations, do a simpler extraction
        if not recommendations:
            recommendations = [line.strip() for line in analysis.split('\\n')
                           if any(phrase in line.lower() for phrase in ["recommend", "should", "approach"])]
        
        return recommendations[:7]  # Limit to top 7 recommendations
    
    def _clean_bullet_point(self, line: str) -> str:
        """Clean up bullet points and numbering from a line"""
        clean_line = line.strip()
        
        for prefix in ['-', '•', '*', '○', '➢', '→']:
            if clean_line.startswith(prefix):
                clean_line = clean_line[1:].strip()
                
        # Remove numbering like "1." or "1)"
        if clean_line and clean_line[0].isdigit() and len(clean_line) > 2:
            if clean_line[1:3] in ['. ', ') ']:
                clean_line = clean_line[3:].strip()
                
        return clean_line

print("✅ Domain integration system ready!")

# ==============================================================================
# --- AGENT PROMPT GENERATOR (Exact copy from Meta_model.ipynb) ---
# ==============================================================================

class AgentPromptGenerator:
    """Generates specialized prompts for different agents with workflow context"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_langchain_llm()
    
    async def generate_agent_prompt(
        self,
        agent_type: AgentType,
        user_query: str,
        workflow_manager: WorkflowManager,
        step_id: str,
        domain_prompts: Dict[str, str],
        integration_report: Dict[str, Any],
        specific_instructions: Optional[str] = None
    ) -> GeneratedPrompt:
        """Generate specialized prompt for specific agent type with workflow context"""
        
        # Get accumulated context from workflow
        accumulated_prompt = workflow_manager.get_accumulated_prompt(step_id, domain_prompts)
        
        # Get agent-specific system instructions
        system_instruction = self._get_agent_system_instruction(agent_type)
        
        # Integration insights
        integration_insights = f"""
CROSS-DOMAIN INTEGRATION INSIGHTS:
{integration_report['integration_analysis'][:500]}...

Key integration issues: {', '.join(integration_report['cross_domain_issues'][:3])}
Unified recommendations: {', '.join(integration_report['unified_recommendations'][:3])}
"""
        
        # Create the comprehensive prompt
        instructions_section = f"SPECIFIC INSTRUCTIONS FOR THIS AGENT:\\n{specific_instructions}" if specific_instructions else ""
        
        agent_prompt_content = f"""
{system_instruction}

ORIGINAL USER REQUEST:
{user_query}

{accumulated_prompt}

{integration_insights}

{instructions_section}

TASK:
Based on all the above context and analyses, create content that addresses the user's original request.
Incorporate insights from all domain experts and previous agent work to create a comprehensive output.
Ensure your output builds upon and complements the work done by previous agents in the workflow.
"""
        
        # Generate enhanced prompt using LLM (if available)
        if LANGCHAIN_AVAILABLE:
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""You are a prompt engineering specialist for {agent_type.value} creation.
                Create an optimized prompt for a specialized {agent_type.value} generation agent that incorporates
                all the provided context and produces the best possible {agent_type.value}."""),
                
                HumanMessage(content=agent_prompt_content)
            ])
            
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            result = await chain.ainvoke({})
            
            enhanced_prompt = result['text'] if isinstance(result, dict) and 'text' in result else str(result)
        else:
            enhanced_prompt = agent_prompt_content
        
        # Create the generated prompt object
        generated_prompt = GeneratedPrompt(
            prompt_type="agent",
            agent_name=agent_type.value,
            prompt_content=enhanced_prompt,
            timestamp=datetime.now().isoformat()
        )
        
        return generated_prompt
    
    def _get_agent_system_instruction(self, agent_type: AgentType) -> str:
        """Get system instruction specific to agent type"""
        if agent_type == AgentType.DIAGRAM:
            return """AGENT TYPE: ARCHITECTURE DIAGRAM GENERATOR

You specialize in creating technical and architectural diagrams. Your output should be:
- Clear visual representations of systems and relationships
- Appropriate diagram types (UML, flowcharts, system architecture, etc.)
- Proper notation and symbols
- Clear component relationships and data flows
- Scalable and maintainable design representations

Focus on translating complex technical requirements into visual diagrams that communicate 
the system architecture, component interactions, and design decisions effectively."""
            
        elif agent_type == AgentType.PRESENTATION:
            return """AGENT TYPE: PRESENTATION GENERATOR

You specialize in creating PowerPoint presentations. Your output should include:
- Well-structured slide layouts with clear narrative flow
- Executive summary and key takeaways
- Technical details appropriate for the audience
- Visual elements and data visualizations
- Compelling storytelling that explains the solution
- Action items and next steps

Focus on creating presentations that effectively communicate technical solutions 
to stakeholders while maintaining engagement and clarity."""
            
        elif agent_type == AgentType.DOCUMENT:
            return """AGENT TYPE: TECHNICAL DOCUMENT GENERATOR

You specialize in creating comprehensive technical documentation. Your output should include:
- Structured document layout with proper sections
- Detailed technical specifications
- Implementation guidelines and best practices
- Risk assessments and mitigation strategies
- Requirements traceability
- Professional formatting and readability

Focus on creating documents that serve as complete references for technical 
implementation and decision-making."""
            
        elif agent_type == AgentType.PDF:
            return """AGENT TYPE: PDF REPORT GENERATOR

You specialize in creating professional PDF reports. Your output should include:
- Executive summary for decision-makers
- Detailed technical analysis and findings
- Data visualizations and charts
- Recommendations and action plans
- Appendices with supporting information
- Professional layout and formatting

Focus on creating comprehensive reports that combine technical depth 
with executive-level clarity and visual appeal."""
            
        elif agent_type == AgentType.CODE:
            return """AGENT TYPE: CODE GENERATOR

You specialize in generating implementation code. Your output should include:
- Clean, well-documented code following best practices
- Appropriate architecture patterns and design principles
- Error handling and validation
- Unit tests and integration examples
- Configuration files and deployment scripts
- Documentation and README files

Focus on creating production-ready code that implements the technical 
requirements while being maintainable and scalable."""
            
        else:
            return f"""AGENT TYPE: {agent_type.value.upper()} GENERATOR

You specialize in creating {agent_type.value} content. Focus on delivering high-quality 
output that meets the user's requirements while incorporating insights from domain experts."""

print("✅ Agent prompt generator with workflow integration ready!")

# ==============================================================================
# --- DOCUMENT GENERATION FUNCTIONS (from attempt2.py) ---
# ==============================================================================

def generate_and_run_script(client, initial_prompt, script_filename, topic):
    """Generate, run, and automatically self-correct a single Python script"""
    current_prompt = initial_prompt
    generated_code = ""
    
    try:
        for attempt in range(MAX_RETRIES):
            print(f"\\n--- Attempt {attempt + 1} of {MAX_RETRIES} for '{topic}' ---")
            try:
                print("Requesting code from the AI model...")
                completion = client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3.1:free",
                    messages=[{"role": "user", "content": current_prompt}]
                )
                generated_code = completion.choices[0].message.content.strip()

                # Clean code markers
                if generated_code.startswith("```python"):
                    generated_code = generated_code[9:]
                if generated_code.endswith("```"):
                    generated_code = generated_code[:-3]

                print(f"Code received. Saving to '{script_filename}'...")
                with open(script_filename, "w", encoding="utf-8") as f:
                    f.write(generated_code)

                print(f"Executing '{script_filename}'...")
                result = subprocess.run(
                    [sys.executable, script_filename],
                    capture_output=True, text=True, check=True, encoding="utf-8"
                )
                
                print("\\n--- ✅ Script Executed Successfully! ---")
                print("--- Output from Generated Script ---")
                print(result.stdout)
                print("------------------------------------")
                return True # Success

            except subprocess.CalledProcessError as e:
                print(f"\\n--- ❌ Script Execution Failed on Attempt {attempt + 1} ---")
                print("STDERR:", e.stderr)
                
                if attempt < MAX_RETRIES - 1:
                    print("Asking AI to self-correct the code...")
                    current_prompt = f"""
The following Python script you generated failed.
Original Goal: {topic}

--- FAILED CODE ---
{generated_code}
--- END FAILED CODE ---

It produced this error:
--- ERROR ---
{e.stderr}
--- END ERROR ---

Please analyze the error and provide a corrected, complete version of the Python script. Your entire output must be ONLY the corrected Python code.
"""
                else:
                    print(f"\\n--- 💥 Failed to generate working code after {MAX_RETRIES} attempts. ---")
                    return False
            except Exception as e:
                print(f"\\nAn unexpected error occurred: {e}")
                return False
    
    finally:
        if os.path.exists(script_filename):
            print(f"Cleaning up by deleting '{script_filename}'...")
            os.remove(script_filename)

def generate_and_build_project(client, initial_prompt, topic):
    """Generate, validate, and build a multi-file project from a JSON blueprint"""
    current_prompt = initial_prompt
    project_blueprint = None
    generated_text = ""

    for attempt in range(MAX_RETRIES):
        print(f"\\n--- Attempt {attempt + 1} of {MAX_RETRIES} for '{topic}' ---")
        try:
            print("Requesting project blueprint from the AI model...")
            completion = client.chat.completions.create(
                model="deepseek/deepseek-chat-v3.1:free",
                messages=[{"role": "user", "content": current_prompt}]
            )
            generated_text = completion.choices[0].message.content.strip()

            print("Blueprint received. Parsing JSON...")
            project_blueprint = json.loads(generated_text)
            print("--- ✅ JSON Blueprint is valid! ---")
            break

        except json.JSONDecodeError as e:
            print(f"\\n--- ❌ AI returned invalid JSON on Attempt {attempt + 1} ---")
            print(f"JSON Error: {e}")
            if attempt < MAX_RETRIES - 1:
                print("Asking AI to correct the JSON format...")
                current_prompt = f"""
The JSON blueprint you generated was invalid and could not be parsed.
Original Goal: {topic}

--- INVALID OUTPUT ---
{generated_text}
--- END INVALID OUTPUT ---

The parser failed with this error: {e}

Please provide a corrected version of the JSON blueprint. Ensure it is a single, valid JSON object with no extra text or markdown.
"""
            else:
                 print(f"\\n--- 💥 Failed to generate a valid JSON blueprint after {MAX_RETRIES} attempts. ---")
                 return False
        except Exception as e:
            print(f"\\nAn unexpected error occurred: {e}")
            return False

    if not project_blueprint:
        return False

    new_project_name = project_blueprint.get("project_name", "generated_project")
    files_to_create = project_blueprint.get("files", [])
    
    if not files_to_create:
        print("Warning: The AI returned a blueprint with no files to create.")
        return False

    print(f"Starting to build project: '{new_project_name}'...")
    os.makedirs(new_project_name, exist_ok=True)

    for file_info in files_to_create:
        full_path = os.path.join(new_project_name, file_info.get("path"))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        print(f"  - Creating file: {full_path}")
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(file_info.get("content", ""))

    print("\\n--- ✅ Project Generation Complete! ---")
    print(f"Your project has been created in the '{new_project_name}' directory.")
    return True

# Document generation prompt functions (from attempt2.py)
def get_pdf_generation_prompt():
    """Gets user input and constructs PDF generation prompt"""
    topic = input("Enter the topic for the PDF report: ").strip()
    image_query = input(f"Enter an image search query for '{topic}': ").strip()
    
    final_prompt = f"""
You are an expert Python script generator specializing in creating professional PDF documents using the `reportlab` library.
The user wants a script that creates a detailed, multi-page PDF report on the topic: "{topic}".

You MUST follow ALL of these rules:
1.  Your ENTIRE output must be ONLY the Python code. Do not include any explanations or markdown.
2.  The script must use the `reportlab` and `requests` libraries.
3.  **Content Generation**: The script MUST generate a detailed, multi-section report about "{topic}". The content should be comprehensive, well-structured, and include an introduction, multiple body paragraphs, and a conclusion.
4.  **Image Sourcing & Handling**:
    a. The script MUST find a royalty-free, reliable image URL related to the user's image query: "{image_query}".
    b. It MUST include a `download_image` function to download this image to a temporary local file.
    c. The `Image` object in ReportLab must use this downloaded local file.
5.  **Cleanup**: The script MUST use a `try...finally` block to ensure that the temporarily downloaded image file is always deleted after execution, even if errors occur.
6.  **Advanced Features**: The script should use different Paragraph styles (e.g., 'h1', 'h2', 'BodyText').
7.  **Filename**: Save the final PDF to a file named based on the user's topic (e.g., '{topic.lower().replace(' ', '_')}_report.pdf').

Now, generate the complete Python script for the user's request: "{topic}".
"""
    return final_prompt, topic

def get_diagram_generation_prompt():
    """Gets user input and constructs diagram generation prompt"""
    topic = input("Enter the topic for the pipeline diagram: ").strip()
    
    final_prompt = f"""
You are an expert Python script generator specializing in creating elegant `graphviz` diagrams.
The user wants a script that creates a detailed pipeline diagram for the topic: "{topic}".

You MUST follow ALL of these rules:
1.  Your entire output must be ONLY the Python code. Do NOT include any explanations or markdown formatting.
2.  The script must use the `graphviz` Python library.
3.  The script must generate a diagram with at least 3 main stages relevant to the topic.
4.  The script MUST use a modern color scheme ('#4a90e2'), and 'Arial' font.
5.  The script MUST use HTML-like labels (<TABLE>...) to structure the text inside the detail nodes. Use bold tags (<B>) for headers and bullet points (&#8226;).
6.  The script MUST use `rank='same'` subgraphs to align the main pipeline nodes on the left with their corresponding detail boxes on the right.
7.  CRITICAL: The content of the nodes (the main pipeline stages and the text in the detail boxes) MUST be adapted to be relevant to the user's specific topic: "{topic}".
8.  Save the final diagram to a PNG file named after the user's topic (e.g., '{topic.lower().replace(' ', '_')}_pipeline.png') and set `view=False`.

Now, generate the complete Python script for the user's request: "{topic}".
"""
    return final_prompt, topic

def get_ppt_generation_prompt():
    """Gets user input and constructs PowerPoint generation prompt"""
    topic = input("Enter the topic for the PowerPoint presentation: ").strip()

    final_prompt = f"""
You are an expert Python script generator. Your task is to generate a complete, immediately executable Python script.
The user wants a script that creates a PowerPoint presentation about: "{topic}".

You MUST follow ALL of these rules:
1.  Your entire output must be ONLY the Python code. Do NOT include any explanations or markdown.
2.  The script must use `python-pptx`, `requests`, and `Pillow`.
3.  The presentation must contain at least 4 slides: a title slide and three content slides.
4.  Each content slide should have a title and a mix of bullet points and an image.
5.  The script MUST find its own royalty-free image URLs for the content.
6.  The image download function MUST be resilient. It should use a `try...except` block to catch `requests.exceptions.RequestException`. If an image fails to download, it should print a warning and return `None`. The main script must check if the path is not `None` before adding it to a slide.
7.  The script MUST clean up all temporary image files using a `try...finally` block.
8.  Save the final presentation based on the topic (e.g., '{topic.lower().replace(' ', '_')}.pptx').

Now, generate the complete Python script for the user's request: "{topic}".
"""
    return final_prompt, topic

def get_word_generation_prompt():
    """Gets user input and constructs Word generation prompt"""
    topic = input("Enter the topic for the Word document: ").strip()
    image_query = input(f"Enter an image search query for '{topic}': ").strip()
    
    final_prompt = f"""
You are an expert Python script generator that creates detailed Microsoft Word documents (.docx).
The user wants a Word document about the topic: "{topic}".

You MUST follow ALL of these rules:
1.  Your ENTIRE output must be ONLY the Python code. Do not include any explanations or markdown.
2.  The script must use the `python-docx`, `requests`, and `os` libraries.
3.  **Content Generation**: The script must contain a detailed, multi-paragraph summary of "{topic}". The document must be well-structured with an introduction, at least two main body sections with subheadings (using 'Heading 1' and 'Heading 2' styles), and a conclusion.
4.  **Image Sourcing**: The script MUST find **two** different, royalty-free, and reliable image URLs related to "{image_query}".
5.  **Image Download Logic**: The `download_image` function must try each URL in order and stop after the first successful download.
6.  **Cleanup**: The script MUST use a `try...finally` block to ensure any downloaded image file is deleted at the end.
7.  **Conditional Image Placement**: The script must only add the image to the document if the download was successful.
8.  **Filename**: Save the final Word document to a file named based on the topic (e.g., '{topic.lower().replace(' ', '_')}.docx').

Now, generate the complete Python script for the user's request.
"""
    return final_prompt, topic

def get_project_generation_prompt():
    """Gets user input and constructs project generation prompt"""
    topic = input("Describe the project you want to build: ").strip()

    final_prompt = f"""
You are an expert software architect. Your task is to generate a complete, multi-file project as a single JSON object.

RULES:
1. Your ENTIRE output must be ONLY a single JSON object. No explanations or markdown.
2. The JSON must have keys "project_name" (string) and "files" (a list of file objects).
3. Each file object in the "files" list must have keys "path" (string, e.g., "src/main.py") and "content" (string, the full code for the file).
4. If dependencies are needed, you MUST include a "requirements.txt" file.
5. Ensure file content is properly escaped for JSON (e.g., newlines as \\\\n).

Now, generate the complete JSON blueprint for this project: "{topic}"
"""
    return final_prompt, topic

print("✅ Document generation functions ready!")

# ==============================================================================
# --- MOCK AGENT FUNCTIONS (for demonstration when real agents not available) ---
# ==============================================================================

async def call_diagram_agent(prompt: str) -> AgentOutput:
    """Call external diagram generation agent"""
    print(f"🔄 Calling external diagram agent with prompt length: {len(prompt)}")
    await asyncio.sleep(1)  # Simulate processing time
    
    return AgentOutput(
        agent_type=AgentType.DIAGRAM.value,
        content="[Generated architecture diagram with component relationships]",
        format="png",
        file_path="./data/generated_diagram.png",
        execution_time=1.0
    )

async def call_presentation_agent(prompt: str) -> AgentOutput:
    """Call external PowerPoint generation agent"""
    print(f"🔄 Calling external presentation agent with prompt length: {len(prompt)}")
    await asyncio.sleep(1.5)  # Simulate processing time
    
    return AgentOutput(
        agent_type=AgentType.PRESENTATION.value,
        content="[Generated PowerPoint presentation with 12 slides]",
        format="pptx",
        file_path="./data/generated_presentation.pptx",
        execution_time=1.5
    )

async def call_document_agent(prompt: str) -> AgentOutput:
    """Call external document generation agent"""
    print(f"🔄 Calling external document agent with prompt length: {len(prompt)}")
    await asyncio.sleep(1.2)  # Simulate processing time
    
    return AgentOutput(
        agent_type=AgentType.DOCUMENT.value,
        content="[Generated Word document with technical specifications]",
        format="docx",
        file_path="./data/generated_document.docx",
        execution_time=1.2
    )

async def call_pdf_agent(prompt: str) -> AgentOutput:
    """Call external PDF generation agent"""
    print(f"🔄 Calling external PDF agent with prompt length: {len(prompt)}")
    await asyncio.sleep(1.3)  # Simulate processing time
    
    return AgentOutput(
        agent_type=AgentType.PDF.value,
        content="[Generated PDF report with data visualizations]",
        format="pdf",
        file_path="./data/generated_report.pdf",
        execution_time=1.3
    )

async def call_code_agent(prompt: str) -> AgentOutput:
    """Call external code generation agent"""
    print(f"🔄 Calling external code agent with prompt length: {len(prompt)}")
    await asyncio.sleep(1.4)  # Simulate processing time
    
    return AgentOutput(
        agent_type=AgentType.CODE.value,
        content="[Generated code repository with implementation]",
        format="zip",
        file_path="./data/generated_code.zip",
        execution_time=1.4
    )

# Agent execution function map
AGENT_FUNCTION_MAP = {
    AgentType.DIAGRAM.value: call_diagram_agent,
    AgentType.PRESENTATION.value: call_presentation_agent,
    AgentType.DOCUMENT.value: call_document_agent,
    AgentType.PDF.value: call_pdf_agent,
    AgentType.CODE.value: call_code_agent
}

print("✅ Mock agent functions ready!")

# ==============================================================================
# --- MAIN COMBINED META SYSTEM (Based on MultiDomainSystem from Meta_model.ipynb) ---
# ==============================================================================

class CombinedMetaSystem:
    """Combined system integrating meta-model architecture with document generation"""
    
    def __init__(self, use_mock: bool = True):
        # Setup configurations
        self.llm_config = LLMConfig(timeout=1500)
        self.conversation_id = str(uuid.uuid4())
        self.conversation_memory = ConversationBufferMemory(return_messages=True) if LANGCHAIN_AVAILABLE else None
        self.current_state = None
        self.workflow_manager = WorkflowManager(self.conversation_id)
        
        # Initialize components (will be set up asynchronously)
        self.domain_experts = None
        self.domain_integrator = DomainIntegrator(self.llm_config)
        self.prompt_generator = AgentPromptGenerator(self.llm_config)
        self.openai_client = setup_openai_client()
        
        # Storage for workflow context
        self.domain_prompts = {}
        self.integration_report = {}
        
    async def setup(self):
        """Initialize the system components"""
        self.domain_experts = await setup_domain_experts(self.llm_config)
        print("✅ Combined Meta AI System initialized and ready!")
    
    async def process_user_query(self, user_query: str, agent_workflow: List[str] = None) -> SystemState:
        """Process a new user query through the entire system with optional workflow"""
        print(f"🔄 Processing user query: {user_query[:100]}{'...' if len(user_query) > 100 else ''}")
        
        # Set default workflow if none provided
        if agent_workflow is None:
            agent_workflow = ["diagram", "presentation", "document", "pdf", "code"]
        
        # Create workflow
        workflow_steps = self.workflow_manager.create_workflow(agent_workflow)
        
        # Add to conversation history
        if self.conversation_memory:
            self.conversation_memory.chat_memory.add_user_message(user_query)
        
        # Step 1: Analyze with domain experts and save their prompts
        domain_outputs = {}
        domain_prompts = {}
        generated_prompts = {}
        
        for domain_name, expert in self.domain_experts.items():
            print(f"🔄 Analyzing with {domain_name} expert...")
            input_data = DomainExpertInput(
                user_query=user_query,
                domain_name=domain_name
            )
            
            # Get both output and generated prompt
            domain_output, generated_prompt = await expert.analyze(input_data, self.conversation_id)
            domain_outputs[domain_name] = domain_output
            domain_prompts[domain_name] = generated_prompt.prompt_content
            generated_prompts[f"{domain_name}_domain"] = generated_prompt
            
            print(f"✅ {domain_name.capitalize()} analysis complete - prompt saved")
        
        # Step 2: Integrate domain analyses
        print("🔄 Integrating domain analyses...")
        integration_report = await self.domain_integrator.integrate_domain_analyses(
            user_query, domain_outputs
        )
        print("✅ Domain integration complete")
        
        # Step 3: Save domain outputs and integration to JSON
        output_files = {}
        for domain, output in domain_outputs.items():
            file_path = f"./data/{domain}_analysis_{self.conversation_id[:8]}.json"
            with open(file_path, 'w') as f:
                json.dump(asdict(output), f, indent=2)
            output_files[domain] = file_path
        
        integration_file = f"./data/integration_{self.conversation_id[:8]}.json"
        with open(integration_file, 'w') as f:
            json.dump(integration_report, f, indent=2)
        output_files["integration"] = integration_file
        
        # Create and save system state
        conversation_history = []
        if self.conversation_memory:
            conversation_history = [{
                "role": msg.type,
                "content": msg.content
            } for msg in self.conversation_memory.chat_memory.messages]
        
        self.current_state = SystemState(
            conversation_id=self.conversation_id,
            user_query=user_query,
            domain_outputs=domain_outputs,
            agent_outputs={},
            conversation_history=conversation_history,
            generated_prompts=generated_prompts,
            workflow_steps=workflow_steps,
            last_updated=datetime.now().isoformat()
        )
        
        # Store domain prompts and integration report for workflow
        self.domain_prompts = domain_prompts
        self.integration_report = integration_report
        
        # Save system state
        state_file = self.current_state.save_to_json()
        print(f"✅ System state saved to {state_file}")
        print(f"✅ Workflow created with {len(agent_workflow)} agents: {', '.join(agent_workflow)}")
        
        # Add summary to conversation
        if self.conversation_memory:
            summary = f"I've analyzed your request across mechanical, electrical, and programming domains and created a workflow for {len(agent_workflow)} agents."
            self.conversation_memory.chat_memory.add_ai_message(summary)
        
        return self.current_state
    
    async def execute_workflow_step(self, step_id: str, specific_instructions: Optional[str] = None) -> AgentOutput:
        """Execute a specific workflow step"""
        if self.current_state is None:
            raise ValueError("No active query to process. Please submit a user query first.")
        
        if step_id not in self.workflow_manager.workflow_steps:
            raise ValueError(f"Unknown step ID: {step_id}")
        
        step = self.workflow_manager.workflow_steps[step_id]
        agent_type = step.agent_type
        
        print(f"🚀 Executing workflow step: {step_id} ({agent_type})")
        
        # Generate agent-specific prompt using workflow context
        agent_enum_type = next(at for at in AgentType if at.value == agent_type)
        generated_prompt = await self.prompt_generator.generate_agent_prompt(
            agent_type=agent_enum_type,
            user_query=self.current_state.user_query,
            workflow_manager=self.workflow_manager,
            step_id=step_id,
            domain_prompts=self.domain_prompts,
            integration_report=self.integration_report,
            specific_instructions=specific_instructions
        )
        
        # Save the generated prompt to workflow and system state
        self.workflow_manager.update_step_prompt(step_id, generated_prompt)
        self.current_state.generated_prompts[f"{agent_type}_agent"] = generated_prompt
        
        # Save prompt to file
        prompt_filename = f"{agent_type}_prompt_{self.conversation_id[:8]}.txt"
        prompt_file_path = f"./data/{prompt_filename}"
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {agent_type.upper()} AGENT PROMPT\\n")
            f.write(f"# Generated: {generated_prompt.timestamp}\\n")
            f.write(f"# Step ID: {step_id}\\n\\n")
            f.write(generated_prompt.prompt_content)
        
        generated_prompt.file_path = prompt_file_path
        
        # Call the appropriate agent function
        agent_function = AGENT_FUNCTION_MAP.get(agent_type)
        
        if agent_function:
            agent_output = await agent_function(generated_prompt.prompt_content)
            
            # Update workflow step and system state
            self.workflow_manager.mark_step_executed(step_id, agent_output)
            self.current_state.agent_outputs[agent_type] = agent_output
            self.current_state.workflow_steps = self.workflow_manager.workflow_steps
            self.current_state.save_to_json()
            
            # Add to conversation
            if self.conversation_memory:
                self.conversation_memory.chat_memory.add_ai_message(
                    f"I've completed the {agent_type} step in the workflow."
                )
            
            print(f"✅ {agent_type.capitalize()} step complete - prompt and output saved")
            return agent_output
        else:
            raise ValueError(f"No implementation found for agent type: {agent_type}")
    
    async def execute_full_workflow(self) -> Dict[str, AgentOutput]:
        """Execute all steps in the workflow sequentially"""
        if self.current_state is None:
            raise ValueError("No active query to process. Please submit a user query first.")
        
        print("🚀 Executing full workflow...")
        all_outputs = {}
        
        for i, agent_type in enumerate(self.workflow_manager.execution_order):
            step_id = f"step_{i+1}_{agent_type}"
            
            if not self.workflow_manager.workflow_steps[step_id].executed:
                output = await self.execute_workflow_step(step_id)
                all_outputs[agent_type] = output
            else:
                print(f"⏭️ Skipping already executed step: {step_id}")
                all_outputs[agent_type] = self.workflow_manager.workflow_steps[step_id].output
        
        print("✅ Full workflow execution complete!")
        return all_outputs
    
    async def execute_document_generation(self, doc_type: str) -> AgentOutput:
        """Execute document generation using the approach from attempt2.py"""
        print(f"\\n📄 Executing {doc_type} generation using attempt2.py approach...")
        
        try:
            if doc_type == "pdf":
                prompt, topic = get_pdf_generation_prompt()
            elif doc_type == "diagram":
                prompt, topic = get_diagram_generation_prompt()  
            elif doc_type == "presentation":
                prompt, topic = get_ppt_generation_prompt()
            elif doc_type == "word":
                prompt, topic = get_word_generation_prompt()
            elif doc_type == "project":
                prompt, topic = get_project_generation_prompt()
                # Use different function for project generation
                success = generate_and_build_project(self.openai_client, prompt, topic)
                
                return AgentOutput(
                    agent_type=doc_type,
                    content=f"Generated {doc_type} for topic: {topic}" if success else f"Failed to generate {doc_type}",
                    format=doc_type if success else "error",
                    file_path=f"./data/generated_{doc_type}" if success else None,
                    execution_time=1.0
                )
            else:
                raise ValueError(f"Unsupported document type: {doc_type}")
            
            # Generate and run script for single-file document types
            script_filename = f"generated_{doc_type}_script.py"
            success = generate_and_run_script(self.openai_client, prompt, script_filename, topic)
            
            return AgentOutput(
                agent_type=doc_type,
                content=f"Generated {doc_type} for topic: {topic}" if success else f"Failed to generate {doc_type}",
                format=doc_type if success else "error",
                file_path=f"./data/generated_{doc_type}" if success else None,
                execution_time=1.0
            )
            
        except Exception as e:
            print(f"❌ Error generating {doc_type}: {e}")
            return AgentOutput(
                agent_type=doc_type,
                content=f"Failed to generate {doc_type}: {str(e)}",
                format="error"
            )
    
    async def modify_step_prompt(
        self,
        step_id: str,
        user_feedback: str
    ) -> Dict[str, AgentOutput]:
        """Modify a step's prompt and re-execute it and all subsequent steps"""
        if self.current_state is None:
            raise ValueError("No active query to process. Please submit a user query first.")
        
        if step_id not in self.workflow_manager.workflow_steps:
            raise ValueError(f"Unknown step ID: {step_id}")
        
        print(f"🔄 Modifying step {step_id} based on feedback...")
        
        # Get steps that need to be redone
        steps_to_redo = self.workflow_manager.get_steps_to_redo(step_id)
        print(f"📝 Steps to redo: {', '.join(steps_to_redo)}")
        
        # Reset the steps
        self.workflow_manager.reset_steps(steps_to_redo)
        
        # Add feedback to conversation history
        if self.conversation_memory:
            self.conversation_memory.chat_memory.add_user_message(
                f"Feedback for {step_id}: {user_feedback}"
            )
        
        # Re-execute the modified step and all subsequent steps
        all_outputs = {}
        for step_id_to_redo in steps_to_redo:
            step = self.workflow_manager.workflow_steps[step_id_to_redo]
            
            # Use feedback as specific instructions for the first modified step
            specific_instructions = user_feedback if step_id_to_redo == step_id else None
            
            output = await self.execute_workflow_step(step_id_to_redo, specific_instructions)
            all_outputs[step.agent_type] = output
        
        print("✅ Workflow modification complete!")
        return all_outputs
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        if not self.workflow_manager.workflow_steps:
            return {"status": "No workflow created"}
        
        status = {
            "total_steps": len(self.workflow_manager.workflow_steps),
            "completed_steps": sum(1 for step in self.workflow_manager.workflow_steps.values() if step.executed),
            "execution_order": self.workflow_manager.execution_order,
            "steps": {}
        }
        
        for step_id, step in self.workflow_manager.workflow_steps.items():
            status["steps"][step_id] = {
                "agent_type": step.agent_type,
                "executed": step.executed,
                "has_prompt": step.generated_prompt is not None,
                "has_output": step.output is not None
            }
        
        return status
    
    def get_all_generated_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Get all generated prompts with their file paths"""
        if not self.current_state:
            return {}
        
        prompts_info = {}
        for prompt_key, prompt_obj in self.current_state.generated_prompts.items():
            prompts_info[prompt_key] = {
                "type": prompt_obj.prompt_type,
                "agent": prompt_obj.agent_name,
                "file_path": prompt_obj.file_path,
                "timestamp": prompt_obj.timestamp,
                "content_preview": prompt_obj.prompt_content[:200] + "..." if len(prompt_obj.prompt_content) > 200 else prompt_obj.prompt_content
            }
        
        return prompts_info
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history"""
        if not self.conversation_memory:
            return []
        
        return [{
            "role": msg.type,
            "content": msg.content
        } for msg in self.conversation_memory.chat_memory.messages]

print("✅ Combined Meta System ready!")

# ==============================================================================
# --- MAIN APPLICATION ---
# ==============================================================================

async def main():
    """Main application function combining Meta Model and Document Generator"""
    print("🚀 Combined Meta AI System - Integrating Meta Model and Document Generator")
    print("=" * 80)
    
    # Create and setup system
    system = CombinedMetaSystem()
    await system.setup()
    
    while True:
        print("\\n" + "=" * 70)
        print("    Combined Meta AI System Menu")
        print("=" * 70)
        print("Select an option:")
        print("  1. Process Engineering Query (Meta Model Workflow)")
        print("  2. Execute Single Workflow Step")
        print("  3. Execute Full Workflow")
        print("  4. Modify Workflow Step")
        print("  5. Generate Document (attempt2.py style)")
        print("  6. Show Workflow Status")
        print("  7. Show Generated Prompts")
        print("  8. Show Conversation History")
        print("  9. Exit")
        
        choice = input("\\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            # Meta model workflow - process query through domain experts
            query = input("\\nEnter your engineering question: ").strip()
            if query:
                workflow_agents = input("Enter agents (comma-separated) or press Enter for default [diagram,presentation,document,pdf,code]: ").strip()
                if workflow_agents:
                    workflow_agents = [agent.strip() for agent in workflow_agents.split(',')]
                else:
                    workflow_agents = ["diagram", "presentation", "document", "pdf", "code"]
                
                print(f"\\n🧠 Processing with agents: {workflow_agents}")
                state = await system.process_user_query(query, workflow_agents)
                
                print("\\n📊 DOMAIN ANALYSIS RESULTS:")
                for domain, output in state.domain_outputs.items():
                    print(f"\\n▶️ {domain.upper()} DOMAIN:")
                    print(f"  • Analysis length: {len(output.analysis)} characters")
                    print(f"  • Key concerns: {output.concerns}")
                    print(f"  • Recommendations: {output.recommendations}")
        
        elif choice == '2':
            # Execute single workflow step
            if system.current_state is None:
                print("❌ No active workflow. Please process a query first (option 1).")
                continue
            
            print("\\nAvailable workflow steps:")
            for step_id, step in system.workflow_manager.workflow_steps.items():
                status = "✅ Executed" if step.executed else "⏳ Pending"
                print(f"  • {step_id} ({step.agent_type}) - {status}")
            
            step_id = input("\\nEnter step ID to execute: ").strip()
            if step_id in system.workflow_manager.workflow_steps:
                instructions = input("Enter specific instructions (optional): ").strip()
                instructions = instructions if instructions else None
                
                try:
                    output = await system.execute_workflow_step(step_id, instructions)
                    print(f"\\n✅ Step {step_id} completed:")
                    print(f"  • Content: {output.content[:100]}...")
                    print(f"  • Format: {output.format}")
                    print(f"  • File: {output.file_path}")
                except Exception as e:
                    print(f"❌ Error executing step: {e}")
            else:
                print("❌ Invalid step ID")
        
        elif choice == '3':
            # Execute full workflow
            if system.current_state is None:
                print("❌ No active workflow. Please process a query first (option 1).")
                continue
            
            try:
                outputs = await system.execute_full_workflow()
                print(f"\\n✅ Full workflow completed with {len(outputs)} steps:")
                for agent_type, output in outputs.items():
                    print(f"  • {agent_type}: {output.content[:50]}...")
            except Exception as e:
                print(f"❌ Error executing workflow: {e}")
        
        elif choice == '4':
            # Modify workflow step
            if system.current_state is None:
                print("❌ No active workflow. Please process a query first (option 1).")
                continue
            
            print("\\nExecuted workflow steps:")
            executed_steps = [(step_id, step) for step_id, step in system.workflow_manager.workflow_steps.items() if step.executed]
            
            if not executed_steps:
                print("❌ No executed steps to modify.")
                continue
            
            for step_id, step in executed_steps:
                print(f"  • {step_id} ({step.agent_type})")
            
            step_id = input("\\nEnter step ID to modify: ").strip()
            if step_id in [s[0] for s in executed_steps]:
                feedback = input("Enter feedback/modification instructions: ").strip()
                if feedback:
                    try:
                        modified_outputs = await system.modify_step_prompt(step_id, feedback)
                        print(f"\\n✅ Modified {len(modified_outputs)} steps:")
                        for agent_type in modified_outputs.keys():
                            print(f"  • {agent_type} re-executed")
                    except Exception as e:
                        print(f"❌ Error modifying step: {e}")
            else:
                print("❌ Invalid step ID")
        
        elif choice == '5':
            # Document generation using attempt2.py approach
            print("\\n📄 Document Generation (attempt2.py approach)")
            print("Select document type:")
            print("  1. PDF Report")
            print("  2. Pipeline Diagram")
            print("  3. PowerPoint Presentation")
            print("  4. Word Document")
            print("  5. Code Project")
            
            doc_choice = input("Enter choice (1-5): ").strip()
            doc_types = {"1": "pdf", "2": "diagram", "3": "presentation", "4": "word", "5": "project"}
            
            if doc_choice in doc_types:
                try:
                    output = await system.execute_document_generation(doc_types[doc_choice])
                    print(f"\\n📄 Document generation result:")
                    print(f"  • Content: {output.content}")
                    print(f"  • Format: {output.format}")
                    print(f"  • File: {output.file_path}")
                except Exception as e:
                    print(f"❌ Error generating document: {e}")
            else:
                print("❌ Invalid choice")
        
        elif choice == '6':
            # Show workflow status
            status = system.get_workflow_status()
            print("\\n📊 WORKFLOW STATUS:")
            
            if "status" in status:
                print(f"  • {status['status']}")
            else:
                print(f"  • Total steps: {status['total_steps']}")
                print(f"  • Completed steps: {status['completed_steps']}")
                print(f"  • Progress: {status['completed_steps']/status['total_steps']*100:.1f}%")
                print(f"  • Execution order: {status['execution_order']}")
                
                print("\\n  Step Details:")
                for step_id, step_info in status['steps'].items():
                    status_icon = "✅" if step_info['executed'] else "⏳"
                    print(f"    {status_icon} {step_id} ({step_info['agent_type']})")
        
        elif choice == '7':
            # Show generated prompts
            prompts = system.get_all_generated_prompts()
            print("\\n📝 GENERATED PROMPTS:")
            
            if not prompts:
                print("  • No prompts generated yet")
            else:
                for prompt_key, prompt_info in prompts.items():
                    print(f"\\n▶️ {prompt_key.upper()}:")
                    print(f"  • Type: {prompt_info['type']}")
                    print(f"  • Agent: {prompt_info['agent']}")
                    print(f"  • File: {prompt_info.get('file_path', 'Not saved')}")
                    print(f"  • Timestamp: {prompt_info['timestamp']}")
                    print(f"  • Preview: {prompt_info['content_preview']}")
        
        elif choice == '8':
            # Show conversation history
            history = system.get_conversation_history()
            print("\\n💬 CONVERSATION HISTORY:")
            
            if not history:
                print("  • No conversation history (Langchain not available or no interactions)")
            else:
                for i, msg in enumerate(history[-10:], 1):  # Show last 10 messages
                    role_icon = "👤" if msg['role'] == 'human' else "🤖"
                    content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                    print(f"  {i}. {role_icon} {msg['role'].title()}: {content_preview}")
        
        elif choice == '9':
            print("\\nExiting Combined Meta AI System. Goodbye!")
            break
        
        else:
            print("\\nInvalid choice. Please enter a number between 1 and 9.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n\\nProgram interrupted by user. Exiting gracefully...")
    except Exception as e:
        print(f"\\n❌ An error occurred: {e}")
        print("Please check your dependencies and configuration.")

# ==============================================================================
# --- DOMAIN EXPERTS ---
# ==============================================================================

class DomainExpert:
    """Base class for domain experts"""
    
    def __init__(self, domain_type: DomainType, llm_config: LLMConfig):
        self.domain_type = domain_type
        self.llm = llm_config.get_langchain_llm()
        self.system_prompt = self._get_domain_system_prompt()
        
    def _get_domain_system_prompt(self) -> str:
        """Get domain-specific system prompt"""
        prompts = {
            DomainType.MECHANICAL: """You are an expert Mechanical Engineer with extensive experience in designing physical systems, 
mechanisms, structures, and manufacturing processes. Think exclusively from a mechanical engineering perspective.

When analyzing problems:
1. Focus on physical principles, materials, structural integrity, and mechanical systems.
2. Consider forces, stresses, thermal effects, vibration, and material properties.
3. Evaluate manufacturability, assembly, maintenance, and mechanical reliability.
4. Identify potential mechanical failure points and physical constraints.
5. Always prioritize safety, durability, and mechanical efficiency.

Provide specific mechanical engineering insights with technical depth.""",
            
            DomainType.ELECTRICAL: """You are an expert Electrical Engineer with extensive experience in designing circuits, power systems, 
and electronic components. Think exclusively from an electrical engineering perspective.

When analyzing problems:
1. Focus on electrical principles, circuit design, power distribution, and signal integrity.
2. Consider voltage levels, current requirements, power management, and EMI/EMC concerns.
3. Evaluate electrical components, PCB design, wiring, and electrical safety.
4. Identify potential electrical failure modes and constraints.
5. Always prioritize electrical safety, reliability, and efficiency.

Provide specific electrical engineering insights with technical depth.""",
            
            DomainType.PROGRAMMING: """You are an expert Software Engineer with extensive experience in designing software architectures, 
algorithms, and embedded systems. Think exclusively from a software engineering perspective.

When analyzing problems:
1. Focus on software architecture, data structures, algorithms, and system design.
2. Consider execution efficiency, memory usage, maintainability, and scalability.
3. Evaluate appropriate programming languages, frameworks, and development methodologies.
4. Identify potential software failure modes and technical debt.
5. Always prioritize code quality, maintainability, and performance.

Provide specific software engineering insights with technical depth."""
        }
        
        return prompts.get(self.domain_type, "You are an engineering expert. Analyze the problem and provide technical insights.")

    async def analyze(self, input_data: DomainExpertInput, conversation_id: str) -> tuple[DomainExpertOutput, GeneratedPrompt]:
        """Analyze the input from domain perspective"""
        
        context_section = f"ADDITIONAL CONTEXT:\\n{input_data.context}" if input_data.context else ""
        instructions_section = f"SPECIFIC INSTRUCTIONS:\\n{input_data.additional_instructions}" if input_data.additional_instructions else ""
        
        analysis_prompt = f"""
Analyze this requirement from your {self.domain_type.value} engineering perspective:

USER REQUIREMENT:
{input_data.user_query}

{context_section}

{instructions_section}

Provide your analysis in this format:
1. Core principles and considerations from your domain
2. Key concerns and potential issues
3. Specific recommendations and approaches

Be thorough, technical, and focus exclusively on {self.domain_type.value} engineering aspects.
"""

        # Save the generated prompt
        generated_prompt = GeneratedPrompt(
            prompt_type="domain",
            agent_name=f"{self.domain_type.value}_expert",
            prompt_content=analysis_prompt,
            timestamp=datetime.now().isoformat()
        )
        
        # Save prompt to file
        prompt_filename = f"{self.domain_type.value}_domain_prompt_{conversation_id[:8]}.txt"
        prompt_file_path = f"./data/{prompt_filename}"
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.domain_type.value.upper()} DOMAIN EXPERT PROMPT\\n")
            f.write(f"# Generated: {generated_prompt.timestamp}\\n\\n")
            f.write(analysis_prompt)
        
        generated_prompt.file_path = prompt_file_path
        
        # Create mock analysis (since we're using mock LLM)
        if USE_REAL_OLLAMA and LANGCHAIN_AVAILABLE:
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ])
            
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            result = await chain.ainvoke({"input": input_data})
            analysis = result['text'] if isinstance(result, dict) and 'text' in result else str(result)
        else:
            # Mock analysis for demo
            analysis = f"Mock {self.domain_type.value} engineering analysis for: {input_data.user_query[:100]}..."
        
        # Extract key points
        concerns = self._extract_concerns(analysis)
        recommendations = self._extract_recommendations(analysis)
        
        domain_output = DomainExpertOutput(
            domain=self.domain_type.value,
            analysis=analysis,
            concerns=concerns,
            recommendations=recommendations
        )
        
        return domain_output, generated_prompt
    
    def _extract_concerns(self, analysis: str) -> List[str]:
        """Extract key concerns from analysis"""
        return [f"Mock concern {i+1} from {self.domain_type.value} analysis" for i in range(2)]
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract recommendations from analysis"""
        return [f"Mock recommendation {i+1} from {self.domain_type.value} analysis" for i in range(2)]

# ==============================================================================
# --- DOCUMENT GENERATION (from attempt2.py) ---
# ==============================================================================

def generate_and_run_script(client, initial_prompt, script_filename, topic):
    """Generate, run, and automatically self-correct a single Python script"""
    current_prompt = initial_prompt
    generated_code = ""
    
    try:
        for attempt in range(MAX_RETRIES):
            print(f"\\n--- Attempt {attempt + 1} of {MAX_RETRIES} for '{topic}' ---")
            try:
                print("Requesting code from the AI model...")
                completion = client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3.1:free",
                    messages=[{"role": "user", "content": current_prompt}]
                )
                generated_code = completion.choices[0].message.content.strip()

                # Clean code markers
                if generated_code.startswith("```python"):
                    generated_code = generated_code[9:]
                if generated_code.endswith("```"):
                    generated_code = generated_code[:-3]

                print(f"Code received. Saving to '{script_filename}'...")
                with open(script_filename, "w", encoding="utf-8") as f:
                    f.write(generated_code)

                print(f"Executing '{script_filename}'...")
                result = subprocess.run(
                    [sys.executable, script_filename],
                    capture_output=True, text=True, check=True, encoding="utf-8"
                )
                
                print("\\n--- ✅ Script Executed Successfully! ---")
                print("--- Output from Generated Script ---")
                print(result.stdout)
                print("------------------------------------")
                return # Success

            except subprocess.CalledProcessError as e:
                print(f"\\n--- ❌ Script Execution Failed on Attempt {attempt + 1} ---")
                print("STDERR:", e.stderr)
                
                if attempt < MAX_RETRIES - 1:
                    print("Asking AI to self-correct the code...")
                    current_prompt = f"""
The following Python script you generated failed.
Original Goal: {topic}

--- FAILED CODE ---
{generated_code}
--- END FAILED CODE ---

It produced this error:
--- ERROR ---
{e.stderr}
--- END ERROR ---

Please analyze the error and provide a corrected, complete version of the Python script. Your entire output must be ONLY the corrected Python code.
"""
                else:
                    print(f"\\n--- 💥 Failed to generate working code after {MAX_RETRIES} attempts. ---")
            except Exception as e:
                print(f"\\nAn unexpected error occurred: {e}")
                return
    
    finally:
        if os.path.exists(script_filename):
            print(f"Cleaning up by deleting '{script_filename}'...")
            os.remove(script_filename)

# Document generation prompt functions (simplified versions from attempt2.py)
def get_pdf_generation_prompt():
    """Gets user input and constructs PDF generation prompt"""
    topic = input("Enter the topic for the PDF report: ").strip()
    image_query = input(f"Enter an image search query for '{topic}': ").strip()
    
    final_prompt = f"""
You are an expert Python script generator. Create a script that generates a detailed PDF report about "{topic}".

Requirements:
1. Use reportlab and requests libraries
2. Generate comprehensive content about the topic
3. Include images related to "{image_query}"
4. Clean up temporary files
5. Output ONLY Python code

Create a professional PDF report with multiple sections, images, and proper formatting.
"""
    return final_prompt, topic

def get_diagram_generation_prompt():
    """Gets user input and constructs diagram generation prompt"""
    topic = input("Enter the topic for the pipeline diagram: ").strip()
    
    final_prompt = f"""
You are an expert Python script generator. Create a script that generates a detailed pipeline diagram about "{topic}".

Requirements:
1. Use graphviz library
2. Create at least 3 main pipeline stages
3. Use professional styling with colors and fonts
4. Save as PNG file
5. Output ONLY Python code

Create a comprehensive pipeline diagram relevant to the topic.
"""
    return final_prompt, topic

def get_ppt_generation_prompt():
    """Gets user input and constructs PowerPoint generation prompt"""
    topic = input("Enter the topic for the PowerPoint presentation: ").strip()
    
    final_prompt = f"""
You are an expert Python script generator. Create a script that generates a PowerPoint presentation about "{topic}".

Requirements:
1. Use python-pptx, requests, and Pillow libraries
2. Create at least 4 slides with title and content
3. Include relevant images
4. Clean up temporary files
5. Output ONLY Python code

Create a professional presentation with comprehensive content.
"""
    return final_prompt, topic

# ==============================================================================
# --- COMBINED META SYSTEM ---
# ==============================================================================

class CombinedMetaSystem:
    """Combined system integrating meta-model architecture with document generation"""
    
    def __init__(self):
        self.llm_config = LLMConfig(timeout=1500)
        self.conversation_id = str(uuid.uuid4())
        self.workflow_manager = WorkflowManager(self.conversation_id)
        self.current_state = None
        self.domain_experts = {}
        self.openai_client = setup_openai_client()
        
    async def setup(self):
        """Initialize the system"""
        print("🚀 Setting up Combined Meta AI System...")
        
        # Setup domain experts
        if LANGCHAIN_AVAILABLE:
            self.domain_experts = {
                "mechanical": DomainExpert(DomainType.MECHANICAL, self.llm_config),
                "electrical": DomainExpert(DomainType.ELECTRICAL, self.llm_config),
                "programming": DomainExpert(DomainType.PROGRAMMING, self.llm_config)
            }
        print("✅ System setup complete!")
    
    async def process_user_query(self, user_query: str, workflow_agents: Optional[List[str]] = None) -> SystemState:
        """Process user query through domain experts and setup workflow"""
        
        if workflow_agents is None:
            workflow_agents = ["diagram", "presentation", "document", "pdf", "code"]
        
        print(f"\\n🧠 Processing query with {len(self.domain_experts)} domain experts...")
        
        # Initialize system state
        domain_outputs = {}
        generated_prompts = {}
        
        # Process through domain experts
        if LANGCHAIN_AVAILABLE:
            for domain_name, expert in self.domain_experts.items():
                print(f"🔄 Analyzing with {domain_name} expert...")
                
                input_data = DomainExpertInput(
                    user_query=user_query,
                    domain_name=domain_name
                )
                
                domain_output, generated_prompt = await expert.analyze(input_data, self.conversation_id)
                domain_outputs[domain_name] = domain_output
                generated_prompts[f"{domain_name}_domain"] = generated_prompt
                
                # Save individual domain analysis
                analysis_filename = f"{domain_name}_analysis_{self.conversation_id[:8]}.json"
                analysis_path = f"./data/{analysis_filename}"
                with open(analysis_path, 'w') as f:
                    json.dump(asdict(domain_output), f, indent=2)
                print(f"💾 Saved {domain_name} analysis to {analysis_path}")
        else:
            print("⚠️ Using mock domain experts (Langchain not available)")
            for domain_name in ["mechanical", "electrical", "programming"]:
                domain_outputs[domain_name] = DomainExpertOutput(
                    domain=domain_name,
                    analysis=f"Mock {domain_name} analysis for the query",
                    concerns=[f"Mock concern 1", f"Mock concern 2"],
                    recommendations=[f"Mock recommendation 1", f"Mock recommendation 2"]
                )
        
        # Create workflow
        self.workflow_manager.create_workflow(workflow_agents)
        print(f"🔄 Created workflow with {len(workflow_agents)} steps: {workflow_agents}")
        
        # Create system state
        self.current_state = SystemState(
            conversation_id=self.conversation_id,
            user_query=user_query,
            domain_outputs=domain_outputs,
            agent_outputs={},
            conversation_history=[{"role": "user", "content": user_query}],
            generated_prompts=generated_prompts,
            workflow_steps=self.workflow_manager.workflow_steps
        )
        
        # Save system state
        state_file = self.current_state.save_to_json()
        print(f"💾 System state saved to {state_file}")
        
        return self.current_state
    
    async def execute_document_generation(self, doc_type: str) -> AgentOutput:
        """Execute document generation using the approach from attempt2.py"""
        print(f"\\n📄 Executing {doc_type} generation...")
        
        try:
            if doc_type == "pdf":
                prompt, topic = get_pdf_generation_prompt()
            elif doc_type == "diagram":
                prompt, topic = get_diagram_generation_prompt()  
            elif doc_type == "presentation":
                prompt, topic = get_ppt_generation_prompt()
            else:
                raise ValueError(f"Unsupported document type: {doc_type}")
            
            # Generate and run script
            script_filename = f"generated_{doc_type}_script.py"
            generate_and_run_script(self.openai_client, prompt, script_filename, topic)
            
            return AgentOutput(
                agent_type=doc_type,
                content=f"Generated {doc_type} for topic: {topic}",
                format=doc_type,
                file_path=f"./data/generated_{doc_type}",
                execution_time=1.0
            )
            
        except Exception as e:
            print(f"❌ Error generating {doc_type}: {e}")
            return AgentOutput(
                agent_type=doc_type,
                content=f"Failed to generate {doc_type}: {str(e)}",
                format="error"
            )
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        if not self.workflow_manager.workflow_steps:
            return {"total_steps": 0, "completed_steps": 0}
        
        total_steps = len(self.workflow_manager.workflow_steps)
        completed_steps = sum(1 for step in self.workflow_manager.workflow_steps.values() if step.executed)
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "execution_order": self.workflow_manager.execution_order,
            "progress_percent": (completed_steps / total_steps * 100) if total_steps > 0 else 0
        }
    
    def get_all_generated_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Get all generated prompts with metadata"""
        if not self.current_state:
            return {}
        
        prompts = {}
        for key, prompt in self.current_state.generated_prompts.items():
            prompts[key] = {
                "type": prompt.prompt_type,
                "agent_name": prompt.agent_name,
                "timestamp": prompt.timestamp,
                "file_path": prompt.file_path,
                "content_preview": prompt.prompt_content[:200] + "..." if len(prompt.prompt_content) > 200 else prompt.prompt_content
            }
        
        return prompts

# ==============================================================================
# --- MAIN APPLICATION ---
# ==============================================================================

async def main():
    """Main application function"""
    print("🚀 Combined Meta AI System - Integrating Meta Model and Document Generator")
    print("=" * 80)
    
    # Create and setup system
    system = CombinedMetaSystem()
    await system.setup()
    
    while True:
        print("\\n" + "=" * 50)
        print("    Combined Meta AI System Menu")
        print("=" * 50)
        print("Select an option:")
        print("  1. Process Engineering Query (Meta Model)")
        print("  2. Generate PDF Report")
        print("  3. Generate Diagram") 
        print("  4. Generate PowerPoint Presentation")
        print("  5. Show Workflow Status")
        print("  6. Show Generated Prompts")
        print("  7. Exit")
        
        choice = input("\\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            # Meta model workflow
            query = input("\\nEnter your engineering question: ").strip()
            if query:
                workflow_agents = input("Enter agents (comma-separated) or press Enter for default [diagram,presentation,document]: ").strip()
                if workflow_agents:
                    workflow_agents = [agent.strip() for agent in workflow_agents.split(',')]
                else:
                    workflow_agents = ["diagram", "presentation", "document"]
                
                print(f"\\n🧠 Processing with agents: {workflow_agents}")
                state = await system.process_user_query(query, workflow_agents)
                
                print("\\n📊 DOMAIN ANALYSIS RESULTS:")
                for domain, output in state.domain_outputs.items():
                    print(f"\\n▶️ {domain.upper()} DOMAIN:")
                    print(f"  • Analysis length: {len(output.analysis)} characters")
                    print(f"  • Key concerns: {output.concerns}")
                    print(f"  • Recommendations: {output.recommendations}")
        
        elif choice == '2':
            # PDF generation
            await system.execute_document_generation("pdf")
            
        elif choice == '3':
            # Diagram generation
            await system.execute_document_generation("diagram")
            
        elif choice == '4':
            # PowerPoint generation
            await system.execute_document_generation("presentation")
            
        elif choice == '5':
            # Show workflow status
            status = system.get_workflow_status()
            print("\\n📊 WORKFLOW STATUS:")
            print(f"  • Total steps: {status['total_steps']}")
            print(f"  • Completed steps: {status['completed_steps']}")
            print(f"  • Progress: {status.get('progress_percent', 0):.1f}%")
            if 'execution_order' in status:
                print(f"  • Execution order: {status['execution_order']}")
        
        elif choice == '6':
            # Show generated prompts
            prompts = system.get_all_generated_prompts()
            print("\\n📝 GENERATED PROMPTS:")
            for prompt_key, prompt_info in prompts.items():
                print(f"\\n▶️ {prompt_key.upper()}:")
                print(f"  • Type: {prompt_info['type']}")
                print(f"  • Agent: {prompt_info['agent_name']}")
                print(f"  • File: {prompt_info.get('file_path', 'Not saved')}")
                print(f"  • Preview: {prompt_info['content_preview']}")
        
        elif choice == '7':
            print("\\nExiting Combined Meta AI System. Goodbye!")
            break
        
        else:
            print("\\nInvalid choice. Please enter a number between 1 and 7.")

if __name__ == "__main__":
    asyncio.run(main())