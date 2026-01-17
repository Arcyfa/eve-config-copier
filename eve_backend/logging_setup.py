import logging
import os
from pathlib import Path


def configure_logging(log_file: str = None, level: int = logging.INFO):
    """Configure root logger: stream + optional file handler.

    Behavior:
    - If the environment variable `EVE_BACKEND_LOG_LEVEL` is set, it overrides `level`.
    - By default writes to ./eve_backend.log when log_file is not provided.
    """
    root = logging.getLogger()
    if root.handlers:
        return

    # allow override from env var
    env_level = os.getenv('EVE_BACKEND_LOG_LEVEL')
    if env_level:
        try:
            lvl = getattr(logging, env_level.upper(), None)
            if isinstance(lvl, int):
                level = lvl
            else:
                # fallback to numeric conversion
                level = int(env_level)
        except Exception:
            pass

    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    # File-only logging: write all logs to a file, do not attach stream/console handlers.

    # allow override of log file via env var
    env_file = os.getenv('EVE_BACKEND_LOG_FILE')
    if not log_file:
        # default to project root logs directory (two levels above the package directory)
        project_root = Path(__file__).resolve().parents[1]
        logs_dir = project_root / 'logs'
        logs_dir.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist
        log_file = env_file or str(logs_dir / "eve_backend.log")
    try:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception:
        # fallback: ignore file handler errors
        # no console logging per policy; if file handler fails, silently continue
        pass
