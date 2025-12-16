"""Response Orchestrator Agent for incident response automation."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

import structlog
from crewai import Agent
from crewai.tools import tool

from core.config import ResponseConfig

logger = structlog.get_logger(__name__)


class ResponseAction(Enum):
    """Available response actions."""
    BLOCK_IP = "block_ip"
    CREATE_TICKET = "create_ticket"
    NOTIFY_ADMIN = "notify_admin"
    UPDATE_FIREWALL = "update_firewall"
    ISOLATE_HOST = "isolate_host"
    LOG_ONLY = "log_only"


class ResponseOrchestratorAgent:
    """Agent for orchestrating automated incident response."""
    
    def __init__(self, config: ResponseConfig, dry_run: bool = False):
        """
        Initialize the Response Orchestrator Agent.
        
        Args:
            config: Response configuration
            dry_run: If True, don't execute actual actions
        """
        self.config = config
        self.dry_run = dry_run
        self.agent: Optional[Agent] = None
        self.active_responses: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Response Orchestrator Agent initialized", dry_run=dry_run)
    
    def get_crewai_agent(self) -> Agent:
        """Get the CrewAI agent instance."""
        if self.agent is None:
            self.agent = Agent(
                role='Incident Response Coordinator',
                goal='Orchestrate appropriate security responses to detected threats',
                backstory="""You are an experienced incident response coordinator who 
                makes rapid, data-driven decisions about how to respond to security threats. 
                You prioritize threats based on severity and business impact, and coordinate 
                automated responses while escalating critical issues to human analysts.""",
                verbose=True,
                allow_delegation=False,
                tools=[self._create_response_tool()]
            )
        return self.agent
    
    def _create_response_tool(self):
        """Create a tool for executing responses."""
        @tool("Execute Response Action")
        def execute_action(action: str, target: str, reason: str) -> Dict[str, Any]:
            """
            Execute a security response action.
            
            Args:
                action: Type of response action
                target: Target of the action (IP, host, etc.)
                reason: Reason for the action
            
            Returns:
                Execution result
            """
            return {
                'success': True,
                'action': action,
                'target': target,
                'executed_at': datetime.utcnow().isoformat()
            }
        
        return execute_action
    
    async def handle_event(self, event: Dict[str, Any]) -> None:
        """
        Handle an event and orchestrate appropriate response.
        
        Args:
            event: Event with enrichment and analysis data
        """
        # Calculate severity
        severity = self._calculate_severity(event)
        
        # Determine response actions
        actions = self._determine_actions(event, severity)
        
        if not actions:
            logger.info("No response actions required", event_id=event.get('id'))
            return
        
        # Apply response delay if configured
        if self.config.response_delay > 0:
            await asyncio.sleep(self.config.response_delay)
        
        # Execute actions
        for action in actions:
            await self._execute_action(event, action, severity)
    
    def _calculate_severity(self, event: Dict[str, Any]) -> int:
        """
        Calculate event severity score.
        
        Args:
            event: Event data
        
        Returns:
            Severity score (0-100)
        """
        base_severity = event.get('severity', 50)
        
        # Adjust based on threat intelligence
        threat_score = event.get('threat_intelligence', {}).get('threat_score', 0)
        
        # Adjust based on behavioral analysis
        behavioral = event.get('behavioral_analysis', {})
        anomaly_score = behavioral.get('anomaly_score', 0)
        
        # Weighted combination
        severity = (
            base_severity * 0.4 +
            threat_score * 0.4 +
            (anomaly_score * 100) * 0.2
        )
        
        return min(int(severity), 100)
    
    def _determine_actions(self, event: Dict[str, Any], severity: int) -> List[ResponseAction]:
        """
        Determine appropriate response actions based on severity.
        
        Args:
            event: Event data
            severity: Calculated severity score
        
        Returns:
            List of response actions to execute
        """
        actions = []
        thresholds = self.config.severity_thresholds
        
        # Critical severity
        if severity >= thresholds.get('critical', 90):
            if self.config.auto_response:
                actions.append(ResponseAction.BLOCK_IP)
                actions.append(ResponseAction.UPDATE_FIREWALL)
            actions.append(ResponseAction.CREATE_TICKET)
            actions.append(ResponseAction.NOTIFY_ADMIN)
        
        # High severity
        elif severity >= thresholds.get('high', 75):
            if self.config.auto_response:
                actions.append(ResponseAction.BLOCK_IP)
            actions.append(ResponseAction.CREATE_TICKET)
            actions.append(ResponseAction.NOTIFY_ADMIN)
        
        # Medium severity
        elif severity >= thresholds.get('medium', 50):
            actions.append(ResponseAction.CREATE_TICKET)
            actions.append(ResponseAction.NOTIFY_ADMIN)
        
        # Low severity
        else:
            actions.append(ResponseAction.LOG_ONLY)
        
        # Filter based on enabled actions in config
        enabled_actions = []
        for action in actions:
            action_config = self.config.actions.get(action.value, {})
            if isinstance(action_config, dict) and action_config.get('enabled', True):
                enabled_actions.append(action)
            elif action == ResponseAction.LOG_ONLY:  # Always allow logging
                enabled_actions.append(action)
        
        return enabled_actions
    
    async def _execute_action(
        self, 
        event: Dict[str, Any], 
        action: ResponseAction, 
        severity: int
    ) -> None:
        """
        Execute a specific response action.
        
        Args:
            event: Event data
            action: Response action to execute
            severity: Event severity
        """
        event_id = event.get('id', 'unknown')
        
        if self.dry_run:
            logger.info(
                "[DRY-RUN] Would execute action",
                action=action.value,
                event_id=event_id,
                severity=severity
            )
            return
        
        try:
            if action == ResponseAction.BLOCK_IP:
                await self._block_ip(event)
            
            elif action == ResponseAction.CREATE_TICKET:
                await self._create_ticket(event, severity)
            
            elif action == ResponseAction.NOTIFY_ADMIN:
                await self._notify_admin(event, severity)
            
            elif action == ResponseAction.UPDATE_FIREWALL:
                await self._update_firewall(event)
            
            elif action == ResponseAction.LOG_ONLY:
                logger.info("Event logged", event_id=event_id, severity=severity)
            
            # Track active response
            response_id = f"{event_id}:{action.value}"
            self.active_responses[response_id] = {
                'event_id': event_id,
                'action': action.value,
                'executed_at': datetime.utcnow().isoformat(),
                'severity': severity
            }
            
            logger.info(
                "Response action executed",
                action=action.value,
                event_id=event_id,
                severity=severity
            )
        
        except Exception as e:
            logger.error(
                "Failed to execute response action",
                action=action.value,
                event_id=event_id,
                error=str(e),
                exc_info=True
            )
    
    async def _block_ip(self, event: Dict[str, Any]) -> None:
        """Block an IP address."""
        src_ip = event.get('src_ip')
        if not src_ip:
            logger.warning("No source IP to block", event_id=event.get('id'))
            return
        
        # In production, this would call actual blocking mechanism
        # (iptables, firewall API, etc.)
        logger.info("IP blocked", ip=src_ip, event_id=event.get('id'))
    
    async def _create_ticket(self, event: Dict[str, Any], severity: int) -> None:
        """Create a ticket in ticketing system."""
        ticket_data = {
            'title': f"Security Alert: {event.get('signature', 'Unknown')}",
            'description': self._format_ticket_description(event),
            'severity': self._severity_to_priority(severity),
            'event_id': event.get('id')
        }
        
        # In production, this would call ticketing system API
        logger.info("Ticket created", event_id=event.get('id'), severity=severity)
    
    async def _notify_admin(self, event: Dict[str, Any], severity: int) -> None:
        """Send notification to administrators."""
        notification = {
            'subject': f"Security Alert [{self._severity_to_label(severity)}]",
            'body': self._format_notification(event, severity),
            'priority': self._severity_to_priority(severity)
        }
        
        # In production, this would send email/slack/etc.
        logger.info("Admin notified", event_id=event.get('id'), severity=severity)
    
    async def _update_firewall(self, event: Dict[str, Any]) -> None:
        """Update firewall rules."""
        src_ip = event.get('src_ip')
        if not src_ip:
            return
        
        # In production, this would call firewall API
        logger.info("Firewall updated", ip=src_ip, event_id=event.get('id'))
    
    def _format_ticket_description(self, event: Dict[str, Any]) -> str:
        """Format event data for ticket description."""
        return f"""
