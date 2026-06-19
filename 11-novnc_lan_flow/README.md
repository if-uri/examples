# 11-novnc_lan_flow — multi-computer noVNC LAN flow

A Docker-based demo where several "computers" (each a container with a noVNC
desktop) communicate over one URI contract. A `dashboard` shows the desktops and
an `orchestrator` drives a multi-step URI flow across them (e.g. `pc://…`,
`log://…`, `browser://…`).

Components:

- `computer/` — a desktop container image (noVNC) acting as a URI node
- `orchestrator/` — runs the cross-machine URI flow
- `dashboard/` — web view of the nodes and the live flow
- `generated/` — compiled bindings/registry for the demo

## Run

Requires Docker. Bring the stack up and run the flow (see the compose/Make
targets inside the component folders):

```bash
docker compose up -d        # start the noVNC computers + dashboard
# then trigger the orchestrator flow (orchestrator/)
```

> Needs Docker + noVNC; not exercised by the host-only test pass.
