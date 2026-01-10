# 🏛️ Agentic Public Grievance Resolver

> Multi-agent AI system for autonomously processing citizen complaints in Maharashtra, India

**Built with LangChain + LangGraph + Supabase | Free APIs Only**

## 🎯 Overview

The Agentic Public Grievance Resolver is a production-ready system that processes citizen complaints, routes them to appropriate authorities, tracks resolution timelines, escalates delays, and communicates status updates in real-time. Unlike traditional complaint-logging platforms, this system owns the complaint lifecycle end-to-end using agentic AI workflows.

### ✨ Key Features

- 🤖 **Multi-Agent AI System**: 8 specialized AI agents working autonomously
- 🗺️ **Real-Time Heatmap**: Geographic visualization of complaint density and trends
- 💬 **AI Chatbot**: Multilingual conversational assistant (English, Hindi, Marathi) with voice support
- 📊 **Sentiment Analysis**: Detects citizen frustration and prioritizes emotionally charged complaints
- 🔄 **Autonomous Follow-Ups**: Proactively monitors and follows up on stale complaints
- 👥 **Community Forum**: Citizens can discuss similar incidents and upvote to boost priority
- 🌐 **Multilingual Support**: Full website translation in English, Hindi, and Marathi
- 🎤 **Voice Input**: Speech-to-text for all input fields across the frontend
- 📧 **Email Notifications**: Automated status updates and escalation alerts
- 🚨 **Emergency Detection**: Automatic detection and routing of fire, medical, and other emergencies
- ⏱️ **Realistic SLAs**: Context-aware resolution times (minutes for emergencies, days for routine)

## 🏗️ Architecture

The system follows strict **MVC (Model-View-Controller)** architecture:

- **Model Layer (M)**: Supabase database schemas and data access
- **View Layer (V)**: REST API response formatters
- **Controller Layer (C)**: Business logic and agent orchestration
- **Agent Layer**: 8 specialized AI agents
- **Workflow Layer**: LangGraph-based orchestration

## 🤖 AI Agents

The system includes **9 specialized AI agents** working autonomously:

### 1. **Classification Agent** 🎯
- **Purpose**: Unified classification of urgency, category, and department routing
- **Capabilities**:
  - Automatic urgency detection (urgent, high, medium, low)
  - Issue categorization (safety, infrastructure, utilities, etc.)
  - Department routing with Maharashtra-specific logic
  - Emergency keyword detection (fire, medical, gas leaks)
  - City-level department routing (BMC, PMC, NMC)
- **LLM**: Groq/OpenAI with keyword-based safety nets

### 2. **Sentiment Analysis Agent** 😊
- **Purpose**: Analyzes citizen emotional state from complaint text
- **Capabilities**:
  - Sentiment score calculation (-1.0 to 1.0)
  - Emotion level detection (angry, frustrated, neutral, satisfied)
  - Urgency boost based on frustration levels
  - Priority recommendation for emotionally charged complaints
- **Impact**: Automatically boosts urgency for frustrated citizens

### 3. **SLA Assignment Agent** ⏰
- **Purpose**: Assigns realistic resolution deadlines based on context
- **Capabilities**:
  - Context-aware deadline assignment
  - Emergency SLAs (15-30 minutes for fire, medical emergencies)
  - Routine SLAs (2-5 days for medium priority)
  - Department-specific SLA adjustments
- **Output**: Realistic resolution times in hours/minutes

### 4. **Follow-Up Agent** 🔄
- **Purpose**: Proactively monitors and follows up on stale complaints
- **Capabilities**:
  - Identifies complaints not updated in N days
  - Generates follow-up actions (email/API calls)
  - Drafts department follow-up communications
  - Updates citizens on follow-up status
- **Trigger**: Runs automatically or manually via API

### 5. **Chatbot Agent** 💬
- **Purpose**: Conversational AI assistant for citizen queries
- **Capabilities**:
  - Answers questions about complaint status
  - Provides similar case analysis
  - Suggests actions and next steps
  - Multilingual responses (English, Hindi, Marathi)
  - Context-aware (uses complaint ID and email)
  - Voice input/output support
- **Integration**: Available across all frontend pages

