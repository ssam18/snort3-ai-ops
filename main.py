"""
Snort3-AI-Ops: Intelligent Threat Analysis & Response Orchestration

Main entry point for the AI-Ops engine.
"""

import asyncio
import signal
import sys
from pathlib import Path
from datetime import datetime, UTC

import click
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from core.engine import AIOpsEngine
from core.config import load_config
from utils.logger import setup_logging

console = Console()
logger = structlog.get_logger(__name__)


def display_banner():
    """Display the startup banner."""
    banner = Text()
    banner.append("╔═══════════════════════════════════════════════════════════╗\n", style="bold cyan")
    banner.append("║         Snort3-AI-Ops - Intelligent Security Ops         ║\n", style="bold cyan")
    banner.append("║                                                           ║\n", style="bold cyan")
    banner.append("║  Transform Snort3 into an Intelligent Security Platform  ║\n", style="bold white")
    banner.append("╚═══════════════════════════════════════════════════════════╝\n", style="bold cyan")
    
    console.print(Panel(banner, border_style="cyan"))


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received", signal=signum)
    console.print("\n[yellow]Shutting down gracefully...[/yellow]")
    sys.exit(0)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Snort3-AI-Ops Command Line Interface."""
    pass


@cli.command()
@click.option(
    '--config',
    '-c',
    type=click.Path(exists=True),
    default='config/config.yaml',
    help='Path to configuration file'
)
@click.option(
    '--debug',
    is_flag=True,
    help='Enable debug mode'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Run in dry-run mode (no actual actions)'
)
def start(config, debug, dry_run):
    """Start the AI-Ops engine."""
    display_banner()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration
        console.print("[cyan]Loading configuration...[/cyan]")
        cfg = load_config(config)
        
        # Setup logging
        log_level = 'DEBUG' if debug else cfg.logging.level
        setup_logging(log_level, cfg.logging.format)
        
        logger.info(
            "Starting Snort3-AI-Ops",
            config_file=config,
            debug=debug,
            dry_run=dry_run
        )
        
        # Initialize the engine
        console.print("[cyan]Initializing AI-Ops engine...[/cyan]")
        engine = AIOpsEngine(cfg, dry_run=dry_run)
        
        # Start the engine
        console.print("[green]✓ Engine initialized successfully[/green]")
        console.print("[cyan]Starting event processing...[/cyan]")
        
        asyncio.run(engine.start())
        
    except Exception as e:
        logger.error("Failed to start AI-Ops engine", error=str(e), exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    '--config',
    '-c',
    type=click.Path(exists=True),
    default='config/config.yaml',
    help='Path to configuration file'
)
def validate(config):
    """Validate configuration file."""
    console.print(f"[cyan]Validating configuration: {config}[/cyan]")
    
    try:
        cfg = load_config(config)
        console.print("[green]✓ Configuration is valid[/green]")
        
        # Display key settings
        console.print("\n[bold]Key Settings:[/bold]")
        console.print(f"  Event Stream: {cfg.event_stream.endpoint}")
        console.print(f"  Enabled Agents: {len([a for a in cfg.agents.__dict__.values() if getattr(a, 'enabled', False)])}")
        console.print(f"  Database: {cfg.database.type}")
        console.print(f"  API Port: {cfg.api.port}")
        
    except Exception as e:
        console.print(f"[red]✗ Configuration validation failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    '--agent',
    '-a',
    type=click.Choice([
        'threat_intel',
        'behavioral',
        'response',
        'rule_optimizer',
        'report'
    ]),
    required=True,
    help='Agent to test'
)
@click.option(
    '--input',
    '-i',
    type=click.Path(exists=True),
    help='Test input file'
)
@click.option(
    '--config',
    '-c',
    type=click.Path(exists=True),
    default='config/config.yaml',
    help='Path to configuration file'
)
def test_agent(agent, input, config):
    """Test a specific agent with sample data."""
    console.print(f"[cyan]Testing {agent} agent...[/cyan]")
    
    try:
        # Load configuration
        cfg = load_config(config)
        
        # Create test event
        test_event = {
            'id': 'test-001',
            'type': 'alert',
            'timestamp': '2025-12-11T10:00:00Z',
            'src_ip': '192.168.1.100',
            'dst_ip': '10.0.0.50',
            'signature': 'Test Signature',
            'severity': 75
        }
        
        # Initialize and test the agent
        import asyncio
        if agent == 'threat_intel':
            from agents.threat_intelligence_agent import ThreatIntelligenceAgent
            test_agent_obj = ThreatIntelligenceAgent(cfg.agents.threat_intelligence)
            result = asyncio.run(test_agent_obj.enrich_event(test_event))
            console.print("[green]✓ Threat Intelligence Agent test completed[/green]")
            console.print(f"Result: {result}")
        
        elif agent == 'behavioral':
            from agents.behavioral_analysis_agent import BehavioralAnalysisAgent
            test_agent_obj = BehavioralAnalysisAgent(cfg.agents.behavioral_analysis)
            result = asyncio.run(test_agent_obj.analyze_event(test_event))
            console.print("[green]✓ Behavioral Analysis Agent test completed[/green]")
            console.print(f"Result: {result}")
        
        elif agent == 'response':
            from agents.response_orchestrator_agent import ResponseOrchestratorAgent
            test_agent_obj = ResponseOrchestratorAgent(cfg.agents.response, dry_run=True)
            asyncio.run(test_agent_obj.handle_event(test_event))
            console.print("[green]✓ Response Orchestrator Agent test completed[/green]")
        
        elif agent == 'rule_optimizer':
            from agents.rule_optimization_agent import RuleOptimizationAgent
            test_agent_obj = RuleOptimizationAgent(cfg.agents.rule_optimization)
            recommendations = asyncio.run(test_agent_obj.analyze_rules())
            console.print("[green]✓ Rule Optimization Agent test completed[/green]")
            console.print(f"Recommendations: {recommendations}")
        
        elif agent == 'report':
            from agents.report_generation_agent import ReportGenerationAgent
            test_agent_obj = ReportGenerationAgent(cfg.agents.report_generation)
            report_path = asyncio.run(test_agent_obj.generate_daily_report())
            console.print("[green]✓ Report Generation Agent test completed[/green]")
            console.print(f"Report saved to: {report_path}")
        
    except Exception as e:
        console.print(f"[red]✗ Agent test failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    '--output',
    '-o',
    type=click.Path(),
    default='reports/status_report.html',
    help='Output file path'
)
@click.option(
    '--config',
    '-c',
    type=click.Path(exists=True),
    default='config/config.yaml',
    help='Path to configuration file'
)
def status(output, config):
    """Generate system status report."""
    console.print("[cyan]Generating status report...[/cyan]")
    
    try:
        from pathlib import Path
        import json
        from datetime import datetime
        
        # Load configuration
        cfg = load_config(config)
        
        # Collect system status
        status_data = {
            'timestamp': datetime.now(UTC).isoformat(),
            'config': {
                'event_stream_endpoint': cfg.event_stream.endpoint,
                'database': cfg.database.type,
                'api_port': cfg.api.port
            },
            'agents': {}
        }
        
        # Check which agents are enabled
        if cfg.agents.threat_intelligence.enabled:
            status_data['agents']['threat_intelligence'] = 'enabled'
        if cfg.agents.behavioral_analysis.enabled:
            status_data['agents']['behavioral_analysis'] = 'enabled'
        if cfg.agents.response.enabled:
            status_data['agents']['response'] = 'enabled'
        if cfg.agents.rule_optimization.enabled:
            status_data['agents']['rule_optimization'] = 'enabled'
        if cfg.agents.report_generation.enabled:
            status_data['agents']['report_generation'] = 'enabled'
        
        # Create output directory if needed
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate HTML report
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Snort3-AI-Ops Status Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .status {{ background: #e8f5e9; padding: 20px; margin: 20px 0; border-left: 4px solid #4caf50; }}
        .agent {{ background: #f5f5f5; padding: 10px; margin: 5px 0; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>Snort3-AI-Ops Status Report</h1>
    <p>Generated: {status_data['timestamp']}</p>
    <div class="status">
        <h2>Configuration</h2>
        <pre>{json.dumps(status_data['config'], indent=2)}</pre>
    </div>
    <div class="status">
        <h2>Enabled Agents</h2>
        <pre>{json.dumps(status_data['agents'], indent=2)}</pre>
    </div>
</body>
</html>"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        console.print(f"[green]✓ Status report generated: {output}[/green]")
        console.print(f"  Enabled agents: {len(status_data['agents'])}")
        
    except Exception as e:
        console.print(f"[red]✗ Status report generation failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    '--ip',
    help='IP address to investigate'
)
@click.option(
    '--domain',
    help='Domain to investigate'
)
@click.option(
    '--hash',
    help='File hash to investigate'
)
@click.option(
    '--config',
    '-c',
    type=click.Path(exists=True),
    default='config/config.yaml',
    help='Path to configuration file'
)
def investigate(ip, domain, hash, config):
    """Investigate an indicator."""
    if not any([ip, domain, hash]):
        console.print("[red]Error: Please provide an IP, domain, or hash to investigate[/red]")
        sys.exit(1)
    
    console.print("[cyan]Starting investigation...[/cyan]")
    
    try:
        import asyncio
        from agents.threat_intelligence_agent import ThreatIntelligenceAgent
        
        # Load configuration
        cfg = load_config(config)
        
        # Initialize threat intelligence agent
        threat_intel = ThreatIntelligenceAgent(cfg.agents.threat_intelligence)
        
        # Determine IOC type and value
        if ip:
            ioc_type = 'ip'
            ioc_value = ip
        elif domain:
            ioc_type = 'domain'
            ioc_value = domain
        else:
            ioc_type = 'hash'
            ioc_value = hash
        
        console.print(f"[cyan]Investigating {ioc_type}: {ioc_value}[/cyan]")
        
        # Lookup IOC
        result = asyncio.run(threat_intel._lookup_ioc(ioc_value, ioc_type))
        
        # Display results
        console.print("\n[bold]Investigation Results:[/bold]")
        console.print(f"  IOC: {result.get('value')}")
        console.print(f"  Type: {result.get('type')}")
        console.print(f"  Threat Score: {result.get('threat_score')}/100")
        console.print(f"  Malicious: {result.get('malicious')}")
        
        if result.get('sources'):
            console.print(f"  Sources: {', '.join(result.get('sources', {}).keys())}")
        
        if result.get('tags'):
            console.print(f"  Tags: {', '.join(result.get('tags', []))}")
        
        # Recommendations
        console.print("\n[bold]Recommendations:[/bold]")
        if result.get('threat_score', 0) >= 70:
            console.print("  ⚠️  [red]HIGH RISK - Consider blocking this IOC[/red]")
        elif result.get('threat_score', 0) >= 40:
            console.print("  ⚡ [yellow]MEDIUM RISK - Monitor closely[/yellow]")
        else:
            console.print("  ✓ [green]LOW RISK - No immediate action required[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Investigation failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    cli()
