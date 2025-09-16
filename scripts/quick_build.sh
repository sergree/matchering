#!/bin/bash

# Quick Build Script for Auralis
# Usage: ./scripts/quick_build.sh [options]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
SKIP_TESTS=false
PORTABLE_ONLY=false
CLEAN_FIRST=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --portable-only)
            PORTABLE_ONLY=true
            shift
            ;;
        --clean)
            CLEAN_FIRST=true
            shift
            ;;
        --help|-h)
            echo "Quick Build Script for Auralis"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-tests     Skip running tests before building"
            echo "  --portable-only  Create portable package only"
            echo "  --clean         Clean build directories first"
            echo "  --help, -h      Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Header
echo -e "${BLUE}🎵 Auralis Quick Build Script${NC}"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "auralis_gui.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the Auralis root directory${NC}"
    exit 1
fi

# Clean if requested
if [ "$CLEAN_FIRST" = true ]; then
    echo -e "${YELLOW}🧹 Cleaning build directories...${NC}"
    rm -rf build/ dist/ __pycache__/
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${BLUE}🐍 Python version: $PYTHON_VERSION${NC}"

if [ "$(echo "$PYTHON_VERSION 3.11" | awk '{print ($1 >= $2)}')" != "1" ]; then
    echo -e "${YELLOW}⚠️  Warning: Python 3.11+ recommended, you have $PYTHON_VERSION${NC}"
fi

# Install dependencies if needed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! python -c "import customtkinter" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip install -r requirements-desktop.txt
fi

if ! python -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing PyInstaller...${NC}"
    pip install pyinstaller
fi

# Build arguments
BUILD_ARGS=""
if [ "$SKIP_TESTS" = true ]; then
    BUILD_ARGS="$BUILD_ARGS --skip-tests"
fi
if [ "$PORTABLE_ONLY" = true ]; then
    BUILD_ARGS="$BUILD_ARGS --portable-only"
fi

# Start build
echo -e "${GREEN}🔨 Starting build...${NC}"
START_TIME=$(date +%s)

python build_auralis.py $BUILD_ARGS

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Build complete
echo ""
echo -e "${GREEN}✅ Build completed in ${DURATION}s!${NC}"

# Show results
if [ -d "dist" ]; then
    echo -e "${BLUE}📊 Build Results:${NC}"
    echo "=================="

    if [ -f "dist/Auralis-"*".tar.gz" ]; then
        PACKAGE_SIZE=$(du -h dist/Auralis-*.tar.gz | cut -f1)
        echo -e "📦 Portable package: ${GREEN}$PACKAGE_SIZE${NC}"
    fi

    if [ -d "dist/Auralis" ]; then
        INSTALL_SIZE=$(du -sh dist/Auralis | cut -f1)
        echo -e "💿 Installation size: ${GREEN}$INSTALL_SIZE${NC}"
    fi

    echo ""
    echo -e "${BLUE}🚀 Ready for distribution!${NC}"
    echo "To test: cd dist/Auralis && ./Auralis"
else
    echo -e "${RED}❌ Build failed - no dist directory created${NC}"
    exit 1
fi