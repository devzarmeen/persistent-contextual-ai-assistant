# 🧠 Persistent Contextual AI Assistant

<p align="center">
  <img src="https://img.shields.io/badge/AI-Powered-6C63FF?style=for-the-badge&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-Frontend-000000?style=for-the-badge&logo=next.js&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/pgvector-RAG-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini-LLM-4285F4?style=for-the-badge&logo=google&logoColor=white" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Gmail-Integration-EA4335?style=for-the-badge&logo=gmail&logoColor=white" />
  <img src="https://img.shields.io/badge/Google%20Calendar-Integration-4285F4?style=for-the-badge&logo=googlecalendar&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-React-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
</p>

<p align="center">
  <b>🧠 Memory • 🔎 RAG • 🤖 Agent • 🛠️ Tools • 🔐 Verification • 📧 Gmail • 📅 Calendar</b>
</p>

<p align="center">
  A persistent AI assistant that remembers context, understands documents,
  uses external tools, and verifies real-world actions before execution.
</p>

---

## 🌟 Overview

**Persistent Contextual AI Assistant** is a full-stack AI assistant designed to go beyond traditional chatbots.

Traditional AI assistants often treat every conversation as an isolated interaction. This project introduces a persistent contextual architecture where the assistant can:

- 🧠 Remember important information
- 🔎 Retrieve relevant memories
- 📚 Understand uploaded documents
- 🤖 Decide which tools to use
- 🛠️ Execute structured tool calls
- 📧 Search and send emails
- 📅 Manage calendar events and reminders
- 🔐 Authenticate through Google OAuth
- ✅ Verify external actions
- ⚔️ Detect conflicting memories
- 💬 Maintain persistent conversations
- 🔔 Notify users about pending and completed actions

The core idea is:

> **An AI assistant should not only answer questions. It should remember, retrieve, reason, act, verify, and maintain context over time.**

---

# 🎯 Project Vision

The project is designed as a **persistent contextual AI system** rather than a simple chatbot.

### Traditional Chatbot

```text
User
  ↓
Message
  ↓
AI
  ↓
Response
````

### Persistent Contextual AI Assistant

```text
User
  ↓
Intent Detection
  ↓
Context Retrieval
  ├── 🧠 Memory
  ├── 📚 Documents / RAG
  └── 💬 Conversation History
  ↓
Agent Planning
  ↓
Tool Selection
  ↓
Tool Execution
  ↓
Verification
  ↓
Memory Update
  ↓
Final Response
```

---

# ✨ Key Features

## 🧠 Persistent Long-Term Memory

The assistant can remember useful information across conversations.

Supported memory categories include:

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

### Example

```text
User:
I prefer concise technical explanations.

Assistant:
Preference saved to memory.
```

Later:

```text
User:
Explain RAG.

Assistant:
The assistant retrieves the stored preference
and provides a concise explanation.
```

---

# 🔎 Semantic Memory Search

The assistant uses embeddings and vector similarity search to retrieve relevant memories.

Instead of depending only on exact keywords, semantic search allows related concepts to be retrieved.

```text
User Query
    ↓
Generate Embedding
    ↓
pgvector Similarity Search
    ↓
Relevant Memories
    ↓
Context Injection
    ↓
AI Response
```

---

# ⚔️ Memory Conflict Detection

The system can detect when new information conflicts with existing memory.

Example:

```text
Existing Memory:
Project deadline = September 20

New Memory:
Project deadline = September 25
```

Instead of silently deleting information, the system can track the conflict.

The memory conflict system can maintain:

* Old memory
* New memory
* Winning memory
* Confidence
* Source reliability
* Resolution
* Memory status

This makes long-term memory more controlled and explainable.

---

# 📚 Document Intelligence

Users can upload documents and ask questions about them directly.

Supported document formats include:

* 📄 PDF
* 📝 TXT
* 📝 Markdown
* 📊 CSV
* 🔧 JSON

### Document Processing Pipeline

```text
Upload Document
      ↓
Text Extraction
      ↓
Text Cleaning
      ↓
Chunking
      ↓
Embedding Generation
      ↓
PostgreSQL + pgvector
      ↓
Semantic Search
      ↓
Relevant Chunks
      ↓
AI Analysis
```

---

# 📄 Document RAG

The assistant uses Retrieval-Augmented Generation for document-based questions.

```text
Document
   ↓
Chunks
   ↓
Embeddings
   ↓
Vector Database
   ↓
Similarity Search
   ↓
