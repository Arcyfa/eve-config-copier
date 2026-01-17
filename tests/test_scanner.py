import json
from pathlib import Path

from eve_backend.scanner import Scanner


def make_tree(base: Path):
    logs_dir = base / 'AppData' / 'Roaming' / 'EVE Online' / 'logs'
    dat_dir = base / 'AppData' / 'Local' / 'CCP' / 'EVE'
    logs_dir.mkdir(parents=True, exist_ok=True)
    dat_dir.mkdir(parents=True, exist_ok=True)
    # create a sample log that the parser will pick up
    log = logs_dir / 'launcher.log'
    with log.open('w') as fh:
        fh.write('Fetching character details for 111, 222, 333\n')
        fh.write('Fetched 3 character details for 1000\n')
    # create dat files so Scanner considers dat_root present
    (dat_dir / 'core_user_1000.dat').write_text('user')
    (dat_dir / 'core_char_111.dat').write_text('char')
    (dat_dir / 'core_char_222.dat').write_text('char')
    (dat_dir / 'core_char_333.dat').write_text('char')
    return str(base)


def test_scan_writes_mappings(tmp_path):
    base = tmp_path / 'steam_prefix'
    base.mkdir()
    root = make_tree(base)

    scanner = Scanner()
    # run scan with our test root as extra root
    mp = tmp_path / 'mappings.json'
    res = scanner.scan(extra_roots=[root], mappings_path=str(mp))
    assert res.success
    assert mp.exists()
    data = json.loads(mp.read_text())
    assert 'mappings' in data
    assert '1000' in data['mappings']
    assert data['mappings']['1000']['chars'] == ['111', '222', '333']
