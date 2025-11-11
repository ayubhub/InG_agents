#!/bin/bash
# Code validation script for InG AI Sales Department
# Analog of "yarn build" for Python

set -e

echo "🔍 Checking Python code..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Syntax check
echo -e "\n${YELLOW}1. Checking syntax...${NC}"
find src -name "*.py" -exec python3 -m py_compile {} \; 2>&1
python3 -m py_compile main.py
echo -e "${GREEN}✓ Syntax check passed${NC}"

# 2. Import check
echo -e "\n${YELLOW}2. Checking imports...${NC}"
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.utils.logger import setup_logger
    from src.utils.config_loader import load_config
    from src.core.models import Lead, SendResult, ResponseAnalysis
    from src.agents.base_agent import BaseAgent
    print('✓ Core imports OK')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
" || exit 1
echo -e "${GREEN}✓ Import check passed${NC}"

# 3. Check for common issues
echo -e "\n${YELLOW}3. Checking for common issues...${NC}"

# Check for undefined variables (basic)
if grep -r "undefined" src/ main.py 2>/dev/null; then
    echo -e "${RED}✗ Found 'undefined' references${NC}"
    exit 1
fi

# Check for TODO/FIXME in code (optional)
if grep -r "TODO\|FIXME" src/ main.py 2>/dev/null | grep -v "# TODO"; then
    echo -e "${YELLOW}⚠ Found TODO/FIXME comments${NC}"
fi

echo -e "${GREEN}✓ Common issues check passed${NC}"

# 4. Check file structure
echo -e "\n${YELLOW}4. Checking file structure...${NC}"
required_files=(
    "main.py"
    "src/agents/base_agent.py"
    "src/agents/sales_manager_agent.py"
    "src/agents/lead_finder_agent.py"
    "src/agents/outreach_agent.py"
    "src/core/models.py"
    "src/integrations/llm_client.py"
    "src/integrations/google_sheets_io.py"
    "src/integrations/linkedin_sender.py"
    "src/integrations/email_service.py"
    "src/communication/state_manager.py"
    "src/communication/message_queue.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Missing required file: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ File structure check passed${NC}"

# 5. Optional: Run linter if available
if command -v flake8 &> /dev/null; then
    echo -e "\n${YELLOW}5. Running flake8...${NC}"
    flake8 src/ main.py --max-line-length=120 --ignore=E501,W503 || echo -e "${YELLOW}⚠ flake8 found issues (non-blocking)${NC}"
elif command -v pylint &> /dev/null; then
    echo -e "\n${YELLOW}5. Running pylint...${NC}"
    pylint src/ main.py --disable=all --enable=E,F || echo -e "${YELLOW}⚠ pylint found issues (non-blocking)${NC}"
else
    echo -e "\n${YELLOW}5. Linter not installed (optional)${NC}"
    echo "   Install with: pip install flake8"
fi

echo -e "\n${GREEN}✅ All checks passed!${NC}"

