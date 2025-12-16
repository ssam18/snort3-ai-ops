"""
SIEM Integration Connectors
Supports Splunk, Elastic Stack, and generic syslog
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

import structlog
import aiohttp

logger = structlog.get_logger(__name__)


class SIEMConnector(ABC):
    """Base class for SIEM connectors."""
    
    @abstractmethod
    async def send_event(self, event: Dict[str, Any]) -> bool:
        """Send a single event to the SIEM."""
        pass
    
    @abstractmethod
    async def send_batch(self, events: List[Dict[str, Any]]) -> bool:
        """Send multiple events to the SIEM."""
        pass


class SplunkConnector(SIEMConnector):
    """
    Splunk HTTP Event Collector (HEC) integration.
    
    Sends events to Splunk via HEC endpoint.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Splunk connector.
        
        Args:
            config: Configuration dict with host, token, index
        """
        self.host = config.get('host', 'https://localhost:8088')
        self.token = config.get('token')
        self.index = config.get('index', 'main')
        self.sourcetype = config.get('sourcetype', 'snort3:ai-ops')
        self.verify_ssl = config.get('verify_ssl', True)
        
        if not self.token:
            raise ValueError("Splunk HEC token is required")
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Splunk connector initialized", host=self.host, index=self.index)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers={
                    'Authorization': f'Splunk {self.token}',
                    'Content-Type': 'application/json'
                }
            )
        return self.session
    
    async def send_event(self, event: Dict[str, Any]) -> bool:
        """Send event to Splunk HEC."""
        try:
            session = await self._get_session()
            
            # Format for Splunk HEC
            hec_event = {
                'time': event.get('timestamp', datetime.utcnow().isoformat()),
                'source': 'snort3-ai-ops',
                'sourcetype': self.sourcetype,
                'index': self.index,
                'event': event
            }
            
            async with session.post(
                f'{self.host}/services/collector/event',
                json=hec_event,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.debug("Event sent to Splunk", event_id=event.get('id'))
                    return True
                else:
                    logger.error("Failed to send event to Splunk", 
                               status=response.status,
                               response=await response.text())
                    return False
                    
        except Exception as e:
            logger.error("Error sending event to Splunk", error=str(e))
            return False
    
    async def send_batch(self, events: List[Dict[str, Any]]) -> bool:
        """Send multiple events to Splunk HEC."""
        try:
            session = await self._get_session()
            
            # Format batch for Splunk HEC (newline-delimited JSON)
            batch_data = '\n'.join([
                json.dumps({
                    'time': event.get('timestamp', datetime.utcnow().isoformat()),
                    'source': 'snort3-ai-ops',
                    'sourcetype': self.sourcetype,
                    'index': self.index,
                    'event': event
                })
                for event in events
            ])
            
            async with session.post(
                f'{self.host}/services/collector/event',
                data=batch_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    logger.info("Event batch sent to Splunk", count=len(events))
                    return True
                else:
                    logger.error("Failed to send batch to Splunk",
                               status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Error sending batch to Splunk", error=str(e))
            return False
    
    async def close(self):
        """Close the connector."""
        if self.session and not self.session.closed:
            await self.session.close()


class ElasticConnector(SIEMConnector):
    """
    Elasticsearch integration for ELK stack.
    
    Sends events to Elasticsearch via REST API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Elastic connector.
        
        Args:
            config: Configuration dict with host, user, password, index
        """
        self.host = config.get('host', 'http://localhost:9200')
        self.user = config.get('user', 'elastic')
        self.password = config.get('password')
        self.index = config.get('index', 'snort3-ai-ops')
        self.verify_ssl = config.get('verify_ssl', True)
        
        if not self.password:
            raise ValueError("Elasticsearch password is required")
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Elasticsearch connector initialized", host=self.host, index=self.index)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            auth = aiohttp.BasicAuth(self.user, self.password)
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self.session = aiohttp.ClientSession(
                connector=connector,
                auth=auth,
                headers={'Content-Type': 'application/json'}
            )
        return self.session
    
    async def send_event(self, event: Dict[str, Any]) -> bool:
        """Send event to Elasticsearch."""
        try:
            session = await self._get_session()
            
            # Add timestamp if not present
            if '@timestamp' not in event:
                event['@timestamp'] = event.get('timestamp', datetime.utcnow().isoformat())
            
            async with session.post(
                f'{self.host}/{self.index}/_doc',
                json=event,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in (200, 201):
                    logger.debug("Event sent to Elasticsearch", event_id=event.get('id'))
                    return True
                else:
                    logger.error("Failed to send event to Elasticsearch",
                               status=response.status,
                               response=await response.text())
                    return False
                    
        except Exception as e:
            logger.error("Error sending event to Elasticsearch", error=str(e))
            return False
    
    async def send_batch(self, events: List[Dict[str, Any]]) -> bool:
        """Send multiple events to Elasticsearch using bulk API."""
        try:
            session = await self._get_session()
            
            # Format batch for Elasticsearch bulk API
            bulk_data = []
            for event in events:
                # Add timestamp if not present
                if '@timestamp' not in event:
                    event['@timestamp'] = event.get('timestamp', datetime.utcnow().isoformat())
                
                # Bulk API requires index action followed by document
                bulk_data.append(json.dumps({'index': {'_index': self.index}}))
                bulk_data.append(json.dumps(event))
            
            bulk_body = '\n'.join(bulk_data) + '\n'
            
            async with session.post(
                f'{self.host}/_bulk',
                data=bulk_body,
                headers={'Content-Type': 'application/x-ndjson'},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if not result.get('errors', False):
                        logger.info("Event batch sent to Elasticsearch", count=len(events))
                        return True
                    else:
                        logger.error("Some events failed in Elasticsearch bulk insert")
                        return False
                else:
                    logger.error("Failed to send batch to Elasticsearch",
                               status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Error sending batch to Elasticsearch", error=str(e))
            return False
    
    async def close(self):
        """Close the connector."""
        if self.session and not self.session.closed:
            await self.session.close()


class SyslogConnector(SIEMConnector):
    """
    Generic syslog integration.
    
    Sends events via syslog protocol for compatibility with various SIEMs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Syslog connector.
        
        Args:
            config: Configuration dict with host, port, protocol
        """
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 514)
        self.protocol = config.get('protocol', 'udp')  # udp or tcp
        self.facility = config.get('facility', 16)  # local0
        self.severity = config.get('severity', 5)  # notice
        
        logger.info("Syslog connector initialized", 
                   host=self.host, port=self.port, protocol=self.protocol)
    
    async def send_event(self, event: Dict[str, Any]) -> bool:
        """Send event via syslog."""
        try:
            # Format as JSON string for syslog message
            message = json.dumps(event)
            
            # Calculate syslog priority
            priority = self.facility * 8 + self.severity
            
            # Format syslog message (RFC 3164)
            timestamp = datetime.now().strftime('%b %d %H:%M:%S')
            syslog_msg = f"<{priority}>{timestamp} snort3-ai-ops: {message}\n"
            
            if self.protocol == 'tcp':
                reader, writer = await asyncio.open_connection(self.host, self.port)
                writer.write(syslog_msg.encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            else:  # UDP
                transport, protocol = await asyncio.get_event_loop().create_datagram_endpoint(
                    lambda: asyncio.DatagramProtocol(),
                    remote_addr=(self.host, self.port)
                )
                transport.sendto(syslog_msg.encode())
                transport.close()
            
            logger.debug("Event sent via syslog", event_id=event.get('id'))
            return True
            
        except Exception as e:
            logger.error("Error sending event via syslog", error=str(e))
            return False
    
    async def send_batch(self, events: List[Dict[str, Any]]) -> bool:
        """Send multiple events via syslog."""
        success_count = 0
        for event in events:
            if await self.send_event(event):
                success_count += 1
        
        if success_count == len(events):
            logger.info("Event batch sent via syslog", count=len(events))
            return True
        else:
            logger.warning("Partial batch sent via syslog", 
                         success=success_count, total=len(events))
            return False
    
    async def close(self):
        """Close the connector."""
        pass  # No persistent connection for syslog


def create_siem_connector(siem_type: str, config: Dict[str, Any]) -> SIEMConnector:
    """
    Factory function to create appropriate SIEM connector.
    
    Args:
        siem_type: Type of SIEM ('splunk', 'elastic', 'syslog')
        config: Configuration dictionary
    
    Returns:
        Appropriate SIEMConnector instance
    """
    connectors = {
        'splunk': SplunkConnector,
        'elastic': ElasticConnector,
        'elasticsearch': ElasticConnector,
        'elk': ElasticConnector,
        'syslog': SyslogConnector,
    }
    
    connector_class = connectors.get(siem_type.lower())
    if not connector_class:
        raise ValueError(f"Unknown SIEM type: {siem_type}")
    
    return connector_class(config)
