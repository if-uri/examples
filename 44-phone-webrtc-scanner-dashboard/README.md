# 44 - phone WebRTC scanner through the urirun dashboard

Use a phone camera as a better receipt/invoice scanner while the host dashboard
keeps every scan as a chat message and host artifact.

The phone page uses the browser camera API (`getUserMedia`, WebRTC media capture)
and uploads still frames to the host dashboard:

```text
phone browser /scanner
  -> POST /api/scanner/capture
  -> artifact:// / scanner:// URI record
  -> chat message with preview + metadata + OCR result when available
```

The scanner is created on demand from the dashboard chat. Open the dashboard,
switch to Chat and write a natural-language request such as:

```text
uruchom skaner telefonu i pokaz QR
```

The dashboard starts the HTTPS scanner service, detects the LAN IP, then appends
a chat message with the scanner URL and a QR-code attachment.

When the phone opens `/scanner`, it posts a lightweight session event back to the
dashboard, so the chat shows `Phone scanner opened`. Starting the camera adds a
second `Phone scanner camera started` message with user-agent and viewport
metadata.

## Run on LAN

Start the operator dashboard:

```bash
cd /home/tom/github/if-uri/urirun
./venv/bin/urirun host dashboard serve \
  --project . \
  --db ~/.urirun/host.db \
  --node-url lenovo=http://192.168.188.201:8765 \
  --identity ~/.ssh/id_ed25519 \
  --host 0.0.0.0 \
  --port 8194
```

Open:

```text
http://127.0.0.1:8194/
```

Then ask from the dashboard Chat:

```text
uruchom skaner telefonu i pokaz QR
```

The service starts on HTTPS, usually:

```text
https://<HOST_LAN_IP>:8196/scanner
```

Most mobile browsers require HTTPS before camera access is allowed. urirun creates
a local self-signed certificate in `~/.urirun/certs` when needed. Accept the local
certificate warning on the phone. For a cleaner setup, install a trusted local CA
certificate or use `mkcert`.

Advanced: the old startup QR path is still available when explicitly requested:

```bash
STARTUP_QR=1 QR_URL=https://<HOST_LAN_IP>:8196/scanner ./run.sh
```

## What appears in dashboard chat

Each scan creates:

- a `scanner://host/capture/<sha>` URI,
- a `camera-scan` artifact in the host DB,
- an automatic `*-receipt-crop.jpg` when the host can detect a receipt/document
  inside the phone frame, using `urirun-connector-smart-crop`
- a chat message with the cropped receipt preview, original file path, crop box,
  size, dimensions, SHA-256 and OCR metadata.
- after the chat request, a `dashboard://host/qr/<sha>` message with a QR-code
  attachment for the phone scanner service.
- when the phone connects, a `scanner://host/session/<sha>` chat message with
  browser metadata.

If `tesseract` is installed on the host, OCR runs on the cropped receipt image.
Without it, the cropped image still appears as an attachment and OCR metadata says
what backend is missing. If the receipt cannot be detected reliably, urirun keeps
the original frame and records the crop reason in metadata.
