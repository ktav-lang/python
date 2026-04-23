"""Micro-benchmark for ``ktav.loads`` / ``ktav.dumps``.

Not a regression-gated benchmark — just a "am I in the right ballpark?"
smoke test. Run after `maturin develop --release`.
"""

from __future__ import annotations

import time

import ktav

# 100 upstreams, 3 typed fields each — representative of a real service
# config (reverse-proxy, feature-flag store, fleet manifest, ...).
UPSTREAMS_BODY = "\n".join(
    f"    {{\n"
    f"        host: upstream-{i:03}.internal\n"
    f"        port:i {1024 + i}\n"
    f"        weight:i {i % 10 + 1}\n"
    f"    }}"
    for i in range(100)
)
TEXT = (
    f"port:i 8080\nname: frontend\ndebug: false\ntimeout:f 2.5\nupstreams: [\n{UPSTREAMS_BODY}\n]\n"
)

OBJ = ktav.loads(TEXT)


def bench(label: str, fn, iters: int = 10_000) -> None:
    # Warmup — kick the JIT-less Python loop into steady state.
    for _ in range(200):
        fn()
    t0 = time.perf_counter()
    for _ in range(iters):
        fn()
    dt = (time.perf_counter() - t0) / iters
    mb_per_s = (len(TEXT) / dt) / 1_000_000 if "loads" in label else 0
    extra = f"   ~{mb_per_s:5.0f} MB/s" if mb_per_s else ""
    print(f"  {label:20} {dt * 1e6:7.2f} µs/op{extra}")


def main() -> None:
    print(
        f"  document: {len(TEXT):>5} bytes, "
        f"{len(OBJ['upstreams'])} upstreams, "
        f"ktav {ktav.__version__}"
    )
    print()
    bench("loads", lambda: ktav.loads(TEXT))
    bench("dumps", lambda: ktav.dumps(OBJ))
    bench("roundtrip", lambda: ktav.loads(ktav.dumps(OBJ)))


if __name__ == "__main__":
    main()
