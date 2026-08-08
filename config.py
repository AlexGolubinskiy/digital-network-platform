from __future__ import annotations
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Класс управления конфигурацией всей платформы.
    Автоматически подтягивает переменные из .env файла или системного окружения.
    """
    # Настройки проекта
    PROJECT_NAME: str = "Digital Network Platform"
    DEBUG_MODE: bool = False
    
    # Настройки PostgreSQL + PostGIS (согласовано с вашей schema.sql)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres_password"
    DB_NAME: str = "digital_network_db"

    # Параметры аудио-архива для предиктивного ядра
    STORAGE_DIR: str = "storage/audio_records"
    SAMPLE_RATE: int = 44100  # Частота дискретизации, зафиксированная в core_analytics

    @property
    def database_url(self) -> str:
        """Формирование строки подключения для SQLAlchemy / asyncpg."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Настройки парсинга: приоритет у системных переменных, затем файл .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

# Глобальный объект настроек для импорта в api.py и database.py
settings = Settings()
