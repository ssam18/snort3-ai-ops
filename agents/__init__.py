"""Agent modules for Snort3-AI-Ops."""

# Only import setup_agent by default to avoid dependency issues
# Other agents are imported on-demand when the system is fully running
try:
    from .setup_agent import SetupAgent
except ImportError:
    pass

# Optional imports - loaded when full system is running
def get_threat_intelligence_agent():
    from .threat_intelligence_agent import ThreatIntelligenceAgent
    return ThreatIntelligenceAgent

def get_behavioral_agent():
    from .behavioral_analysis_agent import BehavioralAnalysisAgent
    return BehavioralAnalysisAgent

def get_response_agent():
    from .response_orchestrator_agent import ResponseOrchestratorAgent
    return ResponseOrchestratorAgent

def get_rule_optimizer():
    from .rule_optimization_agent import RuleOptimizationAgent
    return RuleOptimizationAgent

def get_report_generator():
    from .report_generation_agent import ReportGenerationAgent
    return ReportGenerationAgent

__all__ = [
    'SetupAgent',
    'get_threat_intelligence_agent',
    'get_behavioral_agent',
    'get_response_agent',
    'get_rule_optimizer',
    'get_report_generator',
    'ThreatIntelligenceAgent',
    'BehavioralAnalysisAgent',
    'ResponseOrchestratorAgent',
    'RuleOptimizationAgent',
    'ReportGenerationAgent',
]
