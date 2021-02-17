#! /usr/bin/env python3
"""Firmware implementing shell that echoes line inputs."""

import argparse
import sys


PARSER = argparse.ArgumentParser()
PARSER.add_argument('skip_first_prompt', type=bool, default=False, nargs='?')
PARSER.add_argument('--prompt', type=str, default="> ")


def main(skip_first_prompt=False, prompt="> "):
    """Print some header and echo the output."""
    if not skip_first_prompt:
        print('Starting RIOT Ctrl')
        print('This example shell will echo')
    else:
        print(input())
        print()
    while True:
        print(input(prompt))
        print()


if __name__ == '__main__':
    args = PARSER.parse_args()
    sys.exit(main(**vars(args)))
