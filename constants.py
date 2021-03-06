from pathlib import Path
import configparser
import re
from dataclasses import dataclass, field
import sys

altair_epoch = 74240

source_path = Path(__file__).parent
config_file = source_path / 'config.ini'
validators_file = source_path / 'validators.txt'
notified_file = source_path / 'notified.json'
script_file = source_path / 'eth_sync_committee.py'

run_command = f'{sys.executable} {script_file}'
run_command_notify = f'{run_command} -n'
run_command_cron = f'{run_command_notify} -c'
send_alarm_emails = True
alarm_intervals = [1, 3, 12]

try:
    log_file = Path.home() / "sync_committee.log"
    log_str = f' > {Path.home() / "sync_committee_old.log"}'

except RuntimeError:
    log_file = source_path / "sync_committee.log"
    log_str = ''

cfg = configparser.RawConfigParser()

if not config_file.is_file():
    cfg['beacon'] = {'url': 'localhost', 'port': '5052'}
    cfg['email'] = {'from_address': '', 'from_password': '', 'to_address': ''}
    cfg['options'] = {'number_of_future_committees': '1'}

    with config_file.open('w') as f:
        cfg.write(f)

    print(f'\n config file saved with default values. open "{config_file}" to make changes.')

cfg.read(config_file)

beacon_node_url = cfg['beacon'].get('url', fallback='localhost')
beacon_node_port = cfg['beacon'].get('port', fallback='5052')

number_of_future_committees = cfg['options'].getint('number_of_future_committees', fallback=1)

base_url = f'{"" if re.match(r"^https?://", beacon_node_url) else "http://"}{beacon_node_url}'

if beacon_node_port:
    base_url += f':{beacon_node_port}'

head_url = f'{base_url}/eth/v1/beacon/states/head/sync_committees'
finalized_url = f'{base_url}/eth/v1/beacon/states/finalized/sync_committees'
block_url = f'{base_url}/eth/v2/beacon/blocks/'
genesis_url = f'{base_url}/eth/v1/beacon/genesis'


@dataclass
class EmailDetails:
    from_addr: str = cfg['email'].get('from_address')
    from_pwd: str = cfg['email'].get('from_password')
    to_addr: str = cfg['email'].get('to_address')

    are_valid: bool = field(init=False)

    def __post_init__(self):
        self.are_valid = True if self.is_valid(self.from_addr) and self.is_valid(self.to_addr) else False

    @staticmethod
    def is_valid(address):
        return True if re.match(r'[^@]+@[^@]+\.[^@]+', address) else False


email_details = EmailDetails()
