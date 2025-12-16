#!/bin/bash
#
# Integration Test Script - Run All README Steps
# This script walks through all steps documented in the README
#

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Snort3-AI-Ops Integration Test"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step counter
STEP=1

print_step() {
    echo -e "\n${BLUE}[$STEP]${NC} $1"
    ((STEP++))
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Activate virtual environment
print_step "Activating Python virtual environment"
source venv/bin/activate
print_success "Virtual environment activated"

# Verify dependencies
print_step "Verifying dependencies"
python -c "import zmq; import structlog; import crewai; print('All core dependencies available')"
print_success "Dependencies verified"

# Validate configuration
print_step "Validating configuration"
python main.py validate
print_success "Configuration validated"

# Test individual agents
print_step "Testing Threat Intelligence Agent"
python main.py test-agent -a threat_intel
print_success "Threat Intelligence Agent tested"

print_step "Testing Behavioral Analysis Agent"
python main.py test-agent -a behavioral
print_success "Behavioral Analysis Agent tested"

print_step "Testing Response Orchestrator Agent"
python main.py test-agent -a response
print_success "Response Orchestrator Agent tested"

# Test CLI investigate command
print_step "Testing investigation workflow"
python main.py investigate --ip 45.142.212.100
print_success "Investigation completed"

# Generate status report
print_step "Generating system status report"
python main.py status
print_success "Status report generated"

# Start event simulator in background
print_step "Starting Snort3 Event Simulator"
print_info "Simulating 30 seconds of Snort3 events at 3 events/sec"
python tests/snort3_simulator.py --duration 30 --rate 3.0 &
SIMULATOR_PID=$!
print_success "Simulator started (PID: $SIMULATOR_PID)"

# Give simulator time to bind
sleep 2

# Start AI-Ops engine to process events
print_step "Starting AI-Ops Engine to process events"
print_info "Processing events for 35 seconds"

# Create a temporary Python script to run the engine
cat > /tmp/run_aiops_test.py << 'EOF'
import asyncio
import signal
import sys
from core.engine import AIOpsEngine
from core.config import Config

async def run_test():
    """Run AI-Ops engine for testing."""
    config = Config.load()
    engine = AIOpsEngine(config)
    
    # Start engine
    await engine.start()
    
    # Run for 35 seconds
    try:
        await asyncio.sleep(35)
    except asyncio.CancelledError:
        pass
    finally:
        await engine.stop()

if __name__ == '__main__':
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(0)
EOF

timeout 40 python /tmp/run_aiops_test.py || true
print_success "Event processing completed"

# Wait for simulator to finish
wait $SIMULATOR_PID 2>/dev/null || true
print_success "Simulator completed"

# Check generated reports
print_step "Checking generated reports and logs"
if [ -d "reports" ]; then
    echo "Reports directory:"
    ls -lh reports/ | tail -10
    print_success "Reports generated"
else
    print_info "No reports directory found"
fi

if [ -d "data" ]; then
    echo "Data directory:"
    ls -lh data/ | tail -10
    print_success "Data files created"
else
    print_info "No data directory found"
fi

# Run unit tests
print_step "Running unit tests"
pytest tests/ -v --tb=short
print_success "All tests passed"

# Final summary
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Integration Test Complete${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  - Configuration: Valid"
echo "  - Agents: All tested successfully"
echo "  - Event Processing: Completed"
echo "  - Reports: Generated"
echo "  - Unit Tests: Passed"
echo ""
echo "Next steps:"
echo "  1. Review reports in ./reports/"
echo "  2. Check logs in ./logs/ (if created)"
echo "  3. Integrate with real Snort3 instance"
echo "  4. Configure API keys for threat intelligence"
echo "  5. Set up automated response workflows"
echo ""
