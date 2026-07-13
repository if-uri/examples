#!/usr/bin/env python3
"""Validate and run the examples CI manifest."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shlex
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

EXAMPLE_RE = re.compile(r"^\d{2}-[A-Za-z0-9_.-]+$")
RUNNABLE = {"host", "docker"}
SKIPPED = {"service", "hardware", "self-hosted", "manual", "external-secret"}
CLASSES = RUNNABLE | SKIPPED


def numbered_dirs(root: Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if p.is_dir() and EXAMPLE_RE.match(p.name))


def _simple_yaml_manifest(path: Path) -> dict[str, dict[str, str]]:
    current: str | None = None
    examples: dict[str, dict[str, str]] = {}
    in_examples = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "examples:":
            in_examples = True
            continue
        if not in_examples:
            raise ValueError(f"unsupported top-level key in {path}: {stripped}")
        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current = stripped[:-1]
            examples[current] = {}
            continue
        if current and line.startswith("    ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            examples[current][key.strip()] = value
            continue
        raise ValueError(f"unsupported manifest syntax in {path}: {raw}")
    return examples


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    try:
        import yaml  # type: ignore
    except Exception:
        return _simple_yaml_manifest(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    examples = data.get("examples")
    if not isinstance(examples, dict):
        raise ValueError(f"{path} must contain an 'examples' mapping")
    return examples


def validate_manifest(root: Path, manifest_path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    manifest = load_manifest(manifest_path)
    errors: list[str] = []
    dirs = set(numbered_dirs(root))
    names = set(manifest)
    for name in sorted(dirs - names):
        errors.append(f"Unclassified example: {name}\nAdd it to ci/examples-manifest.yml.")
    for name in sorted(names - dirs):
        errors.append(f"Manifest entry does not match an example directory: {name}")
    for name in sorted(names & dirs):
        entry = manifest[name]
        klass = entry.get("class")
        command = entry.get("command")
        reason = entry.get("skip_reason")
        if klass not in CLASSES:
            errors.append(f"{name}: invalid class {klass!r}; expected one of {sorted(CLASSES)}")
        if klass in RUNNABLE and not command:
            errors.append(f"{name}: class {klass!r} requires command")
        if klass in SKIPPED and not reason:
            errors.append(f"{name}: skipped class {klass!r} requires skip_reason")
        if command and any(token in str(command) for token in ("\n", "\r")):
            errors.append(f"{name}: command must be a single shell command line")
    return manifest, errors


def run_one(root: Path, name: str, entry: dict[str, Any], out_dir: Path, timeout: int) -> dict[str, Any]:
    command = str(entry["command"])
    log_dir = out_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    env = os.environ.copy()
    pythonpath = str(root.parent / "urirun" / "adapters" / "python")
    env["PYTHONPATH"] = pythonpath + os.pathsep + env.get("PYTHONPATH", "")
    cp: subprocess.CompletedProcess[str] | None = None
    error = ""
    try:
        cp = subprocess.run(
            command,
            cwd=root / name,
            shell=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            env=env,
        )
        rc = cp.returncode
    except subprocess.TimeoutExpired as exc:
        rc = 124
        error = f"timeout after {timeout}s"
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
    else:
        stdout = cp.stdout
        stderr = cp.stderr
    elapsed = time.time() - started
    log = log_dir / f"{name}.log"
    log.write_text(
        f"$ {command}\n# cwd: {root / name}\n# exit: {rc}\n\n[stdout]\n{stdout}\n\n[stderr]\n{stderr}\n",
        encoding="utf-8",
    )
    return {
        "name": name,
        "class": entry["class"],
        "command": command,
        "status": "passed" if rc == 0 else "failed",
        "returncode": rc,
        "duration": round(elapsed, 3),
        "log": str(log),
        "error": error or (stderr.strip().splitlines()[-1] if rc != 0 and stderr.strip() else ""),
    }


def junit(results: list[dict[str, Any]], target: Path) -> None:
    suite = ET.Element("testsuite", name="examples-manifest", tests=str(len(results)))
    failures = 0
    skipped = 0
    for result in results:
        case = ET.SubElement(
            suite,
            "testcase",
            name=result["name"],
            classname=f"examples.{result['class']}",
            time=str(result.get("duration", 0)),
        )
        if result["status"] == "failed":
            failures += 1
            fail = ET.SubElement(case, "failure", message=result.get("error") or "command failed")
            fail.text = Path(result["log"]).read_text(encoding="utf-8", errors="replace")[-8000:]
        elif result["status"] == "skipped":
            skipped += 1
            ET.SubElement(case, "skipped", message=result.get("skip_reason") or "skipped")
    suite.set("failures", str(failures))
    suite.set("skipped", str(skipped))
    ET.ElementTree(suite).write(target, encoding="utf-8", xml_declaration=True)


def markdown(results: list[dict[str, Any]], target: Path, urirun_sha: str, examples_sha: str) -> None:
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    lines = [
        "# Examples Compatibility Summary",
        "",
        f"- urirun SHA: `{urirun_sha or 'unknown'}`",
        f"- examples SHA: `{examples_sha or 'unknown'}`",
        f"- PASS: {passed}",
        f"- FAIL: {failed}",
        f"- SKIP: {skipped}",
        "",
        "| Example | Class | Status | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        detail = result.get("skip_reason") or result.get("error") or result.get("command") or ""
        lines.append(
            f"| `{result['name']}` | `{result['class']}` | `{result['status']}` | {html.escape(str(detail))} |"
        )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--class", dest="klass", choices=sorted(CLASSES), action="append")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--out-dir", default="ci-artifacts")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--urirun-sha", default=os.environ.get("URIRUN_SHA", ""))
    parser.add_argument("--examples-sha", default=os.environ.get("EXAMPLES_SHA", ""))
    ns = parser.parse_args(argv)

    root = Path(ns.root).resolve()
    manifest_path = Path(ns.manifest).resolve() if ns.manifest else root / "ci" / "examples-manifest.yml"
    out_dir = (Path(ns.out_dir) if Path(ns.out_dir).is_absolute() else root / ns.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest, errors = validate_manifest(root, manifest_path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    if ns.validate_only:
        print(f"manifest OK: {len(manifest)} examples classified")
        return 0

    selected = set(ns.klass or RUNNABLE)
    results: list[dict[str, Any]] = []
    for name in numbered_dirs(root):
        entry = manifest[name]
        klass = str(entry["class"])
        if klass in selected and klass in RUNNABLE:
            print(f"RUN {name} [{klass}]: {entry['command']}")
            results.append(run_one(root, name, entry, out_dir, ns.timeout))
        elif klass not in RUNNABLE:
            results.append({
                "name": name,
                "class": klass,
                "status": "skipped",
                "skip_reason": entry["skip_reason"],
                "duration": 0,
            })

    (out_dir / "execution-manifest.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    junit(results, out_dir / "junit.xml")
    markdown(results, out_dir / "summary.md", ns.urirun_sha, ns.examples_sha)
    failed = [r for r in results if r["status"] == "failed"]
    if failed:
        print("Failed examples: " + ", ".join(r["name"] for r in failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
