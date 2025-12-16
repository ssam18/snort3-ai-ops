"""
Agent Visualization and Status Monitor
Shows real-time status of all 5 AI agents
"""

import asyncio
import aiohttp
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
import time

console = Console()


class AgentMonitor:
    """Real-time monitor for all 5 AI agents"""
    
    def __init__(self, api_url='http://localhost:8080'):
        self.api_url = api_url
        self.session = None
        self.running = True
    
    async def start(self):
        """Start monitoring"""
        self.session = aiohttp.ClientSession()
        
        with Live(self.generate_display(), refresh_per_second=1, console=console) as live:
            while self.running:
                try:
                    live.update(await self.generate_display())
                    await asyncio.sleep(2)
                except KeyboardInterrupt:
                    self.running = False
                    break
        
        await self.session.close()
    
    async def get_agent_status(self):
        """Fetch agent status from API"""
        try:
            async with self.session.get(f"{self.api_url}/api/v1/agents") as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except:
            return []
    
    async def get_stats(self):
        """Fetch system statistics"""
        try:
            async with self.session.get(f"{self.api_url}/api/v1/stats") as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
        except:
            return {}
    
    async def generate_display(self):
        """Generate the monitoring display"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Header
        layout["header"].update(
            Panel(
                Text.from_markup(
                    "[bold cyan]Snort3-AI-Ops Agent Monitor[/bold cyan]\n"
                    f"[dim]Monitoring 5 AI Agents | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
                ),
                border_style="cyan"
            )
        )
        
        # Main content - agent table
        table = Table(title="[bold]AI Agent Status[/bold]", show_header=True)
        table.add_column("Agent", style="cyan", width=25)
        table.add_column("Role", style="magenta", width=30)
        table.add_column("Status", width=10)
        table.add_column("Tasks", justify="right", width=8)
        table.add_column("Success Rate", justify="right", width=12)
        
        agents = await self.get_agent_status()
        
        if not agents:
            # Show default structure when API not available
            default_agents = [
                ("Threat Intelligence", "Analyzes threat patterns", "🟡", "-", "-"),
                ("Behavioral Analysis", "Detects anomalies", "🟡", "-", "-"),
                ("Incident Response", "Coordinates actions", "🟡", "-", "-"),
                ("Rule Optimization", "Tunes detection rules", "🟡", "-", "-"),
                ("Report Generation", "Creates reports", "🟡", "-", "-"),
            ]
            for agent in default_agents:
                table.add_row(*agent)
        else:
            for agent in agents:
                status_icon = "🟢" if agent['status'] == 'active' else "🔴"
                table.add_row(
                    agent['name'],
                    agent['role'],
                    status_icon,
                    str(agent.get('tasks_completed', 0)),
                    f"{agent.get('success_rate', 0)}%"
                )
        
        layout["main"].update(Panel(table, border_style="green"))
        
        # Footer - stats
        stats = await self.get_stats()
        stats_text = (
            f"[bold]Events:[/bold] {stats.get('events_processed', 0):,} | "
            f"[bold]Incidents:[/bold] {stats.get('incidents_created', 0):,} | "
            f"[bold]Blocked:[/bold] {stats.get('threats_blocked', 0):,} | "
            f"[bold]Reports:[/bold] {stats.get('reports_generated', 0):,}"
        )
        
        layout["footer"].update(
            Panel(
                Text.from_markup(stats_text),
                border_style="yellow"
            )
        )
        
        return layout


async def main():
    """Main entry point"""
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]         Snort3-AI-Ops Real-Time Agent Visualization          [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
    
    console.print("[dim]Monitoring all 5 AI agents:[/dim]")
    console.print("  [cyan]1. Threat Intelligence Agent[/cyan] - IOC enrichment")
    console.print("  [magenta]2. Behavioral Analysis Agent[/magenta] - Anomaly detection")
    console.print("  [green]3. Incident Response Agent[/green] - Action coordination")
    console.print("  [yellow]4. Rule Optimization Agent[/yellow] - Detection tuning")
    console.print("  [blue]5. Report Generation Agent[/blue] - Automated reporting\n")
    
    console.print("[dim]Press Ctrl+C to stop...[/dim]\n")
    
    monitor = AgentMonitor()
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Monitoring stopped[/yellow]")
    
    console.print("\n[green]✓ Agent monitor closed[/green]\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
