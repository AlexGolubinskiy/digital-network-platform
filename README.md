# Digital Network Platform "ЦРО" v1.0

[English](#english) | [Русский](#русский)

---

## Русский

**«ЦРО v1.0» (Цифровой Реестр Объектов)** — интеллектуальная программно-аппаратная платформа непрерывного нейросетевого мониторинга, локализации скрытых утечек и предиктивного управления бюджетами ТОиР распределенных промышленных и муниципальных инженерных сетей.

> 📄 **Интеллектуальная собственность:** Технология находится под государственной защитой приоритета. Подана официальная заявка на изобретение в Роспатент **№ 2026160185 от 21.07.2026 г.** Международный патентный классификатор: **МПК G01M 3/24** (Акустические методы тестирования герметичности трубопроводов).

### Архитектура платформы (4 ИИ-Модуля)
1. **«ЦРО-Водоканал» (Контур гидроакустики):** Круглосуточный удаленный прием сырых аудиофайлов (`SensorPacket`) с NB-IoT логгеров. Использование алгоритмов обобщенной взаимной корреляции **GCC-PHAT с параболической интерполяцией пика** для субдискретной локализации свища с точностью до **±1.5 метров на 100 метров трубы**.
2. **«ЦРО-Теплосеть» (Контур упреждающего ремонта):** Интеграция с КИПиА котельных и обработка данных инфракрасной аэросъемки с БПЛА для предиктивного мониторинга аномального расхода теплоносителя. Фильтрация нестационарных индустриальных шумов методом Баттерворта 4-го порядка с защитой Найквиста.
3. **«ЦРО-Цифровой Шлюз» (Контур оптимизации CAPEX):** Уникальный аналитический движок (`criticality_engine.py`) на основе Матрицы критичности активов. Перемножает физический риск износа на экономический ущерб прорыва ($Priority = Physical\_Risk \times Economic\_Impact$). Автоматически приоритизирует бюджеты ТОиР в условиях дефицита средств.
4. **«ЦРО-ЭкоМониторинг» (Контур муниципального расширения):** Нейросетевой анализ видеопотоков городских камер (контроль ТКО) и спутниковых снимков для выявления незаконных вырубок и изменения кадастровых контуров (KPI Указа Президента РФ № 309).

### Спецификация Backend API (FastAPI / PostgreSQL)

Платформа принимает данные с IoT-регистраторов через защищенный REST API эндпоинт `/api/v1/sensors/packet`.

#### Пример входящего JSON-пакета от датчика (03:00 ночи):
```json
{
  "sensor_id": "snr-nlet-042",
  "timestamp": "2026-08-08T03:00:00Z",
  "battery_voltage": 3.65,
  "signal_to_noise_ratio": 14.2,
  "raw_audio_payload_hex": "A4F3E299FF00B2...",
  "buffer_status": {
    "is_delayed_by_uav_attack": false,
    "cached_packets_count": 0
  }
}
```

#### Пример ответа сервера с расчетом приоритета ремонта:
```json
{
  "status": "success",
  "analysis": {
    "leak_detected": true,
    "distance_from_node_a_meters": 42.15,
    "confidence_score": 0.94,
    "criticality": {
      "impact_level": "CRITICAL",
      "priority_score": 0.60,
      "recommendation": "КРИТИЧЕСКИЙ ПРИОРИТЕТ. Участок под причалом АО 'НЛЭ'. Ремонт в течение 48 часов для предотвращения простоя терминала."
    }
  }
}
```

### Инструкция по локальному развертыванию
```bash
# 1. Клонировать репозиторий
git clone https://github.com
cd digital-network-platform

# 2. Создать и активировать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить модульные тесты ядра ЦОС и движка критичности
pytest -v
```

---

## English

**"ЦРО v1.0" (Digital Object Registry)** is an intelligent software and hardware platform for continuous neural network monitoring, localized leak detection, and predictive maintenance (MRO/CAPEX) budget optimization for distributed industrial and municipal utility networks.

> 📄 **Intellectual Property:** Protected by state priority. Official invention patent application filed with Rospatent **No. 2026160185 dated 07/21/2026**. IPC Class: **G01M 3/24** (Testing tightness of tubes by acoustic means).

### Platform Architecture (4 AI Modules)
1. **"ЦРО-Водоканал" (Hydroacoustic Core):** 24/7 remote ingestion of raw audio logs (`SensorPacket`) from NB-IoT loggers. Employs **GCC-PHAT algorithms with parabolic peak interpolation** for sub-discrete leak localization with an accuracy of **±1.5 meters per 100 meters of pipe**.
2. **"ЦРО-Теплосеть" (District Heating Core):** Integration with boiler facility automation (ASU TP/KIIP) and processing of UAV infrared aerial photography data. Implements 4th-order Butterworth bandpass filtering with Nyquist protection to eliminate non-stationary industrial noise.
3. **"ЦРО-Цифровой Шлюз" (CAPEX Optimization Engine):** A specialized analytical framework (`criticality_engine.py`) based on an Asset Criticality Matrix. Multiplies physical degradation risks by economic failure impacts ($Priority = Physical\_Risk \times Economic\_Impact$), automatically ranking repair schedules under strict budget constraints.
4. **"ЦРО-ЭкоМониторинг" (Environmental Expansion):** Neural network video analytics for municipal camera streams (waste management) and automated pixel-by-pixel satellite imagery comparison for land boundary and forestry tracking (aligned with Russian Presidential Decree No. 309).

### Backend API Specification (FastAPI / PostgreSQL)

The platform ingests telemetry from IoT hardware via a secure REST API endpoint `/api/v1/sensors/packet`.

#### Input JSON Packet Format (03:00 AM Sync):
```json
{
  "sensor_id": "snr-nlet-042",
  "timestamp": "2026-08-08T03:00:00Z",
  "battery_voltage": 3.65,
  "signal_to_noise_ratio": 14.2,
  "raw_audio_payload_hex": "A4F3E299FF00B2...",
  "buffer_status": {
    "is_delayed_by_uav_attack": false,
    "cached_packets_count": 0
  }
}
```

#### Server Response with Maintenance Task Prioritization:
```json
{
  "status": "success",
  "analysis": {
    "leak_detected": true,
    "distance_from_node_a_meters": 42.15,
    "confidence_score": 0.94,
    "criticality": {
      "impact_level": "CRITICAL",
      "priority_score": 0.60,
      "recommendation": "CRITICAL PRIORITIZED TASK. Section located under NLE Port berth. Schedule repair within 48 hours to prevent terminal downtime."
    }
  }
}
```

### Local Deployment Guide
```bash
# 1. Clone the repository
git clone https://github.com
cd digital-network-platform

# 2. Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Execute unit tests for DSP and Criticality Engine
pytest -v
```
