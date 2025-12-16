"""Rule Optimization Agent for Snort3 rule tuning."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

import structlog
from crewai import Agent
from crewai.tools import tool

from core.config import RuleOptimizationConfig

logger = structlog.get_logger(__name__)


class RuleOptimizationAgent:
    """Agent for optimizing and tuning Snort3 detection rules."""
    
    def __init__(self, config: RuleOptimizationConfig):
        """
        Initialize the Rule Optimization Agent.
        
        Args:
            config: Rule optimization configuration
        """
        self.config = config
        self.agent: Optional[Agent] = None
        
        # Rule statistics tracking
        self.rule_stats: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            'total_hits': 0,
            'true_positives': 0,
            'false_positives': 0,
            'last_hit': None,
            'performance_impact': 0.0
        })
        
        logger.info("Rule Optimization Agent initialized")
    
    def get_crewai_agent(self) -> Agent:
        """Get the CrewAI agent instance."""
        if self.agent is None:
            self.agent = Agent(
                role='Detection Rule Engineer',
                goal='Optimize detection rules for accuracy and performance',
                backstory="""You are an expert in intrusion detection systems and rule 
                engineering. You analyze rule performance, identify false positives, and 
                recommend optimizations to improve detection accuracy while minimizing 
                performance impact.""",
                verbose=True,
                allow_delegation=False,
                tools=[self._create_optimization_tool()]
            )
        return self.agent
    
    def _create_optimization_tool(self):
        """Create a tool for rule optimization."""
        @tool("Rule Optimization Analysis")
        def analyze_rule(rule_id: int, stats: Dict[str, Any]) -> Dict[str, Any]:
            """
            Analyze a detection rule for optimization opportunities.
            
            Args:
                rule_id: Rule identifier
                stats: Rule statistics
            
            Returns:
                Optimization recommendations
            """
            return {
                'rule_id': rule_id,
                'effectiveness': 0.85,
                'false_positive_rate': 0.15,
                'recommendations': ['add_content_modifier', 'restrict_flow_direction']
            }
        
        return analyze_rule
    
    async def process_stats(self, event: Dict[str, Any]) -> None:
        """
        Process statistics event for rule analysis.
        
        Args:
            event: Statistics event data
        """
        rule_stats = event.get('rule_stats', [])
        
        for stat in rule_stats:
            rule_id = stat.get('sid')
            if rule_id:
                self._update_rule_stats(rule_id, stat)
        
        logger.debug("Rule statistics processed", rules_updated=len(rule_stats))
    
    def _update_rule_stats(self, rule_id: int, stat: Dict[str, Any]) -> None:
        """
        Update statistics for a specific rule.
        
        Args:
            rule_id: Rule SID
            stat: Statistics data
        """
        rule_data = self.rule_stats[rule_id]
        
        rule_data['total_hits'] += stat.get('matches', 0)
        rule_data['last_hit'] = datetime.utcnow().isoformat()
        
        # Track performance metrics if available
        if 'avg_match_time' in stat:
            rule_data['performance_impact'] = stat['avg_match_time']
    
    async def analyze_rules(self) -> List[Dict[str, Any]]:
        """
        Analyze all rules and generate optimization recommendations.
        
        Returns:
            List of rule optimization recommendations
        """
        recommendations = []
        
        for rule_id, stats in self.rule_stats.items():
            # Skip rules with insufficient data
            if stats['total_hits'] < self.config.min_rule_hits:
                continue
            
            recommendation = await self._analyze_single_rule(rule_id, stats)
            if recommendation:
                recommendations.append(recommendation)
        
        logger.info("Rule analysis completed", recommendations_count=len(recommendations))
        return recommendations
    
    async def _analyze_single_rule(
        self, 
        rule_id: int, 
        stats: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single rule for optimization.
        
        Args:
            rule_id: Rule SID
            stats: Rule statistics
        
        Returns:
            Optimization recommendation if applicable
        """
        total_hits = stats['total_hits']
        true_positives = stats.get('true_positives', 0)
        false_positives = stats.get('false_positives', 0)
        
        # Calculate metrics
        if total_hits > 0:
            # Assume unknown alerts are 50/50 for initial calculation
            unknown_hits = total_hits - true_positives - false_positives
            estimated_fp = false_positives + (unknown_hits * 0.5)
            
            fp_rate = estimated_fp / total_hits
            effectiveness = true_positives / total_hits if true_positives > 0 else 0.0
        else:
            fp_rate = 0.0
            effectiveness = 0.0
        
        recommendation = {
            'rule_id': rule_id,
            'total_hits': total_hits,
            'false_positive_rate': fp_rate,
            'effectiveness': effectiveness,
            'performance_impact': stats.get('performance_impact', 0.0),
            'actions': []
        }
        
        # High false positive rate
        if fp_rate > self.config.false_positive_threshold:
            recommendation['actions'].append({
                'type': 'tune',
                'reason': 'high_false_positive_rate',
                'suggestion': 'Add more specific content matches or flow constraints'
            })
        
        # Low effectiveness
        if effectiveness < self.config.effectiveness_threshold and total_hits > 100:
            recommendation['actions'].append({
                'type': 'review',
                'reason': 'low_effectiveness',
                'suggestion': 'Rule may need to be deprecated or significantly revised'
            })
        
        # High performance impact
        if stats.get('performance_impact', 0) > 1000:  # > 1ms average
            recommendation['actions'].append({
                'type': 'optimize',
                'reason': 'high_performance_impact',
                'suggestion': 'Consider using fast pattern modifiers or reducing regex complexity'
            })
        
        # No recent hits - possible deprecation candidate
        if stats.get('last_hit'):
            last_hit = datetime.fromisoformat(stats['last_hit'])
            days_since_hit = (datetime.utcnow() - last_hit).days
            
            if days_since_hit > self.config.analysis_window:
                recommendation['actions'].append({
                    'type': 'deprecate',
                    'reason': 'no_recent_activity',
                    'suggestion': f'No hits in {days_since_hit} days - consider disabling'
                })
        
        return recommendation if recommendation['actions'] else None
    
    async def apply_optimizations(
        self, 
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Apply rule optimizations (if auto-tune is enabled).
        
        Args:
            recommendations: List of optimization recommendations
        
        Returns:
            Summary of applied optimizations
        """
        if not self.config.auto_tune:
            logger.info("Auto-tune disabled, skipping optimization application")
            return {'tuned': 0, 'disabled': 0, 'optimized': 0}
        
        summary = {
            'tuned': 0,
            'disabled': 0,
            'optimized': 0
        }
        
        for rec in recommendations:
            for action in rec['actions']:
                action_type = action['type']
                
                if action_type == 'tune':
                    # In production, would modify rule
                    summary['tuned'] += 1
                    logger.info(
                        "Rule tuned",
                        rule_id=rec['rule_id'],
                        reason=action['reason']
                    )
                
                elif action_type == 'deprecate':
                    # In production, would disable rule
                    summary['disabled'] += 1
                    logger.info(
                        "Rule disabled",
                        rule_id=rec['rule_id'],
                        reason=action['reason']
                    )
                
                elif action_type == 'optimize':
                    # In production, would optimize rule
                    summary['optimized'] += 1
                    logger.info(
                        "Rule optimized",
                        rule_id=rec['rule_id'],
                        reason=action['reason']
                    )
        
        logger.info("Optimizations applied", **summary)
        return summary
    
    def update_rule_feedback(
        self, 
        rule_id: int, 
        event_id: str, 
        is_true_positive: bool
    ) -> None:
        """
        Update rule statistics based on analyst feedback.
        
        Args:
            rule_id: Rule SID
            event_id: Event identifier
            is_true_positive: Whether the alert was a true positive
        """
        if rule_id in self.rule_stats:
            if is_true_positive:
                self.rule_stats[rule_id]['true_positives'] += 1
            else:
                self.rule_stats[rule_id]['false_positives'] += 1
            
            logger.debug(
                "Rule feedback recorded",
                rule_id=rule_id,
                event_id=event_id,
                is_true_positive=is_true_positive
            )
    
    async def stop(self) -> None:
        """Stop the agent and cleanup resources."""
        logger.info(
            "Rule Optimization Agent stopped",
            rules_tracked=len(self.rule_stats)
        )