Security Event Detected:

Event ID: {event.get('id')}
Signature: {event.get('signature', 'N/A')}
Source IP: {event.get('src_ip', 'N/A')}
Destination IP: {event.get('dst_ip', 'N/A')}
Protocol: {event.get('protocol', 'N/A')}
Timestamp: {event.get('timestamp', 'N/A')}

Threat Intelligence:
{event.get('threat_intelligence', {})}

Behavioral Analysis:
{event.get('behavioral_analysis', {})}
"""
    
    def _format_notification(self, event: Dict[str, Any], severity: int) -> str:
        """Format notification message."""
        return f"[{self._severity_to_label(severity)}] {event.get('signature', 'Security Event')}"
    
    def _severity_to_label(self, severity: int) -> str:
        """Convert severity score to label."""
        if severity >= 90:
            return "CRITICAL"
        elif severity >= 75:
            return "HIGH"
        elif severity >= 50:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _severity_to_priority(self, severity: int) -> str:
        """Convert severity score to ticket priority."""
        if severity >= 90:
            return "P1"
        elif severity >= 75:
            return "P2"
        elif severity >= 50:
            return "P3"
        else:
            return "P4"
    
    async def stop(self) -> None:
        """Stop the agent and cleanup resources."""
        logger.info("Response Orchestrator Agent stopped", active_responses=len(self.active_responses))
