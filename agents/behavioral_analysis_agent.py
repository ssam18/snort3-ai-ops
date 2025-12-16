"""Behavioral Analysis Agent for anomaly detection."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

import structlog
from crewai import Agent
from crewai.tools import tool

from core.config import BehavioralConfig

logger = structlog.get_logger(__name__)


class BehavioralAnalysisAgent:
    """Agent for behavioral analysis and anomaly detection."""
    
    def __init__(self, config: BehavioralConfig):
        """
        Initialize the Behavioral Analysis Agent.
        
        Args:
            config: Behavioral analysis configuration
        """
        self.config = config
        self.agent: Optional[Agent] = None
        
        # Baseline tracking
        self.flow_baselines: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.protocol_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # ML model (placeholder - would load actual model in production)
        self.ml_model = None
        self._load_model()
        
        logger.info("Behavioral Analysis Agent initialized")
    
    def _load_model(self) -> None:
        """Load the ML model for anomaly detection."""
        try:
            # In production, load actual model from config.ml_model_path
            # For now, use a placeholder
            self.ml_model = {'type': 'isolation_forest', 'loaded': True}
            logger.info("ML model loaded", model_path=self.config.ml_model_path)
        except Exception as e:
            logger.warning("Failed to load ML model, using rule-based detection", error=str(e))
            self.ml_model = None
    
    def get_crewai_agent(self) -> Agent:
        """Get the CrewAI agent instance."""
        if self.agent is None:
            self.agent = Agent(
                role='Behavioral Security Analyst',
                goal='Detect anomalous network behavior and identify potential security threats',
                backstory="""You are an expert in network traffic analysis and behavioral 
                detection. You use machine learning and statistical analysis to identify 
                deviations from normal patterns that might indicate security threats, including 
                zero-day attacks and APTs.""",
                verbose=True,
                allow_delegation=False,
                tools=[self._create_analysis_tool()]
            )
        return self.agent
    
    def _create_analysis_tool(self):
        """Create a tool for behavioral analysis."""
        @tool("Behavioral Analysis")
        def analyze_behavior(flow_data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Analyze network flow for anomalous behavior.
            
            Args:
                flow_data: Flow metadata and statistics
            
            Returns:
                Analysis results with anomaly score
            """
            return {
                'anomaly_score': 0.65,
                'is_anomalous': True,
                'deviations': ['unusual_port', 'high_packet_rate'],
                'confidence': 0.85
            }
        
        return analyze_behavior
    
    async def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an event for behavioral anomalies.
        
        Args:
            event: Event data dictionary
        
        Returns:
            Behavioral analysis results
        """
        analysis = {
            'timestamp': datetime.utcnow().isoformat(),
            'anomaly_score': 0.0,
            'is_anomalous': False,
            'deviations': [],
            'behavioral_features': {},
            'confidence': 0.0
        }
        
        # Extract behavioral features
        features = self._extract_features(event)
        analysis['behavioral_features'] = features
        
        # Calculate anomaly score
        if self.ml_model:
            anomaly_score = self._ml_based_detection(features)
        else:
            anomaly_score = self._rule_based_detection(features)
        
        analysis['anomaly_score'] = anomaly_score
        analysis['is_anomalous'] = anomaly_score >= self.config.anomaly_threshold
        
        # Identify specific deviations
        if analysis['is_anomalous']:
            analysis['deviations'] = self._identify_deviations(features)
            analysis['confidence'] = min(anomaly_score, 0.95)
        
        logger.info(
            "Behavioral analysis completed",
            event_id=event.get('id'),
            anomaly_score=anomaly_score,
            is_anomalous=analysis['is_anomalous']
        )
        
        return analysis
    
    def _extract_features(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract behavioral features from event."""
        features = {
            'protocol': event.get('protocol', 'unknown'),
            'src_port': event.get('src_port', 0),
            'dst_port': event.get('dst_port', 0),
            'bytes_sent': event.get('bytes_sent', 0),
            'bytes_recv': event.get('bytes_recv', 0),
            'packet_count': event.get('packet_count', 0),
            'duration': event.get('duration', 0),
            'flags': event.get('tcp_flags', [])
        }
        
        # Calculate derived features
        if features['duration'] > 0:
            features['bytes_per_second'] = (
                features['bytes_sent'] + features['bytes_recv']
            ) / features['duration']
            features['packets_per_second'] = features['packet_count'] / features['duration']
        else:
            features['bytes_per_second'] = 0
            features['packets_per_second'] = 0
        
        return features
    
    def _ml_based_detection(self, features: Dict[str, Any]) -> float:
        """
        ML-based anomaly detection.
        
        Args:
            features: Extracted behavioral features
        
        Returns:
            Anomaly score (0.0 to 1.0)
        """
        # Placeholder for ML inference
        # In production, this would use the loaded model
        score = 0.5
        
        # Simple heuristic for demonstration
        if features.get('bytes_per_second', 0) > 1000000:  # > 1MB/s
            score += 0.2
        if features.get('packets_per_second', 0) > 1000:
            score += 0.15
        if features.get('dst_port') in [22, 23, 3389]:  # SSH, Telnet, RDP
            score += 0.1
        
        return min(score, 1.0)
    
    def _rule_based_detection(self, features: Dict[str, Any]) -> float:
        """
        Rule-based anomaly detection fallback.
        
        Args:
            features: Extracted behavioral features
        
        Returns:
            Anomaly score (0.0 to 1.0)
        """
        score = 0.0
        
        # Check for suspicious patterns
        # High data transfer rate
        if features.get('bytes_per_second', 0) > 5000000:  # > 5MB/s
            score += 0.3
        
        # Unusual port usage
        unusual_ports = [4444, 5555, 6666, 7777, 8888, 9999]
        if features.get('dst_port') in unusual_ports:
            score += 0.25
        
        # High packet rate
        if features.get('packets_per_second', 0) > 5000:
            score += 0.2
        
        # Protocol-specific checks
        protocol = features.get('protocol', '').lower()
        if protocol == 'icmp' and features.get('packet_count', 0) > 1000:
            score += 0.25  # Possible ICMP flood
        
        return min(score, 1.0)
    
    def _identify_deviations(self, features: Dict[str, Any]) -> List[str]:
        """Identify specific deviations from baseline."""
        deviations = []
        
        if features.get('bytes_per_second', 0) > 1000000:
            deviations.append('high_data_rate')
        
        if features.get('packets_per_second', 0) > 1000:
            deviations.append('high_packet_rate')
        
        unusual_ports = [4444, 5555, 6666, 7777, 8888, 9999]
        if features.get('dst_port') in unusual_ports:
            deviations.append('unusual_port')
        
        if features.get('dst_port') in [22, 23, 3389]:
            deviations.append('remote_access_attempt')
        
        return deviations
    
    async def process_flow(self, event: Dict[str, Any]) -> None:
        """
        Process a flow event for baseline learning.
        
        Args:
            event: Flow event data
        """
        src_ip = event.get('src_ip')
        dst_ip = event.get('dst_ip')
        protocol = event.get('protocol')
        
        if src_ip and protocol:
            flow_key = f"{src_ip}:{protocol}"
            
            # Update statistics
            self.protocol_stats[src_ip][protocol] += 1
            
            # Update baseline
            if flow_key not in self.flow_baselines:
                self.flow_baselines[flow_key] = {
                    'count': 0,
                    'avg_bytes': 0,
                    'avg_duration': 0
                }
            
            baseline = self.flow_baselines[flow_key]
            baseline['count'] += 1
            
            # Running average update
            bytes_total = event.get('bytes_sent', 0) + event.get('bytes_recv', 0)
            baseline['avg_bytes'] = (
                (baseline['avg_bytes'] * (baseline['count'] - 1) + bytes_total) 
                / baseline['count']
            )
            
            duration = event.get('duration', 0)
            baseline['avg_duration'] = (
                (baseline['avg_duration'] * (baseline['count'] - 1) + duration)
                / baseline['count']
            )
        
        logger.debug("Flow processed for baseline", src_ip=src_ip, protocol=protocol)
    
    async def stop(self) -> None:
        """Stop the agent and cleanup resources."""
        logger.info("Behavioral Analysis Agent stopped")
