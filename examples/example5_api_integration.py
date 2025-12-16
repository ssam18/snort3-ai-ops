"""
Usage Example 5: API Integration
Demonstrates REST API integration for programmatic control
"""

import asyncio
import logging
import sys
import os
import aiohttp
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIOpsAPIClient:
    """Client for AI-Ops REST API"""
    
    def __init__(self, base_url='http://localhost:8080'):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()
    
    async def investigate(self, target, target_type='ip'):
        """Start an investigation"""
        url = f"{self.base_url}/api/v1/investigate"
        payload = {
            'target': target,
            'type': target_type
        }
        async with self.session.post(url, json=payload) as resp:
            return await resp.json()
    
    async def block_threat(self, indicator, reason, duration='1h'):
        """Block a threat indicator"""
        url = f"{self.base_url}/api/v1/block"
        payload = {
            'indicator': indicator,
            'reason': reason,
            'duration': duration
        }
        async with self.session.post(url, json=payload) as resp:
            return await resp.json()
    
    async def get_incidents(self, severity=None, limit=10):
        """Get recent incidents"""
        url = f"{self.base_url}/api/v1/incidents"
        params = {'limit': limit}
        if severity:
            params['severity'] = severity
        async with self.session.get(url, params=params) as resp:
            return await resp.json()
    
    async def get_stats(self):
        """Get system statistics"""
        url = f"{self.base_url}/api/v1/stats"
        async with self.session.get(url) as resp:
            return await resp.json()


async def main():
    """Example 5: API integration"""
    
    print("=" * 70)
    print("USAGE EXAMPLE 5: API Integration")
    print("=" * 70)
    print()
    print("This example demonstrates programmatic control via REST API:")
    print("  ✓ Start investigations")
    print("  ✓ Block threats")
    print("  ✓ Query incidents")
    print("  ✓ Retrieve statistics")
    print()
    print("Useful for integrating with:")
    print("  - SIEM systems")
    print("  - Ticketing platforms")
    print("  - Custom dashboards")
    print("  - Automation scripts")
    print()
    print("-" * 70)
    
    try:
        async with AIOpsAPIClient() as api:
            # 1. Get system statistics
            logger.info("\n1. Fetching system statistics...")
            stats = await api.get_stats()
            logger.info(f"  Events Processed: {stats.get('events_processed', 0)}")
            logger.info(f"  Incidents Created: {stats.get('incidents_created', 0)}")
            logger.info(f"  Threats Blocked: {stats.get('threats_blocked', 0)}")
            logger.info(f"  Uptime: {stats.get('uptime_seconds', 0)/3600:.1f} hours")
            
            # 2. Query recent incidents
            logger.info("\n2. Querying high-severity incidents...")
            incidents = await api.get_incidents(severity='high', limit=5)
            logger.info(f"  Found {len(incidents)} high-severity incidents")
            for inc in incidents[:3]:
                logger.info(f"    - {inc['id']}: {inc['signature']} "
                           f"(Score: {inc['threat_score']})")
            
            # 3. Start investigation
            logger.info("\n3. Starting investigation of suspicious IP...")
            target_ip = '192.168.1.100'
            inv_result = await api.investigate(target_ip, 'ip')
            logger.info(f"  Investigation ID: {inv_result.get('investigation_id', 'N/A')}")
            logger.info(f"  Status: {inv_result.get('status', 'N/A')}")
            logger.info(f"  Estimated completion: {inv_result.get('estimated_completion', 'N/A')}")
            
            # 4. Block malicious indicator
            logger.info("\n4. Blocking malicious IP address...")
            block_result = await api.block_threat(
                indicator='203.0.113.45',
                reason='Known C2 server',
                duration='24h'
            )
            logger.info(f"  Block status: {block_result.get('status', 'N/A')}")
            logger.info(f"  Rule ID: {block_result.get('rule_id', 'N/A')}")
            logger.info(f"  Expires at: {block_result.get('expires_at', 'N/A')}")
            
            # 5. Continuous monitoring example
            logger.info("\n5. Monitoring for new incidents (10 iterations)...")
            logger.info("  Press Ctrl+C to stop early")
            
            for i in range(10):
                await asyncio.sleep(5)
                stats = await api.get_stats()
                logger.info(f"  [{i+1}/10] Events: {stats.get('events_processed', 0)} | "
                           f"Incidents: {stats.get('incidents_created', 0)}")
            
            logger.info("\n✓ API integration examples completed!")
            logger.info("\nAPI Endpoints demonstrated:")
            logger.info("  GET  /api/v1/stats")
            logger.info("  GET  /api/v1/incidents")
            logger.info("  POST /api/v1/investigate")
            logger.info("  POST /api/v1/block")
            
    except aiohttp.ClientError as e:
        logger.error(f"API connection error: {e}")
        logger.error("Make sure the API server is running on http://localhost:8080")
        return 1
    except KeyboardInterrupt:
        logger.info("\n\nStopped by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
