#!/usr/bin/env python3
"""Forward a sum request to the bundled producer executable."""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Request a sum from the producer.")
    commands = parser.add_subparsers(dest="command", required=True)
    sum_command = commands.add_parser("sum", help="add two integers from 0 through 9")
    sum_command.add_argument("a", help="first integer, 0 through 9")
    sum_command.add_argument("b", help="second integer, 0 through 9")
    arguments = parser.parse_args()

    producer = Path(__file__).resolve().with_name("producer")
    try:
        result = subprocess.run([str(producer), arguments.a, arguments.b], check=False)
    except OSError as error:
        print(f"Cannot run producer: {error}", file=sys.stderr)
        return 1

    return result.returncode if result.returncode >= 0 else 128 - result.returncode


if __name__ == "__main__":
    sys.exit(main())
