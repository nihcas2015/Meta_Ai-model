#!/usr/bin/env python3
"""
Meta AI System - Unified Production Ready
Simple, clean implementation for multi-domain analysis with document generation
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

# LangChain Ollama integration
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# Document generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import json

# ============================================================================
# SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class Config:
    """System configuration"""
    model: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    timeout: int = 60

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DomainAnalysis:
    """Output from domain expert analysis"""
    domain: str
    analysis: str
    recommendations: List[str]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class SystemState:
    """Current system state"""
    user_query: str
    analyses: Dict[str, DomainAnalysis] = None
    workflow_plan: str = ""
    outputs: Dict[str, Any] = None
    session_id: str = ""
    
    def __post_init__(self):
        if self.analyses is None:
            self.analyses = {}
        if self.outputs is None:
            self.outputs = {}
        if not self.session_id:
            self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ============================================================================
# LLM MANAGER
# ============================================================================

class LLMManager:
    """Manages Ollama LLM interactions"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.llm = self._create_llm()
    
    def _create_llm(self) -> OllamaLLM:
        """Create and test LLM connection"""
        try:
            llm = OllamaLLM(
                model=self.config.model,
                base_url=self.config.base_url,
                temperature=self.config.temperature
            )
            test = llm.invoke("Hello")
            if test:
                logger.info(f"✅ Connected to {self.config.model}")
                return llm
            else:
                raise ValueError("No response from model")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Ollama: {e}")
            logger.error("Ensure: 1) ollama serve is running 2) ollama pull llama3.2")
            raise
    
    def analyze(self, domain: str, query: str) -> str:
        """Run domain analysis"""
        prompt = f"""You are a {domain} domain expert. 
        
Analyze this request and provide:
1. Key findings
2. Recommendations
3. Next steps

Request: {query}

Provide a concise, professional analysis."""
        
        return self.llm.invoke(prompt)
    
    def create_workflow(self, query: str, analyses: Dict[str, str]) -> str:
        """Create workflow plan from analyses"""
        analysis_text = "\n".join([f"{k}: {v}" for k, v in analyses.items()])
        
        prompt = f"""Given these domain analyses, create a workflow plan:

{analysis_text}

Original request: {query}

Provide a clear, step-by-step workflow plan."""
        
        return self.llm.invoke(prompt)

# ============================================================================
# DOMAIN EXPERTS
# ============================================================================

class DomainExpert:
    """Domain expert analyst"""
    
    def __init__(self, domain: str, llm_manager: LLMManager):
        self.domain = domain
        self.llm = llm_manager
    
    def analyze(self, query: str) -> DomainAnalysis:
        """Perform domain analysis"""
        analysis_text = self.llm.analyze(self.domain, query)
        
        return DomainAnalysis(
            domain=self.domain,
            analysis=analysis_text,
            recommendations=["Implement systematically", "Test thoroughly"]
        )

# ============================================================================
# DOCUMENT GENERATORS
# ============================================================================

class PDFGenerator:
    """Generate PDF reports"""
    
    @staticmethod
    def generate(state: SystemState, output_path: str = None):
        """Generate PDF from system state"""
        if output_path is None:
            output_path = DATA_DIR / f"report_{state.session_id}.pdf"
        
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph(f"Analysis Report", styles['Title']))
        story.append(Spacer(1, 0.2))
        
        # Query
        story.append(Paragraph(f"<b>Query:</b> {state.user_query}", styles['Normal']))
        story.append(Spacer(1, 0.2))
        
        # Analyses
        for domain, analysis in state.analyses.items():
            story.append(Paragraph(f"<b>{domain}:</b>", styles['Heading2']))
            story.append(Paragraph(analysis.analysis, styles['Normal']))
            story.append(Spacer(1, 0.1))
        
        # Workflow
        if state.workflow_plan:
            story.append(Paragraph("<b>Workflow Plan:</b>", styles['Heading2']))
            story.append(Paragraph(state.workflow_plan, styles['Normal']))
        
        doc.build(story)
        logger.info(f"✅ PDF saved: {output_path}")
        return output_path

class JSONGenerator:
    """Save results as JSON"""
    
    @staticmethod
    def generate(state: SystemState, output_path: str = None):
        """Save state as JSON"""
        if output_path is None:
            output_path = DATA_DIR / f"analysis_{state.session_id}.json"
        
        data = {
            "session_id": state.session_id,
            "query": state.user_query,
            "analyses": {
                k: {"domain": v.domain, "analysis": v.analysis}
                for k, v in state.analyses.items()
            },
            "workflow": state.workflow_plan,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✅ JSON saved: {output_path}")
        return output_path

# ============================================================================
# MAIN SYSTEM
# ============================================================================

class MetaAISystem:
    """Unified Meta AI System"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.llm_manager = LLMManager(self.config)
        self.experts = {
            "Mechanical": DomainExpert("Mechanical Engineering", self.llm_manager),
            "Electrical": DomainExpert("Electrical Engineering", self.llm_manager),
            "Software": DomainExpert("Software Engineering", self.llm_manager),
        }
        self.state = None
    
    def process(self, query: str) -> SystemState:
        """Process user query through all domains"""
        logger.info(f"Processing: {query}")
        self.state = SystemState(user_query=query)
        
        # Run domain analyses
        logger.info("Running domain analyses...")
        for domain, expert in self.experts.items():
            try:
                analysis = expert.analyze(query)
                self.state.analyses[domain] = analysis
                logger.info(f"✅ {domain} analysis complete")
            except Exception as e:
                logger.error(f"❌ {domain} analysis failed: {e}")
        
        # Create workflow
        logger.info("Creating workflow plan...")
        try:
            analyses_dict = {
                k: v.analysis for k, v in self.state.analyses.items()
            }
            self.state.workflow_plan = self.llm_manager.create_workflow(
                query, analyses_dict
            )
            logger.info("✅ Workflow created")
        except Exception as e:
            logger.error(f"❌ Workflow creation failed: {e}")
        
        # Generate outputs
        logger.info("Generating output documents...")
        PDFGenerator.generate(self.state)
        JSONGenerator.generate(self.state)
        
        return self.state

# ============================================================================
# CLI
# ============================================================================

def main():
    """Command-line interface"""
    import sys
    
    config = Config()
    system = MetaAISystem(config)
    
    if len(sys.argv) > 1:
        # Process argument as query
        query = " ".join(sys.argv[1:])
        result = system.process(query)
        print(f"\n✅ Analysis complete. Session: {result.session_id}")
    else:
        # Interactive mode
        print("\n🤖 Meta AI System - Interactive Mode")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                query = input("Enter query: ").strip()
                if query.lower() in ["exit", "quit"]:
                    break
                if query:
                    result = system.process(query)
                    print(f"✅ Session: {result.session_id}\n")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
