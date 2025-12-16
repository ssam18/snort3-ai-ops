"""
Prometheus Metrics Exporter
Exposes metrics for monitoring and alerting
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from prometheus_client import CollectorRegistry
from typing import Dict, Any
import time

# Create custom registry
registry = CollectorRegistry()

# System Info
system_info = Info('snort3_ai_ops_system', 'System information', registry=registry)

# Event Metrics
events_processed_total = Counter(
    'snort3_ai_ops_events_processed_total',
    'Total number of events processed',
    ['event_type'],
    registry=registry
)

events_processing_duration = Histogram(
    'snort3_ai_ops_event_processing_duration_seconds',
    'Event processing duration in seconds',
    ['event_type'],
    buckets=(0.001, 0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry
)

events_in_queue = Gauge(
    'snort3_ai_ops_events_in_queue',
    'Number of events currently in processing queue',
    registry=registry
)

# Agent Metrics
agent_tasks_total = Counter(
    'snort3_ai_ops_agent_tasks_total',
    'Total number of agent tasks executed',
    ['agent_name', 'status'],
    registry=registry
)

agent_task_duration = Histogram(
    'snort3_ai_ops_agent_task_duration_seconds',
    'Agent task execution duration',
    ['agent_name'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
    registry=registry
)

agent_active_tasks = Gauge(
    'snort3_ai_ops_agent_active_tasks',
    'Number of currently active agent tasks',
    ['agent_name'],
    registry=registry
)

# Threat Intelligence Metrics
threat_intel_lookups_total = Counter(
    'snort3_ai_ops_threat_intel_lookups_total',
    'Total number of threat intelligence lookups',
    ['source', 'ioc_type'],
    registry=registry
)

threat_intel_cache_hits = Counter(
    'snort3_ai_ops_threat_intel_cache_hits_total',
    'Total number of cache hits for threat intelligence',
    registry=registry
)

threat_intel_cache_misses = Counter(
    'snort3_ai_ops_threat_intel_cache_misses_total',
    'Total number of cache misses for threat intelligence',
    registry=registry
)

threats_detected_total = Counter(
    'snort3_ai_ops_threats_detected_total',
    'Total number of threats detected',
    ['severity'],
    registry=registry
)

# Response Metrics
responses_executed_total = Counter(
    'snort3_ai_ops_responses_executed_total',
    'Total number of automated responses executed',
    ['action_type', 'status'],
    registry=registry
)

responses_pending = Gauge(
    'snort3_ai_ops_responses_pending',
    'Number of responses waiting to be executed',
    registry=registry
)

# SIEM Integration Metrics
siem_events_sent_total = Counter(
    'snort3_ai_ops_siem_events_sent_total',
    'Total number of events sent to SIEM',
    ['siem_type', 'status'],
    registry=registry
)

siem_send_duration = Histogram(
    'snort3_ai_ops_siem_send_duration_seconds',
    'Duration to send events to SIEM',
    ['siem_type'],
    registry=registry
)

# Firewall Integration Metrics
firewall_actions_total = Counter(
    'snort3_ai_ops_firewall_actions_total',
    'Total number of firewall actions',
    ['firewall_type', 'action', 'status'],
    registry=registry
)

firewall_blocked_ips = Gauge(
    'snort3_ai_ops_firewall_blocked_ips',
    'Number of currently blocked IPs',
    ['firewall_type'],
    registry=registry
)

# System Health Metrics
system_uptime_seconds = Gauge(
    'snort3_ai_ops_uptime_seconds',
    'System uptime in seconds',
    registry=registry
)

system_memory_usage_bytes = Gauge(
    'snort3_ai_ops_memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

system_cpu_usage_percent = Gauge(
    'snort3_ai_ops_cpu_usage_percent',
    'CPU usage percentage',
    registry=registry
)

# Error Metrics
errors_total = Counter(
    'snort3_ai_ops_errors_total',
    'Total number of errors',
    ['component', 'error_type'],
    registry=registry
)


class MetricsCollector:
    """Helper class to collect and update metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.start_time = time.time()
        system_info.info({
            'version': '1.0.0',
            'python_version': '3.12.3'
        })
    
    def record_event(self, event_type: str, duration: float):
        """Record event processing metrics."""
        events_processed_total.labels(event_type=event_type).inc()
        events_processing_duration.labels(event_type=event_type).observe(duration)
    
    def record_agent_task(self, agent_name: str, status: str, duration: float):
        """Record agent task metrics."""
        agent_tasks_total.labels(agent_name=agent_name, status=status).inc()
        agent_task_duration.labels(agent_name=agent_name).observe(duration)
    
    def record_threat_lookup(self, source: str, ioc_type: str, cache_hit: bool):
        """Record threat intelligence lookup metrics."""
        threat_intel_lookups_total.labels(source=source, ioc_type=ioc_type).inc()
        if cache_hit:
            threat_intel_cache_hits.inc()
        else:
            threat_intel_cache_misses.inc()
    
    def record_threat_detection(self, severity: str):
        """Record threat detection metrics."""
        threats_detected_total.labels(severity=severity).inc()
    
    def record_response(self, action_type: str, status: str):
        """Record response execution metrics."""
        responses_executed_total.labels(action_type=action_type, status=status).inc()
    
    def record_siem_send(self, siem_type: str, status: str, duration: float):
        """Record SIEM integration metrics."""
        siem_events_sent_total.labels(siem_type=siem_type, status=status).inc()
        siem_send_duration.labels(siem_type=siem_type).observe(duration)
    
    def record_firewall_action(self, firewall_type: str, action: str, status: str):
        """Record firewall action metrics."""
        firewall_actions_total.labels(
            firewall_type=firewall_type,
            action=action,
            status=status
        ).inc()
    
    def record_error(self, component: str, error_type: str):
        """Record error metrics."""
        errors_total.labels(component=component, error_type=error_type).inc()
    
    def update_system_metrics(self, memory_bytes: int, cpu_percent: float):
        """Update system health metrics."""
        uptime = time.time() - self.start_time
        system_uptime_seconds.set(uptime)
        system_memory_usage_bytes.set(memory_bytes)
        system_cpu_usage_percent.set(cpu_percent)
    
    def get_metrics(self) -> bytes:
        """Get Prometheus formatted metrics."""
        return generate_latest(registry)


# Global metrics collector instance
metrics_collector = MetricsCollector()
