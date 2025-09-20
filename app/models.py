"""Pydantic models for Telegram bot and Todoist integration."""

from typing import Optional
from pydantic import BaseModel


class TodoistTask(BaseModel):
    """Model for creating a new Todoist task."""
    content: str
    project_id: Optional[str] = None
    due_string: Optional[str] = None
    priority: int = 2
    request_id: Optional[str] = None


class TodoistTaskResponse(BaseModel):
    """Model for Todoist task creation response."""
    id: str
    content: str
    project_id: str
    priority: int
    url: str


class BotResponse(BaseModel):
    """Model for bot response to user."""
    message: str
    success: bool
    task_id: Optional[str] = None


class UserToken(BaseModel):
    """Model for storing user Todoist tokens."""
    telegram_user_id: int
    todoist_token: str
    created_at: Optional[str] = None