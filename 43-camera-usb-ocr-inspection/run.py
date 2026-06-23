#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# End-to-end demo of the camera scan station: discover the camera (usb://), capture or
# synthesise a frame, crop tightly to the receipt and deskew it before OCR (camera://),
# decode a QR/barcode, and optionally host the LAN mobile service (webcam://). Runs fully
# offline with a synthetic receipt when no /dev/video* camera is attached.
#
#   python3 run.py                 # synthetic receipt, full pipeline
#   python3 run.py --camera        # capture from a real /dev/video* if present
#   python3 run.py --serve 8780    # also start the mobile webcam service and print the URL
#   python3 run.py --json          # machine-readable summary

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

import urirun_connector_camera.core as cam


def _value(res: dict) -> dict:
    """Connector functions return urirun.ok/fail dicts directly when called in-process."""
    return res if isinstance(res, dict) else {}


def _synthetic_receipt(path: str) -> None:
    """Draw a tilted bright receipt on a dark desk with a QR code — a stand-in for a photo."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (640, 480), (60, 70, 65))
    d = ImageDraw.Draw(img)
    d.polygon([(230, 70), (430, 110), (400, 420), (210, 380)], fill=(248, 248, 248))
    d.text((250, 130), "SKLEP IFURI", fill=(15, 15, 15))
    d.text((250, 170), "PARAGON FISKALNY", fill=(15, 15, 15))
    for i, y in enumerate(range(210, 330, 26)):
        d.text((250, y), f"TOWAR {i + 1} .... {i * 7 + 3},99", fill=(15, 15, 15))
    d.text((250, 350), "SUMA PLN 123,45", fill=(15, 15, 15))
    try:
        import qrcode
        qr = qrcode.make("https://ifuri.com/receipt/INV-2026-0042").convert("RGB").resize((90, 90))
        img.paste(qr, (470, 60))
    except Exception:  # noqa: BLE001 - QR is a bonus
        pass
    img.save(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="camera + usb + ocr scan-station demo")
    ap.add_argument("--camera", action="store_true", help="capture from a real /dev/video* if present")
    ap.add_argument("--serve", type=int, metavar="PORT", help="also start the mobile webcam service")
    ap.add_argument("--json", action="store_true", help="print a JSON summary")
    args = ap.parse_args()

    out_dir = tempfile.mkdtemp(prefix="ex43-")
    summary: dict = {"outputDir": out_dir, "steps": {}}

    # 1. discover the camera over usb://
    cams = _value(cam.list_cameras())
    summary["steps"]["devices"] = {
        "videoNodes": cams.get("videoNodes", []),
        "cameras": [c.get("name") for c in cams.get("cameras", [])],
        "default": cams.get("default", ""),
    }

    # 2. obtain a frame: real capture or synthetic receipt
    photo = os.path.join(out_dir, "frame.jpg")
    have_cam = bool(cams.get("default"))
    if args.camera and have_cam:
        cap = _value(cam.capture(output=photo, beep=False))
        source = "camera" if cap.get("ok") else "synthetic"
        if not cap.get("ok"):
            _synthetic_receipt(photo)
    else:
        _synthetic_receipt(photo)
        source = "synthetic"
    summary["steps"]["frame"] = {"source": source, "path": photo}

    # 3. receipt pipeline: crop to the sheet, deskew, OCR
    scan = _value(cam.analyze(image=photo, output_dir=out_dir, target="receipt",
                              deskew=True, ocr=True, describe=True, lang="pol+eng"))
    obj = scan.get("object", {})
    summary["steps"]["receipt"] = {
        "detector": obj.get("detector"),
        "deskewed": obj.get("deskewed", False),
        "cropPath": obj.get("cropPath"),
        "ocrChars": scan.get("ocr", {}).get("chars", 0),
        "ocrPreview": (scan.get("ocr", {}).get("text") or "")[:120].replace("\n", " "),
        "description": (scan.get("description", {}) or {}).get("text", "")[:120],
    }

    # 4. decode any barcode / QR in the frame
    bc = _value(cam.read_barcodes(image=photo, output_dir=out_dir))
    summary["steps"]["barcodes"] = {"backend": bc.get("barcodeBackend"),
                                    "codes": [c.get("data") for c in bc.get("codes", [])]}

    # 5. optionally host the LAN mobile service
    if args.serve:
        try:
            import urirun_connector_camera_web.core as web
            started = _value(web.start(port=args.serve, action="inspect"))
            summary["steps"]["webcam"] = {"ok": started.get("ok"), "openUrl": started.get("openUrl"),
                                          "healthy": started.get("healthy")}
        except Exception as exc:  # noqa: BLE001
            summary["steps"]["webcam"] = {"ok": False, "error": str(exc)}

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    s = summary["steps"]
    print("== 43 — camera + USB + OCR scan station ==")
    print(f"cameras       : {s['devices']['cameras'] or '(none — using synthetic frame)'}")
    print(f"frame         : {s['frame']['source']}  → {s['frame']['path']}")
    r = s["receipt"]
    print(f"receipt crop  : detector={r['detector']} deskewed={r['deskewed']}")
    print(f"               {r['cropPath']}")
    print(f"OCR ({r['ocrChars']} chars): {r['ocrPreview'] or '(no text read)'}")
    print(f"description   : {r['description']}")
    print(f"barcodes      : backend={s['barcodes']['backend']} codes={s['barcodes']['codes'] or '(none)'}")
    if "webcam" in s:
        w = s["webcam"]
        print(f"mobile service: {'open ' + w['openUrl'] if w.get('ok') else 'failed: ' + str(w.get('error'))}")
        print("                (open that URL on a phone on the same Wi‑Fi; Ctrl-stop with urirun-webcam stop)")
    print(f"\nartifacts in  : {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
