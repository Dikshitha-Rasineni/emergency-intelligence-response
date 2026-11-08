"""WebSocket fan-out to authorized control rooms. Single-process (use Redis pub/sub for multi-worker)."""
import asyncio
import json
from collections import defaultdict
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket

from app.core.logging import logger


class ConnectionManager:
    def __init__(self) -> None:
        self.by_dept: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self, ws: WebSocket, department: str) -> None:
        await ws.accept()
        self.by_dept[department].add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        for conns in self.by_dept.values():
            conns.discard(ws)

    def connected_count(self, department: str) -> int:
        return len(self.by_dept.get(department, ()))

    async def _send(self, department: str, message: Dict[str, Any]) -> int:
        sent = 0
        for ws in list(self.by_dept.get(department, ())):
            try:
                await ws.send_text(json.dumps(message, default=str))
                sent += 1
            except Exception:
                self.disconnect(ws)
        return sent

    def publish(self, department: str, message: Dict[str, Any]) -> int:
        """Thread-safe, non-blocking publish from sync code. Returns the number of open sockets the
        message was queued for. Requests never wait for delivery (a slow client cannot stall a click)."""
        targets = [department] + (["ADMIN"] if department != "ADMIN" else [])
        if not self.loop or not self.loop.is_running():
            return 0
        n = 0
        for dep in targets:
            conns = self.by_dept.get(dep)
            if not conns:
                continue
            if dep == department:
                n = len(conns)
            try:
                if asyncio.get_running_loop() is self.loop:  # called on the loop itself: schedule
                    self.loop.create_task(self._send(dep, message))
                    continue
            except RuntimeError:
                pass  # not inside an event loop (normal case: worker thread)
            fut = asyncio.run_coroutine_threadsafe(self._send(dep, message), self.loop)
            fut.add_done_callback(lambda f, d=dep: f.exception() and logger.warning(f"websocket publish to {d} failed: {f.exception()}"))
        return n


manager = ConnectionManager()
