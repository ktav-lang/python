#!/usr/bin/env bash
set -euo pipefail

args=()
replaced=0
for arg in "$@"; do
  if [[ "$arg" == -lgcc_s ]]; then
    test -s "${KTAV_UNWIND_ARCHIVE:?}"
    args+=("$KTAV_UNWIND_ARCHIVE")
    replaced=1
  else
    args+=("$arg")
  fi
done
if [[ "$replaced" != 1 ]]; then
  printf '%s\n' 'expected -lgcc_s in target link' >&2
  exit 1
fi
if [[ -n "${KTAV_LINK_MAP_DIR:-}" ]]; then
  mkdir -p "$KTAV_LINK_MAP_DIR"
  map="$(mktemp "$KTAV_LINK_MAP_DIR/link.XXXXXXXX")"
  chmod 644 "$map"
  args+=("-Wl,-Map=$map")
fi
test -s "${KTAV_DSO_HANDLE_OBJECT:?}"
exec "${TARGET_CC:?}" -static-libgcc "${args[@]}" -nostartfiles "$KTAV_DSO_HANDLE_OBJECT"
