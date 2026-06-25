# 47 — NL → ui:// plan → execute (autonomous desktop control)

Turn a natural-language desktop task into a sequence of `kvm://.../ui/*` (+ `browser`/`app`)
URIs and run them on a urirun node with a perceive→act→verify loop — the planner that
closes the autonomy loop on top of the cross-platform `urirun-connector-kvm` semantic UI
layer.

```bash
# plan only (prints the URI steps the LLM produced)
python run.py "focus the terminal and type: echo hello"

# plan + execute on a node, saving a host-side screenshot (+ zoom around each click) per step
python run.py "open a new terminal and run echo hi" \
  --node http://192.168.188.201:8765 --execute \
  --identity ~/.ssh/id_ed25519 \
  --save-shots ~/.urirun/artifacts/kvm-laptop
```

LLM via `examples/.env` (`LLM_MODEL` / `OPENROUTER_API_KEY`), in-process (litellm). The
action space is the connector's `ui/query/find|wait|verify`, `ui/command/click|fill`,
`input/*`, `app://.../launch`, `browser://.../open`.

`--save-shots DIR` writes `HHMMSS-stepNN-<route>.png` after every step (and a
`...-zoom.png` tile around the click point when the step has `x,y`) so a session is
reviewable on the host immediately.

## Grounding caveats (read before trusting clicks)

The plan/executor is reliable; the *grounding* depends on the target environment:

* **Element targeting** is rock-solid only when the app exposes accessibility (AT-SPI on
  Linux). For Chrome/Firefox web content, enable it (`chrome://accessibility` → Native API
  on, or `--force-renderer-accessibility`) — otherwise the connector falls back to vision
  (imgl/vql), whose OCR is unreliable on dark-theme UIs.
* **Coordinate clicks (`ui/command/click` with x,y, vision fallback) are unreliable on
  multi-monitor + HiDPI Wayland**: `ydotool` absolute positioning does not map cleanly to
  screenshot pixels there (calibration on a 3200×3800 / 2× HiDPI / dual-monitor host showed
  neither ×1 nor ÷2 mapping landed). Prefer AT-SPI element actions, a single-monitor /
  non-HiDPI target, or a **vdisplay** owned virtual display for deterministic coordinates.
* **GNOME Wayland forbids focus-stealing**: keyboard goes to the *active* window only.
  Launch a fresh window (active on launch) or activate the target before typing.
