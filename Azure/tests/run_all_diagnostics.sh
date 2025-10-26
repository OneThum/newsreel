#!/bin/bash
# Run all diagnostic checks for Newsreel API

echo "========================================"
echo "Newsreel API Diagnostic Test Suite"
echo "========================================"
echo ""
echo "Running comprehensive system diagnostics..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "diagnostics/check_rss_ingestion.py" ]; then
    echo "${RED}Error: Please run this script from the tests/ directory${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "${YELLOW}Warning: .env file not found. Copying from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "${YELLOW}Please edit .env with your credentials before continuing.${NC}"
        exit 1
    else
        echo "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Create reports directory
mkdir -p reports

echo "========================================"
echo "1. RSS Ingestion Health Check"
echo "========================================"
python3 diagnostics/check_rss_ingestion.py
echo ""

echo "========================================"
echo "2. Story Clustering Quality Check"
echo "========================================"
python3 diagnostics/check_clustering_quality.py
echo ""

echo "========================================"
echo "3. Generating Comprehensive Health Report"
echo "========================================"
python3 diagnostics/system_health_report.py
echo ""

echo "========================================"
echo "Diagnostic Suite Complete!"
echo "========================================"
echo ""
echo "${GREEN}✓ All diagnostics completed${NC}"
echo ""
echo "Reports generated:"
echo "  - reports/health_report.html"
echo ""
echo "To view the HTML report:"
echo "  open reports/health_report.html"
echo ""
echo "For detailed bug information, see:"
echo "  reports/BUGS_DISCOVERED.md"
echo ""