Relevant Chunks
   ↓
Context
   ↓
AI
   ↓
Answer
```

Current document processing configuration:

```text
Chunk Size:          1200
Chunk Overlap:       200
Embedding Dimension: 1536
```

---

# 📎 Attached Document Chat

Documents can also be uploaded directly from the chat interface.

Example:

```text
User:
[Uploads project_requirements.pdf]

User:
Analyze this document and summarize the important requirements.
```

The chat request can include the uploaded document reference.

```text
Chat Message
     +
Document ID
     ↓
Backend
     ↓
Agent
     ↓
get_document
     ↓
Document Content
     ↓
Analysis
     ↓
Response
```

This allows users to ask multiple questions about the same uploaded document.

---

# 🤖 Agent Architecture

The assistant follows an agent-style workflow.

Instead of always generating a direct response, the agent first determines what action is required.

Example:

```text
User:
Find my emails about the AI hackathon.
```

The agent determines:

```text
Intent:
Search Gmail

Tool:
search_emails
```

Then:

```text
search_emails
      ↓
Gmail API
      ↓
Relevant Emails
      ↓
Context
      ↓
AI Response
```

---

# 🛠️ Tool Calling

The assistant uses structured tools for different types of operations.

## 🧠 Memory Tools

```text
search_memory
save_memory
get_user_context
```

## 📚 Document Tools

```text
search_documents
get_document
```

## 📧 Gmail Tools

```text
search_emails
get_email
draft_email
send_email
```

## 📅 Calendar Tools

```text
get_calendar_events
find_free_slot
create_calendar_event
update_calendar_event
delete_calendar_event
```

This modular tool architecture makes it possible to add additional integrations later.

---

# 📧 Gmail Integration

The application integrates with Gmail through Google OAuth.

Supported operations include:

* 🔎 Search emails
* 📩 Read email details
* ✍️ Draft emails
* 📤 Send emails

### Example

```text
User:
Find the email about my internship report.
```

The assistant can:

```text
User Request
     ↓
Agent
     ↓
search_emails
     ↓
Gmail API
     ↓
Email Results
     ↓
AI Response
```

---

# 📤 Email Sending

The application provides an Email dashboard where users can compose and send emails.

Example:

```text
Recipient:
example@email.com

Subject:
Project Update

Message:
The project report has been completed.
```

For external actions, the system uses a verification flow.

```text
Compose Email
      ↓
Create Verification Action
      ↓
PENDING
      ↓
User Approval
      ↓
EXECUTING
      ↓
Gmail API
      ↓
VERIFIED
```

---

# 📅 Google Calendar Integration

The assistant can work with Google Calendar.

Supported operations include:

* 📆 View calendar events
* 🔎 Find available time slots
* ➕ Create events
* ✏️ Update events
* 🗑️ Delete events
* ⏰ Create reminders

---

# ⏰ Calendar Reminder UI

The dashboard provides a calendar interface where users can create reminders/events.

Example:

```text
Title:
Project Meeting

Date:
September 20, 2026

Time:
10:00 AM

Description:
Discuss project progress
```

The action follows:

```text
Calendar Form
      ↓
Create Verification Action
      ↓
PENDING
      ↓
Approve
      ↓
Google Calendar
      ↓
Verify
      ↓
Completed
```

---

# 🔐 Verification-First Architecture

One of the core principles of the project is:

> **The assistant should not blindly execute external actions.**

Actions that affect external systems are routed through a verification workflow.

### Verification States

```text
PENDING
EXECUTING
VERIFIED
FAILED
REJECTED
```

### Example

```text
User
 ↓
"Send this email"
 ↓
Agent
 ↓
Create Verification Action
 ↓
PENDING
 ↓
User Approval
 ↓
EXECUTING
 ↓
Gmail
 ↓
VERIFIED
 ↓
