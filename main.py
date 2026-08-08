from __future__ import annotations
import asyncio
import uvicorn
from api import app
from event_bus import event_bus
from config import settings
from signal_emulator import generate_leak_signal, create_signal_record

# Пример фонового воркера, который имитирует непрерывный опрос датчиков водоканала
async def sensor_polling_worker():
    """
    Фоновый процесс, имитирующий получение акустических сигналов с датчиков.
    В продакшене этот воркер заменяется на реальный MQTT/HTTP брокер.
    """
    print("[Worker] Запущен фоновый мониторинг акустических датчиков...")
    
    # Имитируем бесконечный цикл опроса (например, раз в 5 секунд)
    while True:
        try:
            # 1. Генерируем тестовый сигнал (как будто датчик 'sensor_krasnodar_01' прислал аудио)
            raw_signal = generate_leak_signal(duration=2.0, sample_rate=settings.SAMPLE_RATE)
            
            # 2. Формируем карточку замера (имитируем, что ИИ посчитал случайную вероятность свища для теста)
            import random
            mock_probability = round(random.uniform(10.0, 95.0), 2)
            
            record = create_signal_record(
                device_id="sensor_krasnodar_01",
                frequency=850.0,
                snr=12.4,
                probability=mock_probability
            )
            
            # 3. Публикуем событие в асинхронную шину
            # Модуль аналитики или модуль алармов подхватят эту запись без задержки основного API
            await event_bus.publish("new_telemetry", record)
            print(f"[Worker] Получен сигнал с датчика {record.device_id}. Предиктивная вероятность свища: {record.leak_probability}%")
            
            # 4. Если вероятность аварии критическая — отправляем экстренное событие
            if record.leak_probability >= 80.0:
                await event_bus.publish("critical_alarm", record)
                print(f"⚠️ [ALERT] Обнаружен высокий риск появления свища на линии датчика {record.device_id}!")

        except Exception as e:
            print(f"[Worker Error] Сбой в цикле опроса: {str(e)}")
            
        await asyncio.sleep(5.0)

# Обработчики событий для демонстрации работы Pub/Sub шины
async def log_incident_to_console(record):
    print(f"[Bus Listener] Запись телеметрии {record.record_id} успешно передана в очередь логирования.")

async def trigger_emergency_notification(record):
    print(f"🚨 [Bus Listener] ЭКСТРЕННО: Отправка PUSH-уведомления диспетчеру города! Датчик: {record.device_id}")

@app.on_event("startup")
async def startup_event():
    """Логика, запускаемая автоматически при старте веб-сервера FastAPI."""
    # Регистрируем подписчиков в шине событий
    event_bus.subscribe("new_telemetry", log_incident_to_console)
    event_bus.subscribe("critical_alarm", trigger_emergency_notification)
    
    # Запускаем бесконечный опрос датчиков как фоновую задачу asyncio
    asyncio.create_task(sensor_polling_worker())

if __name__ == "__main__":
    # Запуск веб-сервера uvicorn на порту 8000
    # Приложение будет доступно по адресу http://127.0.0.1:8000
    # Автоматическая интерактивная документация API (Swagger): http://127.0.0
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
