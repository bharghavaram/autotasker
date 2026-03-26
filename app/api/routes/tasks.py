"""AutoTasker – Multi-Agent Task Orchestration routes."""
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional
from app.agents.orchestrator import AutoTaskerOrchestrator, get_orchestrator

router = APIRouter(prefix="/tasks", tags=["Task Orchestration"])


class TaskRequest(BaseModel):
    task: str
    workflow_id: Optional[str] = None


class TaskResponse(BaseModel):
    workflow_id: str
    status: str
    message: str


_running_workflows: dict = {}


@router.post("/run", response_model=TaskResponse)
async def run_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    orchestrator: AutoTaskerOrchestrator = Depends(get_orchestrator),
):
    """Submit a task for multi-agent orchestration (Planner → Executor → Critic)."""
    if not request.task.strip():
        raise HTTPException(status_code=400, detail="Task description cannot be empty.")

    workflow_id = request.workflow_id or str(uuid.uuid4())

    def run():
        _running_workflows[workflow_id] = "running"
        result = orchestrator.run_workflow(request.task, workflow_id)
        _running_workflows[workflow_id] = result

    background_tasks.add_task(run)
    return TaskResponse(
        workflow_id=workflow_id,
        status="submitted",
        message="Task submitted to multi-agent orchestration pipeline.",
    )


@router.get("/status/{workflow_id}")
async def get_status(
    workflow_id: str,
    orchestrator: AutoTaskerOrchestrator = Depends(get_orchestrator),
):
    """Get workflow status and result."""
    status = orchestrator.get_workflow_status(workflow_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found.")
    return status


@router.get("/active")
async def list_active():
    """List currently running workflows."""
    return {"active_workflows": list(_running_workflows.keys())}


@router.get("/health")
async def health():
    return {"status": "ok", "service": "AutoTasker - Multi-Agent Task Orchestration"}
