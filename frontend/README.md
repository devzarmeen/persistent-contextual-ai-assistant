Bilkul. Since aap project ko **GitHub par final/polished state** mein push karne wali hain, README ko “implemented/completed” perspective se present karna best rahega.

### Recommended Repository Name

**`persistent-contextual-ai-assistant`**

### Recommended GitHub Description

> **A production-style AI assistant with persistent memory, RAG, tool calling, Google integrations, conflict detection, verification workflows, and context-aware conversations.**

---

# `README.md`

````md
# ContextAI — Persistent Contextual AI Assistant

> A production-style AI assistant that remembers context, retrieves relevant information, uses connected tools, detects conflicting memories, and verifies sensitive actions before execution.

ContextAI is an intelligent personal AI assistant designed to go beyond ordinary chatbot behavior.

Instead of treating every conversation as isolated, ContextAI builds a persistent context layer around the user. It can remember important facts and preferences, search previous memories and documents, interact with external services, reason over retrieved information, and safely handle actions that require user approval.

The system combines **persistent memory, RAG, agentic tool calling, Google integrations, conflict detection, and action verification** into a single full-stack application.

---

## ✨ Highlights

- 🧠 Persistent long-term memory
- 🔎 Semantic memory search
- 📚 Document upload and RAG search
- 🤖 Agent-based tool selection
- 📧 Gmail integration
- 📅 Google Calendar integration
- 🔐 Google OAuth authentication
- ⚔️ Memory conflict detection and resolution
- 🛡️ Verification workflow for sensitive actions
- 💬 Context-aware conversations
- 🧩 14 integrated agent tools
- 📊 Memory intelligence and confidence scoring
- 🗂️ Memory explorer with edit/delete capabilities
- 📄 Document management with upload/search/delete
- 🌙 Light and dark theme support
- 🔒 Protected authenticated API routes
- 🐳 Docker-ready architecture
- 🗄️ PostgreSQL + pgvector
- ⚡ FastAPI backend
- ⚛️ Next.js frontend
- 📱 Responsive dashboard UI

---

# 🎯 Problem

Traditional AI chatbots often suffer from three major limitations:

### 1. No persistent context

A normal chatbot may understand the current conversation but does not reliably maintain useful information across sessions.

### 2. Limited real-world interaction

A chatbot can generate text, but it may not be able to safely interact with email, calendars, documents, or other services.

### 3. Unsafe autonomous actions

Allowing an AI system to send an email or modify a calendar without verification can lead to unintended actions.

ContextAI addresses these limitations through a persistent memory architecture combined with agentic tools and verification.

---

# 💡 Solution

ContextAI follows an agent-style workflow:

```text
User
  ↓
Intent Understanding
  ↓
Memory Retrieval
  ↓
Document Retrieval
  ↓
Context Assembly
  ↓
Agent Reasoning
  ↓
Tool Selection
  ↓
Tool Execution
  ↓
Verification (when required)
  ↓
Result Verification
  ↓
Memory Update
  ↓
Context-Aware Response
````

The assistant can therefore reason using information that already exists in the user's personal context instead of treating every request as a completely new interaction.

---

# 🏗️ System Architecture

```text
┌──────────────────────────────────────────────┐
│                  Next.js UI                  │
│                                              │
│ Chat │ Memory │ Documents │ Email │ Calendar│
│ Verification │ Settings │ Dashboard         │
└──────────────────────┬───────────────────────┘
                       │
                       │ REST API
                       ▼
┌──────────────────────────────────────────────┐
│                FastAPI Backend               │
│                                              │
│ Auth │ Chat │ Memory │ RAG │ Integrations   │
│ Agent │ Verification │ Memory Intelligence  │
└──────────────┬───────────────┬───────────────┘
               │               │
               ▼               ▼
      ┌────────────────┐  ┌─────────────────┐
      │ PostgreSQL     │  │ Gemini AI       │
      │ + pgvector     │  │                 │
      │                │  │ Reasoning       │
      │ Users          │  │ Embeddings      │
      │ Memories       │  │ Structured      │
      │ Documents      │  │ Decisions       │
      │ Conversations  │  └─────────────────┘
      │ Verification   │
      └────────────────┘
               │
               ▼
      ┌──────────────────────┐
      │ Google Integrations  │
      │                      │
      │ Gmail                │
      │ Google Calendar      │
      │ Google Drive         │
      └──────────────────────┘
