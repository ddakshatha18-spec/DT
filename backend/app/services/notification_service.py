import asyncio
import json
from typing import Any, AsyncGenerator

class NotificationService:
    """Manages active listeners and broadcasts real-time alert events."""
    _listeners: list[asyncio.Queue] = []

    @classmethod
    def subscribe(cls) -> asyncio.Queue:
        q = asyncio.Queue()
        cls._listeners.append(q)
        return q

    @classmethod
    def unsubscribe(cls, q: asyncio.Queue) -> None:
        if q in cls._listeners:
            cls._listeners.remove(q)

    @classmethod
    async def broadcast_alert(cls, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast event to all connected admin and dashboard listeners."""
        payload = json.dumps({"event": event_type, "data": data}, default=str)
        for q in list(cls._listeners):
            try:
                await q.put(payload)
            except Exception:
                pass

    @classmethod
    async def event_generator(cls, q: asyncio.Queue) -> AsyncGenerator[str, None]:
        try:
            while True:
                # Wait for next event or send heartbeat
                try:
                    message = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            cls.unsubscribe(q)
