#!/bin/bash
# ===========================================================================
# SOLARA Weather API Test Suite
# Tests all critical fixes in solara_weather_api.py
# ===========================================================================

set -e  # Exit on any error

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║  SOLARA Weather API - Test Suite                                  ║"
echo "║  Testing Critical Fixes v3.1.1                                    ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_TESTS=5

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ===========================================================================
# Test 1: Email Validation (CRITICAL)
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1/5: Email Requirement Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_weather_api import NSRDBWeatherAPI
import sys

try:
    # Should fail without email
    api = NSRDBWeatherAPI(api_key='test_key')
    print("❌ FAILED: Should require email")
    sys.exit(1)
except ValueError as e:
    if "Email required" in str(e):
        print("✓ PASSED: Email validation works correctly")
        print(f"  Error message: {str(e)[:60]}...")
        sys.exit(0)
    else:
        print(f"❌ FAILED: Wrong error - {e}")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAILED: Unexpected error - {e}")
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
# Test 2: Environment Variable Loading
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2/5: Environment Variable Loading"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
export NREL_API_KEY="test_api_key_12345"
export NREL_EMAIL="test@example.com"

python3 << 'PYTHON_EOF'
from solara_weather_api import NSRDBWeatherAPI
import sys

try:
    api = NSRDBWeatherAPI()
    if api.api_key == "test_api_key_12345" and api.email == "test@example.com":
        print("✓ PASSED: Environment variables loaded correctly")
        print(f"  API Key: {api.api_key[:10]}...")
        print(f"  Email: {api.email}")
        sys.exit(0)
    else:
        print("❌ FAILED: Environment variables not loaded correctly")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAILED: {e}")
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
# Test 3: Email Format Validation
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3/5: Email Format Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_weather_api import NSRDBWeatherAPI
import sys

invalid_emails = ['invalid', 'no-at-sign.com', 'no-domain@', '@no-local']
passed = True

for email in invalid_emails:
    try:
        api = NSRDBWeatherAPI(api_key='test', email=email)
        print(f"❌ Should reject invalid email: {email}")
        passed = False
    except ValueError:
        print(f"✓ Correctly rejected: {email}")

if passed:
    print("\n✓ PASSED: Email format validation works")
    sys.exit(0)
else:
    print("\n❌ FAILED: Email validation not strict enough")
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
# Test 4: Retry Session Configuration
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4/5: Retry Logic Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_weather_api import NSRDBWeatherAPI
import sys

try:
    api = NSRDBWeatherAPI(api_key='test', email='test@example.com')
    session = api._create_session_with_retries(max_retries=3)
    
    # Check retry adapter is configured
    adapter = session.get_adapter('https://')
    
    if hasattr(adapter, 'max_retries'):
        retry_config = adapter.max_retries
        print(f"✓ Retry adapter configured")
        print(f"  Max retries: {retry_config.total}")
        print(f"  Backoff factor: {retry_config.backoff_factor}")
        print(f"  Status codes: {retry_config.status_forcelist}")
        
        if retry_config.total == 3:
            print("\n✓ PASSED: Retry logic configured correctly")
            sys.exit(0)
        else:
            print("\n❌ FAILED: Wrong retry count")
            sys.exit(1)
    else:
        print("❌ FAILED: Retry adapter not found")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
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
# Test 5: Cache Path Generation
# ===========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5/5: Cache Path Generation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'PYTHON_EOF'
from solara_weather_api import NSRDBWeatherAPI
import sys

try:
    api = NSRDBWeatherAPI(api_key='test', email='test@example.com')
    
    # Test cache path generation
    lat, lon = 39.7385, -104.985
    cache_path = api._get_cache_path(lat, lon, 'tmy')
    
    print(f"✓ Cache path generated: {cache_path.name}")
    
    # Verify it's consistent
    cache_path2 = api._get_cache_path(lat, lon, 'tmy')
    
    if cache_path == cache_path2:
        print("✓ Cache paths are consistent")
        print(f"  Path: {cache_path}")
        print("\n✓ PASSED: Cache path generation works")
        sys.exit(0)
    else:
        print("❌ FAILED: Cache paths not consistent")
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
    echo -e "${GREEN}║  ✓ ALL TESTS PASSED - Weather API fixes working correctly!       ║${NC}"
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