### 6. **Escalation Agent** 📈
- **Purpose**: Determines escalation levels for delayed complaints
- **Capabilities**:
  - Time-based escalation (Level 1-4)
  - Severity-based escalation
  - Past escalation history consideration
- **Levels**: Department Head → Commissioner → Chief Secretary → CM Office

### 7. **Citizen Communication Agent** 📧
- **Purpose**: Generates human-friendly status updates
- **Capabilities**:
  - Multilingual message generation
  - Tone adaptation (reassuring, informative, urgent)
  - Status update formatting
  - Email subject line generation

### 8. **Policy Intelligence Agent** 📜
- **Purpose**: Maps complaints to government rules, GRs, and regulations
- **Capabilities**:
  - Maps complaints to relevant Maharashtra government policies/Acts/GRs
  - Determines legal SLA from policy documents
  - Detects policy violations (when department exceeds legal SLA)
  - Suggests lawful actions based on policy
  - Provides policy references for citizen communication
- **Policy Database**:
  - Infrastructure: PWD Circular 2023-14, Municipal Act Section 66
  - Sanitation: Swachh Bharat SLA Norms, Municipal Act Section 58
  - Water: Municipal Act Section 55, Water Supply GR 2020-28
  - Electricity: MERC Regulations, MSEDCL Service Standards
  - Fire: Fire Services Act 2006 (15 minutes mandatory)
  - Health: Public Health Act, Health Department GR
  - Police: Police Act 1951, Police Standing Orders
  - And more...
- **Impact**: Makes AI policy-aware, provides legal backing for escalations

### 9. **Monitoring Agent** 👁️
- **Purpose**: Continuously monitors complaint progress
- **Capabilities**:
  - SLA breach detection
  - Stale complaint identification
  - Automatic escalation triggering
  - Background monitoring cycles

## 🎨 Frontend Features

### Pages

1. **Home** (`/`)
   - Complaint submission form
   - Interactive map for location selection
   - Voice input for name and description
   - Form validation and error handling

2. **Complaint Status** (`/status/:id`)
   - Real-time status tracking
   - Time remaining until SLA deadline
   - Department assignment details
   - Urgency and category display
   - Link to forum discussion
   - Integrated chatbot with complaint context

3. **Admin Dashboard** (`/dashboard`)
   - System-wide metrics
   - Department breakdown
   - SLA breach monitoring
   - Status distribution charts

4. **Heatmap** (`/heatmap`)
   - Geographic visualization using Leaflet
   - Complaint density by area
   - Top issue categories per locality
   - Average resolution times by department
   - Sentiment visualization
   - Filters: state, city, time range

5. **Forum** (`/forum/:complaintId`)
   - Complaint details and discussion
   - Upvote/downvote functionality
   - Similar incidents display
   - Community posts and engagement
   - Priority boost from upvotes

### Components

- **Chatbot**: Floating chat button with voice support
- **VoiceInput**: Reusable speech-to-text component
- **MapPicker**: Interactive Leaflet map for location selection
- **LanguageSelector**: Global language switcher (header)
- **ErrorBoundary**: React error boundary for graceful error handling

### Multilingual Support

- **Languages**: English, Hindi (हिंदी), Marathi (मराठी)
- **Global Context**: Language preference stored in localStorage
- **Translation Coverage**: All UI elements, messages, and chatbot responses
- **Voice Support**: Language-aware speech recognition

## 📡 API Endpoints

### Public Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/api/complaints` | POST | Create a new complaint |
| `/api/complaints/{id}` | GET | Get complaint status |

### Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/dashboard` | GET | Get dashboard metrics |

### Monitoring Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/monitoring/run` | POST | Trigger monitoring cycle |

### Follow-Up Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/followups/run` | POST | Run follow-ups for stale complaints (query param: `days_without_update`) |
| `/api/followups/{complaint_id}` | POST | Run follow-up for specific complaint |

### Chatbot Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chatbot/query` | POST | Handle chatbot query (query params: `question`, `complaint_id`, `citizen_email`, `language`) |

### Heatmap Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/heatmap/data` | GET | Get heatmap data (query params: `state`, `city`, `days`) |

### Sentiment Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sentiment/metrics` | GET | Get sentiment metrics (query params: `days`, `department`, `state`) |

