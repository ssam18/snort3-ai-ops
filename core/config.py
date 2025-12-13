"""Configuration management for Snort3-AI-Ops."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, validator


class EventStreamConfig(BaseModel):
    """Event stream configuration."""
    type: str = 'zeromq'
    endpoint: str = 'tcp://127.0.0.1:5555'
    buffer_size: int = 10000
    timeout: int = 5000


class ThreatIntelConfig(BaseModel):
    """Threat intelligence agent configuration."""
    enabled: bool = True
    update_interval: int = 3600
    cache_ttl: int = 86400
    api_keys: Dict[str, str] = Field(default_factory=dict)
    confidence_threshold: float = 0.7


class BehavioralConfig(BaseModel):
    """Behavioral analysis agent configuration."""
    enabled: bool = True
    ml_model_path: str = 'models/anomaly_detector.pkl'
    anomaly_threshold: float = 0.85
    baseline_window: int = 7
    features: List[str] = Field(default_factory=list)


class ResponseConfig(BaseModel):
    """Response orchestrator configuration."""
    enabled: bool = True
    auto_response: bool = False
    response_delay: int = 0
    max_concurrent_actions: int = 10
    severity_thresholds: Dict[str, int] = Field(default_factory=lambda: {
        'critical': 90,
        'high': 75,
        'medium': 50,
        'low': 25
    })
    actions: Dict[str, Any] = Field(default_factory=lambda: {
        'block_ip': {'enabled': True, 'default_duration': 3600},
        'create_ticket': {'enabled': True},
        'notify_admin': {'enabled': True},
        'update_firewall': {'enabled': False},
        'log_only': {'enabled': True}
    })


class RuleOptimizationConfig(BaseModel):
    """Rule optimization agent configuration."""
    enabled: bool = True
    analysis_window: int = 30
    min_rule_hits: int = 10
    false_positive_threshold: float = 0.3
    auto_tune: bool = False


class ReportGenerationConfig(BaseModel):
    """Report generation agent configuration."""
    enabled: bool = True
    output_dir: str = 'reports/'
    formats: List[str] = Field(default_factory=lambda: ['pdf', 'html', 'json'])


class AgentsConfig(BaseModel):
    """All agents configuration."""
    threat_intelligence: ThreatIntelConfig = Field(default_factory=ThreatIntelConfig)
    behavioral_analysis: BehavioralConfig = Field(default_factory=BehavioralConfig)
    response: ResponseConfig = Field(default_factory=ResponseConfig)
    rule_optimization: RuleOptimizationConfig = Field(default_factory=RuleOptimizationConfig)
    report_generation: ReportGenerationConfig = Field(default_factory=ReportGenerationConfig)


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str = 'sqlite'
    path: str = 'data/snort3_aiops.db'
    pool_size: int = 10
    max_overflow: int = 20


class APIConfig(BaseModel):
    """API configuration."""
    host: str = '0.0.0.0'
    port: int = 8000
    workers: int = 4
    reload: bool = False


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = 'INFO'
    format: str = 'json'


class Config(BaseModel):
    """Main configuration class."""
    event_stream: EventStreamConfig = Field(default_factory=EventStreamConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def expand_env_vars(data: Any) -> Any:
    """
    Recursively expand environment variables in configuration.
    
    Variables should be in format ${VAR_NAME} or $VAR_NAME
    """
    if isinstance(data, dict):
        return {k: expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [expand_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Expand ${VAR} and $VAR patterns
        import re
        pattern = r'\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)'
        
        def replacer(match):
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))
        
        return re.sub(pattern, replacer, data)
    return data


def load_config(config_path: str = 'config/config.yaml') -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Config object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        raw_config = yaml.safe_load(f)
    
    # Expand environment variables
    expanded_config = expand_env_vars(raw_config)
    
    # Create and validate config object
    config = Config(**expanded_config)
    
    return config
