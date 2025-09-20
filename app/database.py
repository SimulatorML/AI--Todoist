"""SQLite database for storing user tokens."""

import os
import logging
from typing import Optional
from datetime import datetime
import aiosqlite
from .models import UserToken

logger = logging.getLogger(__name__)


class UserTokenStorage:
    """SQLite storage for user Todoist tokens."""
    
    def __init__(self):
        """Initialize SQLite token storage."""
        # Default to SQLite file, but allow override with DATABASE_URL
        database_url = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
        if database_url.startswith('sqlite:///'):
            self.db_path = database_url.replace('sqlite:///', '')
        else:
            self.db_path = 'bot.db'
        self._initialized = False
    
    async def _ensure_table_exists(self):
        """Create the user_tokens table if it doesn't exist."""
        if self._initialized:
            return
            
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_tokens (
                        telegram_user_id INTEGER PRIMARY KEY,
                        todoist_token TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await conn.commit()
                self._initialized = True
                logger.info(f"SQLite database initialized at {self.db_path}")
            except Exception as e:
                logger.error(f"Error creating table: {e}")
                raise
    
    async def store_token(self, telegram_user_id: int, todoist_token: str) -> None:
        """Store a user's Todoist token.
        
        Args:
            telegram_user_id: Telegram user ID
            todoist_token: User's Todoist API token
        """
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute("""
                    INSERT INTO user_tokens (telegram_user_id, todoist_token, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(telegram_user_id) DO UPDATE SET
                        todoist_token = excluded.todoist_token,
                        updated_at = CURRENT_TIMESTAMP
                """, (telegram_user_id, todoist_token))
                await conn.commit()
                
                logger.info(f"Stored token for user {telegram_user_id}")
            except Exception as e:
                logger.error(f"Error storing token for user {telegram_user_id}: {e}")
                raise
    
    async def get_token(self, telegram_user_id: int) -> Optional[str]:
        """Get a user's Todoist token.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            User's Todoist token or None if not found
        """
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                cursor = await conn.execute(
                    "SELECT todoist_token FROM user_tokens WHERE telegram_user_id = ?",
                    (telegram_user_id,)
                )
                row = await cursor.fetchone()
                return row[0] if row else None
            except Exception as e:
                logger.error(f"Error fetching token for user {telegram_user_id}: {e}")
                return None
    
    async def has_token(self, telegram_user_id: int) -> bool:
        """Check if user has a stored token.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if user has a token stored, False otherwise
        """
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                cursor = await conn.execute(
                    "SELECT 1 FROM user_tokens WHERE telegram_user_id = ?",
                    (telegram_user_id,)
                )
                result = await cursor.fetchone()
                return result is not None
            except Exception as e:
                logger.error(f"Error checking token for user {telegram_user_id}: {e}")
                return False
    
    async def remove_token(self, telegram_user_id: int) -> bool:
        """Remove a user's token.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if token was removed, False if not found
        """
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                cursor = await conn.execute(
                    "DELETE FROM user_tokens WHERE telegram_user_id = ?",
                    (telegram_user_id,)
                )
                await conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Removed token for user {telegram_user_id}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Error removing token for user {telegram_user_id}: {e}")
                return False


# Global instance for the application
user_storage = UserTokenStorage()