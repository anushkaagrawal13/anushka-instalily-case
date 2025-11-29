#!/bin/bash

# PartSelect Chat Agent - Automated Setup Script
# Instalily AI Case Study

set -e  # Exit on error

echo "🚀 Starting PartSelect Chat Agent Setup..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Check Chrome/Chromium
if ! command -v google-chrome &> /dev/null && ! command -v chromium &> /dev/null; then
    echo -e "${YELLOW}⚠️  Chrome/Chromium not found. Web scraping may not work.${NC}"
else
    echo -e "${GREEN}✓ Chrome/Chromium found${NC}"
fi

echo ""
echo "=========================================="
echo "🔧 Setting up Backend..."
echo "=========================================="

# Backend setup
cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Google Custom Search API Configuration
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_CSE_ID=your-search-engine-id-here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=5001
EOF
    echo -e "${YELLOW}⚠️  Please update the .env file with your API keys${NC}"
    echo "   Required:"
    echo "   1. OpenAI API Key (https://platform.openai.com/api-keys)"
    echo "   2. Google API Key (https://console.cloud.google.com/)"
    echo "   3. Google Custom Search Engine ID (https://programmablesearchengine.google.com/)"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create log directories
mkdir -p logs

echo -e "${GREEN}✓ Backend setup complete${NC}"

cd ..

echo ""
echo "=========================================="
echo "🎨 Setting up Frontend..."
echo "=========================================="

# Frontend setup
cd frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "Creating .env.local file..."
    cat > .env.local << EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:5001

# Optional: Analytics
# NEXT_PUBLIC_ANALYTICS_ID=G-XXXXXXXXXX
EOF
    echo -e "${GREEN}✓ Created .env.local${NC}"
else
    echo -e "${GREEN}✓ .env.local already exists${NC}"
fi

echo -e "${GREEN}✓ Frontend setup complete${NC}"

cd ..

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Update API keys in backend/.env:"
echo "   ${YELLOW}nano backend/.env${NC}"
echo ""
echo "2. Start the backend server:"
echo "   ${GREEN}cd backend${NC}"
echo "   ${GREEN}source venv/bin/activate${NC}"
echo "   ${GREEN}python app.py${NC}"
echo ""
echo "3. In a new terminal, start the frontend:"
echo "   ${GREEN}cd frontend${NC}"
echo "   ${GREEN}npm run dev${NC}"
echo ""
echo "4. Open your browser to:"
echo "   ${GREEN}http://localhost:3000${NC}"
echo ""
echo "=========================================="
echo ""
echo "📚 For more information, see README.md"
echo ""
echo ""

# Create a quick start script
cat > start.sh << 'EOF'
#!/bin/bash

# Quick start script - runs both backend and frontend

echo "🚀 Starting PartSelect Chat Agent..."

# Start backend in background
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 3

# Start frontend
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "✅ Both servers are running!"
echo "   Backend:  http://localhost:5001"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
EOF

chmod +x start.sh

echo -e "${GREEN}✓ Created start.sh for easy launching${NC}"
echo "   Run ${GREEN}./start.sh${NC} to start both servers at once"