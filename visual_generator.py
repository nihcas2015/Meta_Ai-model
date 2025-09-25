#!/usr/bin/env python3
"""
Visual Content Generator for Meta AI System
Creates visual previews, diagrams, PPT slides, document previews, and workflow visualizations
"""

import os
import io
import base64
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import networkx as nx
import seaborn as sns
import numpy as np

# Setup
BASE_DIR = Path(__file__).parent
VISUAL_OUTPUT_DIR = BASE_DIR / "visual_outputs"
VISUAL_OUTPUT_DIR.mkdir(exist_ok=True)

# Configure matplotlib for better visuals
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class VisualContentGenerator:
    """Generate visual content for Meta AI system outputs"""
    
    def __init__(self):
        self.output_dir = VISUAL_OUTPUT_DIR
        self.colors = {
            'mechanical': '#FF6B6B',
            'electrical': '#4ECDC4', 
            'programming': '#45B7D1',
            'primary': '#2C3E50',
            'secondary': '#34495E',
            'accent': '#E74C3C',
            'success': '#27AE60',
            'warning': '#F39C12',
            'info': '#3498DB'
        }
    
    def generate_workflow_diagram(self, domain_outputs: Dict, workflow_type: str, conversation_id: str) -> str:
        """Generate a visual workflow diagram showing the process flow"""
        
        fig, ax = plt.subplots(figsize=(14, 10))
        fig.patch.set_facecolor('white')
        
        # Create workflow stages
        stages = [
            {"name": "User Query", "x": 1, "y": 8, "color": self.colors['info']},
            {"name": "Mechanical\nAnalysis", "x": 0.5, "y": 6, "color": self.colors['mechanical']},
            {"name": "Electrical\nAnalysis", "x": 1, "y": 6, "color": self.colors['electrical']},
            {"name": "Programming\nAnalysis", "x": 1.5, "y": 6, "color": self.colors['programming']},
            {"name": "Domain\nIntegration", "x": 1, "y": 4, "color": self.colors['secondary']},
            {"name": f"Workflow:\n{workflow_type.upper()}", "x": 1, "y": 2, "color": self.colors['accent']},
            {"name": "Generated\nOutput", "x": 1, "y": 0.5, "color": self.colors['success']}
        ]
        
        # Draw stages
        for stage in stages:
            circle = plt.Circle((stage["x"], stage["y"]), 0.3, 
                              color=stage["color"], alpha=0.8, zorder=3)
            ax.add_patch(circle)
            
            # Add stage labels
            ax.text(stage["x"], stage["y"], stage["name"], 
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   color='white', zorder=4)
        
        # Draw connections
        connections = [
            (1, 8, 0.5, 6), (1, 8, 1, 6), (1, 8, 1.5, 6),  # User to domains
            (0.5, 6, 1, 4), (1, 6, 1, 4), (1.5, 6, 1, 4),  # Domains to integration
            (1, 4, 1, 2), (1, 2, 1, 0.5)  # Integration to workflow to output
        ]
        
        for x1, y1, x2, y2 in connections:
            ax.arrow(x1, y1-0.3, x2-x1, y2-y1+0.6, 
                    head_width=0.05, head_length=0.1, 
                    fc=self.colors['primary'], ec=self.colors['primary'], alpha=0.7)
        
        # Add domain analysis details
        y_pos = 5.5
        for domain, output in domain_outputs.items():
            findings_count = len(output.get('key_findings', []))
            recommendations_count = len(output.get('recommendations', []))
            
            ax.text(2.5, y_pos, f"{domain.title()}:\n• {findings_count} findings\n• {recommendations_count} recommendations", 
                   fontsize=9, bbox=dict(boxstyle="round,pad=0.3", 
                   facecolor=self.colors[domain], alpha=0.3))
            y_pos -= 0.8
        
        # Set title and formatting
        ax.set_title(f"Meta AI Workflow Visualization\nConversation ID: {conversation_id}", 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlim(-0.5, 3.5)
        ax.set_ylim(0, 9)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Add timestamp
        ax.text(3, 0.2, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
               fontsize=8, alpha=0.7)
        
        # Save the diagram
        output_path = self.output_dir / f"workflow_diagram_{conversation_id}.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(output_path)
    
    def generate_pipeline_diagram(self, user_query: str, domain_outputs: Dict, conversation_id: str) -> str:
        """Generate a technical pipeline/system diagram"""
        
        fig, ax = plt.subplots(figsize=(16, 12))
        fig.patch.set_facecolor('white')
        
        # Create a network graph for the pipeline
        G = nx.DiGraph()
        
        # Add nodes based on domain analysis
        nodes = {
            'input': {'pos': (0, 0), 'color': self.colors['info'], 'size': 800},
            'mech_proc': {'pos': (-2, 2), 'color': self.colors['mechanical'], 'size': 600},
            'elec_proc': {'pos': (0, 3), 'color': self.colors['electrical'], 'size': 600},
            'prog_proc': {'pos': (2, 2), 'color': self.colors['programming'], 'size': 600},
            'integration': {'pos': (0, 5), 'color': self.colors['secondary'], 'size': 700},
            'output': {'pos': (0, 7), 'color': self.colors['success'], 'size': 800}
        }
        
        # Add nodes to graph
        for node_id, data in nodes.items():
            G.add_node(node_id, **data)
        
        # Add edges
        edges = [
            ('input', 'mech_proc'), ('input', 'elec_proc'), ('input', 'prog_proc'),
            ('mech_proc', 'integration'), ('elec_proc', 'integration'), ('prog_proc', 'integration'),
            ('integration', 'output')
        ]
        G.add_edges_from(edges)
        
        # Extract positions and colors
        pos = nx.get_node_attributes(G, 'pos')
        colors = [nodes[node]['color'] for node in G.nodes()]
        sizes = [nodes[node]['size'] for node in G.nodes()]
        
        # Draw the network
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, alpha=0.8)
        nx.draw_networkx_edges(G, pos, edge_color=self.colors['primary'], 
                              arrows=True, arrowsize=20, width=2, alpha=0.7)
        
        # Add labels
        labels = {
            'input': 'User Query\nInput',
            'mech_proc': 'Mechanical\nProcessing',
            'elec_proc': 'Electrical\nProcessing', 
            'prog_proc': 'Programming\nProcessing',
            'integration': 'System\nIntegration',
            'output': 'Final\nOutput'
        }
        
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold')
        
        # Add technical details around the diagram
        ax.text(-4, 6, "Technical Specifications:", fontsize=12, fontweight='bold')
        y_detail = 5.5
        for domain, output in domain_outputs.items():
            key_findings = output.get('key_findings', [])[:2]  # Show top 2
            detail_text = f"{domain.upper()}:\n"
            for finding in key_findings:
                detail_text += f"• {finding[:50]}...\n"
            
            ax.text(-4, y_detail, detail_text, fontsize=9, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors[domain], alpha=0.2))
            y_detail -= 1.5
        
        # Set title and formatting
        ax.set_title(f"System Pipeline Diagram\n{user_query}", 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlim(-5, 5)
        ax.set_ylim(-1, 8)
        ax.axis('off')
        
        # Save the diagram
        output_path = self.output_dir / f"pipeline_diagram_{conversation_id}.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(output_path)
    
    def generate_powerpoint_preview(self, user_query: str, domain_outputs: Dict, conversation_id: str) -> List[str]:
        """Generate PowerPoint slide previews"""
        
        slide_paths = []
        
        # Slide 1: Title Slide
        slide_paths.append(self._create_title_slide(user_query, conversation_id))
        
        # Slide 2: Domain Analysis Overview
        slide_paths.append(self._create_overview_slide(domain_outputs, conversation_id))
        
        # Slides 3-5: Individual Domain Analysis
        for domain, output in domain_outputs.items():
            slide_paths.append(self._create_domain_slide(domain, output, conversation_id))
        
        # Slide 6: Recommendations & Next Steps
        slide_paths.append(self._create_recommendations_slide(domain_outputs, conversation_id))
        
        return slide_paths
    
    def _create_title_slide(self, title: str, conversation_id: str) -> str:
        """Create PowerPoint title slide"""
        
        fig, ax = plt.subplots(figsize=(16, 9))
        fig.patch.set_facecolor('#2C3E50')
        
        # Main title
        ax.text(0.5, 0.65, title.upper(), transform=ax.transAxes, 
               fontsize=28, fontweight='bold', color='white', ha='center')
        
        # Subtitle
        ax.text(0.5, 0.5, "Meta AI System Analysis", transform=ax.transAxes,
               fontsize=18, color='#BDC3C7', ha='center')
        
        # Conversation ID
        ax.text(0.5, 0.35, f"Conversation ID: {conversation_id}", transform=ax.transAxes,
               fontsize=12, color='#95A5A6', ha='center')
        
        # Date
        ax.text(0.5, 0.25, datetime.now().strftime('%B %d, %Y'), transform=ax.transAxes,
               fontsize=14, color='#ECF0F1', ha='center')
        
        # Add decorative elements
        circle1 = plt.Circle((0.2, 0.8), 0.05, color=self.colors['mechanical'], alpha=0.7, transform=ax.transAxes)
        circle2 = plt.Circle((0.5, 0.85), 0.07, color=self.colors['electrical'], alpha=0.7, transform=ax.transAxes)
        circle3 = plt.Circle((0.8, 0.8), 0.05, color=self.colors['programming'], alpha=0.7, transform=ax.transAxes)
        ax.add_patch(circle1)
        ax.add_patch(circle2) 
        ax.add_patch(circle3)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        output_path = self.output_dir / f"slide_1_title_{conversation_id}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#2C3E50')
        plt.close()
        
        return str(output_path)
    
    def _create_overview_slide(self, domain_outputs: Dict, conversation_id: str) -> str:
        """Create overview slide with statistics"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))
        fig.patch.set_facecolor('white')
        
        # Left side - Statistics
        domains = list(domain_outputs.keys())
        findings_counts = [len(output.get('key_findings', [])) for output in domain_outputs.values()]
        recommendations_counts = [len(output.get('recommendations', [])) for output in domain_outputs.values()]
        
        x = np.arange(len(domains))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, findings_counts, width, label='Key Findings', 
                       color=[self.colors[domain] for domain in domains], alpha=0.8)
        bars2 = ax1.bar(x + width/2, recommendations_counts, width, label='Recommendations',
                       color=[self.colors[domain] for domain in domains], alpha=0.6)
        
        ax1.set_xlabel('Domains', fontweight='bold')
        ax1.set_ylabel('Count', fontweight='bold')
        ax1.set_title('Domain Analysis Overview', fontweight='bold', fontsize=16)
        ax1.set_xticks(x)
        ax1.set_xticklabels([d.title() for d in domains])
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width()/2, height),
                           xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')
        
        # Right side - Summary text
        ax2.text(0.05, 0.9, "Analysis Summary", fontsize=18, fontweight='bold', transform=ax2.transAxes)
        
        y_pos = 0.8
        for domain, output in domain_outputs.items():
            summary_text = f"{domain.title()} Domain:\n"
            summary_text += f"• {len(output.get('key_findings', []))} key findings identified\n"
            summary_text += f"• {len(output.get('recommendations', []))} recommendations provided\n"
            summary_text += f"• Analysis: {len(output.get('analysis', ''))} characters\n"
            
            ax2.text(0.05, y_pos, summary_text, fontsize=11, transform=ax2.transAxes,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors[domain], alpha=0.2))
            y_pos -= 0.25
        
        ax2.axis('off')
        
        plt.tight_layout()
        output_path = self.output_dir / f"slide_2_overview_{conversation_id}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(output_path)
    
    def _create_domain_slide(self, domain: str, output: Dict, conversation_id: str) -> str:
        """Create individual domain analysis slide"""
        
        fig, ax = plt.subplots(figsize=(16, 9))
        fig.patch.set_facecolor('white')
        
        # Title
        ax.text(0.5, 0.95, f"{domain.title()} Domain Analysis", 
               fontsize=24, fontweight='bold', ha='center', transform=ax.transAxes,
               color=self.colors[domain])
        
        # Key Findings section
        ax.text(0.05, 0.85, "🔍 Key Findings:", fontsize=16, fontweight='bold', 
               transform=ax.transAxes)
        
        y_pos = 0.78
        for i, finding in enumerate(output.get('key_findings', [])[:4]):  # Top 4 findings
            ax.text(0.08, y_pos, f"• {finding}", fontsize=12, transform=ax.transAxes)
            y_pos -= 0.08
        
        # Recommendations section
        ax.text(0.05, 0.45, "💡 Recommendations:", fontsize=16, fontweight='bold',
               transform=ax.transAxes)
        
        y_pos = 0.38
        for i, recommendation in enumerate(output.get('recommendations', [])[:4]):  # Top 4 recommendations
            ax.text(0.08, y_pos, f"• {recommendation}", fontsize=12, transform=ax.transAxes)
            y_pos -= 0.08
        
        # Add visual element
        rect = FancyBboxPatch((0.6, 0.15), 0.35, 0.7, boxstyle="round,pad=0.02",
                             facecolor=self.colors[domain], alpha=0.1, transform=ax.transAxes)
        ax.add_patch(rect)
        
        # Analysis summary in the visual element
        analysis_summary = output.get('analysis', '')[:300] + "..."
        ax.text(0.775, 0.5, f"Analysis Summary:\n\n{analysis_summary}", 
               fontsize=10, ha='center', va='center', transform=ax.transAxes,
               wrap=True)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        output_path = self.output_dir / f"slide_{domain}_{conversation_id}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(output_path)
    
    def _create_recommendations_slide(self, domain_outputs: Dict, conversation_id: str) -> str:
        """Create final recommendations and next steps slide"""
        
        fig, ax = plt.subplots(figsize=(16, 9))
        fig.patch.set_facecolor('#34495E')
        
        # Title
        ax.text(0.5, 0.9, "🎯 Key Recommendations & Next Steps", 
               fontsize=24, fontweight='bold', ha='center', transform=ax.transAxes,
               color='white')
        
        # Collect all recommendations
        all_recommendations = []
        for domain, output in domain_outputs.items():
            for rec in output.get('recommendations', [])[:2]:  # Top 2 from each domain
                all_recommendations.append(f"{domain.title()}: {rec}")
        
        # Display recommendations
        y_pos = 0.75
        for i, rec in enumerate(all_recommendations[:6]):  # Top 6 overall
            ax.text(0.1, y_pos, f"{i+1}. {rec}", fontsize=14, transform=ax.transAxes,
                   color='white', bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.1))
            y_pos -= 0.11
        
        # Next steps section
        ax.text(0.1, 0.15, "🚀 Immediate Next Steps:", fontsize=18, fontweight='bold',
               transform=ax.transAxes, color='#3498DB')
        
        next_steps = [
            "Review domain-specific recommendations",
            "Prioritize implementation based on resource availability",
            "Create detailed project timeline",
            "Assign responsibilities to team members"
        ]
        
        y_pos = 0.08
        for step in next_steps:
            ax.text(0.15, y_pos, f"• {step}", fontsize=12, transform=ax.transAxes, color='#ECF0F1')
            y_pos -= 0.04
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        output_path = self.output_dir / f"slide_recommendations_{conversation_id}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#34495E')
        plt.close()
        
        return str(output_path)
    
    def generate_document_preview(self, user_query: str, domain_outputs: Dict, conversation_id: str) -> str:
        """Generate a document-style preview"""
        
        fig, ax = plt.subplots(figsize=(8.5, 11))  # Standard letter size
        fig.patch.set_facecolor('white')
        
        # Document header
        ax.text(0.5, 0.95, "TECHNICAL ANALYSIS REPORT", fontsize=20, fontweight='bold',
               ha='center', transform=ax.transAxes)
        
        ax.text(0.5, 0.92, user_query, fontsize=14, ha='center', transform=ax.transAxes,
               style='italic')
        
        # Date and ID
        ax.text(0.5, 0.88, f"Generated: {datetime.now().strftime('%B %d, %Y')}", 
               fontsize=10, ha='center', transform=ax.transAxes)
        ax.text(0.5, 0.86, f"Document ID: {conversation_id}", 
               fontsize=10, ha='center', transform=ax.transAxes)
        
        # Executive Summary
        ax.text(0.05, 0.8, "EXECUTIVE SUMMARY", fontsize=14, fontweight='bold',
               transform=ax.transAxes)
        
        summary_text = f"This comprehensive analysis covers {len(domain_outputs)} technical domains: "
        summary_text += ", ".join([d.title() for d in domain_outputs.keys()]) + ". "
        total_findings = sum(len(output.get('key_findings', [])) for output in domain_outputs.values())
        total_recommendations = sum(len(output.get('recommendations', [])) for output in domain_outputs.values())
        summary_text += f"Analysis yielded {total_findings} key findings and {total_recommendations} actionable recommendations."
        
        ax.text(0.05, 0.73, summary_text, fontsize=11, transform=ax.transAxes, wrap=True)
        
        # Domain sections
        y_pos = 0.65
        for domain, output in domain_outputs.items():
            # Section header
            ax.text(0.05, y_pos, f"{domain.upper()} ANALYSIS", fontsize=12, fontweight='bold',
                   transform=ax.transAxes, color=self.colors[domain])
            y_pos -= 0.04
            
            # Key findings
            ax.text(0.05, y_pos, "Key Findings:", fontsize=10, fontweight='bold',
                   transform=ax.transAxes)
            y_pos -= 0.03
            
            for finding in output.get('key_findings', [])[:2]:
                ax.text(0.08, y_pos, f"• {finding}", fontsize=9, transform=ax.transAxes)
                y_pos -= 0.025
            
            y_pos -= 0.02
        
        # Footer
        ax.text(0.5, 0.05, f"Page 1 of 1 | Meta AI System | {conversation_id}", 
               fontsize=8, ha='center', transform=ax.transAxes, alpha=0.7)
        
        # Add border
        rect = patches.Rectangle((0.02, 0.02), 0.96, 0.96, linewidth=2, 
                               edgecolor='black', facecolor='none', transform=ax.transAxes)
        ax.add_patch(rect)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        output_path = self.output_dir / f"document_preview_{conversation_id}.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(output_path)
    
    def generate_project_structure_visual(self, user_query: str, domain_outputs: Dict, conversation_id: str) -> str:
        """Generate a visual project structure diagram"""
        
        fig, ax = plt.subplots(figsize=(14, 10))
        fig.patch.set_facecolor('white')
        
        # Title
        ax.text(0.5, 0.95, f"Project Structure: {user_query}", fontsize=16, fontweight='bold',
               ha='center', transform=ax.transAxes)
        
        # Create tree structure
        structure = {
            'project_root/': {
                'x': 0.5, 'y': 0.85, 'color': self.colors['primary']
            },
            'src/': {'x': 0.2, 'y': 0.7, 'color': self.colors['programming']},
            'mechanical/': {'x': 0.1, 'y': 0.55, 'color': self.colors['mechanical']},
            'electrical/': {'x': 0.3, 'y': 0.55, 'color': self.colors['electrical']},
            'docs/': {'x': 0.5, 'y': 0.7, 'color': self.colors['info']},
            'tests/': {'x': 0.8, 'y': 0.7, 'color': self.colors['success']},
            'config/': {'x': 0.65, 'y': 0.55, 'color': self.colors['secondary']},
            'README.md': {'x': 0.5, 'y': 0.4, 'color': self.colors['warning']}
        }
        
        # Draw connections
        connections = [
            ('project_root/', 'src/'), ('project_root/', 'docs/'), ('project_root/', 'tests/'),
            ('src/', 'mechanical/'), ('src/', 'electrical/'),
            ('tests/', 'config/'), ('docs/', 'README.md')
        ]
        
        for parent, child in connections:
            x1, y1 = structure[parent]['x'], structure[parent]['y']
            x2, y2 = structure[child]['x'], structure[child]['y']
            ax.plot([x1, x2], [y1, y2], 'k--', alpha=0.5, transform=ax.transAxes)
        
        # Draw nodes
        for name, data in structure.items():
            if name.endswith('/'):
                # Directory
                rect = FancyBboxPatch((data['x']-0.06, data['y']-0.02), 0.12, 0.04,
                                    boxstyle="round,pad=0.01", facecolor=data['color'], alpha=0.7,
                                    transform=ax.transAxes)
                ax.add_patch(rect)
                ax.text(data['x'], data['y'], name, ha='center', va='center', 
                       fontweight='bold', fontsize=10, color='white', transform=ax.transAxes)
            else:
                # File
                circle = plt.Circle((data['x'], data['y']), 0.03, 
                                  color=data['color'], alpha=0.8, transform=ax.transAxes)
                ax.add_patch(circle)
                ax.text(data['x'], data['y']-0.05, name, ha='center', va='center',
                       fontsize=9, transform=ax.transAxes)
        
        # Add technical specifications
        ax.text(0.05, 0.3, "Technical Components:", fontsize=12, fontweight='bold',
               transform=ax.transAxes)
        
        y_pos = 0.25
        components = {
            'mechanical/': "CAD models, stress analysis, material specs",
            'electrical/': "Circuit designs, power calculations, schematics", 
            'programming/': "Core algorithms, APIs, user interfaces",
            'tests/': "Unit tests, integration tests, performance tests",
            'docs/': "Technical documentation, user manuals, specifications"
        }
        
        for comp, desc in components.items():
            ax.text(0.05, y_pos, f"{comp}: {desc}", fontsize=10, transform=ax.transAxes,
                   color=structure[comp]['color'])
            y_pos -= 0.04
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        output_path = self.output_dir / f"project_structure_{conversation_id}.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(output_path)
    
    def create_visual_summary(self, workflow_type: str, user_query: str, domain_outputs: Dict, conversation_id: str) -> Dict[str, Any]:
        """Create all visual content and return paths"""
        
        visual_content = {
            'workflow_diagram': self.generate_workflow_diagram(domain_outputs, workflow_type, conversation_id),
            'conversation_id': conversation_id,
            'workflow_type': workflow_type,
            'user_query': user_query,
            'generated_visuals': []
        }
        
        # Generate appropriate visuals based on workflow type
        if workflow_type == 'pdf':
            visual_content['document_preview'] = self.generate_document_preview(user_query, domain_outputs, conversation_id)
            visual_content['generated_visuals'].append('document_preview')
            
        elif workflow_type == 'diagram':
            visual_content['pipeline_diagram'] = self.generate_pipeline_diagram(user_query, domain_outputs, conversation_id)
            visual_content['generated_visuals'].append('pipeline_diagram')
            
        elif workflow_type == 'powerpoint':
            visual_content['powerpoint_slides'] = self.generate_powerpoint_preview(user_query, domain_outputs, conversation_id)
            visual_content['generated_visuals'].append('powerpoint_slides')
            
        elif workflow_type == 'word':
            visual_content['document_preview'] = self.generate_document_preview(user_query, domain_outputs, conversation_id)
            visual_content['generated_visuals'].append('document_preview')
            
        elif workflow_type == 'project':
            visual_content['project_structure'] = self.generate_project_structure_visual(user_query, domain_outputs, conversation_id)
            visual_content['generated_visuals'].append('project_structure')
        
        return visual_content

# Helper function to convert images to base64 for web display
def image_to_base64(image_path: str) -> str:
    """Convert image to base64 string for web display"""
    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"

if __name__ == "__main__":
    # Test the visual generator
    generator = VisualContentGenerator()
    
    # Mock data for testing
    mock_domain_outputs = {
        'mechanical': {
            'key_findings': ['High stress concentration', 'Material fatigue risk'],
            'recommendations': ['Use stronger alloy', 'Implement stress relief'],
            'analysis': 'Detailed mechanical analysis...'
        },
        'electrical': {
            'key_findings': ['Power consumption high', 'EMI concerns'],
            'recommendations': ['Optimize power circuit', 'Add EMI shielding'],
            'analysis': 'Electrical system analysis...'
        },
        'programming': {
            'key_findings': ['Algorithm efficiency', 'Memory usage'],
            'recommendations': ['Optimize algorithms', 'Implement caching'],
            'analysis': 'Software architecture analysis...'
        }
    }
    
    visuals = generator.create_visual_summary('pdf', 'Smart Home System', mock_domain_outputs, 'test123')
    print("Generated visual content:", visuals)