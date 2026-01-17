import json
import os
from pathlib import Path
from typing import List, Dict, Optional

from .path_detector import PathDetector


class ScanResult:
    def __init__(self, success: bool, mappings_path: Optional[str], summary: Dict, errors: List[str] = None):
        self.success = success
        self.mappings_path = mappings_path
        self.summary = summary
        self.errors = errors or []


class Scanner:
    def __init__(self, detector: Optional[PathDetector] = None):
        self.detector = detector or PathDetector()

    def scan(self, extra_roots: List[str] = None, mappings_path: str = None, progress_callback=None) -> ScanResult:
        # combine candidate_roots with extras
        if extra_roots:
            self.detector.candidate_roots = list(dict.fromkeys(extra_roots + self.detector.candidate_roots))

        roots = self.detector.discover()
        if not roots:
            return ScanResult(False, None, {'found_roots': 0}, errors=['no_roots'])

        final_out = {}
        used_dat_roots = []
        used_logs_dirs = []

        for info in roots:
            logs_dir = info['logs']
            dat_root = info.get('dat_root')
            mappings = self.detector.parse_logs(logs_dir)
            dat_index = self.detector.build_dat_index(dat_root)
            if dat_index and dat_root:
                used_dat_roots.append(os.path.realpath(dat_root))
            if logs_dir:
                used_logs_dirs.append(os.path.realpath(logs_dir))
            for acc, chars in mappings.items():
                final_out[acc] = {'chars': chars}

        out_json = {
            'dat_roots': list(dict.fromkeys(used_dat_roots)),
            'logs_dirs': list(dict.fromkeys(used_logs_dirs)),
            'mappings': final_out,
        }

        mp = mappings_path or str(Path.cwd() / 'mappings.json')
        try:
            with open(mp, 'w') as fh:
                json.dump(out_json, fh, indent=2)
        except Exception as e:
            return ScanResult(False, None, {'found_roots': len(roots)}, errors=[str(e)])

        return ScanResult(True, mp, {'found_roots': len(roots), 'accounts': len(final_out)})
