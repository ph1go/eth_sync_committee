import requests
import re
import smtplib, ssl

from email.message import EmailMessage
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, InitVar
from typing import List
from crontab import CronTab

from constants import (
    validators_file, config_file, log_file,
    run_command, run_command_notify, run_command_cron,
    send_alarm_emails, alarm_intervals,
    finalized_url, genesis_url, block_url,
    email_details, altair_epoch, number_of_future_committees
)


def fetch_url(url):
    # print(url)
    try:
        response = requests.get(url)

    except requests.exceptions.ConnectionError:
        print(f'\n invalid url (are you sure your beacon node is running on this machine?): {url}\n')
        exit()

    else:
        return response.json()


@dataclass
class Epoch:
    name: str
    name_with_num: str = field(init=False)
    epoch_number: int
    is_sync_committee: bool = False
    start_time: datetime = field(init=False)
    end_time: datetime = field(init=False)
    start_str: str = field(init=False, default='')
    end_str: str = field(init=False, default='')
    validators_str: str = field(init=False)

    genesis_time: InitVar[datetime] = None

    def __post_init__(self, genesis_time: datetime):
        _epoch = self.epoch_number - (int(int(self.epoch_number / 256)) * 256) + 1
        self.name_with_num = f'{self.name} epoch ({_epoch} of 256)'
        start_time_utc = genesis_time + timedelta(seconds=384 * self.epoch_number)
        self.start_time = start_time_utc.astimezone()
        start_from_now = (self.start_time - datetime.now().astimezone()).total_seconds()

        if start_from_now > 0:
            self.start_str = (
                f'{self.start_time.strftime("%Y/%m/%d %H:%M:%S")} ({seconds_to_hms(start_from_now)} from now)'
            )

        end_time_utc = genesis_time + timedelta(seconds=384 * (self.epoch_number + 256))
        self.end_time = end_time_utc.astimezone()
        end_from_now = (self.end_time - datetime.now().astimezone()).total_seconds()
        self.end_str = f'{self.end_time.strftime("%Y/%m/%d %H:%M:%S")} ({seconds_to_hms(end_from_now)} from now)'
        self.validators_str = 'n/a'


@dataclass
class SyncCommittee(Epoch):
    sync_committee_number: int = field(init=False)
    all_validators: List[str] = field(init=False, default_factory=list)
    validators: List[str] = field(init=False, default_factory=list)

    my_validators: InitVar[List[str]] = None
    check_for_validators: InitVar[bool] = True

    def __post_init__(self, genesis_time: datetime, my_validators: List[str], check_for_validators: bool):
        super().__post_init__(genesis_time=genesis_time)
        self.sync_committee_number = int((self.epoch_number - altair_epoch) / 256)
        self.name_with_num = f'sync committee {self.sync_committee_number}{f" ({self.name})" if self.name else ""}'
        self.is_sync_committee = True
        if check_for_validators:
            response = fetch_url(f'{finalized_url}?epoch={self.epoch_number}')

            try:
                self.all_validators = sorted(response['data']['validators'], key=int)

            except KeyError:
                self.validators_str = 'validators in this sync committee are not yet known'

            else:
                self.validators = sorted(list(set(self.all_validators).intersection(set(my_validators))), key=int)
                if my_validators:
                    if self.validators:
                        self.validators_str = stringify_list(self.validators)

                    else:
                        self.validators_str = (
                            'your validator isn\'t' if len(my_validators) == 1 else 'none of your validators are'
                        )
                        self.validators_str += f' in the {self.name} sync committee :('

                else:
                    self.validators_str = 'you haven\'t specified any validators'

        else:
            self.validators_str = 'validators in this sync committee are not yet known'


def get_epochs(my_validators):
    response = fetch_url(f'{block_url}head')
    current_slot = int(response['data']['message']['slot'])
    current_epoch = int(current_slot / 32)
    current_sc_start_epoch = int(current_epoch / 256) * 256
    next_sc_start_epoch = current_sc_start_epoch + 256

    response = fetch_url(genesis_url)
    genesis_time = datetime.fromtimestamp(int(response['data']['genesis_time']), timezone.utc)

    epochs = [
        SyncCommittee(
            name='current', epoch_number=current_sc_start_epoch,
            genesis_time=genesis_time, my_validators=my_validators
            ),
        Epoch(
            name='current', epoch_number=current_epoch, genesis_time=genesis_time
            ),
        SyncCommittee(
            name='next', epoch_number=next_sc_start_epoch,
            genesis_time=genesis_time, my_validators=my_validators
        )
    ]

    if number_of_future_committees:
        for c in range(number_of_future_committees):
            epochs.append(
                SyncCommittee(
                    name='', epoch_number=next_sc_start_epoch + ((c + 1) * 256),
                    genesis_time=genesis_time, my_validators=my_validators,
                    check_for_validators=True if c == 0 else False
                )
            )

    return epochs


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
    return f'{", ".join(input_list[:-1])} and {input_list[-1]}' if len(input_list) > 1 else input_list[0]


