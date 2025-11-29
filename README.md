# PartSelect Chat Agent - Instalily AI Case Study, Anushka Agrawal
**AI-Powered Appliance Parts Assistant for Refrigerators & Dishwashers**

## Overview

The PartSelect Chat Agent is an intelligent conversational assistant designed to help users with refrigerator and dishwasher parts. It provides accurate, context-aware responses for installation guidance, compatibility checks, and troubleshooting advice by combining real-time web scraping, semantic search, and GPT-4 powered natural language understanding.

### Criteria Met

- **Scope Restriction**: Only handles refrigerator and dishwasher queries
- **Installation Support**: Step-by-step guides with tools and safety instructions
- **Compatibility Checks**: Real-time part-model verification
- **Troubleshooting**: Diagnoses issues with recommended parts and fix rates
- **Modern UI**: Next.js interface with PartSelect branding
- **Extensible Architecture**: Easy to add new appliance types

---

## Tech Stack

### Frontend
- **Framework**: Next.js 14.1 (React 18.2)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.4
- **Markdown**: ReactMarkdown
- **Icons**: Lucide React
- **HTTP Client**: Fetch API

### Backend
- **Framework**: Flask 3.0 (Python)
- **AI Model**: OpenAI GPT-4
- **Vector Database**: ChromaDB 0.4
- **Embeddings**: OpenAI text-embedding-ada-002
- **Web Scraping**: Selenium + Undetected ChromeDriver
- **Search**: Google Custom Search API
- **LangChain**: For LLM orchestration

### Infrastructure
- **Version Control**: Git
- **Package Management**: npm (frontend), pip (backend)
- **Environment**: Development (local), Production-ready

---

## Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                  USER INTERFACE (Next.js)               │
│  • Modern chat interface                                │
│  • Real-time message updates                            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ HTTP POST /chat
                   │ { message: "query" }
                   ▼
┌─────────────────────────────────────────────────────────┐
│              FLASK API SERVER (app.py)                  │
│  • CORS configuration                                   │
│  • Request validation                                   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           AGENT MANAGER (agent_manager.py)              │
│  ┌─────────────────────────────────────────────────┐    │
│  │         GPT-4 Intent Detection                   │   │
│  │  • Classify: installation/compatibility/         │   │
│  │    troubleshooting/general                       │   │
│  │  • Extract: part numbers, model numbers          │   │
│  └────────────────┬─────────────────────────────────┘   │
│                   │                                     │
│  ┌────────────────▼─────────────────────────────────┐   │
│  │         Query Routing & Processing               │   │
│  │  • Route to appropriate handler                  │   │
│  │  • Orchestrate data retrieval                    │   │
│  └────┬──────────┬──────────┬───────────────────────┘   │
│       │          │          │                           │
└───────┼──────────┼──────────┼───────────────────────────┘
        │          │          │
        ▼          ▼          ▼
┌──────────┐ ┌─────────┐ ┌──────────────┐
│  Google  │ │Scrapers │ │Vector Manager│
│  Search  │ │         │ │              │
│   API    │ │PartSelect│ │  ChromaDB   │
└──────────┘ │Symptom  │ │OpenAI Embed │
             └─────────┘ └──────────────┘
                   │              │
                   ▼              ▼
            ┌──────────────────────────┐
            │   PartSelect.com         │
            │  • Product pages         │
            │  • Symptom pages         │
            │  • User repair stories   │
            └──────────────────────────┘
