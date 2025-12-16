#!/usr/bin/env python3
"""
Autonomous Setup Script for Snort3-AI-Ops

This script provides a one-command setup experience:
    python autonomous_setup.py

The setup agent will:
- Install all dependencies automatically (including Python packages)
- Setup the complete infrastructure
- Run tests
- Provide comprehensive guidance
- Run live demonstrations
- Interactive chat mode for exploration
"""

import sys
import os
import subprocess
import time
import signal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Global flag for cleanup
CLEANUP_ON_EXIT = False
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully with cleanup"""
    global CLEANUP_ON_EXIT
    
    print("\n\n" + "="*80)
    print("⚠️  INTERRUPT SIGNAL RECEIVED")
    print("="*80)
    
    if CLEANUP_ON_EXIT:
        print("\n🧹 Performing cleanup...")
        print("   This will stop and remove all containers, volumes, and networks.\n")
        
        response = input("Do you want to clean up? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            perform_cleanup()
        else:
            print("\n✓ Cleanup skipped. Containers are still running.")
            print("  To clean up later, run: docker compose down -v")
    else:
        print("\n⚠️  Setup interrupted by user")
        print("   The system may be partially configured.\n")
        
        show_recovery_info()
    
    sys.exit(0)


def perform_cleanup():
    """Perform complete cleanup of Docker resources"""
    from rich.console import Console
    console = Console()
    
    console.print("\n[yellow]🧹 Starting cleanup process...[/yellow]\n")
    
    steps = [
        ("Stopping all containers", "docker compose stop"),
        ("Removing containers", "docker compose rm -f"),
        ("Removing volumes", "docker compose down -v"),
        ("Removing networks", "docker network prune -f"),
        ("Removing unused images", "docker image prune -f")
    ]
    
    for description, command in steps:
        console.print(f"  → {description}...")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                console.print(f"    [green]✓[/green] {description} complete")
            else:
                console.print(f"    [yellow]⚠[/yellow] {description} had issues (non-critical)")
        except Exception as e:
            console.print(f"    [yellow]⚠[/yellow] {description} failed: {str(e)}")
    
    console.print("\n[green]✅ Cleanup complete![/green]")
    console.print("[dim]All containers, volumes, and networks have been removed.[/dim]\n")


def show_recovery_info():
    """Show recovery information after interruption"""
    print("="*80)
    print("RECOVERY INFORMATION")
    print("="*80)
    print()
    print("To check system status:")
    print("  docker compose ps")
    print()
    print("To view logs:")
    print("  docker compose logs")
    print()
    print("To restart:")
    print("  docker compose restart")
    print()
    print("To clean and retry:")
    print("  docker compose down -v")
    print("  python autonomous_setup.py")
    print("="*80)


def check_and_install_dependencies():
    """
    Check if required Python packages are installed.
    If not, install them automatically.
    """
    required_packages = {
        'rich': 'rich>=13.0.0',
        'yaml': 'pyyaml>=6.0'
    }
    
    missing_packages = []
    
    # Check each required package
    for package_import, package_install in required_packages.items():
        try:
            __import__(package_import)
            print(f"✓ {package_import} is already installed")
        except ImportError:
            print(f"✗ {package_import} is missing")
            missing_packages.append(package_install)
    
    # Install missing packages
    if missing_packages:
        print(f"\n📦 Installing missing Python dependencies: {', '.join(missing_packages)}")
        print("This will only take a moment...\n")
        
        try:
            # Try pip install
            cmd = [sys.executable, '-m', 'pip', 'install'] + missing_packages
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ All dependencies installed successfully!\n")
                return True
            else:
                # If pip module not found, try direct pip
                print("⚠️  pip module not found, trying direct pip command...")
                cmd = ['pip3', 'install'] + missing_packages
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ All dependencies installed successfully!\n")
                    return True
                else:
                    print(f"❌ Failed to install dependencies: {result.stderr}")
                    print("\nPlease install manually:")
                    print(f"  pip install {' '.join(missing_packages)}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error installing dependencies: {str(e)}")
            print("\nPlease install manually:")
            print(f"  pip install {' '.join(missing_packages)}")
            return False
    else:
        print("✅ All required Python packages are installed!\n")
        return True


# Check and install dependencies BEFORE importing
print("="*70)
print("🔍 Checking Python dependencies for autonomous setup agent...")
print("="*70 + "\n")

if not check_and_install_dependencies():
    print("\n" + "="*70)
    print("⚠️  Setup cannot continue without required dependencies.")
    print("="*70)
    sys.exit(1)

# Now safe to import (dependencies are installed)
try:
    from agents.setup_agent import SetupAgent
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError as e:
    print(f"\n❌ Error importing modules: {str(e)}")
    print("Please ensure all dependencies are installed correctly.")
    sys.exit(1)


def main():
    """Main entry point for autonomous setup"""
    global CLEANUP_ON_EXIT
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    import sys
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    if verbose:
        print("\n🔊 VERBOSE MODE ENABLED - Showing all output in real-time\n")
    
    # Display welcome banner
    banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🤖  SNORT3-AI-OPS AUTONOMOUS SETUP AGENT  🤖            ║
║                                                              ║
║  Your intelligent assistant for complete system setup       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[yellow]What I will do:[/yellow]
  ✓ Check and install all dependencies (Docker, Docker Compose, etc.)
  ✓ Parse and understand the complete README
  ✓ Setup infrastructure (5 AI agents + Database + Cache + API)
  ✓ Run comprehensive tests
  ✓ Provide detailed usage guidance
  ✓ Run live demonstrations with explanations
  ✓ Suggest improvements and best practices
  ✓ Interactive chat mode for exploration

[yellow]Minimal human intervention required![/yellow]
  → You may need to enter your password for sudo commands
  → All other steps are fully automated

[dim]This will take approximately 5-10 minutes depending on your internet speed.[/dim]
    """
    
    if verbose:
        banner += "\n[bold green]🔊 Running in VERBOSE mode - you'll see all command output[/bold green]\n"
    else:
        banner += "\n[dim]💡 Tip: Use --verbose or -v flag to see detailed output[/dim]\n"
    
    banner += "\n[bold red]⚠️  Press Ctrl+C at any time to stop and clean up[/bold red]\n"
    
    console.print(Panel(banner, border_style="cyan"))
    
    # Confirm to proceed (auto-proceed if non-interactive)
    console.print("\n[bold]Ready to begin?[/bold]")
    try:
        response = input("Press Enter to start or Ctrl+C to cancel: ")
    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]Running in non-interactive mode, auto-starting...[/yellow]")
        time.sleep(1)
    
    # Initialize and run setup agent
    project_root = os.path.dirname(os.path.abspath(__file__))
    agent = SetupAgent(project_root=project_root, verbose=verbose)
    
    # Run complete autonomous setup
    setup_result = agent.run_complete_setup()
    
    # Mark that cleanup is now available (after setup completes)
    CLEANUP_ON_EXIT = True
    
    # After setup, ALWAYS offer interactive mode (even if setup had issues)
    console.print("\n")
    console.print("="*80)
    console.print("[bold green]🎉 SETUP PHASE COMPLETE![/bold green]")
    console.print("="*80)
    console.print()
    
    # Show setup status
    if setup_result and setup_result.get('status') == 'success':
        console.print("[bold green]✅ All systems operational![/bold green]")
    elif setup_result and setup_result.get('status') == 'interrupted':
        console.print("[yellow]⚠️  Setup was interrupted but containers may be running.[/yellow]")
    else:
        console.print("[yellow]⚠️  Setup completed with some issues, but system may still be usable.[/yellow]")
    
    console.print()
    console.print("[bold cyan]I'm your autonomous guide and I'll stay active to help you![/bold cyan]")
    console.print()
    console.print("[dim]I can help you:[/dim]")
    console.print("  • Chat and answer questions about the project")
    console.print("  • Run tests and demonstrations")
    console.print("  • Execute commands on your behalf")
    console.print("  • Monitor system status")
    console.print("  • Cleanup and manage containers")
    console.print()
    console.print("[bold yellow]💡 Press Ctrl+C anytime to quit and optionally cleanup[/bold yellow]")
    console.print()
    
    # Now enter interactive mode and stay there
    offer_interactive_mode(agent, console)


