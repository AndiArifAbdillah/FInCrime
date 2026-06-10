"""WebSocket real-time alert stream.

Clients connect to /ws/alerts and receive JSON messages whenever a new alert
is broadcast. Use `broadcast_alert(...)` from anywhere in the codebase to push.
"""
from __future__ import annotations

import asyncio
from src.common.utils import utc_now
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.common.logger import get_logger

log = get_logger("api.ws")

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        log.info("ws.connected", clients=len(self.connections))
        await ws.send_json({
            "type": "welcome",
            "ts": utc_now().isoformat(),
            "message": "Connected to FinCrime alert stream",
        })

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)
        log.info("ws.disconnected", clients=len(self.connections))

    async def broadcast(self, payload: dict):
        dead: list[WebSocket] = []
        for ws in self.connections:
            try:
                await ws.send_json(payload)
            except Exception as e:
                log.warning("ws.send_failed", error=str(e))
                dead.append(ws)
        for d in dead:
            self.disconnect(d)


manager = ConnectionManager()


@router.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive; clients can also send pings.
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=30)
                if msg == "ping":
                    await ws.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                await ws.send_json({"type": "heartbeat",
                                    "ts": utc_now().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ------- helper to push from anywhere -------
async def broadcast_alert(*, severity: str, title: str, subtitle: str,
                          source: str = "system", data: Optional[dict] = None):
    """Broadcast a new alert to all connected websocket clients."""
    payload = {
        "type": "alert",
        "ts": utc_now().isoformat(),
        "severity": severity,
        "title": title,
        "subtitle": subtitle,
        "source": source,
        "data": data or {},
    }
    await manager.broadcast(payload)


# ------- demo endpoint to test broadcasting -------
@router.post("/v1/alerts/test-broadcast")
async def test_broadcast(severity: str = "high", title: str = "Test alert"):
    """Trigger a test broadcast (for verifying client subscription)."""
    await broadcast_alert(
        severity=severity, title=title,
        subtitle=f"Manual test from API at {utc_now().isoformat()}",
        source="manual_test",
    )
    return {"ok": True, "subscribers": len(manager.connections)}
