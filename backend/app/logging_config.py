"""
Structured logging setup. Never log passwords, JWT tokens, or other secrets -
routers only log identifiers (processing_id, user_id).
"""
import logging
import sys


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    # Quiet down noisy third-party loggers
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
