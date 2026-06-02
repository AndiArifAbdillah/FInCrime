"""Kafka producer for streaming transactions into the FinCrime pipeline.

Gracefully no-ops if kafka-python isn't installed (useful for local dev).
"""
from __future__ import annotations

import json
from typing import Optional

try:
    from kafka import KafkaProducer
    _KAFKA_OK = True
except ImportError:
    _KAFKA_OK = False

from src.common.config import settings
from src.common.logger import get_logger
from src.common.schemas import Transaction, Channel

log = get_logger("ingestion.producer")


class TransactionProducer:
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self._producer = None
        if _KAFKA_OK:
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                    key_serializer=lambda k: k.encode("utf-8") if k else None,
                    acks="all",
                    retries=3,
                )
                log.info("kafka.producer.connected", servers=self.bootstrap_servers)
            except Exception as e:
                log.warning("kafka.producer.unavailable", error=str(e))
                self._producer = None
        else:
            log.warning("kafka.producer.skipped — kafka-python not installed")

    def _topic_for(self, channel: str) -> str:
        return {
            Channel.BANK.value: settings.kafka_topic_bank,
            Channel.EWALLET.value: settings.kafka_topic_ewallet,
            Channel.CRYPTO.value: settings.kafka_topic_crypto,
        }.get(channel, settings.kafka_topic_bank)

    def send(self, tx: Transaction) -> bool:
        if not self._producer:
            log.debug("kafka.producer.dry_run", tx_id=tx.tx_id)
            return False
        topic = self._topic_for(tx.channel)
        self._producer.send(topic, key=tx.tx_id, value=tx.model_dump())
        return True

    def flush(self):
        if self._producer:
            self._producer.flush()

    def close(self):
        if self._producer:
            self._producer.close()
