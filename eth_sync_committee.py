#!/usr/bin/python

import argparse
from functions import get_user_validators, get_epochs, print_all_validators, stringify_list

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

    longest_name = len(max([epochs[x].name for x in epochs], key=len))
    print(f'\n {" " * longest_name} {"epoch":>8}   {"start date & time":^19}   validators')
    for k in ['c_sync', 'c_epoch', 'n_sync', 'n_sync_2']:
        print(
            f' {epochs[k].name:{longest_name}} {epochs[k].epoch_number:8}   '
            f'{epochs[k].start_time.strftime("%Y/%m/%d %H:%M:%S")}   '
            f'{epochs[k].validators_str if epochs[k].is_sync_committee else "n/a"}'
        )

    if args.print_all:
        for k in ['c_sync', 'n_sync']:
            print(f'\n {epochs[k].name}:\n')
            print_all_validators(epochs[k].all_validators)

    print()