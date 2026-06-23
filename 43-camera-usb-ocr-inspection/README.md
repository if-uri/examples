# 43 - camera + USB + OCR inspection loop

This example shows the URI shape for a physical scan station:

```text
usb:// camera discovery
  -> camera:// pre-scan beep + photo capture
  -> camera:// object detection/crop/inspection
  -> ocr:// text extraction when richer OCR is needed
  -> alert/log URI when rules fail
```

The important operational detail is the audible pre-scan cue. A flow sets
`beep=true` before `camera://host/photo/...` capture so the person near the
camera knows exactly when a photo is taken. Set `beep_required=true` when the
flow must refuse capture if the audio cue cannot be emitted.

## Connector roles

- `usb://host/cameras/query/list`: which physical USB camera is connected and
  which `/dev/video*` node it exposes.
- `camera://host/photo/command/capture`: beep and capture one frame.
- `camera://host/photo/query/analyze`: capture or reuse an image, describe,
  detect/crop the main region, OCR it.
- `camera://host/photo/query/inspect`: analyze plus simple pass/fail rules and
  structured alerts; persists a verdict (`inspection.json` sidecar + optional JSONL
  `audit_log`) so alerting has a durable trail without a separate `log://` connector.
- `camera://host/photo/query/compare`: change/motion detection — compare two files, a
  reference vs a fresh frame, or two frames captured `interval_ms` apart — returning
  `changed`, `changeRatio` and the changed region, with `beep_on_change`/`fail_on_change`.
- `camera://host/photo/query/barcodes`: decode barcodes / QR codes (pyzbar) — each code's
  `{type, data, rect}` — with `required` + `fail_if_missing` to assert an expected code.
- `ocr://host/image/query/text`: optional richer OCR/layout backend for the
  captured image or crop.

## Flows

- `camera-usb-ocr.flow.yaml`: end-to-end probe + beeped OCR + inspection.
- `camera-alert.flow.yaml`: minimal inspection flow that can stop on alert and writes an
  audit log (no `log://` connector needed).
- `camera-motion-scan.flow.yaml`: detect motion, then beep + scan + OCR + inspect only
  what appeared, recording an audit record.
- `camera-barcode-scan.flow.yaml`: beep + decode a label's QR/barcode and stop on a missing
  expected code.
- `camera-mobile-web.flow.yaml`: host a LAN web service (`webcam://`) so a phone's browser
  camera scans into the same pipeline; review the mobile captures.

## Live run

The live script is intentionally explicit because it touches real hardware:

```bash
cd /home/tom/github/if-uri/examples/43-camera-usb-ocr-inspection
NODE=lenovo \
NODE_URL=http://192.168.188.201:8765 \
IDENTITY=~/.ssh/id_ed25519 \
./run_live_probe.sh
```

It ensures `usb`, `camera` and `ocr` are live on the node, probes devices, then
runs an inspection with `beep=true`. If no `/dev/video*` camera exists, discovery
still works and the capture step reports a clean URI error.

## Lenovo validation

Validated on `lenovo` / node name `laptop` on 2026-06-23:

- `usb://host/cameras/query/list` detects `Chicony Electronics Co.,Ltd. Integrated Camera`
  with `/dev/video0`..`/dev/video3`.
- `camera://host/photo/command/capture` emits a pre-scan beep through `paplay`, captures
  via `ffmpeg`, and writes a 1280x720 JPEG.
- `camera://host/photo/query/inspect` writes `photo.jpg`, `object.jpg` and
  `inspection.json`.
- `ocr://host/document/query/text` works for text/base64 payloads.
- image OCR on that node currently reports missing image backends (`imgl`, `tesseract`,
  `img2nl`). Install one of those on the node, or use the host-compute pattern from
  `SCENARIOS.md` when OCR should run on a stronger machine.

## Scenarios

See `SCENARIOS.md` for concrete office/manufacturing examples.
