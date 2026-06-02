"""Kafka consumer that pulls transactions and feeds them to Layer 1 in real-time."""
from __future__ import annotations

import json
from typing import Iterator, Optional

try:
    from kafka import KafkaConsumer
    _KAFKA_OK = True
except ImportError:
    _KAFKA_OK = False

from src.common.config import settings
from src.common.logger import get_logger
from src.common.schemas import Transaction

log = get_logger("ingestion.consumer")


class TransactionConsumer:
    def __init__(self, topics: Optional[list[str]] = None,
                 group_id: str = "fincrime-layer1",
                 bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.topics = topics or [
            settings.kafka_topic_bank,
            settings.kafka_topic_ewallet,
            settings.kafka_topic_crypto,
        ]
        self._consumer = None
        if not _KAFKA_OK:
            log.warning("kafka.consumer.skipped — kafka-python not installed")
            return
        try:
            self._consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            log.info("kafka.consumer.subscribed", topics=self.topics)
        except Exception as e:
            log.warning("kafka.consumer.unavailable", error=str(e))
            self._consumer = None

    def __iter__(self) -> Iterator[Transaction]:
        if not self._consumer:
            return iter([])
        for msg in self._consumer:
            try:
                yield Transaction(**msg.value)
            except Exception as e:
                log.warning("consumer.bad_msg", error=str(e))
                continue
