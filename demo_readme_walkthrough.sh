#!/bin/bash
#
# Complete README Walkthrough Demo
# Demonstrates all key features documented in the README
#

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🎯 Snort3-AI-Ops - Complete README Walkthrough"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "This demo walks through all major features from the README:"
echo "  1. Configuration validation"
echo "  2. Individual agent testing"
echo "  3. Live event processing with all agents"
echo "  4. Investigation workflows"
echo "  5. Report generation"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

pause() {
    echo -e "\n${YELLOW}Press Enter to continue...${NC}"
    read
}

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Example 1: Basic Event Monitoring (from README)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "As documented in README section: Usage Examples > Example 1"
echo ""
echo "This demonstrates the core event monitoring capability where"
echo "agents automatically process Snort3 events and:"
echo "  - Enrich with threat intelligence"
echo "  - Analyze for anomalies"
echo "  - Respond to incidents"
echo "  - Generate reports"
echo ""

pause

echo -e "\n${BLUE}→${NC} Starting 20-second live event processing demo..."
echo ""

# Start simulator in background
python tests/snort3_simulator.py --duration 25 --rate 2.0 > /tmp/simulator.log 2>&1 &
SIMULATOR_PID=$!
sleep 2

# Start live processing demo
python examples/live_processing_demo.py --duration 20

# Wait for simulator to finish
wait $SIMULATOR_PID 2>/dev/null || true

echo -e "\n${GREEN}✓${NC} Example 1 Complete"

echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Example 3: Interactive Investigation (from README)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "As documented in README section: Usage Examples > Example 3"
echo ""
echo "Demonstrating IP investigation workflow:"
echo ""

pause

# Investigate different IPs
echo -e "${BLUE}→${NC} Investigating known malicious IP..."
python main.py investigate --ip 45.142.212.100

echo ""
echo -e "${BLUE}→${NC} Investigating clean IP (Google DNS)..."
python main.py investigate --ip 8.8.8.8

echo ""
echo -e "${BLUE}→${NC} Investigating private IP..."
python main.py investigate --ip 192.168.1.1

echo -e "\n${GREEN}✓${NC} Example 3 Complete"

echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}CLI Tools Demonstration${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Testing all CLI commands from README:"
echo ""

pause

echo -e "${BLUE}1.${NC} Validating configuration..."
python main.py validate

echo ""
echo -e "${BLUE}2.${NC} Testing individual agents..."
python main.py test-agent -a threat_intel

echo ""
echo -e "${BLUE}3.${NC} Generating system status report..."
python main.py status

echo ""
echo -e "${BLUE}4.${NC} Viewing help..."
python main.py --help

echo -e "\n${GREEN}✓${NC} CLI Tools Demonstration Complete"

echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Report Review${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Generated reports and artifacts:"
echo ""

if [ -d "reports" ]; then
    echo "📄 Reports:"
    ls -lh reports/ | grep -v '^total' | awk '{print "  - " $9 " (" $5 ")"}'
fi

echo ""
if [ -d "data" ]; then
    echo "💾 Data files:"
    ls -lh data/ 2>/dev/null | grep -v '^total' | awk '{print "  - " $9 " (" $5 ")"}' || echo "  (empty)"
fi

echo ""
echo -e "${YELLOW}→${NC} You can view the HTML report:"
echo "  Open: reports/status_report.html in your browser"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Complete README Walkthrough Finished${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Summary of demonstrated features:"
echo "  ✓ Real-time event processing with all 5 agents"
echo "  ✓ Threat intelligence enrichment"
echo "  ✓ Behavioral anomaly detection"
echo "  ✓ Automated response orchestration"
echo "  ✓ Interactive investigation workflows"
echo "  ✓ CLI tools and commands"
echo "  ✓ Report generation"
echo ""
echo "📖 Next Steps:"
echo "  1. Review: cat INTEGRATION_TEST_RESULTS.md"
echo "  2. Install real Snort3 and configure plugin"
echo "  3. Add production API keys to .env"
echo "  4. Configure SIEM integration"
echo "  5. Deploy to production environment"
echo ""
echo "📁 Generated Documentation:"
echo "  - INTEGRATION_TEST_RESULTS.md (comprehensive test results)"
echo "  - reports/status_report.html (system status)"
echo ""
echo "For more information, see:"
echo "  - README.md (complete documentation)"
echo "  - SETUP_GUIDE.md (installation guide)"
echo "  - examples/ (additional code examples)"
echo ""
