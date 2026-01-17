import logging
import os
from typing import Optional
from urllib.parse import urljoin

from .cache import CacheManager

logger = logging.getLogger(__name__)
# control whether to log full ESI responses (set env EVE_BACKEND_LOG_ESI_RESPONSE=1)
LOG_ESI_RESPONSES = os.getenv('EVE_BACKEND_LOG_ESI_RESPONSE', '0').lower() in ('1', 'true', 'yes')


ESI_BASE = 'https://esi.evetech.net/latest/'
IMG_BASE = 'https://images.evetech.net/'


def get_character(character_id: int, cache: Optional[CacheManager] = None) -> Optional[dict]:
    cache = cache or CacheManager()
    cid = str(character_id)
    cached = cache.load_json(cid, 'char')
    if cached:
        logger.debug('Character %s cache hit', cid)
        return cached
    # import requests lazily to avoid hard dep on import time
    import requests
    url = f'https://esi.evetech.net/latest/characters/{character_id}'
    try:
        logger.info('Fetching character %s from ESI', cid)
        logger.debug('Request URL: %s', url)
        r = requests.get(url, timeout=10)
        logger.debug('ESI response for character %s: %s', cid, r.status_code)
        if LOG_ESI_RESPONSES:
            try:
                logger.debug('ESI response body for %s: %s', cid, r.text[:4000])
            except Exception:
                logger.debug('Failed to read response body for %s', cid)
        if r.status_code == 200:
            data = r.json()
            cache.save_json(cid, 'char', data)
            logger.info('Cached character %s JSON', cid)
            return data
    except Exception:
        logger.exception('Failed to fetch character %s', cid)
    return None


def get_corporation(corporation_id: int, cache: Optional[CacheManager] = None) -> Optional[dict]:
    cache = cache or CacheManager()
    cid = str(corporation_id)
    cached = cache.load_json(cid, 'corp')
    if cached:
        logger.debug('Corporation %s cache hit', cid)
        return cached
    import requests
    url = f'https://esi.evetech.net/latest/corporations/{corporation_id}'
    try:
        logger.info('Fetching corporation %s from ESI', cid)
        logger.debug('Request URL: %s', url)
        r = requests.get(url, timeout=10)
        logger.debug('ESI response for corp %s: %s', cid, r.status_code)
        if LOG_ESI_RESPONSES:
            try:
                logger.debug('ESI response body for corp %s: %s', cid, r.text[:4000])
            except Exception:
                logger.debug('Failed to read corp response body for %s', cid)
        if r.status_code == 200:
            data = r.json()
            cache.save_json(cid, 'corp', data)
            logger.info('Cached corporation %s JSON', cid)
            return data
    except Exception:
        logger.exception('Failed to fetch corporation %s', cid)
    return None


def fetch_character_image(character_id: int, size: int = 64, cache: Optional[CacheManager] = None):
    cache = cache or CacheManager()
    cid = str(character_id)
    img = cache.load_image(cid, 'char')
    if img:
        logger.debug('Character image %s cache hit', cid)
        return img
    import requests
    url = f'{IMG_BASE}characters/{character_id}/portrait?size={size}'
    logger.debug('Request URL: %s', url)
    r = requests.get(url, timeout=10)
    try:
        logger.info('Fetching character image %s', cid)
        logger.debug('Image response status for %s: %s', cid, r.status_code)
        if LOG_ESI_RESPONSES:
            try:
                logger.debug('Image response length for %s: %s', cid, len(r.content))
            except Exception:
                logger.debug('Failed to read image content length for %s', cid)
        if r.status_code == 200:
            path = cache.save_image_bytes(cid, 'char', r.content)
            logger.info('Saved character image %s -> %s', cid, path)
            return path
    except Exception:
        logger.exception('Failed to fetch character image %s', cid)
    return None


def fetch_corporation_logo(corporation_id: int, size: int = 64, cache: Optional[CacheManager] = None):
    cache = cache or CacheManager()
    cid = str(corporation_id)
    img = cache.load_image(cid, 'corp')
    if img:
        logger.debug('Corporation logo %s cache hit', cid)
        return img
    import requests
    url = f'{IMG_BASE}corporations/{corporation_id}/logo?size={size}'
    logger.debug('Request URL: %s', url)
    r = requests.get(url, timeout=10)
    try:
        logger.info('Fetching corporation logo %s', cid)
        logger.debug('Corp logo response status for %s: %s', cid, r.status_code)
        if LOG_ESI_RESPONSES:
            try:
                logger.debug('Corp logo response length for %s: %s', cid, len(r.content))
            except Exception:
                logger.debug('Failed to read corp logo content length for %s', cid)
        if r.status_code == 200:
            path = cache.save_image_bytes(cid, 'corp', r.content)
            logger.info('Saved corp logo %s -> %s', cid, path)
            return path
    except Exception:
        logger.exception('Failed to fetch corp logo %s', cid)
    return None
