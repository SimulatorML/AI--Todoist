"""Tests for database storage."""

import pytest
from app.database import UserTokenStorage


@pytest.fixture
def storage():
    """Create a fresh storage instance for each test."""
    return UserTokenStorage()


@pytest.mark.asyncio
async def test_store_and_get_token(storage):
    """Test storing and retrieving a token."""
    user_id = 12345
    token = "test_token_123"
    
    # Store token
    await storage.store_token(user_id, token)
    
    # Retrieve token
    retrieved_token = await storage.get_token(user_id)
    assert retrieved_token == token


@pytest.mark.asyncio
async def test_has_token(storage):
    """Test checking if user has token."""
    user_id = 12345
    token = "test_token_123"
    
    # Initially no token
    assert not await storage.has_token(user_id)
    
    # Store token
    await storage.store_token(user_id, token)
    
    # Now has token
    assert await storage.has_token(user_id)


@pytest.mark.asyncio
async def test_remove_token(storage):
    """Test removing a token."""
    user_id = 12345
    token = "test_token_123"
    
    # Store token
    await storage.store_token(user_id, token)
    assert await storage.has_token(user_id)
    
    # Remove token
    result = await storage.remove_token(user_id)
    assert result is True
    assert not await storage.has_token(user_id)
    
    # Try to remove non-existent token
    result = await storage.remove_token(user_id)
    assert result is False


@pytest.mark.asyncio
async def test_get_nonexistent_token(storage):
    """Test getting a token that doesn't exist."""
    user_id = 99999
    token = await storage.get_token(user_id)
    assert token is None