```

### Component Breakdown

#### 1. Frontend (Next.js)
**File**: `frontend/src/app/page.tsx`

#### 2. Backend API (Flask)
**File**: `backend/app.py`

#### 3. Agent Manager
**File**: `backend/agent_manager.py`

**Core Responsibilities**:
- **Intent Detection**: Uses GPT-4 to classify user queries
- **Entity Extraction**: Identifies part numbers, model numbers, symptoms
- **Query Routing**: Directs queries to specialized handlers
- **Response Generation**: Creates formatted, helpful responses

**Handlers**:
- `handle_installation()`: Installation guidance
- `handle_compatibility()`: Part-model compatibility
- `handle_troubleshoot()`: Issue diagnosis and solutions

#### 4. Vector Manager
**File**: `backend/vector_manager.py`

- Manages ChromaDB vector store
- Creates embeddings with OpenAI text-embedding-ada-002
- Semantic search with intent-based filtering
- Indexes scraped data with metadata tagging

**Document Types**:
- Q&A pairs
- Installation guides
- User repair stories
- Model compatibility data
- Troubleshooting symptoms

#### 5. Web Scrapers
**Files**: 
- `backend/partselect_scraper.py`: Product pages
- `backend/symptom_scraper.py`: Troubleshooting pages

- Selenium with undetected ChromeDriver
- Extracts product details, pricing, Q&A

#### 6. Search Integration
**File**: `backend/google_search.py`

- Google Custom Search API integration
- Restricted to PartSelect.com domain

---

## Getting Started

### Prerequisites

```bash
# Required Software
- Python 3.9+
- Node.js 18+
- Chrome/Chromium browser
- Git
```

### API Keys Required

1. **OpenAI API Key**

2. **Google Custom Search API**

### Installation

For easy installation and startup on Linux/MacOS, simply run ./setup.sh and ./start.sh.
This will create a virtual environment, install dependencies, and start the application.

For manual installation:
#### 1. Clone Repository

```bash
git clone <your-repository-url>
cd partselect-chatbot
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
nano .env  # Add your API keys

# Required .env variables:
# OPENAI_API_KEY=sk-...
# GOOGLE_API_KEY=AIza...
# GOOGLE_CSE_ID=...
```

#### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
nano .env.local

# Required .env.local variables:
# NEXT_PUBLIC_API_URL=http://localhost:5001
```

#### 4. Start the Application

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
python app.py
# Server runs on http://localhost:5001
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
# App runs on http://localhost:3000
```

#### 5. Verify Setup

Open browser to: **http://localhost:3000**

You should see:
- ✅ Styled chat interface with orange header
- ✅ Three quick action buttons
- ✅ Welcome message from the bot
- ✅ Input box at the bottom


## 📁 Project Structure

```
partselect-chatbot/
│
├── README.md                          
├── .gitignore
├── setup.sh
├── start.sh                        
│
├── backend/                           # Flask API
│   ├── app.py                         # Main Flask server
│   ├── agent_manager.py               # AI orchestration & intent handling
│   ├── vector_manager.py              # ChromaDB & embeddings
│   ├── google_search.py               # Google Custom Search integration
│   ├── partselect_scraper.py          # Product page scraper
│   ├── symptom_scraper.py             # Troubleshooting page scraper
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment template
│   ├── .env                           # Your API keys (not in git)
│   └── logs/                          # Application logs
│       ├── flask.log
│       ├── agent_manager.log
│       └── vector_manager.log
│
└── frontend/                          # Next.js application
    ├── src/
    │   └── app/
    │       ├── page.tsx               # Main chat interface
    │       ├── layout.tsx             # Root layout
    │       └── globals.css            # Global styles + Tailwind
    ├── public/                        # Static assets
    ├── package.json                   # Node dependencies
    ├── tsconfig.json                  # TypeScript config
    ├── tailwind.config.js             # Tailwind configuration
    ├── postcss.config.js              # PostCSS configuration
    ├── next.config.js                 # Next.js configuration
    └── .env.local                     # Frontend config (not in git)
```
---


## Future Enhancements
- [ ] Add conversation history persistence
- [ ] Implement user feedback mechanism 
- [ ] Add loading progress indicators
- [ ] Support image uploads for part identification
- [ ] Add "Copy to Clipboard" for responses
- [ ] Integration with PartSelect shopping cart

