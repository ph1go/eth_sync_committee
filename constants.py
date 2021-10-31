from pathlib import Path
import configparser

source_path = Path(__file__).parent
config_file = source_path / 'config.ini'
validators_file = source_path / 'validators.txt'

cfg = configparser.RawConfigParser()

if not config_file.is_file():
    cfg['beacon'] = {'url': 'localhost', 'port': '5052'}

    with config_file.open('w') as f:
        cfg.write(f)

    print(f'\n config file saved with default values. open "{config_file}" to make changes.')

cfg.read(config_file)

base_url = f'http://{cfg["beacon"].get("url", fallback="localhost")}:{cfg["beacon"].get("port", fallback="5052")}'
head_url = base_url + '/eth/v1/beacon/states/head/sync_committees'
finalized_url = base_url + '/eth/v1/beacon/states/finalized/sync_committees'
block_url = base_url + '/eth/v2/beacon/blocks/'
genesis_url = base_url + '/eth/v1/beacon/genesis'