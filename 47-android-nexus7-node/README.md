# Example 47 — Android Nexus 7 as a urirun node

Control a Nexus 7 tablet (or any Android device) from urirun using:
- **ADB connector** (`adb://`) for immediate KVM-style control
- **Termux node** to run urirun natively on the device

## Prerequisites

- Android platform-tools (`adb`) on PATH
- ADB debugging enabled on the tablet

## Quick start (ADB over WiFi)

```bash
# 1. Connect USB cable, enable USB debugging, then switch to WiFi ADB:
adb tcpip 5555
adb connect TABLET_IP:5555

# 2. Install the ADB connector:
pip install -e ../../urirun-connector-adb/

# 3. Capture screen (--entry-points loads the installed connector, --execute runs it,
#    --allow is the security boundary, --payload passes route inputs as JSON):
ADB_SERIAL=TABLET_IP:5555 urirun run "adb://host/screen/query/capture" \
    --entry-points --execute --allow 'adb://*' --payload '{"output":"nexus7.png"}'

# 4. Tap (e.g. center of a 1280x800 Nexus 7 screen):
ADB_SERIAL=TABLET_IP:5555 urirun run "adb://host/input/command/tap" \
    --entry-points --execute --allow 'adb://*' --payload '{"x":640,"y":400}'

# 5. Press HOME:
ADB_SERIAL=TABLET_IP:5555 urirun run "adb://host/input/command/key" \
    --entry-points --execute --allow 'adb://*' --payload '{"keycode":"HOME"}'

# 6. List files:
ADB_SERIAL=TABLET_IP:5555 urirun run "adb://host/fs/query/list" \
    --entry-points --execute --allow 'adb://*' --payload '{"path":"/sdcard/"}'
```

> Note: the connector's own routes are `adb://host/...` (the `host` segment is the
> urirun authoring placeholder). The `adb://nexus7/...` aliases below come from the
> compiled `node-nexus7.bindings.json`, which pins the same handlers to a `nexus7`
> device label.

## Start the setup service (QR code distribution)

```bash
pip install -e ../../urirun-service-android-node/
urirun-android-node serve
# Open http://LAN_IP:8195/ on the tablet
```

## Add as Termux node

On the tablet in Termux:
```bash
curl -fsSL http://HOST_IP:8195/bootstrap.sh | bash
```

Then on the computer:
```bash
urirun host add-node nexus7 http://TABLET_IP:8765
```

## Use compiled bindings

```bash
# Validate and compile the Nexus 7 bindings:
urirun validate node-nexus7.bindings.json
urirun compile node-nexus7.bindings.json --out node-nexus7.registry.json

# Run a route from the registry:
ADB_SERIAL=TABLET_IP:5555 urirun run "adb://nexus7/sys/query/info" \
    --registry node-nexus7.registry.json --execute --allow 'adb://*'
```
