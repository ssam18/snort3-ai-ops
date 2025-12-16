#!/bin/bash
#
# Quick Verification Script for Persistent Agent Implementation
# 
# This script verifies that all changes are in place and working correctly.
#

# Don't exit on error - we want to count all successes/failures
# set -e

echo "================================================================================"
echo "🔍 Verifying Persistent Agent Implementation"
echo "================================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

# Test 1: Check autonomous_setup.py has continue statements
echo -n "1. Checking autonomous_setup.py has persistent loop... "
if grep -q "After chat, loop back to menu" autonomous_setup.py && \
   grep -q "After demo, loop back to menu" autonomous_setup.py && \
   grep -q "# INFINITE LOOP - only exits on user's explicit choice" autonomous_setup.py; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((failed++))
fi

# Test 2: Check setup agent returns status
echo -n "2. Checking setup_agent.py returns status dict... "
if grep -q '"status": "success"' agents/setup_agent.py; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((failed++))
fi

# Test 3: Check README has persistent guide documentation
echo -n "3. Checking README has persistent guide documentation... "
if grep -q "I'm Your Persistent Guide" README.md && \
   grep -q "Interactive Guide Phase" README.md; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((failed++))
fi

# Test 4: Check test file exists
echo -n "4. Checking test_persistent_agent.py exists... "
if [ -f "tests/test_persistent_agent.py" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((failed++))
fi

# Test 5: Run automated tests
echo -n "5. Running automated tests... "
if python3 tests/test_persistent_agent.py > /tmp/test_output.txt 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "   Output: $(cat /tmp/test_output.txt)"
    ((failed++))
fi

# Test 6: Check FAQ exists
echo -n "6. Checking FAQ documentation exists... "
if [ -f "docs/AUTONOMOUS_AGENT_FAQ.md" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((failed++))
fi

# Test 7: Check implementation docs exist
echo -n "7. Checking implementation documentation exists... "
if [ -f "docs/PERSISTENT_AGENT_IMPLEMENTATION.md" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((failed++))
fi

# Test 8: Check demo script exists and runs
echo -n "8. Checking demo script exists and runs... "
if [ -f "docs/demo_persistent_behavior.py" ] && \
   python3 docs/demo_persistent_behavior.py > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((failed++))
fi

# Test 9: Check signal handler for Ctrl+C
echo -n "9. Checking Ctrl+C signal handler exists... "
if grep -q "KeyboardInterrupt" autonomous_setup.py && \
   grep -q "Interrupted by user" autonomous_setup.py; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((failed++))
fi

# Test 10: Check cleanup function exists
echo -n "10. Checking cleanup functionality exists... "
if grep -q "def perform_cleanup" autonomous_setup.py; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((failed++))
fi

echo ""
echo "================================================================================"
echo "📊 Results Summary"
echo "================================================================================"
echo ""
echo -e "Passed: ${GREEN}${passed}/10${NC}"
echo -e "Failed: ${RED}${failed}/10${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! The persistent agent is ready to use.${NC}"
    echo ""
    echo "To try it:"
    echo "  python3 autonomous_setup.py --verbose"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  Some checks failed. Please review the implementation.${NC}"
    echo ""
    exit 1
fi
