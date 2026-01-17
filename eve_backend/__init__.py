from .path_detector import PathDetector
from .scanner import Scanner
from .config_store import ConfigStore
from .cache import CacheManager
from .prefetcher import Prefetcher, CancelToken
from .logging_setup import configure_logging

# configure logging on import (safe no-op if already configured)
# default to DEBUG during development; can be overridden by EVE_BACKEND_LOG_LEVEL
import logging as _logging
# use a less-verbose default (INFO). Can be overridden via EVE_BACKEND_LOG_LEVEL.
configure_logging(level=_logging.INFO)

__all__ = ["PathDetector", "Scanner", "ConfigStore", "CacheManager", "Prefetcher", "CancelToken"]
