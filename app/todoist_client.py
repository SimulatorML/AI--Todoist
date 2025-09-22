"""Async Todoist API client using httpx."""

import logging
from typing import Optional
import httpx
from .models import TodoistTask, TodoistTaskResponse

logger = logging.getLogger(__name__)


class TodoistClient:
    """Async client for Todoist API operations."""
    
    def __init__(self, token: str):
        """Initialize the Todoist client with an API token."""
        self.token = token
        self.base_url = "https://api.todoist.com/rest/v2"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def create_task(self, task: TodoistTask) -> TodoistTaskResponse:
        """Create a new task in Todoist.
        
        Args:
            task: TodoistTask model with task details
            
        Returns:
            TodoistTaskResponse with created task details
            
        Raises:
            httpx.HTTPStatusError: If the API request fails
            ValueError: If the response format is invalid
        """
        async with httpx.AsyncClient() as client:
            try:
                # Prepare task data
                task_data = {
                    "content": task.content,
                    "priority": task.priority
                }
                
                # Add optional fields if provided
                if task.project_id:
                    task_data["project_id"] = task.project_id
                if task.due_date:
                    task_data["due_date"] = task.due_date
                if task.due_string:
                    task_data["due_string"] = task.due_string
                if task.request_id:
                    # Use request_id for idempotency
                    self.headers["X-Request-Id"] = task.request_id
                
                logger.info(f"Creating task: {task.content}")
                
                response = await client.post(
                    f"{self.base_url}/tasks",
                    json=task_data,
                    headers=self.headers,
                    timeout=10.0
                )
                
                response.raise_for_status()
                task_response = response.json()
                
                return TodoistTaskResponse(
                    id=task_response["id"],
                    content=task_response["content"],
                    project_id=task_response["project_id"],
                    priority=task_response["priority"],
                    due=task_response.get("due"),
                    url=task_response["url"]
                )
                
            except httpx.TimeoutException:
                logger.error("Todoist API request timed out")
                raise ValueError("Todoist service is currently unavailable (timeout)")
            except httpx.HTTPStatusError as e:
                logger.error(f"Todoist API error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 401:
                    raise ValueError("Invalid Todoist API token")
                elif e.response.status_code == 403:
                    raise ValueError("Access denied to Todoist API")
                else:
                    raise ValueError(f"Todoist API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Unexpected error creating task: {e}")
                raise ValueError("Failed to create task in Todoist")
    
    async def get_projects(self) -> list:
        """Get all projects for the user.
        
        Returns:
            List of projects
            
        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/projects",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                logger.error(f"Error fetching projects: {e}")
                raise ValueError("Failed to fetch projects from Todoist")