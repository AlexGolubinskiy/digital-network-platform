from __future__ import annotations
import asyncio
import random
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api import app
from event_bus import event_bus
from config import settings
from signal_emulator import generate_leak_signal, create_signal_record

# =======================================================================
# DIGITAL NETWORK PLATFORM v1.0
# BACKGROUND MONITORING WORKER & PUB/SUB ROUTING
# =======================================================================

async def sensor_polling_worker():
    """
    Фоновый процесс, имитирующий непрерывное получение акустических сигналов с датчиков.
    Полностью согласован с ГИС-моделями Pydantic и структурой таблиц schema.sql.
    """
    print("[Worker] Запущен фоновый мониторинг акустических датчиков...")
    
    # Бесконечный цикл симуляции опроса датчиков раз в 5 секунд
    while True:
        try:
            # 1. Имитируем физическое получение акустического сигнала с датчика
            raw_signal = generate_leak_signal(duration=2.0, sample_rate=settings.SAMPLE_RATE)
            
            # 2. Имитируем расчет метрик вашим приватным ядром аналитики (DSP/ИИ)
            mock_rms = round(random.uniform(0.1, 1.5), 4)
            mock_crest = round(random.uniform(2.0, 5.0), 2)
            mock_freq = round(random.uniform(700.0, 900.0), 2)
            mock_snr = round(random.uniform(5.0, 25.0), 2)
            mock_probability = round(random.uniform(10.0, 95.0), 2)
            
            # 3. Формируем архивную карточку замера со строгой Pydantic-валидацией
            record = create_signal_record(
                device_id="sensor_krasnodar_01",
                rms_amplitude=mock_rms,
                crest_factor=mock_crest,
                dominant_frequency=mock_freq,
                snr_db=mock_snr,
                leak_probability=mock_probability
            )
            
            # 4. Публикуем событие в асинхронную Pub/Sub шину
            await event_bus.publish("new_telemetry", record)
            print(f"[Worker] Сигнал {record.device_id} валидирован. RMS: {record.rms_amplitude}, Свищ: {record.leak_probability}%")
            
            # 5. Если риск аварии критический (>= 80%) — инициируем экстренный аларм
            if record.leak_probability >= 80.0:
                await event_bus.publish("critical_alarm", record)
                print(f"⚠️ [ALERT] Обнаружен высокий риск появления свища на линии датчика {record.device_id}!")

        except Exception as e:
            print(f"[Worker Error] Сбой в цикле опроса: {str(e)}")
            
        await asyncio.sleep(5.0)


# =======================================================================
# АСИНХРОННЫЕ ОБРАБОТЧИКИ СОБЫТИЙ ШИНЫ ДАННЫХ
# =======================================================================

async def log_incident_to_console(record):
    """Слушатель событий: Логирование телеметрии в общую очередь."""
    # В продакшене здесь будет асинхронный INSERT записи в таблицу sensor_telemetry базы данных
    pass

async def trigger_emergency_notification(record):
    """Слушатель критических алармов: Моментальное уведомление диспетчера."""
    print(f"🚨 [Bus Listener] ЭКСТРЕННО: Отправка PUSH-уведомления диспетчеру города! Датчик: {record.device_id}")


# =======================================================================
# СОВРЕМЕННЫЙ ЖИЗНЕННЫЙ ЦИКЛ ПРИЛОЖЕНИЯ (LIFESPAN)
# =======================================================================

@asynccontextmanager
async def platform_lifespan(app: FastAPI):
    """
    Управление запуском и остановкой фоновых задач платформы.
    Заменяет устаревший on_event('startup') для гарантированного старта воркера.
    """
    # Логика, выполняемая ПРИ СТАРТЕ сервера:
    # Регистрируем подписчиков в шине событий event_bus
    event_bus.subscribe("new_telemetry", log_incident_to_console)
    event_bus.subscribe("critical_alarm", trigger_emergency_notification)
    
    # Запускаем фонового демона опроса датчиков в неблокирующем потоке asyncio
    worker_task = asyncio.create_task(sensor_polling_worker())
    
    yield  # Здесь сервер работает и принимает внешние HTTP-запросы
    
    # Логика, выполняемая ПРИ ОСТАНОВКЕ сервера:
    # Мягко отменяем задачу фонового воркера при выключении контейнера
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        print("[Worker] Фоновый мониторинг успешно остановлен.")

# Привязываем современный lifespan-контекст к нашему приложению FastAPI
app.router.lifespan_context = platform_lifespan


# =======================================================================
# ТОЧКА СТАРТА
# =======================================================================

if __name__ == "__main__":
    # Запуск сервера на хосте 0.0.0.0 для корректной маршрутизации портов внутри Docker-контейнера
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
