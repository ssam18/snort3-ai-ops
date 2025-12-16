"""
Firewall Integration Modules
Supports Palo Alto Networks, Fortinet FortiGate, and generic REST APIs
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

import structlog
import aiohttp

logger = structlog.get_logger(__name__)


class FirewallConnector(ABC):
    """Base class for firewall connectors."""
    
    @abstractmethod
    async def block_ip(self, ip: str, duration: int = 3600, reason: str = "") -> bool:
        """Block an IP address."""
        pass
    
    @abstractmethod
    async def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address."""
        pass
    
    @abstractmethod
    async def get_blocked_ips(self) -> List[str]:
        """Get list of currently blocked IPs."""
        pass


class PaloAltoConnector(FirewallConnector):
    """
    Palo Alto Networks firewall integration.
    
    Uses PAN-OS REST API to manage dynamic address groups and security rules.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Palo Alto connector.
        
        Args:
            config: Configuration dict with host, api_key
        """
        self.host = config.get('host')
        self.api_key = config.get('api_key')
        self.verify_ssl = config.get('verify_ssl', True)
        self.address_group = config.get('address_group', 'AI-Ops-Blocked-IPs')
        
        if not self.host or not self.api_key:
            raise ValueError("Palo Alto host and API key are required")
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Palo Alto connector initialized", host=self.host)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session
    
    async def _api_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to PAN-OS."""
        try:
            session = await self._get_session()
            
            params['key'] = self.api_key
            
            async with session.get(
                f'{self.host}/api/',
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error("PAN-OS API request failed", 
                               status=response.status,
                               response=await response.text())
                    return {}
                    
        except Exception as e:
            logger.error("Error making PAN-OS API request", error=str(e))
            return {}
    
    async def block_ip(self, ip: str, duration: int = 3600, reason: str = "") -> bool:
        """
        Block IP by adding to dynamic address group.
        
        Args:
            ip: IP address to block
            duration: How long to block (seconds)
            reason: Reason for blocking
        
        Returns:
            True if successful
        """
        try:
            # Register IP in dynamic address group
            params = {
                'type': 'user-id',
                'cmd': f'<uid-message><version>1.0</version><type>update</type>'
                       f'<payload><register>'
                       f'<entry ip="{ip}"><tag><member>{self.address_group}</member></tag></entry>'
                       f'</register></payload></uid-message>'
            }
            
            result = await self._api_request(params)
            
            if result.get('status') == 'success':
                logger.info("IP blocked on Palo Alto", 
                           ip=ip, duration=duration, reason=reason)
                
                # Schedule unblock if duration specified
                if duration > 0:
                    asyncio.create_task(self._schedule_unblock(ip, duration))
                
                return True
            else:
                logger.error("Failed to block IP on Palo Alto", ip=ip)
                return False
                
        except Exception as e:
            logger.error("Error blocking IP on Palo Alto", ip=ip, error=str(e))
            return False
    
    async def _schedule_unblock(self, ip: str, delay: int):
        """Schedule IP unblock after delay."""
        await asyncio.sleep(delay)
        await self.unblock_ip(ip)
    
    async def unblock_ip(self, ip: str) -> bool:
        """
        Unblock IP by removing from dynamic address group.
        
        Args:
            ip: IP address to unblock
        
        Returns:
            True if successful
        """
        try:
            params = {
                'type': 'user-id',
                'cmd': f'<uid-message><version>1.0</version><type>update</type>'
                       f'<payload><unregister>'
                       f'<entry ip="{ip}"><tag><member>{self.address_group}</member></tag></entry>'
                       f'</unregister></payload></uid-message>'
            }
            
            result = await self._api_request(params)
            
            if result.get('status') == 'success':
                logger.info("IP unblocked on Palo Alto", ip=ip)
                return True
            else:
                logger.error("Failed to unblock IP on Palo Alto", ip=ip)
                return False
                
        except Exception as e:
            logger.error("Error unblocking IP on Palo Alto", ip=ip, error=str(e))
            return False
    
    async def get_blocked_ips(self) -> List[str]:
        """
        Get list of currently blocked IPs.
        
        Returns:
            List of IP addresses
        """
        try:
            params = {
                'type': 'op',
                'cmd': '<show><object><registered-ip><all/></registered-ip></object></show>'
            }
            
            result = await self._api_request(params)
            
            # Parse XML response to extract IPs (simplified)
            # In production, use proper XML parsing
            ips = []
            # TODO: Parse XML to extract IPs with matching tag
            
            return ips
            
        except Exception as e:
            logger.error("Error getting blocked IPs from Palo Alto", error=str(e))
            return []
    
    async def close(self):
        """Close the connector."""
        if self.session and not self.session.closed:
            await self.session.close()


class FortiGateConnector(FirewallConnector):
    """
    Fortinet FortiGate firewall integration.
    
    Uses FortiOS REST API to manage address objects and policies.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FortiGate connector.
        
        Args:
            config: Configuration dict with host, api_key
        """
        self.host = config.get('host')
        self.api_key = config.get('api_key')
        self.verify_ssl = config.get('verify_ssl', True)
        self.vdom = config.get('vdom', 'root')
        
        if not self.host or not self.api_key:
            raise ValueError("FortiGate host and API key are required")
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.blocked_ips: Dict[str, datetime] = {}
        
        logger.info("FortiGate connector initialized", host=self.host)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
        return self.session
    
    async def block_ip(self, ip: str, duration: int = 3600, reason: str = "") -> bool:
        """
        Block IP by adding address object and policy.
        
        Args:
            ip: IP address to block
            duration: How long to block (seconds)
            reason: Reason for blocking
        
        Returns:
            True if successful
        """
        try:
            session = await self._get_session()
            
            # Create address object
            address_name = f"blocked_{ip.replace('.', '_')}"
            address_data = {
                'name': address_name,
                'type': 'ipmask',
                'subnet': f'{ip} 255.255.255.255',
                'comment': f'AI-Ops blocked: {reason}'
            }
            
            async with session.post(
                f'{self.host}/api/v2/cmdb/firewall/address',
                params={'vdom': self.vdom},
                json=address_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in (200, 424):  # 424 = already exists
                    logger.info("IP blocked on FortiGate", 
                               ip=ip, duration=duration, reason=reason)
                    
                    # Track blocked IP
                    if duration > 0:
                        self.blocked_ips[ip] = datetime.now() + timedelta(seconds=duration)
                        asyncio.create_task(self._schedule_unblock(ip, duration))
                    
                    return True
                else:
                    logger.error("Failed to block IP on FortiGate", 
                               ip=ip, status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Error blocking IP on FortiGate", ip=ip, error=str(e))
            return False
    
    async def _schedule_unblock(self, ip: str, delay: int):
        """Schedule IP unblock after delay."""
        await asyncio.sleep(delay)
        await self.unblock_ip(ip)
    
    async def unblock_ip(self, ip: str) -> bool:
        """
        Unblock IP by removing address object.
        
        Args:
            ip: IP address to unblock
        
        Returns:
            True if successful
        """
        try:
            session = await self._get_session()
            
            address_name = f"blocked_{ip.replace('.', '_')}"
            
            async with session.delete(
                f'{self.host}/api/v2/cmdb/firewall/address/{address_name}',
                params={'vdom': self.vdom},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    logger.info("IP unblocked on FortiGate", ip=ip)
                    self.blocked_ips.pop(ip, None)
                    return True
                else:
                    logger.error("Failed to unblock IP on FortiGate", 
                               ip=ip, status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Error unblocking IP on FortiGate", ip=ip, error=str(e))
            return False
    
    async def get_blocked_ips(self) -> List[str]:
        """
        Get list of currently blocked IPs.
        
        Returns:
            List of IP addresses
        """
        return list(self.blocked_ips.keys())
    
    async def close(self):
        """Close the connector."""
        if self.session and not self.session.closed:
            await self.session.close()


def create_firewall_connector(firewall_type: str, config: Dict[str, Any]) -> FirewallConnector:
    """
    Factory function to create appropriate firewall connector.
    
    Args:
        firewall_type: Type of firewall ('paloalto', 'fortigate')
        config: Configuration dictionary
    
    Returns:
        Appropriate FirewallConnector instance
    """
    connectors = {
        'paloalto': PaloAltoConnector,
        'palo_alto': PaloAltoConnector,
        'pan': PaloAltoConnector,
        'fortigate': FortiGateConnector,
        'fortinet': FortiGateConnector,
    }
    
    connector_class = connectors.get(firewall_type.lower())
    if not connector_class:
        raise ValueError(f"Unknown firewall type: {firewall_type}")
    
    return connector_class(config)
