"""Python client for Clara Cerebrum REST API (CLIPS expert system).

This client provides a Python interface to interact with the Clara REST API,
which manages CLIPS expert system sessions and evaluations.
"""
import aiohttp
import logging
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


class ClaraSession:
    """Represents a persistent CLIPS session."""

    def __init__(self, session_id: str, api_client: 'CerebrumClient'):
        self.session_id = session_id
        self.client = api_client

    async def eval(self, script: str) -> Dict[str, Any]:
        """Evaluate CLIPS script in this session."""
        return await self.client.eval_session(self.session_id, script)

    async def status(self) -> Dict[str, Any]:
        """Get session status."""
        return await self.client.get_session(self.session_id)

    async def save(self) -> Dict[str, Any]:
        """Save session state."""
        return await self.client.save_session(self.session_id)


class CerebrumClient:
    """Async client for Clara Cerebrum REST API."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self._current_session: Optional[ClaraSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def health_check(self) -> bool:
        """Check if Clara API is healthy."""
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}/healthz") as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def create_session(self, user_id: str = "default") -> ClaraSession:
        """Create a new persistent CLIPS session."""
        await self._ensure_session()

        payload = {
            "user_id": user_id,
            "preload": [],
            "metadata": {"description": "Clara voice session"}
        }

        try:
            async with self.session.post(
                f"{self.base_url}/sessions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 201 or resp.status == 200:
                    data = await resp.json()
                    session_id = data.get("session_id") or data.get("id")
                    logger.info(f"Created session: {session_id}")
                    self._current_session = ClaraSession(session_id, self)
                    return self._current_session
                else:
                    error_text = await resp.text()
                    raise RuntimeError(f"Failed to create session: {resp.status} {error_text}")
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session information."""
        await self._ensure_session()

        try:
            async with self.session.get(
                f"{self.base_url}/sessions/{session_id}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise RuntimeError(f"Failed to get session: {resp.status} {error_text}")
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            raise

    async def eval_session(self, session_id: str, script: str) -> Dict[str, Any]:
        """Evaluate CLIPS script in a session."""
        await self._ensure_session()

        payload = {"script": script}

        try:
            async with self.session.post(
                f"{self.base_url}/sessions/{session_id}/eval",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise RuntimeError(f"Eval failed: {resp.status} {error_text}")
        except Exception as e:
            logger.error(f"Error evaluating script: {e}")
            raise

    async def save_session(self, session_id: str) -> Dict[str, Any]:
        """Save session state."""
        await self._ensure_session()

        try:
            async with self.session.post(
                f"{self.base_url}/sessions/{session_id}/save",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise RuntimeError(f"Save failed: {resp.status} {error_text}")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            raise

    async def eval_ephemeral(self, script: str) -> Dict[str, Any]:
        """Evaluate CLIPS script in an ephemeral session."""
        await self._ensure_session()

        payload = {"script": script}

        try:
            async with self.session.post(
                f"{self.base_url}/eval",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise RuntimeError(f"Ephemeral eval failed: {resp.status} {error_text}")
        except Exception as e:
            logger.error(f"Error in ephemeral eval: {e}")
            raise

    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
