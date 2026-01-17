import json
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self, base: Optional[Path] = None):
        self.base = Path(base) if base else Path.cwd() / 'cache'
        # structure: cache/char, cache/corp, cache/img/char, cache/img/corp
        (self.base / 'char').mkdir(parents=True, exist_ok=True)
        (self.base / 'corp').mkdir(parents=True, exist_ok=True)
        (self.base / 'img' / 'char').mkdir(parents=True, exist_ok=True)
        (self.base / 'img' / 'corp').mkdir(parents=True, exist_ok=True)

    def json_path(self, id: str, kind: str) -> Path:
        if kind == 'char':
            return self.base / 'char' / f'{id}.json'
        if kind == 'corp':
            return self.base / 'corp' / f'{id}.json'
        raise ValueError('unknown kind')

    def image_path(self, id: str, kind: str) -> Path:
        if kind == 'char':
            return self.base / 'img' / 'char' / f'{id}.png'
        if kind == 'corp':
            return self.base / 'img' / 'corp' / f'{id}.png'
        raise ValueError('unknown kind')

    def load_json(self, id: str, kind: str) -> Optional[dict]:
        p = self.json_path(id, kind)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text())
            logger.debug('Loaded JSON cache %s/%s', kind, id)
            return data
        except Exception:
            return None

    def save_json(self, id: str, kind: str, data: dict) -> None:
        p = self.json_path(id, kind)
        p.write_text(json.dumps(data, indent=2))
        logger.info('Saved JSON cache %s/%s -> %s', kind, id, p)

    def load_image(self, id: str, kind: str) -> Optional[Path]:
        p = self.image_path(id, kind)
        if p.exists():
            logger.debug('Image cache hit %s/%s -> %s', kind, id, p)
            return p
        return None

    def save_image_bytes(self, id: str, kind: str, data: bytes) -> Path:
        p = self.image_path(id, kind)
        p.write_bytes(data)
        logger.info('Saved image cache %s/%s -> %s', kind, id, p)
        return p
