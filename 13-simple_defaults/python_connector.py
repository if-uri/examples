from __future__ import annotations

import json

import urirun
from urirun import v2


connector = urirun.connector("defaults-demo", scheme="demo", meta={"area": "example"})


@connector.command("text/query/upper", meta={"label": "Uppercase text"})
def upper(text: str, suffix: str = "") -> list[str]:
    return [
        "python3",
        "-c",
        "import sys; print((sys.argv[1] + sys.argv[2]).upper())",
        "{text}",
        "{suffix}",
    ]


def bindings() -> dict:
    return connector.bindings()


def main() -> int:
    document = bindings()
    registry = v2.compile_registry(document)
    dry = v2.run("demo://host/text/query/upper", registry, {"text": "hello", "suffix": "!"})
    assert dry["result"]["command"][-2:] == ["hello", "!"]
    print(json.dumps(document, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