### Forum Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/forum/complaint/{complaint_id}` | GET | Get forum data for a complaint |
| `/api/forum/post` | POST | Create forum post (query params: `complaint_id`, `author_name`, `author_email`, `content`) |
| `/api/forum/vote` | POST | Vote on complaint (query params: `complaint_id`, `voter_email`, `vote_type`) |
| `/api/forum/trending` | GET | Get trending complaints (query param: `limit`) |

### Notification Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notifications/{id}` | POST | Send status update notification |

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- [Supabase Account](https://supabase.com) (Free tier works)
- [Groq API Key](https://console.groq.com) OR [OpenAI API Key](https://platform.openai.com)
- Gmail account (for email notifications, optional)

### 1. Clone and Setup Backend

```bash
cd dev

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to SQL Editor and run these files in order:
   - `supabase_schema.sql` (main schema)
   - `ADD_FOLLOWUP_FIELDS.sql` (follow-up columns)
   - `ADD_SENTIMENT_FIELDS.sql` (sentiment columns)
   - `ADD_FORUM_TABLES.sql` (forum tables)
   - `FIX_RLS.sql` (RLS policies for service role)
3. Get your project URL and keys from Settings > API:
   - Project URL → `SUPABASE_URL`
   - Anon key → `SUPABASE_KEY`
   - Service role key → `SUPABASE_SERVICE_KEY`

### 3. Configure Environment

Create a `.env` file in the `dev/` directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# LLM Configuration
# Option 1: Groq (Free tier available)
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant
LLM_PROVIDER=groq

# Option 2: OpenAI (Paid)
# OPENAI_API_KEY=your-openai-api-key
# OPENAI_MODEL=gpt-4o-mini
# LLM_PROVIDER=openai

# Email Notifications (Optional)
ENABLE_EMAIL_NOTIFICATIONS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# Application Settings
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

**Note:** For Gmail, you need to create an app password. See `GMAIL_SETUP.md` for detailed instructions.

### 4. Setup Frontend

```bash
cd dev/frontend

# Install dependencies
npm install

# Create .env file (optional, defaults to http://localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

### 5. Run the Application

**Backend:**
```bash
cd dev
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

The API will be available at `http://localhost:8000`

**Frontend:**
```bash
cd dev/frontend
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port shown in terminal)

## 📝 Example Usage

### Create a Complaint

```bash
curl -X POST "http://localhost:8000/api/complaints" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Fire in Hinjewadi, Pune. Urgent!",
    "citizen_name": "Rajesh Kumar",
    "citizen_email": "rajesh@example.com",
    "citizen_phone": "9876543210",
    "location": {
      "state": "Maharashtra",
      "city": "Pune",
      "district": "Pune",
      "pincode": "411057",
      "address": "Hinjewadi Phase 1"
    }
  }'
```

### Get Complaint Status

```bash
curl "http://localhost:8000/api/complaints/{complaint_id}"
```

### Query Chatbot

```bash
curl -X POST "http://localhost:8000/api/chatbot/query?question=When will my complaint be resolved?&complaint_id={complaint_id}&language=en"
```

### Get Heatmap Data

```bash
curl "http://localhost:8000/api/heatmap/data?state=Maharashtra&days=30"
```

### Get Trending Complaints

```bash
curl "http://localhost:8000/api/forum/trending?limit=10"
```

## 🇮🇳 Maharashtra-Specific Features

### Departments Supported

- **Fire Department**: Fire emergencies, safety issues
- **Police**: Law enforcement, security
- **Municipal Corporation**: General civic issues
- **BMC (Brihanmumbai Municipal Corporation)**: Mumbai-specific
- **PMC (Pune Municipal Corporation)**: Pune-specific
- **NMC (Nagpur Municipal Corporation)**: Nagpur-specific
- **MSEDCL**: Electricity issues
- **Water Supply Department**: Water-related complaints
- **PWD (Public Works Department)**: Infrastructure, roads
- **Health Department**: Medical emergencies, public health
- **Transport Department**: Public transport issues

### Location Parsing

- Automatic extraction of state, city, district, and PIN code
- City-level department routing (BMC for Mumbai, PMC for Pune, etc.)
- Maharashtra state validation
- Indian phone number format validation
- Asia/Kolkata timezone handling

## 🔒 Security

- **Row Level Security (RLS)**: Supabase RLS policies enforce access control
- **Citizen Privacy**: Citizens can only view their own complaints
- **Admin Access**: Admins have read-only system oversight
- **Service Role**: Backend uses service role key to bypass RLS for operations
- **Audit Trail**: All agent decisions are logged with structured logging
- **Input Validation**: Pydantic schemas validate all inputs

## 📊 Workflow Stages

1. **Complaint Ingestion**: Receive and validate complaint
2. **Classification**: Extract urgency, category, and route to department
3. **Sentiment Analysis**: Analyze citizen emotional state and boost urgency if needed
4. **SLA Assignment**: Set realistic resolution deadline
5. **Persistence**: Save complaint to database
6. **Citizen Notification**: Send initial status update
7. **Status Monitoring**: Continuously check progress
8. **Conditional Escalation**: Escalate if SLA breached
9. **Follow-Up**: Proactively follow up on stale complaints

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Frontend | React 18 + Vite |
| Database | Supabase (PostgreSQL) |
| AI Framework | LangChain + LangGraph |
| LLM Providers | Groq (Llama) / OpenAI (GPT) |
| Maps | Leaflet + React-Leaflet |
| Email | Gmail SMTP |
| Logging | Structlog |
| Validation | Pydantic |
| Routing | React Router |
| Voice | Web Speech API |

## 📁 Project Structure

```
dev/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── supabase_schema.sql         # Main database schema
├── ADD_FOLLOWUP_FIELDS.sql     # Follow-up migration
├── ADD_SENTIMENT_FIELDS.sql    # Sentiment migration
├── ADD_FORUM_TABLES.sql        # Forum migration
├── FIX_RLS.sql                 # RLS policies fix
├── .env.example               # Environment template
├── test_complaint.json         # Test data
│
├── src/
│   ├── config/                 # Configuration
│   │   ├── settings.py        # Application settings
│   │   └── india_data.py       # India-specific data
│   │
│   ├── models/                 # Model layer (data access)
│   │   ├── schemas.py          # Pydantic schemas
│   │   └── database.py         # Supabase client
│   │
│   ├── views/                  # View layer (API responses)
│   │   └── responses.py        # Response formatters
│   │
│   ├── controllers/            # Controller layer
│   │   ├── complaint_controller.py
│   │   ├── monitoring_controller.py
│   │   ├── admin_controller.py
│   │   ├── notification_controller.py
│   │   ├── followup_controller.py
│   │   ├── chatbot_controller.py
│   │   ├── heatmap_controller.py
│   │   ├── sentiment_controller.py
│   │   └── forum_controller.py
│   │
│   ├── agents/                 # Agent layer
│   │   ├── base.py             # Base agent class
│   │   ├── classification.py   # Unified classification
│   │   ├── sentiment.py        # Sentiment analysis
│   │   ├── sla_assignment.py   # SLA assignment
│   │   ├── followup.py         # Follow-up agent
│   │   ├── chatbot_agent.py   # Chatbot agent
│   │   ├── escalation.py       # Escalation agent
│   │   ├── citizen_communication.py
│   │   ├── monitoring.py       # Monitoring agent
│   │   ├── llm_factory.py      # LLM factory
│   │   ├── prompts.py          # All prompt templates
│   │   └── utils.py            # Agent utilities
│   │
│   ├── workflows/              # Workflow layer (LangGraph)
│   │   ├── complaint_workflow.py
│   │   └── monitoring_workflow.py
│   │
│   └── services/               # Services
│       └── notification_service.py
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    │
    └── src/
        ├── main.jsx            # React entry point
        ├── App.jsx             # Main app component
        ├── App.css
        ├── index.css
        │
        ├── pages/              # Page components
        │   ├── Home.jsx
        │   ├── ComplaintStatus.jsx
        │   ├── Dashboard.jsx
        │   ├── Heatmap.jsx
        │   └── Forum.jsx
        │
        ├── components/         # Reusable components
        │   ├── Layout.jsx
        │   ├── ComplaintForm.jsx
        │   ├── Chatbot.jsx
        │   ├── VoiceInput.jsx
        │   ├── MapPicker.jsx
        │   ├── SuccessMessage.jsx
        │   └── ErrorBoundary.jsx
        │
        ├── contexts/           # React contexts
        │   └── LanguageContext.jsx
        │
        ├── hooks/              # Custom hooks
        │   └── useTranslation.js
        │
        └── translations/       # Translation strings
            └── index.js
```

## 🔄 Monitoring & Escalation

The system includes automated monitoring that:

- Checks for SLA breaches every cycle
- Identifies stale complaints (no updates in 3+ days)
- Automatically escalates based on:
  - Time overdue
  - Urgency level
  - Past escalation history
  - Community upvotes (forum)

**Escalation Levels:**
- **Level 1**: Department Head
- **Level 2**: State/City Commissioner
- **Level 3**: Chief Secretary / Minister
- **Level 4**: Chief Minister / Governor Office

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# Create a test complaint
curl -X POST http://localhost:8000/api/complaints \
  -H "Content-Type: application/json" \
  -d @test_complaint.json

# Test chatbot
curl -X POST "http://localhost:8000/api/chatbot/query?question=What is my complaint status?&complaint_id={id}"

# Test heatmap
curl "http://localhost:8000/api/heatmap/data?days=30"
```

## 📈 Success Metrics

- Time to complaint resolution
- SLA adherence rate
- Escalation frequency
- Citizen satisfaction score (sentiment analysis)
- Community engagement (forum upvotes)
- Average resolution time by department

## 🚨 Troubleshooting

### Supabase Connection Issues

**Error**: `[Errno 8] nodename nor servname provided, or not known`

**Solutions:**
- Verify `SUPABASE_URL` is correct (should start with `https://`)
- Check Supabase project status
- Ensure RLS policies are set correctly (run `FIX_RLS.sql`)
- Verify `SUPABASE_SERVICE_KEY` is set for backend operations

### LLM Provider Issues

**Groq Model Not Found:**
- Check `GROQ_MODEL` in `.env` (default: `llama-3.1-8b-instant`)
- Verify Groq API key is valid
- Check [Groq Console](https://console.groq.com) for available models

**OpenAI Issues:**
- Verify `OPENAI_API_KEY` is set
- Check API key has sufficient credits
- Ensure `LLM_PROVIDER=openai` in `.env`

### Frontend Issues

**White Page:**
- Check browser console for errors
- Verify `VITE_API_URL` in frontend `.env`
- Ensure backend is running on correct port
- Check CORS settings in `main.py`

**Voice Input Not Working:**
- Ensure HTTPS or localhost (Web Speech API requirement)
- Check browser permissions for microphone
- Verify browser supports Web Speech API (Chrome, Edge)

### Import Errors

```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

## 📚 Additional Documentation

- **QUICKSTART.md**: Quick setup guide
- **SETUP.md**: Detailed setup instructions
- **GMAIL_SETUP.md**: Gmail SMTP configuration
- **TROUBLESHOOTING.md**: Common issues and solutions
- **DEPLOYMENT.md**: Production deployment guide
- **PROJECT_CHECKLIST.md**: Feature checklist
- **SUBMISSION_GUIDE.md**: Submission form guide

## 🎯 Key Innovations

1. **Agentic Architecture**: All decisions made by LLM prompts, no hardcoded logic
2. **Policy-Aware Resolution**: Maps complaints to government rules/GRs for legal compliance
3. **Emergency Detection**: Automatic keyword-based routing for fire, medical emergencies
4. **Realistic SLAs**: Context-aware resolution times (minutes for emergencies)
5. **Sentiment-Driven Priority**: Emotion detection boosts urgency for frustrated citizens
6. **Proactive Follow-Ups**: Autonomous agent monitors and follows up on stale complaints
7. **Community Engagement**: Forum with voting system to boost complaint priority
8. **Multilingual AI**: Chatbot and entire system support English, Hindi, Marathi
9. **Voice Integration**: Speech-to-text and text-to-speech across frontend
10. **Legal Compliance**: Policy Intelligence Agent ensures government-AI alignment

## 📄 License

MIT License - feel free to use and modify!

## 🤝 Contributing

This is a hackathon-demo ready system that can be extended for production use. Key areas for extension:

- SMS notification integration
- WhatsApp integration
- Government API integrations
- Advanced analytics and reporting
- Mobile app (React Native)
- Real-time WebSocket updates
- Machine learning for prediction

---

**Built for Maharashtra, India 🇮🇳 | Powered by AI 🤖**