```

---

# 🧠 Persistent Memory

Memory is one of the core components of ContextAI.

The system supports multiple memory types:

```text
FACT
PREFERENCE
DECISION
TASK
DEADLINE
PERSON
PROJECT
CONVERSATION
```

Each memory can contain contextual metadata such as:

* Memory type
* Content
* Importance
* Confidence
* Source type
* Source ID
* Confirmation count
* Active/inactive state
* Embedding vector
* Creation timestamp
* Update timestamp

---

# 🔍 Semantic Memory Search

ContextAI does not rely only on exact keyword matching.

Memory embeddings are generated and stored using PostgreSQL vector storage.

The system can therefore retrieve semantically related memories even when the user's wording is different from the original memory.

Example:

```text
Stored memory:

"Zarmeen is building a Persistent Contextual AI Assistant
for an AI Builders Hackathon."

User:

"What project am I preparing for the hackathon?"
```

The system can retrieve the relevant memory based on semantic similarity.

---

# ⚔️ Memory Conflict Detection

Persistent memory introduces an important problem:

> What happens when the user provides information that conflicts with something remembered earlier?

ContextAI includes memory intelligence to detect and manage conflicting memories.

Example:

```text
Existing Memory
    ↓
"Project deadline is September 10"

New Information
    ↓
"Project deadline is September 15"

        ↓

Conflict Detection
        ↓
┌─────────────────────┐
│ Old Memory          │
│ New Memory          │
│ Confidence          │
│ Source Reliability  │
│ Winning Memory      │
│ Resolution          │
└─────────────────────┘
```

The system evaluates factors including:

* Source reliability
* Confidence
* Importance
* Recency
* Confirmation history

This allows the system to select a winning memory while retaining the conflict history.

---

# 📊 Source Reliability

Memory intelligence assigns different reliability levels to different sources.

```text
Verified Action     → 1.00
Explicit User       → 0.98
Conversation         → 0.90
Document             → 0.88
Calendar             → 0.86
Email                → 0.82
Agent                → 0.70
Inferred             → 0.55
```

This helps ContextAI make more informed decisions when multiple memories disagree.

---

# 📚 Document Intelligence & RAG

ContextAI includes document management and retrieval.

Users can:

* Upload documents
* View stored documents
* Search documents semantically
* Retrieve document content
* Delete documents

The document pipeline provides contextual information to the agent before it makes a response or decision.

```text
Document
   ↓
Upload
   ↓
Processing
   ↓
Embedding
   ↓
Vector Storage
   ↓
Semantic Search
   ↓
Relevant Context
   ↓
Agent
```

---

# 🤖 Agentic Architecture

ContextAI uses an agent-style decision architecture.

Instead of hardcoding every conversation flow, the agent can determine whether it needs:

* A direct response
* Memory retrieval
* Document retrieval
* User context
* Email information
* Calendar information
* A write operation
* A verification workflow

The agent produces structured decisions that are converted into tool executions.

---

# 🛠️ Integrated Agent Tools

ContextAI currently provides **14 agent tools**:

| Tool                    | Purpose                           |
| ----------------------- | --------------------------------- |
| `search_memory`         | Search persistent memories        |
| `search_documents`      | Search uploaded documents         |
| `get_document`          | Retrieve document details/content |
| `get_user_context`      | Retrieve relevant user context    |
| `save_memory`           | Store a new memory                |
| `search_emails`         | Search Gmail messages             |
| `get_email`             | Retrieve a specific email         |
| `draft_email`           | Create an email draft             |
| `send_email`            | Send an email                     |
| `get_calendar_events`   | Retrieve calendar events          |
| `find_free_slot`        | Find available calendar time      |
| `create_calendar_event` | Create a calendar event           |
| `update_calendar_event` | Update an existing event          |
| `delete_calendar_event` | Delete a calendar event           |

---

# 🔐 Verification & Safe Actions

Not every action should be executed immediately.

ContextAI introduces a verification layer for sensitive operations.

The following actions require approval:

```text
send_email
create_calendar_event
update_calendar_event
delete_calendar_event
```

The workflow is:

```text
Agent Decision
     ↓
Sensitive Tool?
     ↓
   YES
     ↓
Create Verification Action
     ↓
AWAITING / PENDING APPROVAL
     ↓
User Approval
     ↓
Execute
     ↓
Verify Result
     ↓
Return Result
```

This provides a safety boundary between AI reasoning and external side effects.

---

# 📧 Gmail Integration

Google OAuth enables ContextAI to work with Gmail.

Supported capabilities include:

* Search emails
* Retrieve emails
* Draft emails
* Send emails

Example:

```text
User:
"Find the email about the internship application."

        ↓

