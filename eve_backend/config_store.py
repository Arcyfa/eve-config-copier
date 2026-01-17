import json
from pathlib import Path
from typing import Optional, Dict


class ConfigStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or (Path.cwd() / '.eve_config_copier.json')

    def load(self) -> Dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {}

    def save(self, config: Dict) -> None:
        self.path.write_text(json.dumps(config, indent=2))
