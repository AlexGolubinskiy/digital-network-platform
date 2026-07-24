"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

CONFIGURATION LAYER

Настройки системы и профили инженерных сетей.

Важно:
Этот файл использует модели,
но модели не знают о конфигурации.
=======================================================================
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from models import NetworkType

# ============================================================
# APPLICATION METADATA
# ============================================================
APP_NAME = "Digital Network Platform"
VERSION = "1.0.0"

# ============================================================
# DIRECTORIES & PATHS
# ============================================================
BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
SIGNAL_DIR = DATA_DIR / "signals"
REPORT_DIR = DATA_DIR / "reports"
LOG_DIR = BASE_DIR / "logs"

DATABASE_PATH = DATA_DIR / "network_platform.db"

def init_directories():
    """Создание рабочих директорий платформы."""
    directories = [DATA_DIR, CACHE_DIR, SIGNAL_DIR, REPORT_DIR, LOG_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# ============================================================
# NETWORK PROFILE STRUCTURE
# ============================================================
@dataclass
class NetworkProfile:
    """Параметры и физические свойства конкретной инженерной сети."""
    name: str
    network_type: NetworkType
    frequency_min: float
    frequency_max: float
    sample_rate: int
    sound_velocity: float
    snr_threshold: float
    description: str = ""

# ============================================================
# PRODUCTION NETWORKS PROFILES
# ============================================================
HEAT_PROFILE = NetworkProfile(
    name="Тепловая сеть",
    network_type=NetworkType.HEAT,
    frequency_min=400.0,
    frequency_max=1200.0,
    sample_rate=8000,
    sound_velocity=1450.0,
    snr_threshold=10.0,
    description="Поиск скрытых утечек теплоносителя"
)

WATER_PROFILE = NetworkProfile(
    name="Водопроводная сеть",
    network_type=NetworkType.WATER,
    frequency_min=200.0,
    frequency_max=900.0,
    sample_rate=8000,
    sound_velocity=1480.0,
    snr_threshold=8.0,
    description="Контроль утечек воды"
)

GAS_PROFILE = NetworkProfile(
    name="Газовая сеть",
    network_type=NetworkType.GAS,
    frequency_min=500.0,
    frequency_max=3000.0,
    sample_rate=16000,
    sound_velocity=430.0,
    snr_threshold=12.0,
    description="Акустический контроль газовых магистралей"
)
