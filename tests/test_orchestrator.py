"""Tests for AutoTasker Orchestrator."""
import pytest
from unittest.mock import MagicMock, patch


def test_redis_memory_fallback():
    """RedisMemory falls back to in-memory when Redis unavailable."""
    with patch("app.agents.orchestrator.redis.from_url") as mock_redis:
        mock_redis.return_value.ping.side_effect = Exception("Connection refused")
        from app.agents.orchestrator import RedisMemory
        mem = RedisMemory("redis://localhost:6379/0")
        assert not mem.available
        mem.store("key1", {"data": "test"})
        result = mem.retrieve("key1")
        assert result == {"data": "test"}


def test_redis_history():
    """History appending and retrieval works."""
    with patch("app.agents.orchestrator.redis.from_url") as mock_redis:
        mock_redis.return_value.ping.side_effect = Exception("unavailable")
        from app.agents.orchestrator import RedisMemory
        mem = RedisMemory("redis://localhost:6379/0")
        mem.append_history("wf-1", {"event": "started"})
        mem.append_history("wf-1", {"event": "completed"})
        hist = mem.get_history("wf-1")
        assert len(hist) == 2
        assert hist[0]["event"] == "started"


def test_health_endpoint():
    """Health endpoint returns ok."""
    with patch("app.agents.orchestrator.redis.from_url") as mock_redis, \
         patch("app.agents.orchestrator.autogen"):
        mock_redis.return_value.ping.side_effect = Exception("unavailable")
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        r = client.get("/api/v1/tasks/health")
        assert r.status_code == 200
