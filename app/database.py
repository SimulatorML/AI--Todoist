"""PostgreSQL database for storing user tokens."""

import os
import logging
from typing import Optional
from datetime import datetime
import asyncpg
from .models import UserToken

logger = logging.getLogger(__name__)


class UserTokenStorage:
    """PostgreSQL storage for user Todoist tokens."""
    
    def __init__(self):
        """Initialize PostgreSQL token storage."""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        self._initialized = False
    
    async def _ensure_table_exists(self):
        """Create the user_tokens table if it doesn't exist."""
        if self._initialized:
            return
            
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_tokens (
                    telegram_user_id BIGINT PRIMARY KEY,
                    todoist_token VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            self._initialized = True
            logger.info("Database table initialized")
        except Exception as e:
            logger.error(f"Error creating table: {e}")
            raise
        finally:
            await conn.close()
    
    async def store_token(self, telegram_user_id: int, todoist_token: str) -> None:
        """Store a user's Todoist token.
        
        Args:
            telegram_user_id: Telegram user ID
            todoist_token: User's Todoist API token
        """
        await self._ensure_table_exists()
        
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute("""
                INSERT INTO user_tokens (telegram_user_id, todoist_token, created_at, updated_at)
                VALUES ($1, $2, NOW(), NOW())
                ON CONFLICT (telegram_user_id)
                DO UPDATE SET
                    todoist_token = EXCLUDED.todoist_token,
                    updated_at = NOW()
            """, telegram_user_id, todoist_token)
            
            logger.info(f"Stored token for user {telegram_user_id}")
        except Exception as e:
            logger.error(f"Error storing token for user {telegram_user_id}: {e}")
            raise
        finally:
            await conn.close()
    
    async def get_token(self, telegram_user_id: int) -> Optional[str]:
        """Get a user's Todoist token.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            User's Todoist token or None if not found
        """
        await self._ensure_table_exists()
        
        conn = await asyncpg.connect(self.database_url)
        try:
            row = await conn.fetchrow(
                "SELECT todoist_token FROM user_tokens WHERE telegram_user_id = $1",
                telegram_user_id
            )
            return row['todoist_token'] if row else None
        except Exception as e:
            logger.error(f"Error fetching token for user {telegram_user_id}: {e}")
            return None
        finally:
            await conn.close()
    
    async def has_token(self, telegram_user_id: int) -> bool:
        """Check if user has a stored token.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if user has a token stored, False otherwise
        """
        await self._ensure_table_exists()
        
        conn = await asyncpg.connect(self.database_url)
        try:
            result = await conn.fetchval(
                "SELECT 1 FROM user_tokens WHERE telegram_user_id = $1",
                telegram_user_id
            )
            return result is not None
        except Exception as e:
            logger.error(f"Error checking token for user {telegram_user_id}: {e}")
            return False
        finally:
            await conn.close()
    
    async def user_exists(self, telegram_user_id: int) -> bool:
        """Check if user exists in database (has had any interaction).
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if user exists in database, False otherwise
        """
        # For simplicity, we'll consider a user as 'existing' if they have a token entry
        # This works because tokens are stored on first interaction
        return await self.has_token(telegram_user_id)
    
    async def remove_token(self, telegram_user_id: int) -> bool:
        """Remove a user's token.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if token was removed, False if not found
        """
        await self._ensure_table_exists()
        
        conn = await asyncpg.connect(self.database_url)
        try:
            result = await conn.execute(
                "DELETE FROM user_tokens WHERE telegram_user_id = $1",
                telegram_user_id
            )
            
            if result == 'DELETE 1':
                logger.info(f"Removed token for user {telegram_user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing token for user {telegram_user_id}: {e}")
            return False
        finally:
            await conn.close()


# Global instance for the application
user_storage = UserTokenStorage()