Notification
```

This gives the user control over external actions.

---

# 🔔 Notification System

The dashboard includes a notification interface for important assistant actions.

Notifications can represent:

* 📧 Email actions
* 📅 Calendar actions
* ⏳ Pending approvals
* ✅ Completed actions
* ❌ Failed actions
* ⚠️ Verification events

The notification interface provides visibility into assistant activity.

---

# 💬 Persistent Conversations

The application maintains conversation history.

Users can:

* 💬 Start a new chat
* 🔎 Search conversations
* 📂 Open previous conversations
* 🔄 Continue previous conversations
* 📎 Upload documents
* 🧠 Use previous context

Conversation history works together with long-term memory to provide better contextual responses.

---

# 🔎 Conversation Search

The chat dashboard provides conversation search.

Users can search their conversations using keywords such as:

```text
AI
Python
Hackathon
Project
Internship
Calendar
Email
RAG
Memory
```

This makes previous discussions easier to locate.

---

# 🖥️ Dashboard

The application provides a centralized dashboard.

```text
Dashboard
│
├── 💬 Chat
│
├── 🧠 Memory
│
├── 📚 Documents
│
├── 📅 Calendar
│
├── 📧 Email
│
└── 🔔 Notifications
```

---

# 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                         USER                                │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      NEXT.JS FRONTEND                       │
│                                                             │
│  💬 Chat   🧠 Memory   📚 Documents   📅 Calendar   📧 Email│
│                                                             │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ REST API
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                       │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    AGENT LAYER                        │  │
│  │                                                       │  │
│  │ Intent → Context → Planning → Tools → Verification  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐ │
│  │    Memory    │   │     RAG      │   │ Verification   │ │
│  │   Service    │   │   Service    │   │    Engine      │ │
│  └──────────────┘   └──────────────┘   └────────────────┘ │
│                                                             │
│  ┌────────────────┐   ┌─────────────────────────────────┐ │
│  │ Gmail Service  │   │       Calendar Service          │ │
│  └────────────────┘   └─────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Document Processing                      │  │
│  │          PDF / TXT / MD / CSV / JSON                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  POSTGRESQL + PGVECTOR                     │
│                                                             │
│ Users │ Conversations │ Messages │ Memories │ Documents     │
│ Chunks │ Conflicts │ Integrations │ Verification Actions  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 🧩 Technology Stack

| Layer               | Technology                  |
| ------------------- | --------------------------- |
| 🎨 Frontend         | Next.js                     |
| ⚛️ UI               | React                       |
| 🔷 Language         | TypeScript                  |
| ⚡ Backend           | FastAPI                     |
| 🐍 Backend Language | Python 3.14                 |
| 📦 Package Manager  | Poetry                      |
| 🤖 AI Model         | Gemini                      |
| 🧠 Embeddings       | Gemini Embeddings           |
| 🗃️ Database        | PostgreSQL                  |
| 🔎 Vector Search    | pgvector                    |
| 🧬 ORM              | SQLModel                    |
| 🔐 Authentication   | Google OAuth                |
| 📧 Email            | Gmail API                   |
| 📅 Calendar         | Google Calendar API         |
| 📄 Documents        | PDF / TXT / MD / CSV / JSON |
| 🐳 Deployment       | Docker                      |

---

# 📁 Project Structure

```text
persistent-contextual-ai-assistant/
│
├── backend/
│   │
│   ├── app/
│   │   │
│   │   ├── agents/
│   │   │   ├── agent.py
│   │   │   ├── decision.py
│   │   │   ├── models.py
│   │   │   ├── runner.py
│   │   │   └── tools.py
│   │   │
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── auth.py
│   │   │       ├── chat.py
│   │   │       ├── documents.py
│   │   │       ├── google.py
│   │   │       ├── verification.py
│   │   │       └── ...
│   │   │
│   │   ├── integrations/
│   │   │   ├── gmail.py
│   │   │   ├── calendar.py
│   │   │   └── google.py
│   │   │
│   │   ├── memory/
│   │   │
│   │   ├── models/
│   │   │
│   │   ├── rag/
│   │   │
│   │   ├── schemas/
│   │   │
│   │   ├── services/
│   │   │
│   │   └── verification/
│   │
│   ├── tests/
│   ├── migrations/
│   ├── pyproject.toml
│   └── .env
│
├── frontend/
│   │
│   ├── app/
│   │   ├── dashboard/
│   │   │   ├── chat/
│   │   │   ├── memory/
│   │   │   ├── documents/
│   │   │   ├── calendar/
│   │   │   └── email/
│   │   │
│   │   └── ...
│   │
│   ├── components/
│   │   ├── chat/
│   │   ├── layout/
│   │   ├── memory/
│   │   └── ...
│   │
│   ├── lib/
│   │   └── api.ts
│   │
│   ├── package.json
│   └── .env.local
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

# ⚙️ Installation & Setup

## 1️⃣ Clone the Repository

```powershell
git clone https://github.com/devzarmeen/persistent-contextual-ai-assistant.git
cd persistent-contextual-ai-assistant
```

---

# 🐍 Backend Setup

Move into the backend directory:

```powershell
cd backend
```

