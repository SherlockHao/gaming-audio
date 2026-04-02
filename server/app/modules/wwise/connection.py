"""WAAPI (Wwise Authoring API) connection manager.

Provides WebSocket connection to Wwise Authoring Application with:
- Configurable endpoint (default ws://127.0.0.1:8080/waapi)
- Auto-reconnect with exponential backoff
- Connection health check via ak.wwise.core.getInfo
- Context manager for clean resource management

Note: Requires Wwise Authoring Application running with WAAPI enabled.
waapi-client is optional — module fails gracefully if not installed.
"""
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from waapi import WaapiClient
    WAAPI_AVAILABLE = True
except ImportError:
    WAAPI_AVAILABLE = False
    WaapiClient = None


class WaapiConnectionError(Exception):
    pass


class WaapiConnection:
    def __init__(
        self,
        url: str = "ws://127.0.0.1:8080/waapi",
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
    ):
        self.url = url
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._client: WaapiClient | None = None

    async def connect(self) -> None:
        if not WAAPI_AVAILABLE:
            raise WaapiConnectionError(
                "waapi-client package not installed. Install with: pip install waapi-client"
            )
        for attempt in range(self.max_retries):
            try:
                self._client = WaapiClient(url=self.url)
                info = self._client.call("ak.wwise.core.getInfo")
                logger.info(f"Connected to Wwise {info.get('displayName', 'Unknown')}")
                return
            except Exception as e:
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"WAAPI connect attempt {attempt + 1}/{self.max_retries} failed: {e}. Retrying in {delay}s...")
                if self._client:
                    try:
                        self._client.disconnect()
                    except Exception:
                        pass
                    self._client = None
                await asyncio.sleep(delay)
        raise WaapiConnectionError(f"Failed to connect to WAAPI at {self.url} after {self.max_retries} attempts")

    def disconnect(self) -> None:
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
            self._client = None

    async def call(self, procedure: str, args: dict | None = None, options: dict | None = None) -> Any:
        if not self._client:
            raise WaapiConnectionError("Not connected. Call connect() first.")
        try:
            return self._client.call(procedure, args or {}, options=options)
        except Exception as e:
            logger.error(f"WAAPI call '{procedure}' failed: {e}")
            raise WaapiConnectionError(f"WAAPI call failed: {e}") from e

    async def get_info(self) -> dict:
        return await self.call("ak.wwise.core.getInfo")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
