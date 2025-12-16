# Autonomous Setup Agent

This directory contains the autonomous setup agent for Snort3-AI-Ops.

## What is the Setup Agent?

The Setup Agent is an intelligent assistant that handles the complete installation, configuration, testing, and demonstration of Snort3-AI-Ops with minimal human intervention.

## Key Features

### 🤖 Fully Autonomous
- Reads and understands the README documentation
- Executes each setup step automatically
- Explains what it's doing and why

### 🔧 Self-Healing
- Detects and fixes common errors automatically
- Handles permission issues, port conflicts, missing dependencies
- Retries failed operations with exponential backoff

### 📚 Educational
- Provides detailed explanations for each step
- Runs live demonstrations with "What, Why, How" format
- Teaches best practices

### ✅ Comprehensive Testing
- Verifies all prerequisites
- Tests all services after setup
- Validates agent initialization
- Checks API endpoints

## Usage

### Quick Start
```bash
python autonomous_setup.py
```

### What It Does

1. **Prerequisites Check**
   - Verifies Docker installation
   - Checks Docker Compose
   - Tests internet connectivity
   - Auto-installs missing dependencies

2. **README Parsing**
   - Extracts all setup steps
   - Identifies commands to execute
   - Understands the architecture

3. **Infrastructure Setup**
   - Pulls Docker images
   - Starts all containers
   - Waits for services to initialize
   - Verifies health checks

4. **Testing**
   - API health checks
   - Agent status verification
   - Database connectivity tests
   - Integration tests

5. **Guidance**
   - How to run the system
   - How to test features
   - How to use the API
   - Advantages and limitations
   - Improvement suggestions

6. **Live Demo**
   - Interactive demonstrations
   - Step-by-step explanations
   - Real command execution
   - Output interpretation

## Error Handling

The agent includes intelligent error recovery:

### Automatic Fixes
- **Permission Denied**: Adjusts file permissions
- **Docker Not Found**: Installs Docker automatically
- **Port Conflicts**: Kills processes on required ports
- **Disk Space**: Cleans up Docker resources
- **Network Issues**: Recreates Docker networks

### Retry Logic
- Exponential backoff (1s, 2s, 4s)
- Up to 3 retry attempts per command
- Detailed error logging

## Architecture

```
autonomous_setup.py          # Entry point
├── agents/setup_agent.py    # Main agent logic
│   ├── parse_readme()       # Extract setup steps
│   ├── check_prerequisites() # Verify dependencies
│   ├── install_dependencies() # Auto-install missing deps
│   ├── setup_infrastructure() # Deploy containers
│   ├── verify_setup()       # Validate deployment
│   ├── run_tests()          # Execute tests
│   ├── provide_guidance()   # User education
│   └── run_live_demo()      # Interactive demo
```

## Example Output

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🤖  SNORT3-AI-OPS AUTONOMOUS SETUP AGENT  🤖            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🔍 Checking prerequisites...
✓ Docker: Installed
✓ Docker Compose: Installed
✓ Git: Installed
✓ Internet: Connected

📖 Reading and parsing README.md...
✓ README parsed successfully

📦 Installing dependencies...
All dependencies satisfied

🚀 Setting up infrastructure...
  📌 Pulling Docker images
     Why: Downloading pre-built container images from Docker Hub
  ✓ Success
  
  📌 Starting all services
     Why: Launching 5 AI agents, PostgreSQL, Redis, and API server
  ✓ Success

✅ Verifying setup...
✓ Containers Running
✓ Database Available
✓ Redis Available
✓ API Server Responding
✓ 5 Agents Initialized
✓ ZeroMQ Stream Active

🧪 Running tests...
✓ API Health Check: PASSED
✓ Agent Status Check: PASSED
✓ Database Connection: PASSED

📚 SNORT3-AI-OPS USER GUIDE
...
```

## Requirements

Minimal requirements for the setup agent:
```
rich>=13.0.0
pyyaml>=6.0
```

System requirements (auto-installed if missing):
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+

## Advanced Usage

### Skip Certain Steps
```python
from agents.setup_agent import SetupAgent

agent = SetupAgent()
agent.check_prerequisites()
agent.setup_infrastructure()
# Skip tests
agent.provide_guidance()
```

### Custom Configuration
```python
agent = SetupAgent(project_root="/custom/path")
agent.max_retries = 5  # More retry attempts
agent.run_complete_setup()
```

## Troubleshooting

### Agent Fails to Install Docker
- **Issue**: Requires sudo password
- **Solution**: Run with sudo or add user to docker group
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```

### Port Already in Use
- **Issue**: Ports 8080, 5432, 6379, or 5555 occupied
- **Solution**: Agent auto-kills processes or specify different ports

### Internet Connection Issues
- **Issue**: Cannot download Docker images
- **Solution**: Check firewall, proxy settings, or use pre-downloaded images

## Contributing

To enhance the setup agent:
1. Add new error detection patterns in `_auto_heal()`
2. Extend verification checks in `verify_setup()`
3. Add more demos in `run_live_demo()`
4. Improve README parsing in `parse_readme()`

## License

Same as main project (GPL v2.0)
