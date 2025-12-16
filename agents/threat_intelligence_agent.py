"""Threat Intelligence Agent for IOC enrichment and threat analysis."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, UTC

import structlog
from crewai import Agent, Task
from crewai.tools import tool

from core.config import ThreatIntelConfig

logger = structlog.get_logger(__name__)


class ThreatIntelligenceAgent:
    """Agent for threat intelligence enrichment and IOC analysis."""
    
    def __init__(self, config: ThreatIntelConfig):
        """
        Initialize the Threat Intelligence Agent.
        
        Args:
            config: Threat intelligence configuration
        """
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.agent: Optional[Agent] = None
        
        # Initialize API clients (stubs for now)
        self.api_clients = self._initialize_api_clients()
        
        logger.info("Threat Intelligence Agent initialized")
    
    def _initialize_api_clients(self) -> Dict[str, Any]:
        """Initialize API clients for threat intelligence feeds."""
        clients = {}
        
        # Note: In production, these would be actual API client instances
        if self.config.api_keys.get('virustotal'):
            clients['virustotal'] = {'enabled': True}
            logger.info("VirusTotal client initialized")
        
        if self.config.api_keys.get('abuseipdb'):
            clients['abuseipdb'] = {'enabled': True}
            logger.info("AbuseIPDB client initialized")
        
        if self.config.api_keys.get('alienvault_otx'):
            clients['otx'] = {'enabled': True}
            logger.info("AlienVault OTX client initialized")
        
        if self.config.api_keys.get('shodan'):
            clients['shodan'] = {'enabled': True}
            logger.info("Shodan client initialized")
        
        return clients
    
    def get_crewai_agent(self) -> Agent:
        """Get the CrewAI agent instance."""
        if self.agent is None:
            self.agent = Agent(
                role='Threat Intelligence Analyst',
                goal='Enrich security events with threat intelligence and assess threat levels',
                backstory="""You are an expert threat intelligence analyst with access to 
                multiple threat feeds and databases. Your mission is to quickly enrich IOCs 
                (IP addresses, domains, file hashes) with relevant threat intelligence and 
                provide accurate threat assessments.""",
                verbose=True,
                allow_delegation=False,
                tools=[self._create_lookup_tool()]
            )
        return self.agent
    
    def _create_lookup_tool(self):
        """Create a tool for threat intelligence lookup."""
        @tool("Threat Intelligence Lookup")
        def lookup_ioc(ioc: str, ioc_type: str) -> Dict[str, Any]:
            """
            Look up an Indicator of Compromise in threat intelligence feeds.
            
            Args:
                ioc: The indicator (IP, domain, hash, etc.)
                ioc_type: Type of indicator (ip, domain, hash, url)
            
            Returns:
                Threat intelligence data
            """
            # This would call actual APIs in production
            return {
                'ioc': ioc,
                'type': ioc_type,
                'threat_score': 75,
                'reputation': 'malicious',
                'sources': ['virustotal', 'abuseipdb'],
                'first_seen': '2025-01-01',
                'last_seen': '2025-12-11'
            }
        
        return lookup_ioc
    
    async def enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich an event with threat intelligence.
        
        Args:
            event: Event data dictionary
        
        Returns:
            Enrichment data
        """
        enrichment = {
            'timestamp': datetime.now(UTC).isoformat(),
            'iocs': [],
            'threat_score': 0,
            'recommendations': []
        }
        
        # Extract IOCs from event
        src_ip = event.get('src_ip')
        dst_ip = event.get('dst_ip')
        domain = event.get('domain')
        
        # Check cache first
        iocs_to_check = []
        if src_ip:
            iocs_to_check.append(('ip', src_ip))
        if dst_ip:
            iocs_to_check.append(('ip', dst_ip))
        if domain:
            iocs_to_check.append(('domain', domain))
        
        # Lookup IOCs
        for ioc_type, ioc_value in iocs_to_check:
            cache_key = f"{ioc_type}:{ioc_value}"
            
            if cache_key in self.cache:
                # Check if cache is still valid
                cached_data = self.cache[cache_key]
                cache_age = datetime.utcnow() - datetime.fromisoformat(cached_data['cached_at'])
                if cache_age.total_seconds() < self.config.cache_ttl:
                    ioc_data = cached_data['data']
                    logger.debug("Using cached threat intel", ioc=ioc_value, type=ioc_type)
                else:
                    ioc_data = await self._lookup_ioc(ioc_value, ioc_type)
                    self._cache_result(cache_key, ioc_data)
            else:
                ioc_data = await self._lookup_ioc(ioc_value, ioc_type)
                self._cache_result(cache_key, ioc_data)
            
            enrichment['iocs'].append(ioc_data)
            enrichment['threat_score'] = max(enrichment['threat_score'], ioc_data.get('threat_score', 0))
        
        # Generate recommendations based on threat score
        if enrichment['threat_score'] >= 80:
            enrichment['recommendations'].append('BLOCK_IMMEDIATELY')
            enrichment['recommendations'].append('CREATE_INCIDENT')
        elif enrichment['threat_score'] >= 50:
            enrichment['recommendations'].append('MONITOR_CLOSELY')
            enrichment['recommendations'].append('NOTIFY_ANALYST')
        
        logger.info(
            "Event enriched with threat intelligence",
            event_id=event.get('id'),
            threat_score=enrichment['threat_score'],
            ioc_count=len(enrichment['iocs'])
        )
        
        return enrichment
    
    async def _lookup_ioc(self, ioc: str, ioc_type: str) -> Dict[str, Any]:
        """
        Lookup an IOC across multiple threat intelligence sources.
        
        Args:
            ioc: The indicator value
            ioc_type: Type of indicator
        
        Returns:
            IOC intelligence data
        """
        # Simulate API lookup delay
        await asyncio.sleep(0.1)
        
        # In production, this would query actual APIs
        # For now, return mock data
        result = {
            'value': ioc,
            'type': ioc_type,
            'threat_score': 0,
            'malicious': False,
            'sources': {},
            'tags': [],
            'first_seen': None,
            'last_seen': None
        }
        
        # Simulate scoring logic
        if ioc_type == 'ip':
            # Mock scoring for demonstration
            if ioc.startswith('10.') or ioc.startswith('192.168.'):
                result['threat_score'] = 10
                result['tags'].append('private_ip')
            else:
                result['threat_score'] = 45
                result['sources']['abuseipdb'] = {'confidence': 70, 'reports': 5}
        
        logger.debug("IOC lookup completed", ioc=ioc, type=ioc_type, score=result['threat_score'])
        
        return result
    
    def _cache_result(self, key: str, data: Dict[str, Any]) -> None:
        """Cache threat intelligence result."""
        self.cache[key] = {
            'cached_at': datetime.now(UTC).isoformat(),
            'data': data
        }
    
    async def stop(self) -> None:
        """Stop the agent and cleanup resources."""
        logger.info("Threat Intelligence Agent stopped")
