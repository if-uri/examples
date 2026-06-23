# Camera/USB/OCR scenarios

## 1. Desk document / receipt (paragon) OCR

Goal: put a receipt, invoice or shipping label under a webcam and read it — cropped to the
sheet, not the whole desk.

URI steps (see `camera-receipt-scan.flow.yaml`):

1. `usb://host/cameras/query/list`
2. `camera://host/photo/query/analyze` (or `inspect`) with `beep=true`, `crop=true`,
   `target="receipt"`, `ocr=true`
3. inspect `ocr.text` and save the result to a local report

`target="receipt"` (aka `document`/`paragon`) runs a numpy projection detector that hugs the
bright, text-dense sheet on the darker background, so OCR sees only the receipt. Use
`target="object"` for a 3‑D item, or `target="auto"` to let the connector decide.

Add `deskew=true` when the receipt is photographed at an angle: the connector finds the four
corners and warps the sheet **flat** (perspective correction) before OCR — OpenCV is used for
corner detection if installed, otherwise a numpy detector; the warp is Pillow-only.

Use when: a person manually places documents in front of a camera.

## 2. Known-label inspection

Goal: verify that the camera sees a label containing expected text, for example
`FAKTURA`, `SN:`, `LOT`, `PASS`, or a product name.

URI step:

`camera://host/photo/query/inspect`

Useful payload:

```json
{
  "required_text": "FAKTURA",
  "min_chars": 5,
  "require_object": true,
  "beep": true,
  "beep_on_alert": true,
  "fail_on_alert": false
}
```

The route returns `inspection.passed=false` plus `inspection.alerts` when the
text is missing, the frame is too dark/bright, or no object was detected.

## 3. Stop-the-line inspection

Goal: abort a URI flow when the expected text is absent.

Set `fail_on_alert=true` on `camera://host/photo/query/inspect`. The route then
returns `ok=false` when rules fail, so a normal URI flow stops before the next
step.

## 4. Rich OCR on a stronger host

Goal: capture on a weak node, OCR on a stronger host.

Pattern:

```text
camera://node/photo/command/capture {return_base64:true}
  -> ocr://host/document/query/text {filename:"scan.jpg", bytes_b64:"..."}
```

Use when the camera is physically attached to the node but OCR/LLM packages run
better on the host.

## 5. Environmental sanity check

Goal: make sure the scan station is ready before work starts.

Probe:

- `usb://host/devices/query/probe`
- `usb://host/cameras/query/list`
- `camera://host/devices/query/list`
- `ocr://host/backend/query/probe`

This separates hardware issues from OCR/backend issues.

## 6. Motion-triggered scan (scan only when something appears)

Goal: don't OCR a static empty desk on a loop — only scan when a document/hand/part
enters the frame.

URI steps (see `camera-motion-scan.flow.yaml`):

1. `camera://host/photo/query/compare` — captures two frames `interval_ms` apart and
   returns `changed` + `changeRatio` + the changed region. `beep_on_change=true` beeps
   the instant motion is seen.
2. `camera://host/photo/query/inspect` — runs after motion, with `beep=true` so the
   operator hears the capture and `audit_log` to record the verdict.

Variants:

- **Reference comparison**: pass `reference=<baseline.jpg>` to `compare` to detect any
  change versus a known-good empty scene (one capture instead of two).
- **Stop-when-still**: set `fail_on_change=true` to make the flow stop when nothing moved.

## 7. Durable alert/audit trail

Goal: keep a history of every inspection for later review, without a database.

`camera://host/photo/query/inspect` writes two artefacts on every scan:

- `inspection.json` next to the photo (full structured verdict), and
- one JSON line appended to `audit_log` (`{timestamp, passed, alerts, textChars,
  brightness, device, photo}`) when `audit_log` is set.

Tail the JSONL to drive dashboards or downstream alerting (e.g. pipe failed lines to
`email://` or `mqtt://`). No separate `log://` connector is required.

## 8. Barcode / QR scan-and-assert

Goal: read the QR or barcode on a parcel/label and alert when the expected code is absent.

URI step (see `camera-barcode-scan.flow.yaml`):

`camera://host/photo/query/barcodes` with, e.g.:

```json
{
  "required": "INV-2026-",
  "beep": true,
  "beep_on_read": true,
  "fail_if_missing": true
}
```

Returns every code as `{type, data, rect}`. `required` matches an expected substring,
`beep_on_read` confirms a successful read audibly, and `fail_if_missing=true` stops the
flow (alert) when the expected code is not visible. Needs `pyzbar` + system `libzbar0`;
without them the route returns `found=false` with a clear `decodeError`.

## 9. Mobile / browser camera over the LAN

Goal: no USB camera on the node? Use a phone. Host a small web service and let any phone's
browser camera scan into the same pipeline.

URI steps (see `camera-mobile-web.flow.yaml`):

1. `webcam://host/server/command/start` — `{port, action, token}` → returns `openUrl`.
2. Open `openUrl` on the phone (same Wi‑Fi), allow the camera, pick the action, tap **Scan**.
   The page uses `getUserMedia` (rear camera) and posts each frame to `/ingest`, which runs
   `camera://host/upload/command/ingest` (analyze | inspect | barcodes | ocr | describe).
3. `webcam://host/captures/query/list` — review the captured frames + their results.
4. `webcam://host/server/command/stop` — stop the service.

Notes:

- Browsers grant the camera only on a secure context — `http://localhost` or `https://…`.
  On a plain `http://<lan-ip>` some mobile browsers block it; tunnel via HTTPS or allowlist
  the origin. (`webcam://` README has details.)
- Pass `token` to require a shared secret on an untrusted LAN.
- Frames are processed by `urirun-connector-camera`, so OCR/barcode/inspection/scene work
  identically whether the frame came from `/dev/video*` or a phone.

