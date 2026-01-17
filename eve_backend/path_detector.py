import os
import glob
import platform
from typing import List, Dict


class PathDetector:
    """Detect launcher log and DAT roots across platforms.

    Lightweight, pure-Python. Returns list of dicts with keys: root, logs, dat_root.
    """

    def __init__(self, candidate_roots: List[str] = None):
        self.candidate_roots = candidate_roots or []
        self.platform = platform.system()
        if not self.candidate_roots:
            self._populate_default_candidates()

    def _populate_default_candidates(self):
        cands = []
        if self.platform == 'Linux':
            cands += [
                '~/.steam/debian-installation/steamapps/compatdata/8500/pfx/drive_c/users/steamuser',
                '~/.local/share/Steam/steamapps/compatdata/8500/pfx/drive_c/users/steamuser',
                '~/.steam/steam/steamapps/compatdata/8500/pfx/drive_c/users/steamuser',
            ]
        elif self.platform == 'Darwin':
            cands += [
                '~/Library/Application Support/EVE Online',
                '/Applications/EVE Online.app/Contents',
            ]
        else:
            cands += [
                os.path.expandvars(r'%LOCALAPPDATA%\EVE Online'),
                r'C:\Program Files (x86)\Steam\steamapps\compatdata\8500\pfx\drive_c\users\steamuser',
            ]
        self.candidate_roots = cands

    def _expand(self, p: str) -> str:
        return os.path.expanduser(os.path.expandvars(p))

    def discover(self) -> List[Dict[str, str]]:
        found = []
        for base in self.candidate_roots:
            b = self._expand(base)
            logs_candidates = []
            logs_candidates.append(os.path.join(b, 'AppData', 'Roaming', 'EVE Online', 'logs'))
            logs_candidates.append(os.path.join(b, '.local', 'share', 'EVE Online', 'logs'))
            logs_candidates.append(os.path.join(b, 'Library', 'Application Support', 'EVE Online', 'logs'))
            logs_candidates.append(os.path.join(b, 'EVE Online', 'logs'))
            logs_candidates.append(os.path.join(b, 'logs'))

            dat_candidates = []
            dat_candidates.append(os.path.join(b, 'AppData', 'Local', 'CCP', 'EVE'))
            dat_candidates.append(os.path.join(b, 'Local', 'CCP', 'EVE'))
            dat_candidates.append(os.path.join(b, 'CCP', 'EVE'))
            dat_candidates.append(os.path.join(b, '.local', 'share', 'CCP', 'EVE'))
            dat_candidates.append(os.path.join(b, 'EVE Online', 'AppData', 'Local', 'CCP', 'EVE'))

            chosen_logs = None
            for p in logs_candidates:
                if os.path.isdir(p):
                    chosen_logs = p
                    break
            chosen_dat = None
            for d in dat_candidates:
                if os.path.isdir(d):
                    chosen_dat = d
                    break
            if chosen_logs:
                found.append({'root': b, 'logs': chosen_logs, 'dat_root': chosen_dat})
        return found

    def build_dat_index(self, dat_root: str) -> Dict[str, str]:
        idx = {}
        if not dat_root or not os.path.isdir(dat_root):
            return idx
        for p in glob.glob(os.path.join(dat_root, '**', 'core_user_*.dat'), recursive=True):
            idx[os.path.basename(p)] = p
        for p in glob.glob(os.path.join(dat_root, '**', 'core_char_*.dat'), recursive=True):
            idx[os.path.basename(p)] = p
        return idx

    def parse_logs(self, logs_dir: str) -> Dict[str, List[str]]:
        fetch_re = __import__('re').compile(r'Fetching character details for ([0-9, ]+)')
        fetched_re = __import__('re').compile(r'Fetched (\d+) character details for (\d+)')
        logs = sorted(glob.glob(os.path.join(logs_dir, '*.log')))
        recent = []
        mappings = {}
        for logfile in logs:
            try:
                with open(logfile, 'r', errors='ignore') as fh:
                    for line in fh:
                        line = line.rstrip('\n\r')
                        m = fetch_re.search(line)
                        if m:
                            chars = [c.strip() for c in m.group(1).split(',') if c.strip()]
                            recent.append(chars)
                            if len(recent) > 200:
                                recent.pop(0)
                            continue
                        m2 = fetched_re.search(line)
                        if m2:
                            count = int(m2.group(1))
                            acc = m2.group(2)
                            chosen = None
                            for chars in reversed(recent):
                                if len(chars) == count:
                                    chosen = chars
                                    break
                            if chosen is None:
                                chosen = recent[-1] if recent else []
                            mappings[acc] = chosen
            except FileNotFoundError:
                continue
        return mappings
