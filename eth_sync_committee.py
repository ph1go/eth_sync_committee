#!/usr/bin/python

import argparse
from functions import get_user_validators, get_epochs, print_all_validators, stringify_list, generate_notification

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--print-all', action='store_true')
    parser.add_argument('-v', '--validators', nargs='*', action='store', type=str)

    args = parser.parse_args()

    my_validators = get_user_validators(user_provided=args.validators)
    epochs = get_epochs(my_validators=my_validators)

    if my_validators:
        check_str = f' checking validator{"s" if len(my_validators) > 1 else ""}: {stringify_list(my_validators)}'

    else:
        check_str = ' no validators specified.'

    print(f'\n{check_str}')

    longest_name = len(max([x.name_with_num for x in epochs], key=len))
    longest_val_str = len(max([x.validators_str for x in epochs], key=len))

    print(
        f'\n {" " * longest_name} {"epoch":>7}   {"start date & time":^19}   validators\n'
        f' {"-" * (longest_name + 33 + longest_val_str)}'
    )

    for e in epochs:
        print(
            f' {e.name_with_num:{longest_name}} {e.epoch_number:>7}   '
            f'{e.start_time.strftime("%Y/%m/%d %H:%M:%S")}   '
            f'{e.validators_str if e.is_sync_committee else "n/a"}'
        )

    current_committee = [e for e in epochs if e.name == 'current'][0]
    next_committee = [e for e in epochs if e.name == 'next'][0]

    if current_committee.validators or next_committee.validators:
        generate_notification(current_committee=current_committee, next_committee=next_committee)

    if args.print_all:
        for committee in [current_committee, next_committee]:
            print(f'\n {committee.name_with_num}:\n')
            print_all_validators(committee.all_validators)

    print()