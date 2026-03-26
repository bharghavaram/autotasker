"""Celery tasks for AutoTasker workflow processing."""
import logging
from app.tasks.celery_app import celery_app
from app.agents.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.workflow_tasks.run_workflow_task", max_retries=2)
def run_workflow_task(self, task: str, workflow_id: str) -> dict:
    """Run a multi-agent workflow asynchronously via Celery."""
    logger.info("Celery worker starting workflow %s", workflow_id)
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.run_workflow(task, workflow_id)
        return result
    except Exception as exc:
        logger.error("Workflow %s failed: %s", workflow_id, exc)
        raise self.retry(exc=exc, countdown=30)
