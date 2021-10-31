from pathlib import Path

source_path = Path(__file__).parent
validators_file = source_path / 'validators.txt'

base_url = 'http://localhost:5052'
head_url = base_url + '/eth/v1/beacon/states/head/sync_committees'
finalized_url = base_url + '/eth/v1/beacon/states/finalized/sync_committees'
block_url = base_url + '/eth/v2/beacon/blocks/'
genesis_url = base_url + '/eth/v1/beacon/genesis'
