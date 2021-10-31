import requests
import re
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, InitVar
from typing import List

from constants import validators_file, finalized_url, genesis_url, block_url


def fetch_url(url):
    try:
        response = requests.get(url)

    except requests.exceptions.ConnectionError:
        print(f'\n invalid url (are you sure your beacon node is running on this machine?): {url}\n')
        exit()

    else:
        return response.json()


def get_genesis_time():
    response = fetch_url(genesis_url)
    gen_time_s = int(response['data']['genesis_time'])

    return datetime.fromtimestamp(gen_time_s, timezone.utc)


@dataclass
class Epoch:
    name: str
    epoch_number: int
    is_sync_committee: bool = False
    start_time: datetime = field(init=False)

    genesis_time: InitVar[datetime] = None

    def __post_init__(self, genesis_time: datetime):
        start_time_utc = genesis_time + timedelta(seconds=384 * self.epoch_number)
        self.start_time = start_time_utc.astimezone()


@dataclass
class SyncCommittee(Epoch):
    all_validators: List[str] = field(init=False)
    validators: List[str] = field(init=False)
    validators_str: str = field(init=False)

    my_validators: InitVar[List[str]] = None
    genesis_time: InitVar[datetime] = None

    def __post_init__(self, genesis_time: datetime, my_validators: List[str]):
        super().__post_init__(genesis_time=genesis_time)
        self.is_sync_committee = True
        response = fetch_url(f'{finalized_url}?epoch={self.epoch_number}')
        try:
            self.all_validators = sorted(response['data']['validators'], key=int)

        except KeyError:
            self.validators_str = 'validators in this sync committee are not yet known'

        else:
            self.validators = list(set(self.all_validators).intersection(set(my_validators)))
            if my_validators:
                if self.validators:
                    if len(self.validators) == 1:
                        self.validators_str = self.validators[0]

                    else:
                        self.validators_str = f'{", ".join(self.validators[:-1])} and {self.validators[-1]}'

                else:
                    self.validators_str = 'your validator isn\'t' if len(
                        my_validators) == 1 else 'none of your validators are'
                    self.validators_str += f' in the {self.name} :('

            else:
                self.validators_str = 'you haven\'t specified any validators'


def get_user_validators(user_provided):
    found_in_file = []
    if validators_file.is_file():
        with validators_file.open() as f:
            lines = [x.strip() for x in f.readlines()]

        for line in lines:
            found_in_file.extend(re.split(r'\W+', line))

        try:
            _ = [int(x) for x in found_in_file]

        except ValueError:
            print(f'\n make sure all saved validator indexes are integers: {" ".join(found_in_file)}\n')
            exit()

    my_validators = []

    if user_provided:
        try:
            _ = [int(x) for x in user_provided]

        except ValueError:
            print(f'\n make sure all provided validator indexes are integers: {" ".join(user_provided)}\n')
            exit()

        indexes = [str(x) for x in user_provided]
        my_validators.extend(indexes)
        differences = list(set(my_validators).difference(set(found_in_file)))

        if differences:
            print()
            d_str = ' you\'ve specified '
            d_str += 'validators that aren\'t' if len(differences) > 1 else 'a validator that isn\'t'
            d_str += f' in the validators file. would you like to add {"them" if len(differences) > 1 else "it"}? y/n '

            while True:
                add_confirm = input(d_str).lower()
                if add_confirm in 'yn':
                    if add_confirm == 'y':
                        found_in_file.extend(differences)
                        try:
                            my_validators = found_in_file = sorted(list(set(found_in_file)), key=int)

                        except ValueError:
                            print(my_validators)

                        with validators_file.open('w') as f:
                            f.write('\n'.join(found_in_file))
                            f.write('\n')

                    else:
                        my_validators = differences

                    break

    else:
        my_validators.extend(found_in_file)

    return sorted(my_validators, key=int)


def get_epochs(my_validators):
    response = fetch_url(f'{block_url}head')
    current_slot = int(response['data']['message']['slot'])
    current_epoch = int(current_slot / 32)
    current_sc_start_epoch = int(current_epoch / 256) * 256
    next_sc_start_epoch = current_sc_start_epoch + 256
    next_sc_2_start_epoch = current_sc_start_epoch + 512

    response = fetch_url(genesis_url)
    genesis_time =  datetime.fromtimestamp(int(response['data']['genesis_time']), timezone.utc)

    epochs = {
        'c_sync': SyncCommittee(
            name='current sync committee', epoch_number=current_sc_start_epoch,
            genesis_time=genesis_time, my_validators=my_validators
        ),
        'c_epoch': Epoch(
            name='current epoch', epoch_number=current_epoch, genesis_time=genesis_time
        ),
        'n_sync': SyncCommittee(
            name='next sync committee', epoch_number=next_sc_start_epoch,
            genesis_time=genesis_time, my_validators=my_validators
        ),
        'n_sync_2': SyncCommittee(
            name='next sync committee', epoch_number=next_sc_2_start_epoch,
            genesis_time=genesis_time, my_validators=my_validators
        )
    }

    return epochs


def print_all_validators(validators):
    start_idx = 0
    per_line = 20
    longest = len(str(validators[-1]))

    while True:
        sub_list = validators[start_idx:start_idx + per_line]
        sub_str = ''
        if sub_list:
            for val in sub_list:
                sub_str += f'{val:>{longest}}  '

            print(f'  {sub_str}')

        if start_idx > len(validators):
            break

        start_idx += per_line


def stringify_list(input_list):
    return f'{", ".join(input_list[:-1])} and {input_list[-1]}' if len(input_list) > 1 else f'{input_list[0]}'