Install dependencies:

```powershell
poetry install
```

Run the backend environment:

```powershell
poetry run uvicorn app.main:app --reload
```

Backend will be available at:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# ⚛️ Frontend Setup

Open another terminal.

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Run the development server:

```powershell
npm run dev
```

Frontend will be available at:

```text
http://localhost:3000
```

---

# 🔑 Environment Variables

## Backend

Create:

```text
backend/.env
```

Example:

```env
APP_NAME=Persistent Contextual AI Assistant

DATABASE_URL=postgresql://postgres:password@localhost:5432/context_ai

GEMINI_API_KEY=your_gemini_api_key

GEMINI_CHAT_MODEL=your_gemini_chat_model

GEMINI_EMBEDDING_MODEL=your_gemini_embedding_model

GOOGLE_CLIENT_ID=your_google_client_id

GOOGLE_CLIENT_SECRET=your_google_client_secret

GOOGLE_REDIRECT_URI=http://localhost:8000/api/integrations/google/callback
```

---

## Frontend

Create:

```text
frontend/.env.local
```

Example:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

> ⚠️ Never commit API keys, OAuth secrets, database passwords, or `.env` files to GitHub.

---

# 🗃️ PostgreSQL + pgvector

The application uses PostgreSQL with the `pgvector` extension.

Create the database:

```sql
CREATE DATABASE context_ai;
```

Enable vector support:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The current vector configuration uses:

```text
Embedding Dimension: 1536
```

---

# 🔐 Google OAuth Configuration

The application uses Google OAuth for Gmail and Google Calendar access.

Required Google services include:

```text
Google OAuth
Gmail API
Google Calendar API
```

Configure the OAuth redirect URI:

```text
http://localhost:8000/api/integrations/google/callback
```

The OAuth flow allows the application to securely connect supported Google services to the authenticated user account.

---

# 🔄 Complete AI Request Flow

```text
                    USER
                      │
                      ▼
               User Message
                      │
                      ▼
              Authentication
                      │
                      ▼
            Conversation Context
                      │
                      ▼
              Context Retrieval
                 /          \
                /            \
               ▼              ▼
          🧠 Memory        📚 RAG
               \              /
                \            /
                 ▼          ▼
                 Agent Planning
                      │
                      ▼
                 Tool Selection
                      │
                      ▼
                 Tool Execution
                      │
                      ▼
                 Verification
                      │
              ┌───────┴────────┐
              ▼                ▼
          External          Response
           Action
              │
              ▼
          Verify Result
              │
              ▼
         Update Memory
              │
              ▼
          Final Answer
```

---

# 🧠 Memory Architecture

The memory system considers several factors before storing or retrieving information.

```text
User Information
      ↓
Memory Extraction
      ↓
Memory Type
      ↓
Confidence
      ↓
Importance
      ↓
Source Reliability
      ↓
Duplicate Check
      ↓
Conflict Detection
      ↓
Save / Update / Reject
```

Memory source reliability can be considered from sources such as:

```text
Verified Action
Explicit User Information
Conversation
Document
Calendar
Email
Agent
Inferred Information
```

This helps prevent low-quality information from dominating long-term context.

---

# 📚 Document Architecture

```text
                    DOCUMENT
                        │
                        ▼
                 Text Extraction
                        │
                        ▼
                     Chunking
                        │
                        ▼
                   Embeddings
                        │
                        ▼
                 PostgreSQL
                  + pgvector
                        │
                        ▼
                Similarity Search
                        │
                        ▼
                Relevant Chunks
                        │
                        ▼
                     Agent
                        │
                        ▼
                    Response
```

---

# 📧 Gmail Architecture

```text
User
 ↓
Email Request
 ↓
Agent
 ↓
Gmail Tool
 ↓
Google Gmail API
 ↓
Email Data
 ↓
Agent
 ↓
Response
```

For sending:

```text
User
 ↓
Compose
 ↓
Verification Action
 ↓
Approval
 ↓
Gmail API
 ↓
Verification
 ↓
Notification
```

---

# 📅 Calendar Architecture

```text
User
 ↓
Calendar Request
 ↓
Agent / Calendar UI
 ↓
Create Verification Action
 ↓
Approval
 ↓
Google Calendar API
 ↓
Verification
 ↓
Completed Event
```

---

# 🔔 Notification Architecture

```text
External Action
      ↓
Verification Action
      ↓
Status Change
      ↓
Notification System
      ↓
Dashboard Notification Bell
      ↓
User
```

---

