# 12 - full E2E connect lab

This lab verifies the complete user path:

1. `get.ifuri.com` provides the node installer.
2. `connect.ifuri.com` provides connector/install metadata.
3. `pc1` and `pc2` install and run `urirun node`.
4. `host` installs urirun + connectors, discovers both nodes and runs a URI flow.
5. `registry-runtime` exposes a live registry built from the node routes.
6. `ifuri-site` serves a local test page representing `ifuri.com`.

The default test intentionally uses public installer endpoints:

```txt
https://get.ifuri.com/node.sh
https://connect.ifuri.com/install?connectors=planfile
https://ifuri.com/
```

You can override them for local development:

```bash
GET_BASE_URL=http://get-site CONNECT_BASE_URL=http://connect-site make test
```

## Quick public smoke

```bash
make public-smoke
```

This checks public `ifuri.com`, `get.ifuri.com` and `connect.ifuri.com` without
Docker.

## Full Docker scenario

```bash
make test
```

The scenario writes artifacts to `generated/`:

- `nodes.json`
- `routes.json`
- `agents.json`
- `registry-runtime.json`
- `flow-result.json`
- `ifuri-test-page.html`

## Manual commands

```bash
make up
make scenario
make down
```

To inspect a node:

```bash
docker compose exec pc1 bash
curl -fsSL http://127.0.0.1:8765/health
curl -fsSL http://127.0.0.1:8765/routes
```
