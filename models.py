"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

MODELS LAYER

Базовые структуры данных платформы.

Важно:
Этот файл НЕ импортирует config.py.
Он является нижним уровнем архитектуры.
=======================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

# ============================================================
# NETWORK & SENSOR ENUMS
# ============================================================
class NetworkType(Enum):
    HEAT = "heat"
    WATER = "water"
    GAS = "gas"
    INDUSTRIAL = "industrial"

class SensorType(Enum):
    ACOUSTIC = "acoustic"
    PRESSURE = "pressure"
    FLOW = "flow"
    TEMPERATURE = "temperature"
    VIBRATION = "vibration"
    GPS = "gps"

class DeviceStatus(Enum):
    ACTIVE = "active"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class AssetCondition(Enum):
    NORMAL = "normal"
    AGING = "aging"
    CRITICAL = "critical"

class PipeMaterial(Enum):
    STEEL = "steel"
    CAST_IRON = "cast_iron"
    PLASTIC = "plastic"

class MaintenanceStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class EventType(Enum):
    SIGNAL_DATA_RECEIVED = "signal_data_received"
    ALARM_CREATED = "alarm_created"
    RISK_UPDATED = "risk_updated"
    MAINTENANCE_CREATED = "maintenance_created"

# ============================================================
# DATA STRUCTURES & MODEL CLASSES
# ============================================================
@dataclass
class Coordinate:
    latitude: float
    longitude: float
    altitude: float = 0.0

@dataclass
class Device:
    device_id: str
    name: str
    sensor_type: SensorType
    coordinate: Coordinate
    network_type: NetworkType
    organization: str = "АТЭК"
    status: DeviceStatus = DeviceStatus.ACTIVE
    installation_date: Optional[str] = None
    last_signal_time: Optional[str] = None
    metadata: dict = field(default_factory=dict)

@dataclass
class AudioData:
    signal: object
    sample_rate: int
    duration: float = 0.0

@dataclass
class SignalRecord:
    record_id: str
    device_id: str
    timestamp: datetime
    frequency: float
    snr: float
    probability: float
    file_path: str
    metadata: dict = field(default_factory=dict)

@dataclass
class AnalysisResult:
    anomaly_detected: bool
    probability: float
    description: str
    parameters: dict = field(default_factory=dict)

@dataclass
class NetworkAsset:
    asset_id: str
    name: str
    length: float
    installation_year: int
    material: PipeMaterial
    sensor_ids: list[str]
    metadata: dict = field(default_factory=dict)

@dataclass
class AssetRiskResult:
    asset_id: str
    risk_score: float
    condition: AssetCondition
    factors: dict
    recommendation: str

@dataclass
class AlarmLocation:
    coordinate: Coordinate
    distance_from_start: float
    confidence: float

@dataclass
class Alarm:
    alarm_id: str
    device_id: str
    network_type: NetworkType
    location: AlarmLocation
    analysis: AnalysisResult
    created_at: datetime
    status: str = "active"

@dataclass
class LocalizationResult:
    delay_seconds: float
    distance_to_leak: float
    valid: bool
    confidence: float = 0.0

@dataclass
class PredictionResult:
    device_id: str
    risk_score: float
    trend: str
    factors: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MaintenanceTask:
    task_id: str
    asset_id: str
    priority: str
    description: str
    status: MaintenanceStatus = MaintenanceStatus.OPEN
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

@dataclass
class SystemEvent:
    event_id: str
    event_type: EventType
    data: dict
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "Unknown"