def offer_interactive_mode(agent, console):
    """Offer interactive chat and exploration mode - STAYS ACTIVE as persistent guide"""
    console.print("[bold cyan]🤖 Interactive Mode - I'm Your Persistent Guide[/bold cyan]\n")
    
    while True:  # INFINITE LOOP - only exits on user's explicit choice
        console.print("\n" + "="*80)
        console.print("[bold]What would you like to do?[/bold]")
        console.print("="*80 + "\n")
        
        console.print("  [bold]1.[/bold] 💬 Chat with Agent - Ask questions about the system")
        console.print("  [bold]2.[/bold] 🎬 Run Live Demo - See demonstrations of capabilities")
        console.print("  [bold]3.[/bold] 🔧 Run Custom Command - Execute Docker/system commands")
        console.print("  [bold]4.[/bold] 📊 View System Status - Check containers and agents")
        console.print("  [bold]5.[/bold] 🧹 Cleanup and Exit - Stop and remove all containers")
        console.print("  [bold]6.[/bold] 🚪 Exit - Leave containers running\n")
        
        try:
            choice = input("Enter your choice (1-6) or 'help': ").strip()
            
            if choice == '1':
                chat_mode(agent, console)
                # After chat, loop back to menu
                continue
            elif choice == '2':
                run_demo_mode(agent, console)
                # After demo, loop back to menu
                continue
            elif choice == '3':
                run_custom_command(console)
                # After command, loop back to menu
                continue
            elif choice == '4':
                show_system_status(console)
                # After status, loop back to menu
                continue
            elif choice == '5':
                # User wants to cleanup and exit
                perform_cleanup()
                break  # Exit the loop
            elif choice == '6':
                # User wants to exit without cleanup
                console.print("\n[green]✓[/green] Exiting. Containers are still running.")
                console.print("[dim]Access dashboard: http://localhost:8080[/dim]")
                console.print("[dim]Stop services: docker compose stop[/dim]\n")
                break  # Exit the loop
            elif choice.lower() == 'help':
                console.print("\n[bold]Available Commands:[/bold]")
                console.print("  1 - Interactive chat with AI agent")
                console.print("  2 - Watch live demonstrations")
                console.print("  3 - Run custom Docker commands")
                console.print("  4 - View current system status")
                console.print("  5 - Clean up everything and exit")
                console.print("  6 - Exit without cleanup")
                console.print("\n[dim]💡 You can also press Ctrl+C anytime to exit[/dim]\n")
            else:
                console.print("[yellow]Invalid choice. Enter 1-6 or 'help'[/yellow]\n")
                
        except (EOFError, KeyboardInterrupt):
            console.print("\n\n[yellow]⚠️  Interrupted by user (Ctrl+C)[/yellow]")
            console.print("[dim]Exiting interactive mode...[/dim]\n")
            break  # Exit on Ctrl+C


