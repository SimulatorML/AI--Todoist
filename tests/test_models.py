"""Tests for Pydantic models."""

import pytest
from app.models import TodoistTask, TodoistTaskResponse, BotResponse, TokenAttempts, UserToken


def test_todoist_task_creation():
    """Test TodoistTask model creation."""
    task = TodoistTask(
        content="Test task",
        priority=4,
        request_id="test_123"
    )
    
    assert task.content == "Test task"
    assert task.priority == 4
    assert task.request_id == "test_123"
    assert task.project_id is None
    assert task.due_string is None


def test_todoist_task_defaults():
    """Test TodoistTask model with defaults."""
    task = TodoistTask(content="Test task")
    
    assert task.content == "Test task"
    assert task.priority == 3  # Default priority
    assert task.project_id is None
    assert task.due_string is None
    assert task.request_id is None


def test_todoist_task_response():
    """Test TodoistTaskResponse model."""
    response = TodoistTaskResponse(
        id="123456",
        content="Test task",
        project_id="789",
        priority=3,
        url="https://todoist.com/showTask?id=123456"
    )
    
    assert response.id == "123456"
    assert response.content == "Test task"
    assert response.project_id == "789"
    assert response.priority == 3
    assert response.url == "https://todoist.com/showTask?id=123456"


def test_bot_response():
    """Test BotResponse model."""
    response = BotResponse(
        message="Task created successfully",
        success=True,
        task_id="123456"
    )
    
    assert response.message == "Task created successfully"
    assert response.success is True
    assert response.task_id == "123456"


def test_user_token():
    """Test UserToken model."""
    token = UserToken(
        telegram_user_id=12345,
        todoist_token="abc123xyz",
        created_at="2025-01-01T00:00:00"
    )
    
    assert token.telegram_user_id == 12345
    assert token.todoist_token == "abc123xyz"
    assert token.created_at == "2025-01-01T00:00:00"



def test_token_attempts():
    """Test TokenAttempts model."""
    token = TokenAttempts(
        telegram_user_id=12345,
        attempt_time="2025-01-01T00:00:00",
        success=True
    )
    
    assert token.telegram_user_id == 12345
    assert token.attempt_time == "2025-01-01T00:00:00"
    assert token.success == True
