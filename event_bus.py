"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

EVENT BUS

Production Event Dispatcher
=======================================================================
"""

from __future__ import annotations
from typing import Callable, Dict, List
import logging
from models import SystemEvent, EventType

logger = logging.getLogger("DigitalNetworkPlatform.EventBus")

class EventBus:
    """Центральная шина событий с изолированной защитой от падения подписчиков."""

    def __init__(self):
        self.handlers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable):
        """Регистрация функционального подписчика на тип системного события."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def publish(self, event: SystemEvent):
        """Каскадная публикация события с журналированием и пропуском ошибок."""
        listeners = self.handlers.get(event.event_type, [])
        for handler in listeners:
            try:
                handler(event)
            except Exception as error:
                logger.exception(
                    "Event handler error: %s | type=%s",
                    error,
                    event.event_type.value
                )
                continue