def chat_mode(agent, console):
    """Interactive chat with the agent"""
    console.print("\n" + "="*80)
    console.print("[bold cyan]💬 CHAT MODE[/bold cyan]")
    console.print("="*80)
    console.print("\n[dim]Ask me anything about Snort3-AI-Ops, usage, configuration, etc.[/dim]")
    console.print("[dim]Type 'exit' to return to main menu.[/dim]\n")
    
    while True:
        try:
            question = input("[bold green]You:[/bold green] ").strip()
            
            if question.lower() in ['exit', 'quit', 'back']:
                break
            
            if not question:
                continue
            
            # Process the question
            console.print(f"\n[bold cyan]Agent:[/bold cyan] ", end="")
            
            # Provide intelligent responses based on keywords
            answer = get_agent_response(question, agent)
            console.print(answer + "\n")
            
        except (EOFError, KeyboardInterrupt):
            break
    
    console.print("\n[dim]Returning to main menu...[/dim]\n")


def get_agent_response(question, agent):
    """Generate intelligent responses to user questions"""
    q = question.lower()
    
    # Question patterns and responses
    if 'status' in q or 'running' in q:
        result = subprocess.run(
            "docker compose ps",
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        return f"Current system status:\n\n{result.stdout}\n\nAll services should show 'running (healthy)' status."
    
    elif 'dashboard' in q or 'url' in q or 'access' in q:
        return "Access the dashboard at: http://localhost:8080\nAPI documentation: http://localhost:8080/docs"
    
    elif 'agent' in q and ('what' in q or 'tell' in q):
        return """5 AI Agents are working for you:

1. Threat Intelligence Agent - Enriches IOCs from 50+ threat feeds
2. Behavioral Analysis Agent - Detects anomalies using ML
3. Response Orchestration Agent - Recommends and executes actions
4. Rule Optimization Agent - Tunes Snort3 rules automatically
5. Report Generation Agent - Creates compliance and executive reports

Each agent works autonomously and collaborates with others."""
    
    elif 'test' in q or 'demo' in q:
        return "Run a demo with: docker compose exec aiops-engine python examples/apt_detection_demo.py\n\nThis generates synthetic attacks to see the agents in action."
    
    elif 'logs' in q or 'view' in q:
        return "View logs with:\n  docker compose logs -f aiops-engine   (AI agents)\n  docker compose logs -f api-server    (API server)\n  docker compose logs -f postgres      (database)\n  docker compose logs -f redis         (cache)"
    
    elif 'stop' in q or 'shutdown' in q:
        return "To stop the system:\n  docker compose stop     (stop containers)\n  docker compose down     (remove containers)\n  docker compose down -v  (remove everything including data)"
    
    elif 'api' in q or 'endpoint' in q:
        return "Key API endpoints:\n  GET  /api/v1/health         - System health\n  GET  /api/v1/events         - List events\n  POST /api/v1/events         - Submit event\n  GET  /api/v1/agents/status  - Agent status\n  GET  /api/v1/reports/weekly - Weekly report\n\nFull docs: http://localhost:8080/docs"
    
    elif 'config' in q or 'configuration' in q:
        return "Configuration file: config/config.yaml\n\nKey sections:\n  - event_stream: ZeroMQ settings\n  - agents: Enable/disable agents, API keys\n  - integrations: SIEM, firewalls, ticketing\n  - database: PostgreSQL connection\n\nRestart after changes: docker compose restart"
    
    elif 'help' in q:
        return """I can help with:

• System status and health checks
• How to access dashboard and APIs  
• Information about the 5 AI agents
• How to run tests and demos
• Viewing logs and troubleshooting
• API endpoints and usage
• Configuration and customization
• Stopping and managing containers

Just ask your question naturally!"""
    
    else:
        return """I'm not sure about that specific question, but here are some things I can help with:

• "What is the status?" - Check system health
• "How do I access the dashboard?" - Get URLs
• "Tell me about the agents" - Learn about AI agents
• "How do I run a test?" - Testing instructions
• "Show me the logs" - View log commands
• "What are the API endpoints?" - API documentation
• "How do I stop the system?" - Shutdown instructions

Or type 'help' for more options."""


def run_demo_mode(agent, console):
    """Run interactive demonstrations"""
    console.print("\n" + "="*80)
    console.print("[bold cyan]🎬 DEMONSTRATION MODE[/bold cyan]")
    console.print("="*80 + "\n")
    
    console.print("Available demonstrations:\n")
    console.print("  [bold]1.[/bold] System Health Check")
    console.print("  [bold]2.[/bold] Generate Synthetic Attacks")
    console.print("  [bold]3.[/bold] View Agent Processing")
    console.print("  [bold]4.[/bold] API Examples")
    console.print("  [bold]5.[/bold] Back to main menu\n")
    
    choice = input("Select demo (1-5): ").strip()
    
    if choice == '1':
        console.print("\n[bold]Demo 1: System Health Check[/bold]\n")
        subprocess.run("curl -s http://localhost:8080/api/v1/health | python -m json.tool", shell=True)
        input("\n[bold cyan]Press Enter to return to demonstration menu...[/bold cyan] ")
        
    elif choice == '2':
        console.print("\n[bold]Demo 2: Generating Synthetic Attacks[/bold]\n")
        console.print("[dim]Running APT detection demo...[/dim]\n")
        subprocess.run(
            "docker compose exec aiops-engine python examples/apt_detection_demo.py",
            shell=True,
            cwd=PROJECT_ROOT
        )
        input("\n[bold cyan]Press Enter to return to demonstration menu...[/bold cyan] ")
        
    elif choice == '3':
        console.print("\n[bold]Demo 3: Viewing Agent Processing[/bold]\n")
        console.print("[yellow]═" * 70 + "[/yellow]")
        console.print("[bold yellow]  ⚡ Press Ctrl+C at any time to stop log streaming and return  [/bold yellow]")
        console.print("[yellow]═" * 70 + "[/yellow]\n")
        console.print("[dim]Showing last 50 lines of agent logs (streaming live)...[/dim]\n")
        try:
            subprocess.run(
                "docker compose logs --tail=50 -f aiops-engine",
                shell=True,
                cwd=PROJECT_ROOT
            )
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Log streaming stopped by user[/yellow]")
        
        input("\n[bold cyan]Press Enter to return to demonstration menu...[/bold cyan] ")
        
    elif choice == '4':
        console.print("\n[bold]Demo 4: API Examples[/bold]\n")
        
        console.print("1. Agent Status:")
        subprocess.run("curl -s http://localhost:8080/api/v1/agents/status | python -m json.tool", shell=True)
        
        print("\n2. Recent Events:")
        subprocess.run("curl -s 'http://localhost:8080/api/v1/events?limit=5' | python -m json.tool", shell=True)
        
        input("\n[bold cyan]Press Enter to return to demonstration menu...[/bold cyan] ")


def run_custom_command(console):
    """Allow running custom commands"""
    console.print("\n" + "="*80)
    console.print("[bold cyan]🔧 CUSTOM COMMAND MODE[/bold cyan]")
    console.print("="*80 + "\n")
    
    console.print("[dim]Enter Docker or system commands. Type 'back' to return.[/dim]\n")
    console.print("[yellow]Examples:[/yellow]")
    console.print("  docker compose ps")
    console.print("  docker compose logs api-server --tail=20")
    console.print("  docker stats --no-stream\n")
    
    while True:
        try:
            cmd = input("[bold green]Command:[/bold green] ").strip()
            
            if cmd.lower() in ['exit', 'quit', 'back']:
                break
            
            if not cmd:
                continue
            
            console.print()
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=PROJECT_ROOT
            )
            console.print()
            
        except (EOFError, KeyboardInterrupt):
            break
    
    console.print("\n[dim]Returning to main menu...[/dim]\n")


def show_system_status(console):
    """Display comprehensive system status"""
    console.print("\n" + "="*80)
    console.print("[bold cyan]📊 SYSTEM STATUS[/bold cyan]")
    console.print("="*80 + "\n")
    
    console.print("[bold]Docker Containers:[/bold]")
    subprocess.run("docker compose ps", shell=True, cwd=PROJECT_ROOT)
    
    console.print("\n[bold]Resource Usage:[/bold]")
    subprocess.run("docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'", shell=True)
    
    console.print("\n[bold]Agent Health:[/bold]")
    result = subprocess.run(
        "curl -s http://localhost:8080/api/v1/agents/status",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        console.print(result.stdout)
    else:
        console.print("[yellow]Could not fetch agent status[/yellow]")
    
    input("\n\nPress Enter to return to menu...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled by user.[/yellow]")
        if CLEANUP_ON_EXIT:
            response = input("Do you want to clean up? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                perform_cleanup()
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
