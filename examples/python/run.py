# /// script
# requires-python = ">=3.14"
# ///

import argparse
import os


parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
arguments = parser.parse_args()
message = os.environ["RUNWISP_EXAMPLE_MESSAGE"]

if arguments.dry_run:
    print(f"dry-run: {message}")
else:
    print(message)
