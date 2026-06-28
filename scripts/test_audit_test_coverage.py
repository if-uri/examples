from __future__ import annotations

from scripts.audit_test_coverage import audit


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