Agent
        ↓

search_emails
        ↓

Relevant Gmail message
        ↓

ContextAI
        ↓

Context-aware response
```

Sending an email requires verification before execution.

---

# 📅 Google Calendar Integration

ContextAI can interact with Google Calendar.

Supported operations include:

* Retrieve events
* Find free slots
* Create events
* Update events
* Delete events

Calendar write operations are protected by the verification layer.

---

# 🔑 Google OAuth

The application uses Google OAuth for connected Google services.

The OAuth flow allows users to securely connect their Google account and authorize the required integrations.

The architecture supports persistent connection information so that users do not need to authenticate for every individual operation.

---

# 💬 Context-Aware Chat

The chat system supports persistent conversations.

Each conversation contains:

```text
Conversation
    ├── User Message
    ├── Assistant Message
    ├── Agent Decision
    ├── Tool Activity
    └── Context
```

The frontend also displays agent activity so users can understand when ContextAI used:

* Memory
* Documents
* Email
* Calendar
* Other tools

This improves transparency and makes the assistant's actions easier to understand.

---

# 🧭 Dashboard

The application provides a unified dashboard with dedicated areas for:

```text
Dashboard
│
├── Chat
├── Memory
├── Documents
├── Email
├── Calendar
├── Verification
└── Settings
```

---

# 🧠 Memory Dashboard

The Memory interface provides:

* Memory statistics
* Memory search
* Stored memories
* Confidence information
* Importance information
* Source information
* Conflict information
* Memory deletion

Users can inspect and manage what ContextAI remembers.

---

# 📄 Document Dashboard

The Documents interface provides:

* Document upload
* Document listing
* Document search
* Document metadata
* Document deletion
* Search result visualization

This gives users control over the knowledge available to the assistant.

---

# 🛡️ Verification Dashboard

The verification interface provides visibility into sensitive AI actions.

Users can inspect:

* Action ID
* Tool name
* Action status
* Requested action
* Approval state
* Execution result

This creates an auditable boundary between agent reasoning and external side effects.

---

# 🎨 Frontend

The frontend is built with:

* Next.js
* React
* TypeScript
* Tailwind CSS
* Lucide React

The UI includes:

* Responsive dashboard
* Sidebar navigation
* Authentication pages
* Chat workspace
* Agent activity indicators
* Memory management
* Document management
* Verification management
* Calendar interface
* Email interface
* Settings
* Light/dark theme

---

# ⚙️ Backend

The backend is built using:

* Python
* FastAPI
* SQLModel
* PostgreSQL
* pgvector
* Google APIs
* Gemini
* OAuth

The backend is organized into modular components:

```text
backend/
│
├── app/
│   ├── agents/
│   ├── api/
│   │   └── routes/
│   ├── integrations/
│   ├── memory/
│   ├── models/
│   ├── rag/
│   ├── schemas/
│   ├── services/
│   └── verification/
│
├── data/
├── docs/
├── tests/
└── pyproject.toml
```

---

# 🔌 API Modules

The FastAPI backend exposes modular API routes for:

```text
/api/auth
/api/chat
/api/memories
/api/documents
/api/integrations/google
/api/memory-intelligence
/api/verification
```

Interactive API documentation is available through FastAPI's Swagger interface.

---

# 🔒 Authentication

ContextAI includes authenticated user sessions.

Authentication supports:

* User registration
* User login
* Current-user retrieval
* Access-token based API authorization
* Protected application routes

The frontend automatically attaches the access token to authenticated API requests.

---

# 🗄️ Database

The application uses:

```text
PostgreSQL
     +
pgvector
```

Vector storage enables semantic retrieval for:

* Memories
* Documents
* Contextual information

The relational database stores application state such as:

* Users
* Conversations
* Messages
* Memories
* Memory conflicts
* Documents
* Verification actions
* Google connections

---

# 🧩 Project Structure

```text
persistent-contextual-ai-assistant/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── integrations/
│   │   ├── memory/
│   │   ├── models/
│   │   ├── rag/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── verification/
│   │
│   ├── data/
│   ├── docs/
│   ├── tests/
│   ├── pyproject.toml
│   └── ...
│
├── frontend/
│   ├── app/
│   │   ├── dashboard/
│   │   │   ├── calendar/
│   │   │   ├── chat/
│   │   │   ├── documents/
│   │   │   ├── email/
│   │   │   ├── memory/
│   │   │   ├── settings/
│   │   │   └── verification/
│   │   ├── login/
│   │   └── register/
│   │
│   ├── components/
│   ├── lib/
│   ├── public/
│   └── ...
│
└── README.md
```

---

# 🚀 Getting Started

## Prerequisites

Make sure the following are installed:

* Python 3.14+
* Poetry
* Node.js
* npm
* PostgreSQL
* pgvector
* Google Cloud project
* Gemini API access

---

# ⚙️ Backend Setup

Navigate to the backend:

```bash
cd backend
```

Install dependencies:

```bash
poetry install
```

Create your environment configuration:

```env
DATABASE_URL=your_postgresql_connection_string

