"""Ingestion pipeline — Kafka producers/consumers + channel-specific connectors."""
from .kafka_producer import TransactionProducer
from .kafka_consumer import TransactionConsumer

__all__ = ["TransactionProducer", "TransactionConsumer"]
