from pathlib import Path
import json

from eve_backend.path_detector import PathDetector


def make_tree(base: Path):
    # create a fake steam-like tree with logs and dats
    logs_dir = base / 'AppData' / 'Roaming' / 'EVE Online' / 'logs'
    dat_dir = base / 'AppData' / 'Local' / 'CCP' / 'EVE'
    logs_dir.mkdir(parents=True, exist_ok=True)
    dat_dir.mkdir(parents=True, exist_ok=True)
    # create sample log
    log = logs_dir / 'launcher.log'
    with log.open('w') as fh:
        fh.write('Some startup\n')
        fh.write('Fetching character details for 111, 222, 333\n')
        fh.write('Fetched 3 character details for 1000\n')
    # create sample dats
    (dat_dir / 'core_user_1000.dat').write_text('userdat')
    (dat_dir / 'core_char_111.dat').write_text('chardat')
    (dat_dir / 'core_char_222.dat').write_text('chardat')
    (dat_dir / 'core_char_333.dat').write_text('chardat')
    return str(base)


def test_discover_and_parse(tmp_path):
    base = tmp_path / 'steam_prefix'
    base.mkdir()
    root = make_tree(base)

    pd = PathDetector(candidate_roots=[root])
    found = pd.discover()
    assert len(found) >= 1
    item = found[0]
    assert 'logs' in item
    assert 'dat_root' in item

    mappings = pd.parse_logs(item['logs'])
    # account should be 1000 mapping to 111,222,333
    assert '1000' in mappings
    assert mappings['1000'] == ['111', '222', '333']

    idx = pd.build_dat_index(item['dat_root'])
    assert 'core_user_1000.dat' in idx
    assert 'core_char_111.dat' in idx
