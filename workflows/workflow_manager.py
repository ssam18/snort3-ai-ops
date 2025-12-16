"""Workflow Manager for orchestrating agent workflows."""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

import structlog

from core.config import Config

logger = structlog.get_logger(__name__)


class WorkflowType(Enum):
    """Types of workflows."""
    ALERT_PROCESSING = "alert_processing"
    FLOW_ANALYSIS = "flow_analysis"
    STATS_ANALYSIS = "stats_analysis"
    INCIDENT_RESPONSE = "incident_response"
    THREAT_HUNTING = "threat_hunting"


class WorkflowPriority(Enum):
    """Workflow execution priority."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Workflow:
    """Represents a workflow for processing events."""
    
    def __init__(
        self,
        name: str,
        workflow_type: WorkflowType,
        priority: WorkflowPriority = WorkflowPriority.MEDIUM,
        steps: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize a workflow.
        
        Args:
            name: Workflow name
            workflow_type: Type of workflow
            priority: Execution priority
            steps: List of workflow steps
        """
        self.name = name
        self.workflow_type = workflow_type
        self.priority = priority
        self.steps = steps or []
        
        self.event_filters: List[Callable] = []
        self.stats = {
            'executed': 0,
            'successful': 0,
            'failed': 0
        }
    
    def add_filter(self, filter_func: Callable[[Dict[str, Any]], bool]) -> None:
        """
        Add an event filter to determine if workflow should execute.
        
        Args:
            filter_func: Function that returns True if event matches
        """
        self.event_filters.append(filter_func)
    
    def matches_event(self, event: Dict[str, Any]) -> bool:
        """
        Check if event matches workflow filters.
        
        Args:
            event: Event data
        
        Returns:
            True if event matches all filters
        """
        if not self.event_filters:
            # No filters means match all events of this type
            return event.get('type') == self.workflow_type.value
        
        return all(f(event) for f in self.event_filters)
    
    async def execute(
        self, 
        event: Dict[str, Any], 
        agents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the workflow for an event.
        
        Args:
            event: Event data
            agents: Available agents
        
        Returns:
            Workflow execution results
        """
        self.stats['executed'] += 1
        
        logger.info(
            "Executing workflow",
            workflow=self.name,
            event_id=event.get('id'),
            event_type=event.get('type')
        )
        
        results = {
            'workflow': self.name,
            'event_id': event.get('id'),
            'steps_completed': [],
            'success': False,
            'error': None
        }
        
        try:
            for step in self.steps:
                step_result = await self._execute_step(step, event, agents)
                results['steps_completed'].append(step_result)
                
                # Stop on critical failure if configured
                if step.get('critical', False) and not step_result.get('success', False):
                    raise Exception(f"Critical step failed: {step.get('name')}")
            
            results['success'] = True
            self.stats['successful'] += 1
            
            logger.info(
                "Workflow completed successfully",
                workflow=self.name,
                event_id=event.get('id')
            )
        
        except Exception as e:
            results['error'] = str(e)
            results['success'] = False
            self.stats['failed'] += 1
            
            logger.error(
                "Workflow execution failed",
                workflow=self.name,
                event_id=event.get('id'),
                error=str(e),
                exc_info=True
            )
        
        return results
    
    async def _execute_step(
        self,
        step: Dict[str, Any],
        event: Dict[str, Any],
        agents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single workflow step.
        
        Args:
            step: Step configuration
            event: Event data
            agents: Available agents
        
        Returns:
            Step execution result
        """
        step_name = step.get('name', 'unknown')
        agent_name = step.get('agent')
        action = step.get('action')
        
        logger.debug(
            "Executing workflow step",
            step=step_name,
            agent=agent_name,
            action=action
        )
        
        result = {
            'step': step_name,
            'success': False,
            'output': None,
            'error': None
        }
        
        try:
            if agent_name not in agents:
                raise ValueError(f"Agent '{agent_name}' not available")
            
            agent = agents[agent_name]
            
            # Execute the action on the agent
            if hasattr(agent, action):
                method = getattr(agent, action)
                output = await method(event)
                result['output'] = output
                result['success'] = True
            else:
                raise AttributeError(f"Agent '{agent_name}' has no action '{action}'")
        
        except Exception as e:
            result['error'] = str(e)
            logger.error(
                "Step execution failed",
                step=step_name,
                error=str(e)
            )
        
        return result


class WorkflowManager:
    """Manager for workflow orchestration."""
    
    def __init__(self, agents: Dict[str, Any], config: Config):
        """
        Initialize the Workflow Manager.
        
        Args:
            agents: Dictionary of available agents
            config: Application configuration
        """
        self.agents = agents
        self.config = config
        self.workflows: Dict[str, Workflow] = {}
        
        logger.info("Workflow Manager initialized")
    
    def register_workflow(self, workflow: Workflow) -> None:
        """
        Register a workflow.
        
        Args:
            workflow: Workflow to register
        """
        self.workflows[workflow.name] = workflow
        logger.info("Workflow registered", workflow=workflow.name, type=workflow.workflow_type.value)
    
    def get_workflow_for_event(self, event: Dict[str, Any]) -> Optional[Workflow]:
        """
        Find the appropriate workflow for an event.
        
        Args:
            event: Event data
        
        Returns:
            Matching workflow or None
        """
        # Find all matching workflows
        matching_workflows = [
            wf for wf in self.workflows.values()
            if wf.matches_event(event)
        ]
        
        if not matching_workflows:
            return None
        
        # Return highest priority workflow
        return max(matching_workflows, key=lambda wf: wf.priority.value)
    
    def load_default_workflows(self) -> None:
        """Load default workflow configurations."""
        # Alert Processing Workflow
        alert_workflow = Workflow(
            name="alert_processing",
            workflow_type=WorkflowType.ALERT_PROCESSING,
            priority=WorkflowPriority.HIGH,
            steps=[
                {
                    'name': 'threat_intelligence_enrichment',
                    'agent': 'threat_intel',
                    'action': 'enrich_event',
                    'critical': False
                },
                {
                    'name': 'behavioral_analysis',
                    'agent': 'behavioral',
                    'action': 'analyze_event',
                    'critical': False
                },
                {
                    'name': 'response_orchestration',
                    'agent': 'response',
                    'action': 'handle_event',
                    'critical': False
                }
            ]
        )
        alert_workflow.add_filter(lambda e: e.get('type') == 'alert')
        self.register_workflow(alert_workflow)
        
        # Flow Analysis Workflow
        flow_workflow = Workflow(
            name="flow_analysis",
            workflow_type=WorkflowType.FLOW_ANALYSIS,
            priority=WorkflowPriority.MEDIUM,
            steps=[
                {
                    'name': 'behavioral_analysis',
                    'agent': 'behavioral',
                    'action': 'process_flow',
                    'critical': False
                }
            ]
        )
        flow_workflow.add_filter(lambda e: e.get('type') == 'flow')
        self.register_workflow(flow_workflow)
        
        # Stats Analysis Workflow
        stats_workflow = Workflow(
            name="stats_analysis",
            workflow_type=WorkflowType.STATS_ANALYSIS,
            priority=WorkflowPriority.LOW,
            steps=[
                {
                    'name': 'rule_optimization',
                    'agent': 'rule_optimizer',
                    'action': 'process_stats',
                    'critical': False
                }
            ]
        )
        stats_workflow.add_filter(lambda e: e.get('type') == 'stats')
        self.register_workflow(stats_workflow)
        
        logger.info(
            "Default workflows loaded",
            count=len(self.workflows)
        )
    
    def get_workflow_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for all workflows.
        
        Returns:
            Dictionary of workflow statistics
        """
        return {
            name: workflow.stats.copy()
            for name, workflow in self.workflows.items()
        }
