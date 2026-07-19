from __future__ import annotations

import subprocess

from scripts.audit_test_coverage import audit
from scripts.run_ci_manifest import numbered_dirs, validate_manifest


def test_audit_reports_pytest_dirs_missing_from_smoke(tmp_path):
    root = tmp_path / "examples"
    root.mkdir()
    (root / "01-json").mkdir()
    (root / "01-json" / "test_json.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    (root / "02-demo").mkdir()
    (root / "02-demo" / "test_demo.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    (root / "03-script").mkdir()
    script = root / "run_tests.sh"
    script.write_text("cd 01-json\n# skip 03-script\n", encoding="utf-8")

    rep = audit(root, script)

    assert rep["counts"]["examples"] == 3
    assert rep["pytestDirs"] == ["01-json", "02-demo"]
    assert rep["smokeDirs"] == ["01-json", "03-script"]
    assert rep["pytestDirsNotInSmoke"] == ["02-demo"]
    assert rep["smokeDirsWithoutPytest"] == ["03-script"]


def test_manifest_requires_every_numbered_example(tmp_path):
    root = tmp_path / "examples"
    root.mkdir()
    (root / "01-json").mkdir()
    (root / "02-demo").mkdir()
    manifest = root / "manifest.yml"
    manifest.write_text(
        "examples:\n"
        "  01-json:\n"
        "    class: host\n"
        "    command: python -m pytest -q .\n",
        encoding="utf-8",
    )

    _, errors = validate_manifest(root, manifest)

    assert "Unclassified example: 02-demo\nAdd it to ci/examples-manifest.yml." in errors


def test_manifest_requires_skip_reason_for_skipped_classes(tmp_path):
    root = tmp_path / "examples"
    root.mkdir()
    (root / "47-android").mkdir()
    manifest = root / "manifest.yml"
    manifest.write_text(
        "examples:\n"
        "  47-android:\n"
        "    class: hardware\n",
        encoding="utf-8",
    )

    _, errors = validate_manifest(root, manifest)

    assert "47-android: skipped class 'hardware' requires skip_reason" in errors


def test_numbered_dirs_ignores_untracked_developer_examples(tmp_path):
    root = tmp_path / "examples"
    root.mkdir()
    tracked = root / "01-tracked"
    tracked.mkdir()
    (tracked / "README.md").write_text("tracked\n", encoding="utf-8")
    ignored = root / "41-local-data"
    ignored.mkdir()
    (ignored / "private.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "01-tracked/README.md"], check=True)

    assert numbered_dirs(root) == ["01-tracked"]
