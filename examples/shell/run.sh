#!/usr/bin/env bash
set -Eeuo pipefail

dry_run=false
case "$#" in
  0) ;;
  1)
    if [[ "$1" == "--dry-run" ]]; then
      dry_run=true
    else
      printf 'usage: %s [--dry-run]\n' "$0" >&2
      exit 2
    fi
    ;;
  *)
    printf 'usage: %s [--dry-run]\n' "$0" >&2
    exit 2
    ;;
esac

message=${RUNWISP_EXAMPLE_MESSAGE}
if [[ "$dry_run" == true ]]; then
  printf 'dry-run: %s\n' "$message"
else
  printf '%s\n' "$message"
fi
