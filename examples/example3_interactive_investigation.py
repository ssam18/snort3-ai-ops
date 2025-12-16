"""
Usage Example 3: Interactive Investigation
Demonstrates using the Investigation Crew for manual threat hunting
"""

import asyncio
import logging
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AIOpsEngine
from core.investigation import InvestigationCrew

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def investigate_ip(ip_address: str, timerange: str, depth: str):
    """Investigate a specific IP address"""
    
    print(f"\n{'=' * 70}")
    print(f"Investigating IP: {ip_address}")
    print(f"Timerange: {timerange} | Depth: {depth}")
    print('=' * 70)
    print()
    
    # Create investigation crew
    crew = InvestigationCrew()
    
    logger.info(f"Starting investigation of {ip_address}...")
    logger.info("Agents involved:")
    logger.info("  1. Threat Intelligence Agent - Checking reputation")
    logger.info("  2. Behavioral Analysis Agent - Analyzing patterns")
    logger.info("  3. Forensics Agent - Deep investigation")
    print()
    
    # Run investigation
    result = await crew.investigate_ip(
        ip_address=ip_address,
        timerange=timerange,
        depth=depth
    )
    
    print("\n" + "=" * 70)
    print("INVESTIGATION RESULTS")
    print("=" * 70)
    print()
    print(f"Summary:\n{result.summary}")
    print()
    print(f"Threat Score: {result.threat_score}/100")
    print()
    print("Recommendations:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")
    print()
    print("Detailed Findings:")
    print(json.dumps(result.details, indent=2))
    print()
    print("=" * 70)
    
    return result


async def main():
    """Example 3: Interactive investigation"""
    
    print("=" * 70)
    print("USAGE EXAMPLE 3: Interactive Investigation")
    print("=" * 70)
    print()
    print("This example demonstrates manual threat hunting using")
    print("the Investigation Crew (multi-agent collaboration)")
    print()
    print("-" * 70)
    
    # Example investigations
    investigations = [
        {
            'ip': '192.168.1.100',
            'timerange': '24h',
            'depth': 'quick'
        },
        {
            'ip': '203.0.113.45',
            'timerange': '7d',
            'depth': 'thorough'
        },
        {
            'ip': '198.51.100.88',
            'timerange': '1h',
            'depth': 'deep'
        }
    ]
    
    try:
        for inv in investigations:
            result = await investigate_ip(
                ip_address=inv['ip'],
                timerange=inv['timerange'],
                depth=inv['depth']
            )
            
            # Wait before next investigation
            await asyncio.sleep(2)
        
        logger.info("\n✓ All investigations completed!")
        
    except Exception as e:
        logger.error(f"Investigation error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
