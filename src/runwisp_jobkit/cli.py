from __future__ import annotations

import argparse
import pathlib
import sys
from collections.abc import Mapping, Sequence

from .execution import doctor_lines, execute_job, prepare_job
from .manifest import JobConfigurationError, load_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="runwisp-job")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("job_dir", type=pathlib.Path)
    run_parser.add_argument("job_args", nargs=argparse.REMAINDER)

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("job_dir", type=pathlib.Path)

    return parser


def main(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> int:
    arguments = build_parser().parse_args(argv)
    label = arguments.job_dir.name
    try:
        manifest = load_manifest(arguments.job_dir)
        label = manifest.job_id
        if arguments.command == "run":
            prepared = prepare_job(manifest, arguments.job_args, environ)
        else:
            prepared = prepare_job(manifest, environ=environ)
    except JobConfigurationError as error:
        print(f"runwisp-job: {label}: {error}", file=sys.stderr)
        return 2

    if arguments.command == "run":
        return execute_job(prepared, environ)

    for line in doctor_lines(prepared):
        print(line)
    return 0


def entrypoint() -> None:
    raise SystemExit(main())
