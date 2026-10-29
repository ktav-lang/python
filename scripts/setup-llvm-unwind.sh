#!/usr/bin/env bash
set -euo pipefail

source_root="$GITHUB_WORKSPACE/llvm-unwind-source"
revision=87f0227cb60147a26a1eeb4fb06e3b505e9c7261
case "${RUST_MUSL_CROSS_TARGET:?}" in
  x86_64-unknown-linux-musl) processor=x86_64; flags= ;;
  aarch64-unknown-linux-musl) processor=aarch64; flags=-mno-outline-atomics ;;
  *) printf '%s\n' 'unexpected musllinux target' >&2; return 1 ;;
esac
test "$(git -c safe.directory="$source_root" -C "$source_root" rev-parse HEAD)" = "$revision"
test -z "$(git -c safe.directory="$source_root" -C "$source_root" status --porcelain)"
build="$GITHUB_WORKSPACE/probe/llvm-unwind-build"
cmake -S "$source_root/runtimes" -B "$build" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_SYSTEM_NAME=Linux \
  -DCMAKE_SYSTEM_PROCESSOR="$processor" \
  -DCMAKE_C_COMPILER="${TARGET_CC:?}" -DCMAKE_CXX_COMPILER="${TARGET_CXX:?}" \
  -DCMAKE_ASM_COMPILER="$TARGET_CC" \
  -DCMAKE_C_FLAGS="$flags" -DCMAKE_CXX_FLAGS="$flags" \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DLLVM_DEFAULT_TARGET_TRIPLE="$RUST_MUSL_CROSS_TARGET" \
  -DLLVM_ENABLE_RUNTIMES=libunwind -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_DOCS=OFF \
  -DLIBUNWIND_ENABLE_SHARED=OFF -DLIBUNWIND_ENABLE_STATIC=ON \
  -DLIBUNWIND_HIDE_SYMBOLS=ON -DLIBUNWIND_ENABLE_ASSERTIONS=OFF
cmake --build "$build" --target unwind_static --parallel 2
export KTAV_UNWIND_ARCHIVE="$build/lib/libunwind.a"
test -s "$KTAV_UNWIND_ARCHIVE"
export KTAV_DSO_HANDLE_OBJECT="$GITHUB_WORKSPACE/probe/ktav-dso.o"
"$TARGET_CC" -fPIC -fvisibility=hidden -c scripts/musllinux-dso.c -o "$KTAV_DSO_HANDLE_OBJECT"
"$TARGET_CXX" -fPIC -fvisibility=hidden -fno-exceptions -fno-rtti -fuse-cxa-atexit \
  -c tests/fixtures/unwind-probe/crt-probe.cpp -o probe/crt-probe.o
"$TARGET_CC" -shared -nostartfiles -nodefaultlibs probe/crt-probe.o \
  "$KTAV_DSO_HANDLE_OBJECT" -lc -Wl,-Map=probe/crt-probe.map -o probe/crt_probe.so
test -z "$(git -c safe.directory="$source_root" -C "$source_root" status --porcelain)"
python3 scripts/add_llvm_unwind_notice.py "$source_root/libunwind" \
  "$KTAV_UNWIND_ARCHIVE" "$RUST_MUSL_CROSS_TARGET" \
  probe/NOTICE.json probe/NOTICE-LLVM.json
cp probe/NOTICE-LLVM.json python/ktav/_third_party/NOTICE.json
export CARGO_TARGET_X86_64_UNKNOWN_LINUX_MUSL_LINKER="$GITHUB_WORKSPACE/scripts/musllinux-unwind-linker.sh"
export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_MUSL_LINKER="$GITHUB_WORKSPACE/scripts/musllinux-unwind-linker.sh"
