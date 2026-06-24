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

# 3. Capture screen:
ADB_SERIAL=TABLET_IP:5555 urirun invoke "adb://nexus7/screen/query/capture" --output nexus7.png

# 4. Tap (e.g. center of 1280x800 Nexus 7 screen):
ADB_SERIAL=TABLET_IP:5555 urirun invoke "adb://nexus7/input/command/tap" --x 640 --y 400

# 5. Press HOME:
ADB_SERIAL=TABLET_IP:5555 urirun invoke "adb://nexus7/input/command/key" --keycode HOME

# 6. List files:
ADB_SERIAL=TABLET_IP:5555 urirun invoke "adb://nexus7/fs/query/list" --path /sdcard/
```

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
urirun compile node-nexus7.bindings.json -o node-nexus7.registry.json

# Run a route from the registry:
ADB_SERIAL=TABLET_IP:5555 urirun run --registry node-nexus7.registry.json \
    "adb://nexus7/sys/query/info"
```
