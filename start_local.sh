#!/bin/bash
# LandingOS Local Startup Script
# Event-Driven Visual Navigation for Precision Planetary Landing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=============================================="
echo "   LandingOS - Local Development Server"
echo "   Event-Driven Visual Navigation Platform"
echo "=============================================="
echo -e "${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is required but not installed.${NC}"
    exit 1
fi

# Check for npm/yarn
if ! command -v yarn &> /dev/null && ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm or yarn is required but not installed.${NC}"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Install backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
cd "$BACKEND_DIR"
pip3 install -r requirements.txt -q

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd "$FRONTEND_DIR"
if command -v yarn &> /dev/null; then
    yarn install --silent
else
    npm install --silent
fi

echo -e "${GREEN}Dependencies installed successfully!${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${BLUE}Starting backend server on http://localhost:8001${NC}"
cd "$BACKEND_DIR"
python3 -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

sleep 3

# Start frontend
echo -e "${BLUE}Starting frontend server on http://localhost:3000${NC}"
cd "$FRONTEND_DIR"
if command -v yarn &> /dev/null; then
    BROWSER=none PORT=3000 yarn start &
else
    BROWSER=none PORT=3000 npm start &
fi
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}=============================================="
echo "   LandingOS is running!"
echo "=============================================="
echo -e "${NC}"
echo ""
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8001"
echo "API Docs:  http://localhost:8001/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for processes
wait
