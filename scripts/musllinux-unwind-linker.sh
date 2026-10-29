#!/usr/bin/env bash
set -euo pipefail

args=()
replaced=0
for arg in "$@"; do
  if [[ "$arg" == -lgcc_s ]]; then
    args+=("-Wl,-Bstatic" "-lgcc_eh" "-Wl,-Bdynamic")
    replaced=1
  else
    args+=("$arg")
  fi
done
if [[ "$replaced" != 1 ]]; then
  printf '%s\n' 'expected -lgcc_s in target link' >&2
  exit 1
fi
exec "${TARGET_CC:?}" -static-libgcc "${args[@]}"
