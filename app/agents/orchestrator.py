"""
AutoTasker – Multi-Agent Orchestration using AutoGen.
Agents: Planner → Executor → Critic (with tool-use and Redis memory).
"""
import json
import logging
import redis
from typing import Any, Optional
import autogen
from app.core.config import settings

logger = logging.getLogger(__name__)


PLANNER_PROMPT = """You are the Planner agent. Given a high-level task, break it into
an ordered list of concrete, executable sub-tasks. Each sub-task should be specific,
measurable, and achievable. Output ONLY valid JSON:
{
  "task_id": "<uuid>",
  "original_task": "<task>",
  "sub_tasks": [
    {"id": 1, "description": "...", "estimated_effort": "low|medium|high", "depends_on": []}
  ]
}"""

EXECUTOR_PROMPT = """You are the Executor agent. You receive a specific sub-task and
execute it step by step. Use available tools when needed. Report the outcome clearly.
If you cannot complete a step, explain why and suggest an alternative."""

CRITIC_PROMPT = """You are the Critic agent. You review completed tasks and:
1. Verify the output meets the original requirements
2. Identify any gaps or errors
3. Suggest improvements or corrections
4. Approve or request revision

Score quality 0-10 and provide structured feedback."""


class RedisMemory:
    def __init__(self, redis_url: str):
        try:
            self.client = redis.from_url(redis_url)
            self.client.ping()
            self.available = True
        except Exception as exc:
            logger.warning("Redis unavailable: %s – using in-memory fallback", exc)
            self.available = False
            self._memory: dict = {}

    def store(self, key: str, value: Any, ttl: int = 3600):
        if self.available:
            self.client.setex(key, ttl, json.dumps(value))
        else:
            self._memory[key] = value

    def retrieve(self, key: str) -> Optional[Any]:
        if self.available:
            val = self.client.get(key)
            return json.loads(val) if val else None
        return self._memory.get(key)

    def append_history(self, workflow_id: str, entry: dict):
        history = self.retrieve(f"history:{workflow_id}") or []
        history.append(entry)
        self.store(f"history:{workflow_id}", history)

    def get_history(self, workflow_id: str) -> list:
        return self.retrieve(f"history:{workflow_id}") or []


class AutoTaskerOrchestrator:
    def __init__(self):
        self.memory = RedisMemory(settings.REDIS_URL)
        self.llm_config = {
            "config_list": [
                {
                    "model": settings.LLM_MODEL,
                    "api_key": settings.OPENAI_API_KEY,
                }
            ],
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS,
        }
        self._build_agents()

    def _build_agents(self):
        self.user_proxy = autogen.UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=settings.MAX_ROUNDS,
            code_execution_config=False,
        )

        self.planner = autogen.AssistantAgent(
            name="Planner",
            system_message=PLANNER_PROMPT,
            llm_config=self.llm_config,
        )

        self.executor = autogen.AssistantAgent(
            name="Executor",
            system_message=EXECUTOR_PROMPT,
            llm_config=self.llm_config,
        )

        self.critic = autogen.AssistantAgent(
            name="Critic",
            system_message=CRITIC_PROMPT,
            llm_config=self.llm_config,
        )

        self.group_chat = autogen.GroupChat(
            agents=[self.user_proxy, self.planner, self.executor, self.critic],
            messages=[],
            max_round=settings.MAX_ROUNDS,
            speaker_selection_method="round_robin",
        )

        self.manager = autogen.GroupChatManager(
            groupchat=self.group_chat,
            llm_config=self.llm_config,
        )

    def run_workflow(self, task: str, workflow_id: str) -> dict:
        logger.info("Starting workflow %s for task: %s", workflow_id, task)
        self.memory.store(f"workflow:{workflow_id}:status", "running")
        self.memory.append_history(workflow_id, {"event": "started", "task": task})

        chat_result = self.user_proxy.initiate_chat(
            self.manager,
            message=f"TASK: {task}\nWorkflow ID: {workflow_id}",
        )

        messages = [m for m in self.group_chat.messages]
        result = {
            "workflow_id": workflow_id,
            "task": task,
            "status": "completed",
            "message_count": len(messages),
            "messages": [
                {"role": m.get("name", "unknown"), "content": m.get("content", "")[:500]}
                for m in messages[-5:]
            ],
            "history": self.memory.get_history(workflow_id),
        }

        self.memory.store(f"workflow:{workflow_id}:status", "completed")
        self.memory.store(f"workflow:{workflow_id}:result", result)
        self.memory.append_history(workflow_id, {"event": "completed"})
        return result

    def get_workflow_status(self, workflow_id: str) -> dict:
        status = self.memory.retrieve(f"workflow:{workflow_id}:status") or "not_found"
        result = self.memory.retrieve(f"workflow:{workflow_id}:result")
        history = self.memory.get_history(workflow_id)
        return {"workflow_id": workflow_id, "status": status, "result": result, "history": history}


_orchestrator: Optional[AutoTaskerOrchestrator] = None


def get_orchestrator() -> AutoTaskerOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AutoTaskerOrchestrator()
    return _orchestrator
