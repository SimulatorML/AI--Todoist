"""Simple in-memory database for storing user tokens."""

import logging
from typing import Optional, Dict
from datetime import datetime
from .models import UserToken

logger = logging.getLogger(__name__)


class UserTokenStorage:
    """In-memory storage for user Todoist tokens."""
    
    def __init__(self):
        """Initialize empty token storage."""
        self._tokens: Dict[int, UserToken] = {}
    
    async def store_token(self, telegram_user_id: int, todoist_token: str) -> None:
        """Store a user's Todoist token.
        
        Args:
            telegram_user_id: Telegram user ID
            todoist_token: User's Todoist API token
        """
        user_token = UserToken(
            telegram_user_id=telegram_user_id,
            todoist_token=todoist_token,
            created_at=datetime.now().isoformat()
        )
        
        self._tokens[telegram_user_id] = user_token
        logger.info(f"Stored token for user {telegram_user_id}")
    
    async def get_token(self, telegram_user_id: int) -> Optional[str]:
        """Get a user's Todoist token.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            User's Todoist token or None if not found
        """
        user_token = self._tokens.get(telegram_user_id)
        if user_token:
            return user_token.todoist_token
        return None
    
    async def has_token(self, telegram_user_id: int) -> bool:
        """Check if user has a stored token.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if user has a token stored, False otherwise
        """
        return telegram_user_id in self._tokens
    
    async def remove_token(self, telegram_user_id: int) -> bool:
        """Remove a user's token.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if token was removed, False if not found
        """
        if telegram_user_id in self._tokens:
            del self._tokens[telegram_user_id]
            logger.info(f"Removed token for user {telegram_user_id}")
            return True
        return False


# Global instance for the application
user_storage = UserTokenStorage()