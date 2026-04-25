"""End-to-end demo: parse a Ktav document, pull out typed fields, walk
the dynamic shape, then build a fresh document in Python and render it
back to Ktav text.

Run from the repo root:

    pip install -e .            # or `pip install ktav`
    python examples/basic.py
"""

import ktav

SRC = """
service: web
port:i 8080
ratio:f 0.75
tls: true
tags: [
    prod
    eu-west-1
]
db.host: primary.internal
db.timeout:i 30
"""


def main() -> None:
    cfg = ktav.loads(SRC)

    # ── 1. Read typed fields straight off the dict. ────────────────────
    service: str = cfg["service"]
    port: int = cfg["port"]
    ratio: float = cfg["ratio"]
    tls: bool = cfg["tls"]
    tags: list[str] = cfg["tags"]
    db_host: str = cfg["db"]["host"]
    db_timeout: int = cfg["db"]["timeout"]

    print(f"service={service} port={port} tls={tls} ratio={ratio:.2f}")
    print(f"tags={tags}")
    print(f"db: {db_host} (timeout={db_timeout}s)\n")

    # ── 2. Walk the document, dispatching on the runtime type. ─────────
    print("shape:")
    for k, v in cfg.items():
        print(f"  {k:<12} -> {describe(v)}")

    # ── 3. Build a config in code, render it as Ktav text. ─────────────
    doc = {
        "name": "frontend",
        "port": 8443,
        "tls": True,
        "ratio": 0.95,
        "upstreams": [
            upstream("a.example", 1080),
            upstream("b.example", 1080),
            upstream("c.example", 1080),
        ],
        "notes": None,
    }
    rendered = ktav.dumps(doc)
    print("\n--- rendered ---")
    print(rendered, end="")


def describe(v: object) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):  # bool first — `True` is also an `int`!
        return f"bool={v}"
    if isinstance(v, int):
        return f"int={v}"
    if isinstance(v, float):
        return f"float={v}"
    if isinstance(v, str):
        return f"str={v!r}"
    if isinstance(v, list):
        return f"array({len(v)})"
    if isinstance(v, dict):
        return f"object({len(v)})"
    return type(v).__name__


def upstream(host: str, port: int) -> dict:
    return {"host": host, "port": port}


if __name__ == "__main__":
    main()