GEMINI_API_KEY=your_gemini_api_key

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost/8000
```

Run the FastAPI server:

```bash
poetry run uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 💻 Frontend Setup

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create:

```text
.env.local
```

with:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# 🏭 Production Build

To verify the frontend production build:

```bash
npm run build
```

Start the production frontend:

```bash
npm start
```

---

# 🧪 Validation

The project has been validated across the main application layers.

### Backend

```bash
poetry run python -m compileall app
```

### Frontend

```bash
npm run build
```

The frontend build includes the main application routes:

```text
/
├── login
├── register
└── dashboard
    ├── calendar
    ├── chat
    ├── chat/new
    ├── documents
    ├── email
    ├── memory
    ├── settings
    └── verification
```

---

# 🧠 Agent Execution Model

The agent follows a structured execution pattern.

```text
1. Receive user request
        ↓
2. Understand intent
        ↓
3. Retrieve relevant memory
        ↓
4. Retrieve relevant documents
        ↓
5. Build context
        ↓
6. Select appropriate tool
        ↓
7. Determine whether verification is required
        ↓
8. Execute or request approval
        ↓
9. Verify result
        ↓
10. Update memory when appropriate
        ↓
11. Generate final response
```

---

# 🛡️ Safety Philosophy

ContextAI follows a simple principle:

> **Reason freely, but execute sensitive external actions carefully.**

Read-only operations can be executed directly when appropriate.

External side-effect operations are protected with approval workflows.

This architecture helps prevent accidental:

* Emails
* Calendar changes
* Event deletions
* Other external side effects

---

# 🔎 Transparency

ContextAI exposes agent activity to the user.

For example:

```text
ContextAI used:

✓ Get User Context
✓ Search Memory
✓ Search Documents
```

For sensitive operations:

```text
Verification Required

Action ID: 123
Tool: send_email
Status: PENDING
```

This gives users visibility into what the AI is doing instead of hiding all agent activity behind a simple chatbot response.

---

# 📈 Memory Intelligence

The memory system goes beyond simple storage.

It considers:

```text
Memory
 ├── Importance
 ├── Confidence
 ├── Source Reliability
 ├── Confirmation Count
 ├── Recency
 └── Conflict State
```

This enables ContextAI to maintain a more reliable long-term context.

---

# 🔮 Future Improvements

The architecture is designed to support future extensions such as:

* Slack integration
* More productivity tools
* Advanced autonomous workflows
* Improved memory consolidation
* More sophisticated conflict resolution
* Additional document formats
* Expanded evaluation datasets
* Production-grade observability
* Background task processing
* More granular permission controls

---

# 🏆 Project Focus

ContextAI is designed as a complete AI application rather than a simple chatbot demo.

The project demonstrates the combination of:

```text
Persistent Memory
        +
RAG
        +
Agentic Reasoning
        +
Tool Calling
        +
External APIs
        +
Conflict Detection
        +
Verification
        +
Full-Stack SaaS Architecture
```

The central idea is:

> **An AI assistant should not only answer questions — it should understand the user's ongoing context, remember what matters, use the right tools, and safely act on the user's behalf.**


---

# 👩‍💻 Author

**Zarmeen Rasool**
AI Engineer

GitHub:
[https://github.com/devzarmeen](https://github.com/devzarmeen)

LinkedIn:
[https://www.linkedin.com/in/zarmeenrasool/](https://www.linkedin.com/in/zarmeenrasool/)

Email:
[devzarmeenrasool@gmail.com](mailto:devzarmeenrasool@gmail.com)

---

# ⭐ Project Vision

ContextAI aims to move personal AI assistants from:

```text
Stateless Chatbots
        ↓
Context-Aware Assistants
        ↓
Persistent Personal AI
        ↓
Safe Agentic AI
```

The long-term vision is an assistant that can remember the right information, retrieve it at the right time, reason over multiple sources, interact with real-world tools, and keep the user in control of important actions.

---


