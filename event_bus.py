from __future__ import annotations
import asyncio
from typing import Callable, Any, Dict, List

class EventBus:
    """
    Асинхронная шина событий для обмена данными между компонентами системы.
    Позволяет изолировать логику приема сигналов от отправки алармов.
    """
    def __init__(self):
        # Хранилище подписчиков: { "event_type": [callback_function_1, callback_function_2] }
        self._listeners: Dict[str, List[Callable[[Any], Any]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[Any], Any]) -> None:
        """Подписка модуля (например, модуля алармов) на определенный тип события."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if listener not in self._listeners[event_type]:
            self._listeners[event_type].append(listener)

    def unsubscribe(self, event_type: str, listener: Callable[[Any], Any]) -> None:
        """Отписка от событий."""
        if event_type in self._listeners and listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)

    async def publish(self, event_type: str, data: Any) -> None:
        """
        Асинхронная публикация события.
        Мгновенно уведомляет все подписанные модули без блокировки основного потока.
        """
        if event_type not in self._listeners:
            return

        # Запускаем все функции-обработчики параллельно в фоне
        tasks = [
            asyncio.create_task(self._execute_listener(listener, data))
            for listener in self._listeners[event_type]
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_listener(self, listener: Callable[[Any], Any], data: Any) -> None:
        """Вспомогательный метод для безопасного вызова обработчика."""
        try:
            if asyncio.iscoroutinefunction(listener):
                await listener(data)
            else:
                listener(data)
        except Exception as e:
            # В продакшене здесь должен быть вызов логгера (logger.error)
            print(f"[EventBus Error] Сбой при обработке события {listener.__name__}: {str(e)}")

# Глобальный экземпляр шины событий для использования во всем приложении
event_bus = EventBus()
