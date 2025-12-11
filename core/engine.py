"""
Core AI-Ops Engine

Orchestrates all agents and manages the event processing pipeline.
"""

import asyncio
from typing import Dict, List, Optional

import structlog
from crewai import Crew, Process

from agents.threat_intelligence_agent import ThreatIntelligenceAgent
from agents.behavioral_analysis_agent import BehavioralAnalysisAgent
from agents.response_orchestrator_agent import ResponseOrchestratorAgent
from agents.rule_optimization_agent import RuleOptimizationAgent
from agents.report_generation_agent import ReportGenerationAgent
from connectors.snort3_event_stream import Snort3EventStream
from core.config import Config
from workflows.workflow_manager import WorkflowManager

logger = structlog.get_logger(__name__)


class AIOpsEngine:
    """Main AI-Ops engine that coordinates all components."""
    
    def __init__(self, config: Config, dry_run: bool = False):
        """
        Initialize the AI-Ops engine.
        
        Args:
            config: Configuration object
            dry_run: If True, don't execute actual actions
        """
        self.config = config
        self.dry_run = dry_run
        self.running = False
        
        # Initialize components
        self.event_stream: Optional[Snort3EventStream] = None
        self.agents: Dict[str, any] = {}
        self.crew: Optional[Crew] = None
        self.workflow_manager: Optional[WorkflowManager] = None
        
        logger.info(
            "AI-Ops engine initialized",
            dry_run=dry_run,
            config_version=config.version if hasattr(config, 'version') else 'unknown'
        )
    
    def _initialize_agents(self):
        """Initialize all configured agents."""
        logger.info("Initializing agents...")
        
        agent_configs = self.config.agents
        
        # Threat Intelligence Agent
        if agent_configs.threat_intelligence.enabled:
            self.agents['threat_intel'] = ThreatIntelligenceAgent(
                config=agent_configs.threat_intelligence
            )
            logger.info("Threat Intelligence Agent initialized")
        
        # Behavioral Analysis Agent
        if agent_configs.behavioral_analysis.enabled:
            self.agents['behavioral'] = BehavioralAnalysisAgent(
                config=agent_configs.behavioral_analysis
            )
            logger.info("Behavioral Analysis Agent initialized")
        
        # Response Orchestrator Agent
        if agent_configs.response.enabled:
            self.agents['response'] = ResponseOrchestratorAgent(
                config=agent_configs.response,
                dry_run=self.dry_run
            )
            logger.info("Response Orchestrator Agent initialized")
        
        # Rule Optimization Agent
        if agent_configs.rule_optimization.enabled:
            self.agents['rule_optimizer'] = RuleOptimizationAgent(
                config=agent_configs.rule_optimization
            )
            logger.info("Rule Optimization Agent initialized")
        
        # Report Generation Agent
        if agent_configs.report_generation.enabled:
            self.agents['report'] = ReportGenerationAgent(
                config=agent_configs.report_generation
            )
            logger.info("Report Generation Agent initialized")
        
        logger.info(f"Initialized {len(self.agents)} agents")
    
    def _create_crew(self):
        """Create the agent crew for collaborative work."""
        logger.info("Creating agent crew...")
        
        # Get agent instances
        crew_agents = [
            agent.get_crewai_agent()
            for agent in self.agents.values()
            if hasattr(agent, 'get_crewai_agent')
        ]
        
        # Create the crew
        self.crew = Crew(
            agents=crew_agents,
            process=Process.sequential,  # Can be changed to hierarchical
            verbose=2 if self.config.logging.level == 'DEBUG' else 0
        )
        
        logger.info("Agent crew created", agent_count=len(crew_agents))
    
    def _initialize_event_stream(self):
        """Initialize connection to Snort3 event stream."""
        logger.info("Initializing event stream connection...")
        
        self.event_stream = Snort3EventStream(
            endpoint=self.config.event_stream.endpoint,
            buffer_size=self.config.event_stream.buffer_size,
            timeout=self.config.event_stream.timeout
        )
        
        logger.info(
            "Event stream initialized",
            endpoint=self.config.event_stream.endpoint
        )
    
    def _initialize_workflow_manager(self):
        """Initialize the workflow manager."""
        logger.info("Initializing workflow manager...")
        
        self.workflow_manager = WorkflowManager(
            agents=self.agents,
            config=self.config
        )
        
        # Load default workflows
        self.workflow_manager.load_default_workflows()
        
        logger.info("Workflow manager initialized")
    
    async def _process_event(self, event: Dict):
        """
        Process a single event from Snort3.
        
        Args:
            event: Event data dictionary
        """
        try:
            event_type = event.get('type')
            
            logger.debug(
                "Processing event",
                event_type=event_type,
                event_id=event.get('id')
            )
            
            # Route to appropriate workflow
            workflow = self.workflow_manager.get_workflow_for_event(event)
            
            if workflow:
                await workflow.execute(event, self.agents)
            else:
                # Default processing
                await self._default_event_processing(event)
                
        except Exception as e:
            logger.error(
                "Error processing event",
                error=str(e),
                event_id=event.get('id'),
                exc_info=True
            )
    
    async def _default_event_processing(self, event: Dict):
        """
        Default event processing pipeline.
        
        Args:
            event: Event data dictionary
        """
        event_type = event.get('type')
        
        # Alert events - full analysis
        if event_type == 'alert':
            # Threat intelligence enrichment
            if 'threat_intel' in self.agents:
                enriched = await self.agents['threat_intel'].enrich_event(event)
                event.update(enriched)
            
            # Behavioral analysis
            if 'behavioral' in self.agents:
                analysis = await self.agents['behavioral'].analyze_event(event)
                event['behavioral_analysis'] = analysis
            
            # Determine response
            if 'response' in self.agents:
                await self.agents['response'].handle_event(event)
        
        # Flow events - behavioral analysis
        elif event_type == 'flow':
            if 'behavioral' in self.agents:
                await self.agents['behavioral'].process_flow(event)
        
        # Stats events - rule optimization
        elif event_type == 'stats':
            if 'rule_optimizer' in self.agents:
                await self.agents['rule_optimizer'].process_stats(event)
    
    async def _event_processing_loop(self):
        """Main event processing loop."""
        logger.info("Starting event processing loop")
        
        try:
            async for event in self.event_stream.stream():
                if not self.running:
                    break
                
                await self._process_event(event)
                
        except asyncio.CancelledError:
            logger.info("Event processing loop cancelled")
        except Exception as e:
            logger.error("Event processing loop error", error=str(e), exc_info=True)
            raise
    
    async def start(self):
        """Start the AI-Ops engine."""
        logger.info("Starting AI-Ops engine...")
        
        try:
            # Initialize all components
            self._initialize_agents()
            self._create_crew()
            self._initialize_event_stream()
            self._initialize_workflow_manager()
            
            # Connect to event stream
            await self.event_stream.connect()
            
            self.running = True
            logger.info("AI-Ops engine started successfully")
            
            # Start event processing
            await self._event_processing_loop()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            await self.stop()
        except Exception as e:
            logger.error("Failed to start engine", error=str(e), exc_info=True)
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the AI-Ops engine gracefully."""
        logger.info("Stopping AI-Ops engine...")
        
        self.running = False
        
        # Disconnect event stream
        if self.event_stream:
            await self.event_stream.disconnect()
        
        # Stop all agents
        for name, agent in self.agents.items():
            if hasattr(agent, 'stop'):
                await agent.stop()
                logger.info(f"Stopped {name} agent")
        
        logger.info("AI-Ops engine stopped")
