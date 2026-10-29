#!/usr/bin/env bash
set -euo pipefail

case "${RUST_MUSL_CROSS_TARGET:?}" in
  x86_64-unknown-linux-musl) expected=975e964745276d7669f389473d5150223be491ff40217faf5676f98cd18e914a ;;
  aarch64-unknown-linux-musl) expected=0ef3ef20cc85454372d957fddf83f5fcf9a18ac6166aee251d776e3765ef64c8 ;;
  *) printf '%s\n' 'unexpected musllinux target' >&2; return 1 ;;
esac
archive="$("${TARGET_CC:?}" -print-file-name=libgcc_eh.a)"
test -f "$archive"
printf '%s  %s\n' "$expected" "$archive" | sha256sum --check
test -x "$GITHUB_WORKSPACE/scripts/musllinux-unwind-linker.sh"
export CARGO_TARGET_X86_64_UNKNOWN_LINUX_MUSL_LINKER="$GITHUB_WORKSPACE/scripts/musllinux-unwind-linker.sh"
export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_MUSL_LINKER="$GITHUB_WORKSPACE/scripts/musllinux-unwind-linker.sh"
