# 48 - API and device nodes

This example shows how to register external APIs and multi-interface devices as
URI nodes without writing a dedicated connector first.

Use this when the target is:

- a SaaS or local HTTP API (`api` node),
- a device with several interfaces, such as RPi, IP camera or NAS (`device`
  node),
- an object that should appear in discovery as a controllable URI surface.

## Register an API node

```bash
URIRUN=/home/tom/github/if-uri/urirun/venv/bin/urirun
CONFIG=/tmp/urirun-api-device.mesh.json

$URIRUN host init --config "$CONFIG" --name api-device-demo

$URIRUN host add-node crm-api https://api.example.test/v1 \
  --config "$CONFIG" \
  --kind api \
  --api-id main \
  --api-kind rest \
  --auth-type bearer \
  --auth-token 'PASTE_ONCE'
```

`--auth-token` is passed once. The host stores it in keyring when possible and
keeps only a `secretRef` in the mesh config.

## Register a device node

```bash
$URIRUN host add-node rpi-camera http://rpi.local \
  --config "$CONFIG" \
  --kind device \
  --api '{"id":"panel","kind":"web","url":"http://rpi.local"}' \
  --api '{"id":"stream","kind":"rtsp","role":"camera","url":"rtsp://rpi.local/live"}' \
  --api '{"id":"share","kind":"smb","url":"smb://rpi.local/share"}' \
  --api '{"id":"ssh","kind":"ssh","url":"ssh://pi@rpi.local"}'
```

Discovery will expose configured routes such as:

```text
api://crm-api/main/command/request
device://rpi-camera/panel/query/status
media://rpi-camera/stream/query/stream
fs://rpi-camera/share/query/list
ssh://rpi-camera/ssh/command/run
```

## Execute HTTP-like APIs

HTTP/REST/OpenAPI interfaces can be called directly by the host:

```bash
curl -sS http://127.0.0.1:8194/api/uri/invoke \
  -H 'Content-Type: application/json' \
  -d '{
    "uri":"api://crm-api/main/command/request",
    "mode":"execute",
    "payload":{"method":"GET","path":"/accounts","query":{"limit":10}}
  }'
```

The neutral planner route is:

```text
configured://host/node-api/command/request
```

with payload:

```json
{
  "node": "crm-api",
  "apiId": "main",
  "method": "GET",
  "path": "/accounts",
  "query": {"limit": 10}
}
```

## Non-HTTP protocols

RTSP, SMB/NFS, SSH and camera snapshot routes are metadata until a connector or
service owns the scheme. The host should return `connector_required` rather than
pretending that it can execute the protocol.

That is intentional: discovery can show what the object has, while execution
still goes through a specific connector boundary.

## Natural language examples

```text
Dodaj API node crm-api z bazowym URL https://api.example.test/v1 i bearer tokenem.
Pokaz status interfejsu main w API node crm-api.
Wykonaj GET /accounts?limit=10 na crm-api przez URI.
Dodaj rpi-camera jako device node z panelem HTTP, strumieniem RTSP, SMB i SSH.
Pokaz jakie route'y ma device node rpi-camera i ktore wymagaja connectora.
```

