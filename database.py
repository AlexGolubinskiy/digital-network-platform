"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

DATABASE ENGINE

SQLite persistence layer
=======================================================================
"""

from __future__ import annotations
import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH, DATA_DIR
from models import Device, NetworkAsset, SignalRecord, Alarm, MaintenanceTask

class Database:
    """Центральное хранилище данных платформы на базе СУБД SQLite."""

    def __init__(self, path=DATABASE_PATH):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Обеспечиваем многопоточность и доступ к данным по именам колонок таблицы
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        """Инициализация структуры таблиц реляционной базы данных."""
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS devices
            (
                device_id TEXT PRIMARY KEY,
                name TEXT,
                sensor_type TEXT,
                network_type TEXT,
                organization TEXT,
                latitude REAL,
                longitude REAL,
                status TEXT,
                created_at TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS signals
            (
                record_id TEXT PRIMARY KEY,
                device_id TEXT,
                timestamp TEXT,
                frequency REAL,
                snr REAL,
                probability REAL,
                file_path TEXT,
                metadata TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assets
            (
                asset_id TEXT PRIMARY KEY,
                name TEXT,
                length REAL,
                installation_year INTEGER,
                material TEXT,
                sensor_ids TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alarms
            (
                alarm_id TEXT PRIMARY KEY,
                device_id TEXT,
                network_type TEXT,
                latitude REAL,
                longitude REAL,
                distance REAL,
                confidence REAL,
                probability REAL,
                status TEXT,
                created_at TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance
            (
                task_id TEXT PRIMARY KEY,
                asset_id TEXT,
                priority TEXT,
                description TEXT,
                status TEXT,
                created_at TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events
            (
                event_id TEXT PRIMARY KEY,
                event_type TEXT,
                timestamp TEXT,
                payload TEXT
            )
            """
        )
        self.connection.commit()

    def save_device(self, device: Device):
        """Сохранение или обновление параметров измерительного прибора."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO devices
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                device.device_id,
                device.name,
                device.sensor_type.value,
                device.network_type.value,
                device.organization,
                device.coordinate.latitude,
                device.coordinate.longitude,
                device.status.value,
                datetime.now().isoformat()
            )
        )
        self.connection.commit()

    def save_signal(self, record: SignalRecord):
        """Запись архивной карточки сырого сигнала на диск СУБД."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO signals
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.record_id,
                record.device_id,
                record.timestamp.isoformat(),
                record.frequency,
                record.snr,
                record.probability,
                record.file_path,
                json.dumps(record.metadata, ensure_ascii=False)
            )
        )
        self.connection.commit()

    def save_asset(self, asset: NetworkAsset):
        """Запись или обновление параметров цифрового паспорта участка сети."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO assets
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                asset.asset_id,
                asset.name,
                asset.length,
                asset.installation_year,
                asset.material.value,
                json.dumps(asset.sensor_ids)
            )
        )
        self.connection.commit()

    def save_alarm(self, alarm: Alarm):
        """Запись зарегистрированной аварийной утечки."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO alarms
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alarm.alarm_id,
                alarm.device_id,
                alarm.network_type.value,
                alarm.location.coordinate.latitude,
                alarm.location.coordinate.longitude,
                alarm.location.distance_from_start,
                alarm.location.confidence,
                alarm.analysis.probability,
                alarm.status,
                alarm.created_at.isoformat()
            )
        )
        self.connection.commit()

    def save_maintenance(self, task: MaintenanceTask):
        """Запись наряда-задания для ремонтных бригад ТОиР."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO maintenance
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task.task_id,
                task.asset_id,
                task.priority,
                task.description,
                task.status.value,
                task.created_at.isoformat()
            )
        )
        self.connection.commit()

    def save_event(self, event_id: str, event_type: str, payload: dict):
        """Логирование системных событий в сквозной исторический архив."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO events
            VALUES (?, ?, ?, ?)
            """,
            (
                event_id,
                event_type,
                datetime.now().isoformat(),
                json.dumps(payload, ensure_ascii=False)
            )
        )
        self.connection.commit()
