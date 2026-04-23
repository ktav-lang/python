"""End-to-end example: parse a Ktav document, inspect, serialize back."""

import ktav

SAMPLE = """
# a small service config
port:i 8080
name: frontend

upstreams: [
    {
        host: a.example
        port:i 1080
    }
    {
        host: b.example
        port:i 1080
    }
]

# Regex needs the literal-string marker so `[` is not parsed as an array.
ip_allowlist:: [::1]

timeouts: {
    connect:f 1.5
    read:f 30.0
}
"""


def main() -> None:
    cfg = ktav.loads(SAMPLE)

    print("ktav version:", ktav.__version__)
    print("spec version:", ktav.__spec_version__)
    print()
    print(f"Service {cfg['name']!r} on port {cfg['port']}")
    print(f"  upstreams: {len(cfg['upstreams'])}")
    for u in cfg["upstreams"]:
        print(f"    - {u['host']}:{u['port']}")
    print(f"  allowlist: {cfg['ip_allowlist']!r}")
    print(f"  connect timeout: {cfg['timeouts']['connect']}s")

    # Round-trip.
    back = ktav.dumps(cfg)
    assert ktav.loads(back) == cfg
    print()
    print("--- re-serialised ---")
    print(back)


if __name__ == "__main__":
    main()
