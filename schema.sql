-- ============================================================================
-- SQL SCHEMA FOR DIGITAL NETWORK PLATFORM "ЦРО" v1.0
-- Database: PostgreSQL 15+
-- Patent Application: No. 2026160185 (IPC G01M 3/24)
-- Author: Alex Golubinskiy (c) 2026
-- ============================================================================

-- Enable UUID extension for secure distributed task assignment (Module 3)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ENUMS & DICTIONARIES
CREATE TYPE asset_material_type AS ENUM ('STEEL', 'CAST_IRON', 'HDPE_PLASTIC');
CREATE TYPE economic_impact_level AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE task_priority_status AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

-- 2. INFRASTRUCTURE ASSETS TABLE (Module 1 & 2 Passportization)
CREATE TABLE network_assets (
    asset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,                               -- Название (Причал №3, Магистраль Больницы)
    material asset_material_type NOT NULL,                     -- Материал (Сталь, Чугун, Пластик)
    diameter_mm INT NOT NULL CHECK (diameter_mm > 0),         -- Диаметр трубы
    length_meters NUMERIC(10, 2) NOT NULL,                    -- Длина контролируемого участка
    criticality_level economic_impact_level DEFAULT 'MEDIUM', -- Весовой коэффициент ущерба (Матрица КИИ)
    geom_start_lat NUMERIC(9, 6) NOT NULL,                    -- ГИС координаты: Начало участка (Колодец А)
    geom_start_lon NUMERIC(9, 6) NOT NULL,
    geom_end_lat NUMERIC(9, 6) NOT NULL,                      -- ГИС координаты: Конец участка (Колодец Б)
    geom_end_lon NUMERIC(9, 6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. IOT HARDWARE REGISTRY (Module 1 & 2 Firmware Sync)
CREATE TABLE iot_sensors (
    sensor_id VARCHAR(50) PRIMARY KEY,                         -- Серийный номер регистратора (IP68)
    linked_asset_id UUID REFERENCES network_assets(asset_id) ON DELETE SET NULL,
    installation_depth_meters NUMERIC(4, 2) DEFAULT 0.0,
    battery_level_voltage NUMERIC(4, 2) NOT NULL,             -- Контроль разряда батареи автономного логгера
    firmware_version VARCHAR(20) NOT NULL,                    -- Версия микропрограммы асинхронного сна
    last_ping_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. HYDROACOUSTIC PACKETS STORAGE (Module 1 Ingestion Core - 03:00 AM Sync)
CREATE TABLE sensor_telemetry_packets (
    packet_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(50) NOT NULL REFERENCES iot_sensors(sensor_id) ON DELETE CASCADE,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,            -- Таймстамп записи (строго 03:00 ночи)
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Таймстамп фактического приема сервером
    snr_value NUMERIC(5, 2) NOT NULL,                          -- Отношение сигнал/шум для ИИ-фильтрации
    raw_audio_payload_hex TEXT NOT NULL,                      -- Сжатый бинарный аудио-лог шума свища
    is_delayed_by_uav_attack BOOLEAN DEFAULT FALSE,           -- Флаг РЭБ-буферизации (атака БПЛА / глушение связи)
    cached_days_count INT DEFAULT 0                           -- Количество дней хранения лога в автономной Flash-памяти
);

-- 5. AI LEAK DETECTION & RISK MATRIX OUTPUT (Module 3 & 4 Analytics)
CREATE TABLE predictive_maintenance_tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES network_assets(asset_id) ON DELETE CASCADE,
    trigger_packet_id UUID REFERENCES sensor_telemetry_packets(packet_id) ON DELETE SET NULL,
    leak_detected BOOLEAN DEFAULT FALSE,
    confidence_score NUMERIC(4, 3) CHECK (confidence_score BETWEEN 0 AND 1), -- ИИ индекс уверенности модели
    calculated_distance_meters NUMERIC(10, 2),                -- Субдискретная локализация GCC-PHAT (метры от колодца А)
    physical_risk_score NUMERIC(4, 3) NOT NULL,               -- Физическая вероятность прорыва (0.0 - 1.0)
    final_priority_score NUMERIC(4, 3) NOT NULL,              -- Сквозной индекс для Директора (Риск * Ущерб)
    priority_status task_priority_status NOT NULL,            -- Ранжированный статус (Критический/Высокий/Плановый)
    automated_recommendation TEXT NOT NULL,                   -- Текстовая b2b-директива для подрядчика порта
    is_verified_by_field_geophone BOOLEAN DEFAULT FALSE,      -- Подтверждение течеискателем-слухалкой на поверхности
    is_repaired BOOLEAN DEFAULT FALSE,                        -- Закрытие наряда-допуска казначейским сплитом
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- CREATE INDEXES FOR MAXIMUM FASTAPI/POSTGRESQL PERFORMANCE
CREATE INDEX idx_assets_criticality ON network_assets(criticality_level);
CREATE INDEX idx_telemetry_sensor_time ON sensor_telemetry_packets(sensor_id, recorded_at DESC);
CREATE INDEX idx_tasks_priority ON predictive_maintenance_tasks(final_priority_score DESC, is_repaired);
