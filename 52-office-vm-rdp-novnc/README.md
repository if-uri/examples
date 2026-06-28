# 52 — office work on a virtual machine over RDP, surfaced through noVNC

A user asks for an **office task on a remote VM in plain language**; a planner turns
it into a **multi-step URI flow** over a VM-office **MCP tool surface**; urirun
**executes** the flow step by step against a fleet of virtual machines reached over
**RDP** and viewed through an **HTML5 noVNC canvas**; then a **verification step
checks the system state** — not only that the task happened, but that the RDP
session and noVNC view were **torn down cleanly** (no dangling connections).

This is the everyday corporate pattern: a worker (or an agent) connects to a
Windows/Linux VM over RDP, the session is surfaced through noVNC in the browser, and
office apps (Excel / Outlook / a billing form) run *inside the VM*.

```
NL request ──► action space = 20 MCP tools (URIs + JSON Schemas)
          ──► plan: [{uri, payload}, …]   (≥10 steps; deterministic, or --llm)
          ──► urirun.run each step (policy-gated)
                vm://    fleet power (start/stop/list)
                rdp://   gateway session (connect/disconnect/list)
                novnc:// HTML5 view over the session (open/close/status)
                desktop://, screen://, fs://, clipboard://, notify://  — inside the VM
          ──► verify(state): did the task happen AND did RDP/noVNC close cleanly?
```

Six tasks, each a **≥10-step** flow that drives a VM end to end:

| # | task | what it does (verified) |
|---|------|--------------------------|
| `finance`   | Excel on a Win11 VM | start VM → RDP → noVNC → enter Q3 revenue → save → screenshot+OCR → disconnect → **OCR shows the figure, .xlsx saved, 0 dangling sessions** |
| `multi-vm`  | move a value between VMs | two RDP sessions, copy via **RDP clipboard redirection**, paste in the sales VM → **clipboard set, value OCR-visible on the 2nd VM** |
| `onboard`   | on-demand VM lifecycle | spin a fresh VM up → work over noVNC → close view → disconnect → **power the VM back off, nothing left running** |
| `invoice`   | OCR → billing form | OCR an invoice image inside the VM, key 2 fields, save the record → **record saved, amount OCR-confirmed** |
| `secure`    | end-of-day teardown | explicit close-view-then-disconnect ordering → **0 sessions AND 0 views remain** |
| `resilient` | reach a maybe-off VM | check the fleet, power the VM on, *then* connect & save a note → **note saved, OCR-visible** |

## Run

```bash
python3 run.py                 # all 6 scenarios, deterministic plans, with verification
python3 run.py --scenario finance
python3 run.py --json          # machine-readable
```

```
VM-office MCP tool surface: 20 URI tools (schemes: clipboard, desktop, fs, notify, novnc, rdp, screen, vm)
✓ [finance] 13 steps — Connect to the Win11 finance VM over RDP/noVNC, enter Q3 revenue in Excel, save & verify
    executed 13/13 ok=True  ·  verified: True (ocr=True saved=True sessions=0 views=0)
...
RESULT: 6/6 VM-office tasks completed AND verified
```

## Drive a REAL noVNC desktop

`--live` runs the headline finance task against an actual noVNC desktop in Docker,
reusing [example 28](../28-llm-novnc-desktop)'s connector — proving the same plan
shape (`start → launch → type → screenshot → stop`) drives a real HTML5 canvas, not
just the simulator:

```bash
python3 run.py --live          # needs Docker; pulls dorowu/ubuntu-desktop-lxde-vnc
```

## Plan with a real LLM

`--llm` sends the NL request **plus the MCP tool schemas** to a model (`LLM_MODEL` +
key from [`examples/.env`](../.env)) and executes the plan it returns, then verifies:

```bash
python3 run.py --scenario finance --llm
```

The verification is the point: a model that connects before powering the VM on, or
that forgets to disconnect, is reported `verified: False` (dangling session), not
silently "done". The deterministic flows in `scenarios.py` are the reference of what
a capable model produces.

## Why this examines *correct behaviour*, not just "it ran"

The verification on each scenario asserts **teardown** (`sessions == 0`,
`views == 0`), and `test_vm_office.py` exercises the state machine directly:

- connecting to a **powered-off VM is rejected** (`start it before connecting`);
- opening a **noVNC view requires an RDP session** first;
- **disconnect** closes the dependent noVNC views; **power-off** tears down the VM's
  sessions — no dangling artefacts either way;
- the **RDP clipboard is shared** across gateway sessions (redirection);
- **files persist on the VM** across reconnects.

These are the things that go wrong on real RDP/noVNC gateways, so they are what the
example checks.

## How it maps to a real machine

`vm_office_system.py` keeps a JSON state (VM power, RDP sessions, noVNC views, the
shared clipboard, per-VM files, an OCR log). Every route mutates it, so step N sees
step N-1 and `verify()` checks the real outcome. Swap these routes for the tellmesh
desktop connectors (`rdp`/`kvm`/`novnc`/`uriscreen` — see
[example 31](../31-llm-remote-office)) or the live noVNC connector from
[example 28](../28-llm-novnc-desktop) and the same flows drive an actual VM. Because
they are ordinary URI routes, they also run on a remote, NAT'd gateway through
`mesh.urirun.com` exactly like [example 32](../32-host-ask-over-relay).

## Files

- `vm_office_system.py` — the VM-fleet + RDP/noVNC simulator and the 20-route MCP tool surface.
- `scenarios.py` — the 6 NL tasks: request, the ≥10-step flow, and `verify(state)` (incl. teardown).
- `run.py` — planner (deterministic, `--llm`, or `--live` on a real desktop) → execute → verify → report.
- `test_vm_office.py` — every task plans ≥10 steps, executes and verifies; plus direct behaviour checks; opt-in live (`URIRUN_NOVNC_LIVE=1`).

## Test

```bash
python3 -m pytest test_vm_office.py -q
```
