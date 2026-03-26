"""
AutoTasker – Multi-Agent Task Orchestration System
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings

app = FastAPI(
    title="AutoTasker – Multi-Agent Task Orchestration",
    description=(
        "AutoGen-powered multi-agent system with Planner, Executor, and Critic agents. "
        "Tool-use, Redis-backed persistent memory, inter-agent communication, "
        "and Celery-based async workflow processing."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": "AutoTasker – Multi-Agent Task Orchestration System",
        "version": "1.0.0",
        "docs": "/docs",
        "agents": ["Planner", "Executor", "Critic"],
        "endpoints": {
            "run_task": "POST /api/v1/tasks/run",
            "get_status": "GET /api/v1/tasks/status/{workflow_id}",
            "list_active": "GET /api/v1/tasks/active",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
