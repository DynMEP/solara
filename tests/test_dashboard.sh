#!/bin/bash
# ===========================================================================
# SOLARA Dashboard Test Suite
# Tests all critical fixes in solara_dashboard.py
# ===========================================================================

set -e  # Exit on any error

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║  SOLARA Dashboard - Test Suite                                    ║"
echo "║  Testing Error Handling v3.1.1                                    ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_TESTS=6

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ===========================================================================
# Test 1: Empty Optimizer Handling
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1/6: Empty Optimizer Handling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_dashboard import SOLARADashboard
import sys

class EmptyOptimizer:
    pass

try:
    dash = SOLARADashboard(EmptyOptimizer())
    print("✓ PASSED: Dashboard handles empty optimizer without crashing")
    sys.exit(0)
except Exception as e:
    print(f"❌ FAILED: Dashboard crashed with empty optimizer - {e}")
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test 1 PASSED${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ Test 1 FAILED${NC}"
    ((FAIL_COUNT++))
fi
echo ""

# ===========================================================================
# Test 2: Missing evaluation_history Attribute
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2/6: Missing History Attribute Handling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_dashboard import SOLARADashboard
import sys

class NoHistoryOptimizer:
    def __init__(self):
        self.some_other_attr = "value"
        # No evaluation_history attribute

try:
    dash = SOLARADashboard(NoHistoryOptimizer())
    print("✓ Dashboard created successfully")
    print("✓ PASSED: Dashboard handles missing history attribute")
    sys.exit(0)
except Exception as e:
    print(f"❌ FAILED: Dashboard crashed - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test 2 PASSED${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ Test 2 FAILED${NC}"
    ((FAIL_COUNT++))
fi
echo ""

# ===========================================================================
# Test 3: Empty History Handling
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3/6: Empty History Handling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_dashboard import SOLARADashboard
import sys

class EmptyHistoryOptimizer:
    evaluation_history = []

try:
    dash = SOLARADashboard(EmptyHistoryOptimizer())
    print("✓ Dashboard created successfully with empty history")
    print("✓ PASSED: Dashboard handles empty history list")
    sys.exit(0)
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test 3 PASSED${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ Test 3 FAILED${NC}"
    ((FAIL_COUNT++))
fi
echo ""

# ===========================================================================
# Test 4: Corrupted History Data
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4/6: Corrupted History Data Handling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_dashboard import SOLARADashboard
import sys

class CorruptedOptimizer:
    evaluation_history = [
        "not a dict",
        None,
        {'score': 'not a number'},
        {'no_score_key': 123}
    ]

try:
    dash = SOLARADashboard(CorruptedOptimizer())
    print("✓ Dashboard created successfully with corrupted data")
    print("✓ PASSED: Dashboard handles corrupted history gracefully")
    sys.exit(0)
except Exception as e:
    print(f"❌ FAILED: Dashboard crashed with corrupted data - {e}")
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test 4 PASSED${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ Test 4 FAILED${NC}"
    ((FAIL_COUNT++))
fi
echo ""

# ===========================================================================
# Test 5: Helper Methods Existence
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5/6: Helper Methods Existence"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_dashboard import SOLARADashboard, MockOptimizer
import sys

required_methods = [
    '_create_error_display',
    '_create_info_status',
    '_create_empty_figure',
    '_create_info_figure',
    '_create_error_figure'
]

try:
    dash = SOLARADashboard(MockOptimizer())
    
    missing_methods = []
    for method in required_methods:
        if not hasattr(dash, method):
            missing_methods.append(method)
        else:
            print(f"✓ Method exists: {method}")
    
    if not missing_methods:
        print("\n✓ PASSED: All helper methods present")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED: Missing methods - {missing_methods}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test 5 PASSED${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ Test 5 FAILED${NC}"
    ((FAIL_COUNT++))
fi
echo ""

# ===========================================================================
# Test 6: Mock Optimizer Test
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 6/6: Mock Optimizer Integration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_dashboard import SOLARADashboard, MockOptimizer
import sys

try:
    # Create mock optimizer with fake data
    mock = MockOptimizer(n_evals=50)
    print(f"✓ Mock optimizer created with {len(mock.evaluation_history)} evaluations")
    
    # Create dashboard
    dash = SOLARADashboard(mock)
    print("✓ Dashboard created successfully")
    
    # Check that history is accessible
    if hasattr(dash.optimizer, 'evaluation_history'):
        print(f"✓ Dashboard can access evaluation history")
        print(f"  History length: {len(dash.optimizer.evaluation_history)}")
        
        # Check data format
        if dash.optimizer.evaluation_history:
            first_entry = dash.optimizer.evaluation_history[0]
            if 'score' in first_entry:
                print(f"✓ History entries have correct format")
                print(f"  First score: {first_entry['score']:.4f}")
            else:
                print("❌ History entries missing 'score' key")
                sys.exit(1)
        
        print("\n✓ PASSED: Mock optimizer integration works")
        sys.exit(0)
    else:
        print("❌ FAILED: Cannot access evaluation history")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test 6 PASSED${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ Test 6 FAILED${NC}"
    ((FAIL_COUNT++))
fi
echo ""

# ===========================================================================
# Final Summary
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}║  ✓ ALL TESTS PASSED - Dashboard fixes working correctly!         ║${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                   ║${NC}"
    echo -e "${RED}║  ✗ SOME TESTS FAILED - Review errors above                       ║${NC}"
    echo -e "${RED}║                                                                   ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
