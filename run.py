"""
Command-line interface for Multi-Domain Specialized Agent System
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path

# Import the notebook as a module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # These imports assume the notebook has been converted to a module
    # You might need to do this conversion first using nbconvert
    from Meta_model import EnhancedMultiDomainSystem, InteractiveInterface, AgentType
    HAS_IMPORTS = True
except ImportError:
    HAS_IMPORTS = False
    print("⚠️  Could not import from Meta_model. Make sure it's been converted to a module.")
    print("   You can do this with: jupyter nbconvert --to python Meta_model.ipynb")

# Configuration
CONFIG_PATH = Path("./config/config.json")

def load_config():
    """Load configuration from file or use defaults"""
    default_config = {
        "llm": {
            "use_real_llm": False,
            "model_name": "llama3.2",
            "base_url": "http://localhost:11434",
            "temperature": 0.7
        },
        "agents": {
            "use_real_agents": False,
            "api_config_path": "./config/agent_api_config.json"
        },
        "storage": {
            "data_dir": "./data",
            "save_prompts": True,
            "save_outputs": True
        }
    }
    
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
            return default_config
    else:
        return default_config

async def run_interactive_mode():
    """Run the system in interactive mode"""
    if not HAS_IMPORTS:
        print("❌ Cannot run interactive mode without proper imports.")
        return
    
    config = load_config()
    system = EnhancedMultiDomainSystem(
        use_real_agents=config["agents"]["use_real_agents"],
        use_mock_llm=not config["llm"]["use_real_llm"]
    )
    
    try:
        await system.setup()
        interface = InteractiveInterface(system)
        
        print("\n🌟 MULTI-DOMAIN SPECIALIZED AGENT SYSTEM 🌟")
        print("=" * 60)
        print("Type your engineering request, or /help for commands.")
        print("Type 'exit' to quit.")
        
        while True:
            user_input = input("\n👤 > ")
            if user_input.lower().strip() in ["exit", "quit"]:
                break
            
            response = await interface.process_input(user_input)
            print(f"\n🤖 > {response}")
    except KeyboardInterrupt:
        print("\nSession terminated by user.")
    finally:
        await system.close()
        print("Session ended.")

async def run_batch_mode(input_file, output_dir, agents=None):
    """Run the system in batch mode with a file of queries"""
    if not HAS_IMPORTS:
        print("❌ Cannot run batch mode without proper imports.")
        return
    
    config = load_config()
    system = EnhancedMultiDomainSystem(
        use_real_agents=config["agents"]["use_real_agents"],
        use_mock_llm=not config["llm"]["use_real_llm"]
    )
    
    await system.setup()
    
    try:
        with open(input_file, 'r') as f:
            queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not agents:
            agents = [at.value for at in AgentType]
            
        os.makedirs(output_dir, exist_ok=True)
            
        for i, query in enumerate(queries, 1):
            print(f"\n🔄 Processing query {i}/{len(queries)}: {query[:50]}...")
            
            # Process query
            state = await system.process_user_query(query)
            
            # Save state
            state_file = state.save_to_json(f"{output_dir}/query_{i}_state.json")
            print(f"  ✅ State saved to {state_file}")
            
            # Execute requested agents
            for agent_type in agents:
                try:
                    print(f"  🚀 Executing {agent_type} agent...")
                    output = await system.execute_agent(agent_type)
                    print(f"  ✅ {agent_type.capitalize()} generated: {output.file_path}")
                except Exception as e:
                    print(f"  ❌ Error executing {agent_type}: {e}")
            
            print(f"✅ Query {i} processing complete")
    finally:
        await system.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Multi-Domain Specialized Agent System")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--batch", "-b", help="Run in batch mode with a file of queries")
    parser.add_argument("--output", "-o", default="./output", help="Output directory for batch mode")
    parser.add_argument("--agents", "-a", nargs="+", help="Agents to execute in batch mode")
    
    args = parser.parse_args()
    
    if not HAS_IMPORTS:
        print("\nTo use this script, you need to convert the notebook to a Python module first:")
        print("  jupyter nbconvert --to python Meta_model.ipynb")
        print("Then ensure all dependencies are installed:")
        print("  pip install langchain aiohttp")
        return
    
    if args.interactive:
        asyncio.run(run_interactive_mode())
    elif args.batch:
        if not os.path.exists(args.batch):
            print(f"❌ Input file not found: {args.batch}")
            return
        asyncio.run(run_batch_mode(args.batch, args.output, args.agents))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