# 🔐 Security Architecture

The project follows user-scoped data access.

For example, document access is checked against the authenticated user:

```text
Authenticated User ID
        +
Document ID
        ↓
Ownership Validation
        ↓
Document Access
```

Security principles include:

* 🔐 Google OAuth authentication
* 👤 User-scoped queries
* 🔑 Environment-based secrets
* 🛡️ Verification before external actions
* 🚫 No secrets committed to source control
* 🧩 Modular service boundaries
* ✅ Validation before tool execution

---

# 🧪 Testing

Run backend tests:

```powershell
cd backend
poetry run pytest
```

Run frontend checks:

```powershell
cd frontend
npm run build
```

Start backend:

```powershell
cd backend
poetry run uvicorn app.main:app --reload
```

Start frontend:

```powershell
cd frontend
npm run dev
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🧪 Example Use Cases

## 💬 Contextual Conversation

```text
User:
What did we decide about the project architecture?
```

The assistant can retrieve relevant conversation and memory context before answering.

---

## 🧠 Persistent Preference

```text
User:
I prefer short technical explanations.
```

The assistant can store this as a preference.

Later:

```text
User:
Explain vector databases.
```

The response can use the stored preference.

---

## 📄 Document Analysis

```text
User:
[Uploads requirements.pdf]

User:
What are the main project requirements?
```

The assistant retrieves the document content and generates a contextual answer.

---

## 📧 Email Search

```text
User:
Find my emails related to the internship report.
```

The assistant can search Gmail through the configured integration.

---

## 📤 Send Email

```text
User:
Send an email saying the project report is completed.
```

Flow:

```text
Draft
 ↓
Verification
 ↓
Approval
 ↓
Send
 ↓
Verify
```

---

## 📅 Create Reminder

```text
User:
Remind me about the project meeting tomorrow at 10 AM.
```

Flow:

```text
Reminder Request
 ↓
Calendar Action
 ↓
Verification
 ↓
Approval
 ↓
Google Calendar
 ↓
Verified
```

---

# 🖥️ Frontend Dashboard

The dashboard is organized around the user's daily workflow.

```text
┌──────────────────────────────────────────────────────────┐
│                  CONTEXT AI DASHBOARD                    │
├─────────────────┬────────────────────────────────────────┤
│                 │                                        │
│ 💬 Chat         │       AI Conversation                  │
│                 │                                        │
│ 🧠 Memory       │       Context + Tools                  │
│                 │                                        │
│ 📚 Documents    │       Agent Activity                   │
│                 │                                        │
│ 📅 Calendar     │       Verification                    │
│                 │                                        │
│ 📧 Email        │       Results                          │
│                 │                                        │
│ 🔔 Notifications│                                        │
│                 │                                        │
└─────────────────┴────────────────────────────────────────┘
```

---

# 🧭 Application Modules

## 💬 Chat

Central AI interaction interface.

Features:

* Persistent conversations
* Conversation search
* Context-aware responses
* Tool execution
* Agent activity
* Document attachments

---

## 🧠 Memory

Long-term user context.

Features:

* Memory browsing
* Memory types
* Confidence
* Source information
* Conflict handling
* Active/inactive memories

---

## 📚 Documents

Document management and RAG.

Features:

* Upload documents
* Process documents
* Semantic retrieval
* Document-based questions
* Attached document analysis

---

## 📅 Calendar

Calendar and reminder management.

Features:

* View events
* Create reminders
* Create events
* Find free slots
* Update events
* Delete events
* Verification workflow

---

## 📧 Email

Email management interface.

Features:

* Compose email
* Search Gmail
* Read email
* Draft email
* Send email
* Verification workflow

---

## 🔔 Notifications

Central action visibility.

Features:

* Pending actions
* Completed actions
* Failed actions
* Verification status
* Assistant activity

---

# 🌟 Core Design Principles

## 1. 🧠 Memory First

Important information should persist beyond a single conversation.

## 2. 🔎 Retrieve Before Answering

Relevant context should be retrieved before generating context-sensitive answers.

## 3. 🛠️ Tools Over Guessing

When reliable external information is available through a tool, the system should use the tool rather than invent information.

## 4. ✅ Verify External Actions

Actions affecting external systems should pass through a verification process.

## 5. 🔐 User Control

Users should remain in control of actions involving external services.

## 6. 🧩 Modular Architecture

Memory, RAG, tools, integrations and verification are separated into dedicated layers.

## 7. ⚡ Extensible Design

New tools and integrations can be added without redesigning the entire system.

---

# 🚀 Future Roadmap

## Phase 1 — Core Assistant

* [x] Authentication
* [x] Chat
* [x] Persistent conversations
* [x] Long-term memory
* [x] Memory search
* [x] Document upload
* [x] RAG
* [x] Agent tool calling

---

## Phase 2 — Integrations

* [x] Google OAuth
* [x] Gmail integration
* [x] Google Calendar integration
* [ ] Advanced Google Drive workflows
* [ ] Slack integration
* [ ] Additional productivity tools

---

## Phase 3 — Intelligence

* [x] Memory confidence
* [x] Memory importance
* [x] Memory conflicts
* [x] Source reliability
* [x] Verification workflow
* [ ] Advanced agent planning
* [ ] Memory consolidation
* [ ] Improved context ranking
* [ ] Advanced personalization

---

## Phase 4 — Production

* [ ] Docker deployment
* [ ] Production PostgreSQL
* [ ] Background workers
* [ ] Observability
* [ ] Rate limiting
* [ ] Advanced authentication
* [ ] Automated evaluation
* [ ] Production monitoring
* [ ] Cloud deployment

---

# 📈 Project Goals

The project aims to demonstrate how modern AI systems can combine:

```text
🧠 Long-Term Memory
        +
