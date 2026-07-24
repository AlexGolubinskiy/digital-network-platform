"""
=======================================================================
DIGITAL NETWORK PLATFORM v1.0

REST API (FastAPI)

Промышленный REST API для платформы автоматического обнаружения утечек.

=======================================================================
"""

from __future__ import annotations

import logging

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import HEAT_PROFILE, init_directories

from models import (
    Coordinate,
    Device,
    SensorType,
    NetworkType,
)

from database import Database
from event_bus import EventBus

from dsp import DSPEngine
from analysis import AnalysisEngine
from localization import LocalizationEngine
from geo import GeoEngine
from pipeline import SignalProcessingPipeline


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("DigitalNetworkPlatform.API")


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Digital Network Platform API",
    version="1.0.0",
    description="REST API промышленной платформы обнаружения утечек"
)


# ============================================================
# PLATFORM INITIALIZATION
# ============================================================

init_directories()

profile = HEAT_PROFILE

database = Database()

event_bus = EventBus()

geo = GeoEngine()

pipeline = SignalProcessingPipeline(
    profile=profile,
    dsp_engine=DSPEngine(profile),
    analysis_engine=AnalysisEngine(profile),
    localization_engine=LocalizationEngine(),
    geo_engine=geo,
    database=database,
    event_bus=event_bus,
)


# ============================================================
# REQUEST MODEL
# ============================================================

class TelemetryRequest(BaseModel):
    """
    Телеметрия пары датчиков.
    """

    device_id_a: str = Field(...)

    lat_a: float = Field(...)

    lon_a: float = Field(...)

    device_id_b: str = Field(...)

    lat_b: float = Field(...)

    lon_b: float = Field(...)

    signal_a: list[float]

    signal_b: list[float]


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "Digital Network Platform",
        "version": "1.0.0",
        "status": "running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/v1/health")
def health():

    return {

        "status": "green",

        "profile": profile.name,

        "sample_rate": profile.sample_rate,

        "supported_networks": [
            "heat",
            "water",
            "gas"
        ],

        "supported_sensors": [
            "acoustic",
            "pressure"
        ]
    }


# ============================================================
# ANALYZE
# ============================================================

@app.post("/api/v1/analyze")
def analyze(request: TelemetryRequest):

    logger.info(
        "Incoming request: %s <-> %s",
        request.device_id_a,
        request.device_id_b,
    )

    try:

        device_a = Device(
            device_id=request.device_id_a,
            name=f"Sensor {request.device_id_a}",
            sensor_type=SensorType.ACOUSTIC,
            coordinate=Coordinate(
                latitude=request.lat_a,
                longitude=request.lon_a,
            ),
            network_type=NetworkType.HEAT,
        )

        device_b = Device(
            device_id=request.device_id_b,
            name=f"Sensor {request.device_id_b}",
            sensor_type=SensorType.ACOUSTIC,
            coordinate=Coordinate(
                latitude=request.lat_b,
                longitude=request.lon_b,
            ),
            network_type=NetworkType.HEAT,
        )

        signal_a = np.asarray(
            request.signal_a,
            dtype=np.float64,
        )

        signal_b = np.asarray(
            request.signal_b,
            dtype=np.float64,
        )

        section_length = geo.distance(
            device_a.coordinate,
            device_b.coordinate,
        )

        alarm = pipeline.process(
            device_a,
            device_b,
            signal_a,
            signal_b,
            section_length,
        )

        if alarm is None:
            raise RuntimeError(
                "Pipeline returned no Alarm object."
            )

        logger.info(
            "Alarm created: %s",
            alarm.alarm_id,
        )
                # ========================================================
        # RESPONSE
        # ========================================================

        return {

            "success": True,

            "alarm": {

                "alarm_id":
                    alarm.alarm_id,

                "anomaly_detected":
                    alarm.analysis.anomaly_detected,

                "probability":
                    round(
                        float(alarm.analysis.probability),
                        4
                    ),

                "description":
                    alarm.analysis.description,
            },

            "location": {

                "distance_from_sensor_a":
                    round(
                        float(
                            alarm.location.distance_from_start
                        ),
                        2
                    ),

                "latitude":
                    round(
                        float(
                            alarm.location.coordinate.latitude
                        ),
                        6
                    ),

                "longitude":
                    round(
                        float(
                            alarm.location.coordinate.longitude
                        ),
                        6
                    ),

                "confidence":
                    round(
                        float(
                            alarm.location.confidence
                        ),
                        4
                    ),
            },

            "pipe": {

                "length":
                    round(
                        float(section_length),
                        2
                    )
            }
        }

    except Exception as error:

        logger.exception(
            "Pipeline execution failed."
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# VERSION
# ============================================================

@app.get("/api/v1/version")
def version():

    return {

        "platform":
            "Digital Network Platform",

        "version":
            "1.0.0",

        "api":
            "REST",

        "status":
            "stable"
    }


# ============================================================
# INFO
# ============================================================

@app.get("/api/v1/info")
def info():

    return {

        "profile":
            profile.name,

        "sample_rate":
            profile.sample_rate,

        "frequency_range": {

            "min":
                profile.frequency_min,

            "max":
                profile.frequency_max,
        },

        "processing": [

            "DSP",

            "Analysis",

            "Localization",

            "Prediction",

            "Digital Twin"
        ]
    }


# ============================================================
# DATABASE
# ============================================================

@app.get("/api/v1/database")
def database_status():

    return {

        "database":

            "connected",

        "engine":

            "SQLite",

        "thread_safe":

            True
    }


# ============================================================
# EVENT BUS
# ============================================================

@app.get("/api/v1/eventbus")
def event_bus_status():

    return {

        "status":
            "running",

        "subscribers":
            len(event_bus.subscribers)
    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
