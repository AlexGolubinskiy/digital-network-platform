-- Активация ГИС-расширения PostGIS для работы с географическими координатами
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. ТАБЛИЦА ТРУБОПРОВОДОВ (Граф сети)
CREATE TABLE IF NOT EXISTS pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipe_number VARCHAR(50) UNIQUE NOT NULL,      -- Инвентарный номер трубы в Водоканале
    material VARCHAR(30) NOT NULL,               -- Материал (steel, pnd, iron) - важно для фильтров ИИ
    diameter_mm INT NOT NULL,                     -- Диаметр трубы в миллиметрах
    length_m NUMERIC(10, 2) NOT NULL,            -- Физическая длина участка в метрах
    install_year INT,                            -- Год укладки (критический фактор износа для прогноза)
    geom GEOMETRY(LineString, 4326) NOT NULL     -- Географическая линия трубы (координаты PostGIS WGS-84)
);

-- Создание пространственного индекса для ускорения поиска труб на карте города
CREATE INDEX IF NOT EXISTS idx_pipelines_geom ON pipelines USING gist(geom);


-- 2. ТАБЛИЦА АКУСТИЧЕСКИХ ДАТЧИКОВ
CREATE TABLE IF NOT EXISTS acoustic_sensors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(50) UNIQUE NOT NULL,       -- Идентификатор физического прибора (из signal_emulator)
    status VARCHAR(20) DEFAULT 'active',         -- Статус работы (active, maintenance, offline)
    battery_level INT,                           -- Уровень заряда батареи логгера
    associated_pipe_id UUID REFERENCES pipelines(id) ON DELETE SET NULL, -- К какой трубе прикреплен
    geom GEOMETRY(Point, 4326) NOT NULL          -- Точка установки датчика на карте (колодец/камера)
);

CREATE INDEX IF NOT EXISTS idx_sensors_geom ON acoustic_sensors USING gist(geom);


-- 3. ТАБЛИЦА ТЕЛЕМЕТРИИ И МЕТРИК СИГНАЛОВ (Сюда пишет эмулятор)
CREATE TABLE IF NOT EXISTS sensor_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(50) REFERENCES acoustic_sensors(device_id) ON DELETE CASCADE,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Метрики, которые рассчитывает ваше приватное ядро core_analytics.py
    rms_amplitude NUMERIC(12, 6) NOT NULL,       -- Энергия звука
    crest_factor NUMERIC(8, 4) NOT NULL,         -- Пик-фактор (характер шума)
    dominant_frequency NUMERIC(8, 2) NOT NULL,   -- Главная частота "свиста" в Гц
    snr_db NUMERIC(6, 2) NOT NULL,               -- Соотношение сигнал/шум в децибелах
    
    -- Предиктивная аналитика
    leak_probability NUMERIC(5, 2) NOT NULL,     -- Вероятность свища от 0.00 до 100.00 %
    file_path VARCHAR(255)                       -- Путь к архивному аудиофайлу (например, "emulated.wav")
);

-- Индекс для быстрой выборки временных рядов (временного тренда) по датчику для ИИ
CREATE INDEX IF NOT EXISTS idx_telemetry_device_time ON sensor_telemetry (device_id, recorded_at DESC);


-- 4. ТАБЛИЦА ПОДТВЕРЖДЕННЫХ СВИЩЕЙ И АВАРИЙ (Ваш будущий датасет / Таргет)
CREATE TABLE IF NOT EXISTS leak_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipe_id UUID REFERENCES pipelines(id) ON DELETE CASCADE,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    leak_type VARCHAR(30) DEFAULT 'свищ',         -- Тип аварии (свищ, трещина, разрыв)
    distance_from_sensor_m NUMERIC(10, 2),       -- Расстояние, которое рассчитал core_localization.py
    geom GEOMETRY(Point, 4326) NOT NULL          -- Подтвержденная точка раскопки свища на карте
);

CREATE INDEX IF NOT EXISTS idx_incidents_geom ON leak_incidents USING gist(geom);
