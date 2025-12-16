"""
Usage Example 2: Custom Workflow
Demonstrates creating a custom security workflow for web application protection
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AIOpsEngine
from core.config import load_config
from core.workflows import CustomWorkflow, WorkflowTrigger, WorkflowAction

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Example 2: Custom workflow for web application protection"""
    
    print("=" * 70)
    print("USAGE EXAMPLE 2: Custom Workflow - Web App Protection")
    print("=" * 70)
    print()
    print("This example creates a custom workflow that:")
    print("  ✓ Triggers on HTTP alerts, SQL injection, and XSS attempts")
    print("  ✓ Engages Threat Intel, Behavioral, and Response agents")
    print("  ✓ Executes automated actions:")
    print("    - Block malicious IPs")
    print("    - Notify admin")
    print("    - Update WAF rules")
    print()
    print("-" * 70)
    
    try:
        # Load configuration
        config = load_config('config/config.yaml')
        
        # Define custom workflow
        logger.info("Creating custom web app protection workflow...")
        
        workflow = CustomWorkflow(
            name='web_application_protection',
            description='Protect web applications from common attacks',
            
            # Triggers - what events activate this workflow
            triggers=[
                WorkflowTrigger(
                    event_type='http_alert',
                    conditions={'severity': ['high', 'critical']}
                ),
                WorkflowTrigger(
                    event_type='sql_injection',
                    conditions={}
                ),
                WorkflowTrigger(
                    event_type='xss_attempt',
                    conditions={}
                )
            ],
            
            # Agents - which agents to involve
            agents=['threat_intel', 'behavioral', 'response'],
            
            # Actions - what to do when triggered
            actions=[
                WorkflowAction(
                    name='block_ip',
                    params={'duration': '1h', 'scope': 'global'}
                ),
                WorkflowAction(
                    name='notify_admin',
                    params={'priority': 'high', 'channel': 'email'}
                ),
                WorkflowAction(
                    name='update_waf',
                    params={'ruleset': 'web_attacks'}
                )
            ]
        )
        
        logger.info(f"✓ Workflow created: {workflow.name}")
        logger.info(f"  Triggers: {len(workflow.triggers)}")
        logger.info(f"  Agents: {', '.join(workflow.agents)}")
        logger.info(f"  Actions: {len(workflow.actions)}")
        print()
        
        # Initialize engine and deploy workflow
        logger.info("Deploying workflow to AI-Ops Engine...")
        engine = AIOpsEngine(config)
        engine.add_workflow(workflow)
        
        logger.info("✓ Workflow deployed successfully")
        print()
        
        # Start the engine
        logger.info("Starting AI-Ops Engine with custom workflow...")
        await engine.start()
        
        logger.info("✓ Custom workflow is now active!")
        logger.info("")
        logger.info("Monitoring for web application attacks...")
        logger.info("  - SQL Injection attempts")
        logger.info("  - Cross-Site Scripting (XSS)")
        logger.info("  - HTTP anomalies")
        logger.info("")
        logger.info("Press Ctrl+C to stop...")
        logger.info("-" * 70)
        
        # Keep running and show workflow activations
        while True:
            await asyncio.sleep(5)
            
            workflow_stats = engine.get_workflow_stats(workflow.name)
            if workflow_stats:
                logger.info(f"Workflow '{workflow.name}': "
                           f"Triggered {workflow_stats.get('triggers', 0)} times | "
                           f"Actions executed: {workflow_stats.get('actions', 0)}")
            
    except KeyboardInterrupt:
        logger.info("\n\nShutting down...")
        await engine.stop()
        logger.info("✓ Stopped")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
