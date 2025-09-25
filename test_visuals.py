#!/usr/bin/env python3
"""
Test Visual Content Generation
Verify that all visual components work properly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from visual_generator import VisualContentGenerator

def test_visual_generation():
    """Test all visual generation functions"""
    
    print("🎨 Testing Visual Content Generation...")
    
    # Initialize generator
    generator = VisualContentGenerator()
    
    # Mock domain outputs for testing
    mock_domain_outputs = {
        'mechanical': {
            'key_findings': [
                'High stress concentration at joint connections',
                'Material fatigue risk in cyclic loading conditions',
                'Thermal expansion concerns in multi-material assembly',
                'Vibration resonance at operational frequency'
            ],
            'recommendations': [
                'Use stronger alloy (e.g., titanium-aluminum composite)',
                'Implement stress relief features in critical joints',
                'Add thermal compensation mechanisms'
            ],
            'next_steps': [
                'Conduct finite element analysis',
                'Prototype testing with accelerated fatigue'
            ],
            'analysis': 'Comprehensive mechanical analysis reveals critical stress points in the design. The current material selection may not withstand long-term operational loads. Recommend immediate design optimization focusing on stress distribution and material upgrade.'
        },
        'electrical': {
            'key_findings': [
                'Power consumption exceeds initial specifications by 15%',
                'EMI interference from switching power supply',
                'Heat generation in power management circuit',
                'Signal integrity issues at high frequencies'
            ],
            'recommendations': [
                'Optimize power circuit with advanced switching topology',
                'Add EMI shielding and filtering components',
                'Implement thermal management for power components'
            ],
            'next_steps': [
                'EMC testing and certification',
                'Power efficiency optimization'
            ],
            'analysis': 'Electrical system analysis indicates power inefficiencies and electromagnetic compatibility concerns. The current power management approach needs refinement to meet regulatory standards and operational requirements.'
        },
        'programming': {
            'key_findings': [
                'Algorithm efficiency can be improved by 40%',
                'Memory usage spikes during data processing',
                'Real-time performance constraints in critical paths',
                'API response times exceed acceptable thresholds'
            ],
            'recommendations': [
                'Implement optimized algorithms (e.g., advanced caching)',
                'Add memory pooling and garbage collection tuning',
                'Optimize critical code paths with profiling data'
            ],
            'next_steps': [
                'Performance profiling and optimization',
                'Load testing with realistic data sets'
            ],
            'analysis': 'Software architecture analysis reveals performance bottlenecks in data processing and API response handling. Current implementation needs algorithmic improvements and memory optimization to meet scalability requirements.'
        }
    }
    
    test_cases = [
        ('pdf', 'Smart Home Automation System'),
        ('diagram', 'Industrial IoT Sensor Network'),  
        ('powerpoint', 'Autonomous Vehicle Control System'),
        ('word', 'Renewable Energy Management Platform'),
        ('project', 'AI-Powered Robotics Platform')
    ]
    
    for workflow_type, query in test_cases:
        print(f"\n📊 Testing {workflow_type.upper()} workflow with: {query}")
        
        try:
            # Generate visual content
            visual_content = generator.create_visual_summary(
                workflow_type, query, mock_domain_outputs, f'test_{workflow_type}'
            )
            
            print(f"✅ Generated visual content for {workflow_type}")
            print(f"   Workflow diagram: {'✓' if 'workflow_diagram' in visual_content else '✗'}")
            print(f"   Specific content: {'✓' if visual_content.get('generated_visuals') else '✗'}")
            print(f"   Generated items: {visual_content.get('generated_visuals', [])}")
            
            # Verify files were created
            if 'workflow_diagram' in visual_content:
                workflow_path = Path(visual_content['workflow_diagram'])
                if workflow_path.exists():
                    print(f"   📁 Workflow diagram saved: {workflow_path.name}")
                else:
                    print(f"   ❌ Workflow diagram file not found: {workflow_path}")
            
        except Exception as e:
            print(f"❌ Error testing {workflow_type}: {e}")
    
    print(f"\n📁 Visual outputs directory: {generator.output_dir}")
    print(f"Generated files:")
    for file_path in generator.output_dir.glob("*.png"):
        print(f"   📄 {file_path.name}")
    
    print("\n🎉 Visual generation testing completed!")

if __name__ == "__main__":
    test_visual_generation()