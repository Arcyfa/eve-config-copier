#!/usr/bin/env python3
"""Run the Prefetcher headless and print logs to stdout.

Usage:
  EVE_BACKEND_LOG_ESI_RESPONSE=1 python3 run_prefetch.py
"""
import os
import logging
from pathlib import Path

from eve_backend.logging_setup import configure_logging

# ensure logs go to logs directory
project_root = Path(__file__).resolve().parent
logs_dir = project_root / 'logs'
logs_dir.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist
log_file = str(logs_dir / 'eve_backend.log')
configure_logging(level=logging.DEBUG, log_file=log_file)

from eve_backend.prefetcher import Prefetcher

if __name__ == '__main__':
    print('Running Prefetcher (headless). Log file:', log_file)
    p = Prefetcher()
    res = p.run(progress_callback=lambda m: print('PROG:', m))
    print('RESULT:', res)
    print('\nLast 200 lines of log:')
    try:
        with open(log_file, 'r') as fh:
            lines = fh.readlines()[-200:]
            print(''.join(lines))
    except Exception as e:
        print('Failed to read log file:', e)
