"""SQLite database for storing user tokens."""

import os
import logging
from typing import Optional
from datetime import datetime
import aiosqlite
from .models import UserToken, TokenAttempts

logger = logging.getLogger(__name__)


class TokenRateLimiter:
    """Rate limiter for token input attempts."""
    
    def __init__(self, max_attempts: int = 5, timeout_minutes: int = 2):
        """Initialize rate limiter.
        
        Args:
            max_attempts: Maximum number of attempts allowed
            timeout_minutes: Timeout period in minutes after max attempts reached
        """
        #Initialize SQLite token storage.
        # Default to SQLite file, but allow override with DATABASE_URL
        database_url = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
        if database_url.startswith('sqlite:///'):
            self.db_path = database_url.replace('sqlite:///', '')
        else:
            self.db_path = 'bot.db'

        self._initialized = False
        self.max_attempts = max_attempts
        self.timeout_minutes = timeout_minutes

    async def _ensure_table_exists(self):
        """Create the token_attempts table if it doesn't exist."""
        if self._initialized:
            return
            
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS token_attempts (
                        telegram_user_id INTEGER NOT NULL,
                        attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN DEFAULT FALSE,
                        PRIMARY KEY (telegram_user_id, attempt_time)
                    )
                """)
                await conn.commit()
                self._initialized = True
                logger.info(f"SQLite database initialized at {self.db_path}")
            except Exception as e:
                logger.error(f"Error creating table: {e}")
                raise


    async def can_attempt(self, telegram_user_id: int) -> tuple[bool, str]:
        """Check if user can make a token input attempt.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            Tuple of (can_attempt, message)
        """
        recent_attempts = await self.get_recent_attempts(telegram_user_id, self.timeout_minutes)
        
        if recent_attempts >= self.max_attempts:
            return False, f"❌ Превышено максимальное количество попыток ввода токена ({self.max_attempts}).\n\n⏰ Попробуйте снова через {self.timeout_minutes} минут."
        
        remaining = self.max_attempts - recent_attempts
        if remaining <= 2:  # Warning when 1-2 attempts left
            return True, f"⚠️ Осталось попыток: {remaining}"
        
        return True, ""
    
    async def record_attempt(self, telegram_user_id: int, success: bool) -> None:
        """Record a token input attempt.
        
        Args:
            telegram_user_id: Telegram user ID
            success: Whether the attempt was successful
        """
        await self.record_token_attempt(telegram_user_id, success)
        
        # Clean up old attempts periodically
        if success:  # Only cleanup on successful attempts to avoid frequent DB operations
            await self.cleanup_old_attempts(telegram_user_id)

    async def record_token_attempt(self, telegram_user_id: int, success: bool = False) -> None:
        """Record a token input attempt.
        
        Args:
            telegram_user_id: Telegram user ID
            success: Whether the attempt was successful
        """
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute(
                    "INSERT INTO token_attempts (telegram_user_id, success) VALUES (?, ?)",
                    (telegram_user_id, success)
                )
                await conn.commit()
                logger.info(f"Recorded token attempt for user {telegram_user_id}, success: {success}")
            except Exception as e:
                logger.error(f"Error recording token attempt for user {telegram_user_id}: {e}")
    
    async def get_recent_attempts(self, telegram_user_id: int, minutes: int = 60) -> int:
        """Get count of recent token attempts within specified minutes.
        
        Args:
            telegram_user_id: Telegram user ID
            minutes: Time window in minutes (default 60)
            
        Returns:
            Number of attempts in the time window
        """
        await self._ensure_table_exists()

        async with aiosqlite.connect(self.db_path) as conn:
            try:
                cursor = await conn.execute(
                    """SELECT COUNT(*) FROM token_attempts 
                       WHERE telegram_user_id = ?
                       AND (strftime('%s', CURRENT_TIMESTAMP) - strftime('%s', attempt_time)) / 60 <= ?""",
                    (telegram_user_id, minutes)
                )
                result = await cursor.fetchone()
                return result[0] if result else 0
            except Exception as e:
                logger.error(f"Error getting recent attempts for user {telegram_user_id}: {e}")
                return 0
    
    async def cleanup_old_attempts(self, telegram_user_id: int, days: int = 1) -> None:
        """Clean up old token attempts older than specified hours.
        
        Args:
            telegram_user_id: Telegram user ID
            days: Age threshold in days (default 1)
        """
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                cursor = await conn.execute(
                    """DELETE FROM token_attempts
                       WHERE telegram_user_id = ?
                       AND (success = FALSE
                       OR JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(attempt_time) > ?)""",
                    (telegram_user_id, days)
                )
                await conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Cleaned up {cursor.rowcount} old token attempts")
            except Exception as e:
                logger.error(f"Error cleaning up old attempts: {e}")

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
rate_limiter = TokenRateLimiter(max_attempts=4, timeout_minutes=2)