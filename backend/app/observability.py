from __future__ import annotations

import logging
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)
_langfuse = None


def init_langfuse() -> Any:
    global _langfuse
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        logger.info("Langfuse is disabled because credentials are not configured.")
        return None

    try:
        from langfuse import Langfuse

        _langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        logger.info("Langfuse initialized successfully.")
        return _langfuse
    except Exception as exc:  # pragma: no cover - safe fallback
        logger.warning("Langfuse initialization failed: %s", exc)
        return None


def get_langfuse() -> Any:
    return _langfuse
