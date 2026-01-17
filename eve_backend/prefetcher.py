import json
from pathlib import Path
from typing import Callable, Optional

from .cache import CacheManager
from .esi_client import get_character, get_corporation, fetch_character_image, fetch_corporation_logo
import logging

logger = logging.getLogger(__name__)


class CancelToken:
    def __init__(self):
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    @property
    def cancelled(self):
        return self._cancelled


class Prefetcher:
    """Prefetch character and corporation data/images for IDs found in mappings.json.

    Usage: Prefetcher().run(progress_callback=callable, cancel_token=CancelToken())
    progress_callback receives a string message.
    """

    def __init__(self, cache: Optional[CacheManager] = None, mappings_path: Optional[str] = None):
        self.cache = cache or CacheManager()
        self.mappings_path = Path(mappings_path) if mappings_path else (Path.cwd() / 'mappings.json')

    def _emit(self, cb: Optional[Callable], msg: str):
        if cb:
            try:
                cb(msg)
            except Exception:
                pass

    def run(self, progress_callback: Optional[Callable] = None, cancel_token: Optional[CancelToken] = None):
        cancel_token = cancel_token or CancelToken()
        logger.info('Prefetcher starting with mappings: %s', self.mappings_path)
        if not self.mappings_path.exists():
            self._emit(progress_callback, 'mappings.json not found')
            return {'status': 'no_mappings'}

        try:
            data = json.loads(self.mappings_path.read_text())
        except Exception:
            self._emit(progress_callback, 'failed to read mappings.json')
            return {'status': 'bad_mappings'}

        mappings = data.get('mappings', {})
        # collect unique char ids
        char_ids = set()
        for acc, info in mappings.items():
            for c in info.get('chars', []):
                char_ids.add(int(c))

        total = len(char_ids)
        i = 0
        for cid in sorted(char_ids):
            if cancel_token.cancelled:
                self._emit(progress_callback, 'cancelled')
                logger.info('Prefetcher cancelled after %s items', i)
                return {'status': 'cancelled', 'done': i}
            i += 1
            self._emit(progress_callback, f'Fetching char {cid} ({i}/{total})')
            logger.info('Prefetcher fetching char %s (%s/%s)', cid, i, total)

            # fetch JSON
            try:
                char = get_character(cid, cache=self.cache)
                logger.debug('get_character(%s) returned type=%s', cid, type(char))
            except Exception:
                char = None
                logger.exception('get_character(%s) raised', cid)

            # fetch portrait
            try:
                img_path = fetch_character_image(cid, cache=self.cache)
                logger.debug('fetch_character_image(%s) -> %s', cid, img_path)
            except Exception:
                logger.exception('Error fetching portrait for %s', cid)
            # fetch corp info if present
            corp_id = None
            if isinstance(char, dict):
                corp_id = char.get('corporation_id')
            if corp_id:
                self._emit(progress_callback, f'Fetching corp {corp_id}')
                logger.info('Prefetcher fetching corp %s for char %s', corp_id, cid)
                try:
                    corp = get_corporation(corp_id, cache=self.cache)
                    logger.debug('get_corporation(%s) returned type=%s', corp_id, type(corp))
                except Exception:
                    corp = None
                    logger.exception('Error fetching corp %s', corp_id)

                try:
                    logo = fetch_corporation_logo(corp_id, cache=self.cache)
                    logger.debug('fetch_corporation_logo(%s) -> %s', corp_id, logo)
                except Exception:
                    logger.exception('Error fetching corp logo %s', corp_id)

        self._emit(progress_callback, 'prefetch complete')
        logger.info('Prefetch complete (%s items)', total)
        return {'status': 'ok', 'done': total}