def seconds_to_hms(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    t_str = ''
    if days:
        t_str += f'{days}d{" " if hours or minutes or seconds else ""}'

    if hours:
        t_str += f'{hours}h{" " if minutes or seconds else ""}'

    if minutes:
        t_str += f'{minutes}m{" " if seconds else ""}'

    if seconds:
        t_str += f'{seconds}s'

    return t_str


def pluralise(input_num):
    return "s" if input_num > 1 else ""


def send_email(msg):
    port = 465
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', port, context=context) as server:
        server.login(email_details.from_addr, email_details.from_pwd)
        server.send_message(msg)


def generate_notification(current_committee, next_committee):
    in_current = True if current_committee.validators else False
    in_next = True if next_committee.validators else False
    in_both = True if in_current and in_next else False
    num_current = len(current_committee.validators)
    num_next = len(next_committee.validators)
    num_both = num_current + num_next

    v_str = 'validators are' if num_both > 1 else 'validator is'

    v_msg_1 = '\n one or more of your validators are in the '

    if in_current and not in_next:
        v_msg_1 += 'current sync committee!'
        v_msg_2 = (
            f'to maximise your rewards (and avoid increased penalties), make sure your {v_str}\n '
            f'online until {current_committee.end_str}.')

    elif in_next and not in_current:
        v_msg_1 += 'next sync committee!'
        v_msg_2 = (
            f'the next sync committee runs from {next_committee.start_str} until\n '
            f'{next_committee.end_str}. to maximise your rewards (and avoid\n '
            f'increased penalties), make sure your {v_str} online between these times.'
        )

    else:
        v_msg_1 += 'current and next sync committees!'
        v_msg_2 = (
            f'to maximise your rewards (and avoid increased penalties), make sure your {v_str}\n '
            f'online until {next_committee.end_str}.'
        )

    if in_current or in_next or in_both:
        print(f'{v_msg_1}\n\n {v_msg_2}')

    if email_details.are_valid:
        msg = EmailMessage()

        msg['subject '] = (
            f'You have {"validators" if num_both > 1 else "a validator"} in the '
            f'{"current and next" if in_both else "current" if in_current else "next"} '
            f'sync committee{"s" if in_both else ""}!'
        )

        body = ''

        if num_current:
            body += (
                f'sync committee: current\n'
                f'validators: {current_committee.validators_str}\n'
                f'committee end time: {current_committee.end_str}'
            )

        if num_next:
            body += "\n\n" if num_current else ""
            body += (
                f'sync committee: next\n'
                f'validators: {next_committee.validators_str}\n'
                f'committee start time: {next_committee.start_str}\n'
                f'committee end time: {next_committee.end_str}'
            )

        a = v_msg_2.replace("\n ", "\n")
        body += f'\n\n{a}'

        msg.set_content(body)
        msg['From'] = email_details.from_addr
        msg['To'] = email_details.to_addr

        send_email(msg)

    else:
        print(
            f'\n invalid/missing email credentials. add your email credentials and the destination '
            f'address to the config file ({config_file}) \n in order to send notification emails.'
        )


def add_cron_job(next_start_time, in_next_committee=False):
    c_str = ''

    cron_test = CronTab(user=True)
    try:
        cron_test.write()

    except OSError:
        c_str += ' crontab not found...'

    else:
        cron = CronTab(user=True)
        cron.remove_all(command=run_command)

        if in_next_committee and send_alarm_emails and alarm_intervals:
            for i in sorted(alarm_intervals, reverse=True):
                a_time = next_start_time - timedelta(hours=i)
                job = cron.new(command=run_command_notify, comment=f'{i}h alarm')
                job.setall(a_time)
                c_str += f' added {i}h alarm cron job: {a_time.strftime("%Y/%m/%d %H:%M")}\n'

        two_epochs_in = next_start_time + timedelta(seconds=(12 * 32 * 2))
        m_time = two_epochs_in + timedelta(minutes=2 if two_epochs_in.second > 40 else 1)

        job = cron.new(command=run_command_cron, comment='added by eth_sync_committee.py')
        job.setall(m_time)
        c_str += f' added cron job for next run: {m_time.strftime("%Y/%m/%d %H:%M")}'

        cron.write()

    return c_str


def write_log(log_file_str):
    with log_file.open('a') as f:
        f.write(log_file_str)
