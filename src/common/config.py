"""Centralized configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_env: str = Field(default="development")
    app_log_level: str = Field(default="INFO")
    app_data_dir: Path = Field(default=Path("./data"))
    app_models_dir: Path = Field(default=Path("./data/models"))

    # --- Neo4j ---
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="fincrime-dev-password")

    # --- Blockchain ---
    etherscan_api_key: str = Field(default="")
    eth_rpc_url: str = Field(default="")

    # --- Kafka ---
    kafka_bootstrap_servers: str = Field(default="localhost:9092")
    kafka_topic_bank: str = Field(default="fincrime.bank.transactions")
    kafka_topic_ewallet: str = Field(default="fincrime.ewallet.transactions")
    kafka_topic_crypto: str = Field(default="fincrime.crypto.transactions")
    kafka_topic_alerts: str = Field(default="fincrime.alerts")

    # --- API ---
    # Secure default: bind loopback only. Docker/production overrides via
    # API_HOST=0.0.0.0 (docker/Dockerfile.api already passes --host explicitly).
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000)
    api_secret_key: str = Field(default="change-me")
    api_cors_origins: str = Field(default="http://localhost:8501")

    # --- PPATK ---
    ppatk_endpoint: str = Field(default="")
    ppatk_api_key: str = Field(default="")
    ppatk_institution_code: str = Field(default="BANK001")

    # --- Thresholds ---
    risk_score_high: float = Field(default=70.0)
    risk_score_critical: float = Field(default=85.0)
    fraud_anomaly_threshold: float = Field(default=0.7)
    gnn_layering_threshold: float = Field(default=0.6)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

    def ensure_dirs(self) -> None:
        for d in (self.app_data_dir, self.app_models_dir,
                  self.app_data_dir / "raw",
                  self.app_data_dir / "processed",
                  self.app_data_dir / "sample"):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def _load() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s


settings = _load()
