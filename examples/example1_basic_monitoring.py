"""
Usage Example 1: Basic Event Monitoring
Demonstrates the AI-Ops engine processing Snort3 events automatically
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AIOpsEngine
from core.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Example 1: Basic event monitoring with all 5 agents"""
    
    print("=" * 70)
    print("USAGE EXAMPLE 1: Basic Event Monitoring")
    print("=" * 70)
    print()
    print("This example demonstrates:")
    print("  ✓ Automatic event processing from Snort3")
    print("  ✓ Threat intelligence enrichment")
    print("  ✓ Behavioral analysis")
    print("  ✓ Automated incident response")
    print("  ✓ Report generation")
    print()
    print("All 5 AI agents are working together:")
    print("  1. Threat Intelligence Agent - Enriches IOCs")
    print("  2. Behavioral Analysis Agent - Detects anomalies")
    print("  3. Response Orchestrator Agent - Coordinates actions")
    print("  4. Rule Optimization Agent - Tunes detection rules")
    print("  5. Report Generation Agent - Creates reports")
    print()
    print("-" * 70)
    
    try:
        # Load configuration
        config_path = os.getenv('CONFIG_PATH', 'config/config.yaml')
        config = load_config(config_path)
        
        logger.info("Initializing AI-Ops Engine...")
        engine = AIOpsEngine(config)
        
        # Start the engine
        logger.info("Starting AI-Ops Engine with all 5 agents...")
        await engine.start()
        
        logger.info("✓ AI-Ops Engine is now running!")
        logger.info("✓ All agents are actively monitoring events")
        logger.info("")
        logger.info("Monitoring events (Press Ctrl+C to stop)...")
        logger.info("-" * 70)
        
        # Keep running
        while True:
            await asyncio.sleep(10)
            
            # Show stats every 10 seconds
            stats = engine.get_stats()
            logger.info(f"Events Processed: {stats.get('events_processed', 0)} | "
                       f"Incidents: {stats.get('incidents_created', 0)} | "
                       f"Threats Blocked: {stats.get('threats_blocked', 0)}")
            
    except KeyboardInterrupt:
        logger.info("\n\nShutting down gracefully...")
        await engine.stop()
        logger.info("✓ AI-Ops Engine stopped")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
