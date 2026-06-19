# device_mesh_lab

Local URI mesh demo with a dashboard, two device agents and URI-addressed flows.

## Browser execution in this demo

`browser://desktop/page/command/open` reaches the `desktop` agent through the URI
registry. By default the agent does not open the host browser. It delegates the
action into the mapped noVNC computer through `pc://.../terminal/command/run`:

```text
browser://desktop/page/command/open -> pc://pc1/terminal/command/run
browser://laptop/page/command/open  -> pc://pc2/terminal/command/run
```

This is a demo environment, so browser execution is enabled by default:

```bash
URIRUN_MESH_ALLOW_BROWSER=1
URIRUN_MESH_BROWSER_BACKEND=novnc
URIRUN_MESH_BROWSER_TARGETS=desktop=pc1@http://127.0.0.1:9001,laptop=pc2@http://127.0.0.1:9002
```

To run the same demo in a safer dry-run/policy mode, set:

```bash
URIRUN_MESH_ALLOW_BROWSER=0
```

With `0`, the agent records a `browser.blocked` log and returns a policy error.
Other safe URI routes, such as `proc://`, `shell://.../which`, `note://` and
`log://`, still execute.

For local debugging only, you can explicitly switch back to host execution:

```bash
URIRUN_MESH_BROWSER_BACKEND=host
```

Without this opt-in, `browser://` must be handled by the mapped noVNC PC API.

## Run

Start the dashboard and agents from this directory:

```bash
cd 10-device_mesh_lab

python3 controller.py
```

In another terminal:

```bash
URIRUN_MESH_DEVICE_NAME=desktop \
URIRUN_MESH_DEVICE_ROLE=controller \
URIRUN_MESH_AGENT_PORT=18765 \
URIRUN_MESH_ALLOW_BROWSER=1 \
URIRUN_MESH_BROWSER_BACKEND=novnc \
URIRUN_MESH_BROWSER_TARGETS=desktop=pc1@http://127.0.0.1:9001,laptop=pc2@http://127.0.0.1:9002 \
python3 device_agent.py
```

For the second simulated device:

```bash
URIRUN_MESH_DEVICE_NAME=laptop \
URIRUN_MESH_DEVICE_ROLE=remote-laptop \
URIRUN_MESH_AGENT_PORT=18766 \
URIRUN_MESH_ALLOW_BROWSER=1 \
URIRUN_MESH_BROWSER_BACKEND=novnc \
URIRUN_MESH_BROWSER_TARGETS=desktop=pc1@http://127.0.0.1:9001,laptop=pc2@http://127.0.0.1:9002 \
python3 device_agent.py
```

Then open:

```text
http://127.0.0.1:8193/
```

## noVNC note

The noVNC containers must expose their PC API on ports `9001`, `9002`, `9003`
and `9004`. The adapter sends a shell command into that API and starts the first
available browser from this list: `firefox-esr`, `firefox`, `chromium`,
`chromium-browser`, `google-chrome`, `x-www-browser`.

If a noVNC image does not contain a browser, the command still runs inside noVNC
and opens an `xterm` warning there. Install Firefox or Chromium in the noVNC
image to make the URL open visually in the remote desktop.