🔎 Semantic Retrieval
        +
📚 RAG
        +
🤖 Agent Reasoning
        +
🛠️ Tool Calling
        +
📧 Real Integrations
        +
📅 Calendar Automation
        +
🔐 Verification
        +
⚡ Full-Stack Engineering
```

The result is an assistant designed to be more contextual, persistent, useful and controlled than a standard conversational interface.

---

# 🤝 Contributing

Contributions, suggestions and improvements are welcome.

```text
Fork Repository
      ↓
Create Feature Branch
      ↓
Implement Feature
      ↓
Run Tests
      ↓
Commit Changes
      ↓
Push Branch
      ↓
Create Pull Request
```

---

# 🐛 Issues & Suggestions

If you discover a bug or have an improvement idea, open an issue in the repository.

Useful issue information includes:

* Problem description
* Steps to reproduce
* Expected behavior
* Actual behavior
* Relevant logs
* Screenshots when applicable

---

# 👨‍💻 Developer

## Zarmeen Rasool

**AI Engineer**

This project is developed by **Zarmeen Rasool** as a practical exploration of modern AI engineering and agent-based application development.

### Areas of Focus

* 🤖 Artificial Intelligence
* 🧠 Agentic AI
* 🔎 Retrieval-Augmented Generation
* 🧠 Long-Term AI Memory
* 🛠️ LLM Tool Calling
* 📚 Document Intelligence
* 📧 AI Integrations
* 📅 Workflow Automation
* ⚡ FastAPI
* ⚛️ Next.js
* 🗃️ PostgreSQL
* 🔎 Vector Databases
* 🏗️ Production-Oriented AI Systems

### 🔗 Developer Links

<p align="center">

<a href="https://github.com/devzarmeen">
  <img src="https://img.shields.io/badge/GitHub-devzarmeen-181717?style=for-the-badge&logo=github&logoColor=white" />
</a>

<a href="https://www.linkedin.com/in/zarmeenrasool/">
  <img src="https://img.shields.io/badge/LinkedIn-Zarmeen%20Rasool-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" />
</a>

<a href="mailto:devzarmeenrasool@gmail.com">
  <img src="https://img.shields.io/badge/Email-devzarmeenrasool%40gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white" />
</a>

</p>

---

# 📄 License

This project is developed for educational, research and hackathon purposes.

---

# ⭐ Support the Project

If you find this project useful:

⭐ Star the repository
🍴 Fork the repository
🐛 Report issues
💡 Suggest improvements
🤝 Contribute

---

<p align="center">

🧠 <b>Remember</b>
  •  
🔎 <b>Retrieve</b>
  •  
🤖 <b>Reason</b>
  •  
🛠️ <b>Act</b>
  •  
✅ <b>Verify</b>

</p>

<p align="center">

<img src="https://img.shields.io/badge/Built%20with-AI%20%26%20Engineering-6C63FF?style=for-the-badge" />
<img src="https://img.shields.io/badge/Made%20by-Zarmeen%20Rasool-111827?style=for-the-badge" />

</p>

<p align="center">

<b>Persistent Contextual AI Assistant</b>

<br/>

Building AI that remembers context, uses tools, and acts responsibly.

</p>
