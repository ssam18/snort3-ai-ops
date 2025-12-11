"""
Snort3-AI-Ops: Intelligent Threat Analysis & Response Orchestration

Main entry point for the AI-Ops engine.
"""

import asyncio
import signal
import sys
from pathlib import Path

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
def test_agent(agent, input):
    """Test a specific agent with sample data."""
    console.print(f"[cyan]Testing {agent} agent...[/cyan]")
    
    # TODO: Implement agent testing
    console.print("[yellow]Agent testing functionality coming soon[/yellow]")


@cli.command()
@click.option(
    '--output',
    '-o',
    type=click.Path(),
    default='reports/status_report.html',
    help='Output file path'
)
def status(output):
    """Generate system status report."""
    console.print("[cyan]Generating status report...[/cyan]")
    
    # TODO: Implement status reporting
    console.print("[yellow]Status reporting functionality coming soon[/yellow]")


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
def investigate(ip, domain, hash):
    """Investigate an indicator."""
    if not any([ip, domain, hash]):
        console.print("[red]Error: Please provide an IP, domain, or hash to investigate[/red]")
        sys.exit(1)
    
    console.print("[cyan]Starting investigation...[/cyan]")
    
    # TODO: Implement investigation functionality
    console.print("[yellow]Investigation functionality coming soon[/yellow]")


if __name__ == '__main__':
    cli()
