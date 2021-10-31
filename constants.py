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

beacon_node_url = cfg["beacon"].get("url", fallback="localhost")
beacon_node_port = cfg["beacon"].get("port", fallback="5052")

base_url = f'http://{beacon_node_url}:{beacon_node_port}'
head_url = f'{base_url}/eth/v1/beacon/states/head/sync_committees'
finalized_url = f'{base_url}/eth/v1/beacon/states/finalized/sync_committees'
block_url = f'{base_url}/eth/v2/beacon/blocks/'
genesis_url = f'{base_url}/eth/v1/beacon/genesis'
