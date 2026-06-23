from pathlib import Path


ROOT = Path(__file__).parent


def test_flows_reference_expected_uri_surface():
    text = (ROOT / "camera-usb-ocr.flow.yaml").read_text(encoding="utf-8")
    alert = (ROOT / "camera-alert.flow.yaml").read_text(encoding="utf-8")
    motion = (ROOT / "camera-motion-scan.flow.yaml").read_text(encoding="utf-8")

    assert "usb://host/cameras/query/list" in text
    assert "camera://host/devices/query/list" in text
    assert "ocr://host/backend/query/probe" in text
    assert "camera://host/photo/query/analyze" in text
    assert "camera://host/photo/query/inspect" in text
    assert "beep: true" in text
    assert "fail_on_alert: true" in alert
    # the alert flow persists its own verdict instead of a non-existent log:// connector
    assert "audit_log" in alert
    assert "log://" not in alert
    # motion flow: change/motion detection gates the scan step
    assert "camera://host/photo/query/compare" in motion
    assert "camera://host/photo/query/inspect" in motion

    # barcode flow: decode + assert an expected code is present
    barcode = (ROOT / "camera-barcode-scan.flow.yaml").read_text(encoding="utf-8")
    assert "camera://host/photo/query/barcodes" in barcode
    assert "fail_if_missing: true" in barcode

    # mobile/browser flow: host the LAN webcam service and review captures
    mobile = (ROOT / "camera-mobile-web.flow.yaml").read_text(encoding="utf-8")
    assert "webcam://host/server/command/start" in mobile
    assert "webcam://host/captures/query/list" in mobile


def test_no_flow_references_missing_log_connector():
    for flow in ROOT.glob("*.flow.yaml"):
        assert "log://" not in flow.read_text(encoding="utf-8"), flow.name

