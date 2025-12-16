#!/usr/bin/env python3
"""
Live Event Processing Demo
Demonstrates the complete Snort3-AI-Ops workflow with simulated events
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

from connectors.snort3_event_stream import Snort3EventStream
from agents.threat_intelligence_agent import ThreatIntelligenceAgent
from agents.behavioral_analysis_agent import BehavioralAnalysisAgent
from agents.response_orchestrator_agent import ResponseOrchestratorAgent
from core.config import load_config

console = Console()
logger = structlog.get_logger(__name__)


class LiveDashboard:
    """Live updating dashboard for event processing."""
    
    def __init__(self):
        self.event_count = 0
        self.alert_count = 0
        self.flow_count = 0
        self.threat_count = 0
        self.anomaly_count = 0
        self.response_count = 0
        self.latest_events = []
        
    def generate_table(self) -> Layout:
        """Generate the live dashboard layout."""
        layout = Layout()
        
        # Statistics table
        stats_table = Table(title="📊 Event Processing Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", justify="right", style="green")
        
        stats_table.add_row("Total Events", str(self.event_count))
        stats_table.add_row("Alerts", str(self.alert_count))
        stats_table.add_row("Flows", str(self.flow_count))
        stats_table.add_row("Threats Detected", str(self.threat_count))
        stats_table.add_row("Anomalies", str(self.anomaly_count))
        stats_table.add_row("Responses", str(self.response_count))
        
        # Latest events table
        events_table = Table(title="🔔 Latest Events")
        events_table.add_column("Time", style="dim")
        events_table.add_column("Type", style="cyan")
        events_table.add_column("Source", style="yellow")
        events_table.add_column("Threat Score", justify="right", style="red")
        
        for event in self.latest_events[-10:]:
            events_table.add_row(
                event.get('time', '-'),
                event.get('type', '-'),
                event.get('source', '-'),
                str(event.get('threat_score', 0))
            )
        
        layout.split_column(
            Layout(stats_table, name="stats"),
            Layout(events_table, name="events")
        )
        
        return layout


async def process_events(duration: int = 60):
    """
    Process live events from the simulator.
    
    Args:
        duration: How long to process events in seconds
    """
    console.print(Panel.fit(
        "[bold cyan]🚀 Snort3-AI-Ops Live Event Processing Demo[/bold cyan]\n\n"
        f"Duration: {duration} seconds\n"
        "Press Ctrl+C to stop early",
        border_style="cyan"
    ))
    
    # Load configuration
    config = load_config()
    
    # Initialize agents
    console.print("\n[yellow]→[/yellow] Initializing AI agents...")
    threat_agent = ThreatIntelligenceAgent(config.agents.threat_intelligence)
    behavioral_agent = BehavioralAnalysisAgent(config.agents.behavioral_analysis)
    response_agent = ResponseOrchestratorAgent(config.agents.response, dry_run=True)
    console.print("[green]✓[/green] Agents initialized\n")
    
    # Initialize event stream
    event_stream = Snort3EventStream(config.event_stream)
    
    # Initialize dashboard
    dashboard = LiveDashboard()
    
    # Track when to stop
    start_time = asyncio.get_event_loop().time()
    
    try:
        with Live(dashboard.generate_table(), refresh_per_second=2, console=console) as live:
            async for event in event_stream.stream():
                # Update statistics
                dashboard.event_count += 1
                
                event_type = event.get('type', 'unknown')
                if event_type == 'alert':
                    dashboard.alert_count += 1
                elif event_type == 'flow':
                    dashboard.flow_count += 1
                
                # Process with agents
                try:
                    # Threat Intelligence
                    threat_result = await threat_agent.enrich_event(event)
                    threat_score = threat_result.get('threat_score', 0)
                    
                    if threat_score > 50:
                        dashboard.threat_count += 1
                    
                    # Behavioral Analysis
                    behavioral_result = await behavioral_agent.analyze_event(event)
                    if behavioral_result.get('is_anomalous', False):
                        dashboard.anomaly_count += 1
                    
                    # Response Orchestration
                    combined_event = {
                        **event,
                        'threat_intel': threat_result,
                        'behavioral': behavioral_result,
                        'severity': max(threat_score, int(behavioral_result.get('anomaly_score', 0) * 100))
                    }
                    
                    await response_agent.handle_event(combined_event)
                    dashboard.response_count += 1
                    
                    # Add to latest events
                    dashboard.latest_events.append({
                        'time': event.get('timestamp', '')[-12:-4],  # HH:MM:SS
                        'type': event_type,
                        'source': event.get('src_ip', '-'),
                        'threat_score': threat_score
                    })
                    
                except Exception as e:
                    logger.error("Error processing event", error=str(e))
                
                # Update dashboard
                live.update(dashboard.generate_table())
                
                # Check if duration elapsed
                if asyncio.get_event_loop().time() - start_time >= duration:
                    break
                    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠[/yellow] Processing interrupted by user")
    
    # Final summary
    console.print(f"\n\n[green]✓[/green] Processing complete!")
    console.print(f"\n📊 Final Statistics:")
    console.print(f"  Total Events: {dashboard.event_count}")
    console.print(f"  Alerts: {dashboard.alert_count}")
    console.print(f"  Flows: {dashboard.flow_count}")
    console.print(f"  Threats: {dashboard.threat_count}")
    console.print(f"  Anomalies: {dashboard.anomaly_count}")
    console.print(f"  Responses: {dashboard.response_count}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Live Event Processing Demo')
    parser.add_argument('--duration', type=int, default=30,
                        help='Processing duration in seconds (default: 30)')
    
    args = parser.parse_args()
    
    try:
        asyncio.run(process_events(duration=args.duration))
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo terminated[/yellow]")
        sys.exit(0)
