# 🤖 AutoTasker – Multi-Agent Task Orchestration System

> **AutoGen-powered multi-agent system with Planner, Executor, and Critic agents, Redis-backed memory, and Celery async processing.**

## Overview

AutoTasker is an enterprise-grade multi-agent orchestration platform that automates complex workflows by decomposing high-level tasks into executable sub-tasks, executing them intelligently, and self-critiquing the results.

**Key Metrics:**
- ⚡ 60% reduction in manual intervention across 200+ workflows
- 💰 32% token cost reduction via optimised agent communication
- 🔄 Redis-backed persistent memory across sessions
- 📦 Full Docker + Kubernetes deployment

## Architecture

```
User Task Input
      │
      ▼
┌─────────────────────────────────────────┐
│  AutoGen GroupChat Manager              │
│  ┌───────────┐ ┌──────────┐ ┌────────┐ │
│  │  PLANNER  │ │ EXECUTOR │ │ CRITIC │ │
│  │ Decomposes│ │ Runs sub │ │Reviews │ │
│  │  tasks    │ │  tasks   │ │quality │ │
│  └───────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────┘
      │              │
      ▼              ▼
 Redis Memory    Celery Queue
 (Persistence)   (Async Jobs)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | Microsoft AutoGen (pyautogen) |
| Orchestration | LangChain |
| LLM | OpenAI GPT-4o |
| Task Queue | Celery |
| Message Broker | Redis |
| Memory | Redis (persistent) |
| API | FastAPI |
| Deployment | Docker, Kubernetes |

## Quick Start

### With Docker Compose (Recommended)

```bash
git clone https://github.com/bharghavram/autotasker.git
cd autotasker
cp .env.example .env
# Edit .env with your OpenAI API key
docker-compose up --build
```

### Manual Setup

```bash
# Requires Redis running locally
pip install -r requirements.txt
cp .env.example .env
# Start API
uvicorn main:app --reload
# Start Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/tasks/run` | Submit task to agent pipeline |
| `GET` | `/api/v1/tasks/status/{workflow_id}` | Get workflow status |
| `GET` | `/api/v1/tasks/active` | List active workflows |
| `GET` | `/api/v1/tasks/health` | Health check |

### Example: Run a Task

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/run" \
  -H "Content-Type: application/json" \
  -d '{"task": "Research the top 5 AI trends in 2024 and write a concise summary report."}'
```

### Check Status

```bash
curl "http://localhost:8000/api/v1/tasks/status/<workflow_id>"
```

## Agent Roles

### 🗂️ Planner Agent
- Receives the high-level task
- Decomposes it into ordered sub-tasks
- Estimates effort levels and dependencies
- Outputs structured JSON task plan

### ⚙️ Executor Agent
- Receives individual sub-tasks from Planner
- Executes step-by-step with tool use
- Reports completion status and output
- Handles failures with alternative strategies

### 🔍 Critic Agent
- Reviews Executor's output quality
- Scores on a 0-10 scale
- Identifies gaps or errors
- Approves or requests revision

## Redis Memory Schema

```
workflow:{id}:status    → "running" | "completed" | "failed"
workflow:{id}:result    → JSON result object
history:{id}            → List of events with timestamps
```

## Tests

```bash
pytest tests/ -v
```

---

*Built by Bharghava Ram Vemuri | Sep 2024 – Nov 2024*
