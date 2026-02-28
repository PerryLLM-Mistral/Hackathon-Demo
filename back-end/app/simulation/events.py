from __future__ import annotations

from typing import Callable, Any, List


class EventBus:
    """
    Minimal observable/event bus.

    - Simulation emits events (TurnDelta or other dicts).
    - Listeners can subscribe callbacks.
    - Later: WebSocket layer will subscribe and broadcast.
    """

    def __init__(self):
        self._subscribers: List[Callable[[Any], None]] = []

    def subscribe(self, callback: Callable[[Any], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, event: Any) -> None:
        for cb in self._subscribers:
            cb(event)