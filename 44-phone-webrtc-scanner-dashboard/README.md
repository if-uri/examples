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

## Run on LAN

For desktop-only testing:

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
http://127.0.0.1:8194/scanner
```

For a phone, most mobile browsers require HTTPS before camera access is allowed.
Generate a local certificate and serve HTTPS:

```bash
mkdir -p ~/.urirun/certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout ~/.urirun/certs/urirun-dashboard.key \
  -out ~/.urirun/certs/urirun-dashboard.crt \
  -days 365 \
  -subj "/CN=urirun-dashboard.local"

cd /home/tom/github/if-uri/urirun
./venv/bin/urirun host dashboard serve \
  --project . \
  --db ~/.urirun/host.db \
  --node-url lenovo=http://192.168.188.201:8765 \
  --identity ~/.ssh/id_ed25519 \
  --host 0.0.0.0 \
  --port 8194 \
  --tls-cert ~/.urirun/certs/urirun-dashboard.crt \
  --tls-key ~/.urirun/certs/urirun-dashboard.key
```

Then open this from the phone on the same Wi-Fi:

```text
https://<HOST_LAN_IP>:8194/scanner
```

Accept the local certificate warning if needed. For a cleaner setup, install a
trusted local CA certificate or use `mkcert`.

## What appears in dashboard chat

Each scan creates:

- a `scanner://host/capture/<sha>` URI,
- a `camera-scan` artifact in the host DB,
- a chat message with image preview, file path, size, dimensions, SHA-256 and OCR
  metadata.

If `tesseract` is installed on the host, the scanner message includes OCR text.
Without it, the image still appears as an attachment and OCR metadata says what
backend is missing.

