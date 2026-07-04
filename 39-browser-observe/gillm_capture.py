# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# gillm's Wayland screen capture wrapped as a urirun URI route. The screenshot goes
# through org.freedesktop.portal.Screenshot (DBus + GLib, interactive=False) — the path
# that works on GNOME/Wayland where gnome-screenshot/x11grab/pipewire fail. Deploy onto
# a node with `host deploy --code gillm_capture.py --bindings <its bindings>`; the node
# needs python3-dbus + python3-gobject (present on a GNOME desktop).
# Capture logic adapted from semcod/gillm (gillm.capture.portal_backend; PyPI: gillm>=0.1).
# Deliberately vendored, NOT imported: this file's source is shipped verbatim to the remote
# node by observe.py, so the node needs zero pip installs beyond the GNOME system packages.
# If gillm's portal backend changes, re-sync from the package instead of patching here.

import base64, shutil, subprocess, urllib.parse
from pathlib import Path

_PORTAL = r"""
import sys
import dbus
import dbus.mainloop.glib
from gi.repository import GLib

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
token = "koruvision_portal"
sender = bus.get_unique_name()[1:].replace(".", "_")
request_path = f"/org/freedesktop/portal/desktop/request/{sender}/{token}"
state = {"uri": None, "error": None}

def _on_response(response, results):
    if int(response) != 0:
        state["error"] = f"portal response code {response}"
    elif "uri" in results:
        state["uri"] = str(results["uri"])
    else:
        state["error"] = "portal response missing uri"
    loop.quit()

bus.add_signal_receiver(
    _on_response,
    dbus_interface="org.freedesktop.portal.Request",
    path=request_path,
    signal_name="Response",
)
proxy = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
iface = dbus.Interface(proxy, "org.freedesktop.portal.Screenshot")
iface.Screenshot("", {"handle_token": token, "interactive": False})

loop = GLib.MainLoop()
GLib.timeout_add(12000, lambda: (loop.quit(), False)[1])
loop.run()

if state["error"]:
    print(state["error"], file=sys.stderr)
    sys.exit(2)
if not state["uri"]:
    print("portal screenshot timed out", file=sys.stderr)
    sys.exit(3)
print(state["uri"])
"""


def _portal_python():
    for cand in ("/usr/bin/python3", shutil.which("python3")):
        if not cand:
            continue
        try:
            if subprocess.run([cand, "-c", "import dbus, gi"], capture_output=True, timeout=5).returncode == 0:
                return cand
        except Exception:
            pass
    return None


def capture(**_p):
    """Capture the node's screen via the XDG Desktop Portal. Returns a full base64 PNG."""
    py = _portal_python()
    if not py:
        return {"ok": False, "error": "node has no python with dbus+gi (install python3-dbus python3-gobject)"}
    try:
        proc = subprocess.run([py, "-c", _PORTAL], capture_output=True, timeout=25, text=True)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    if proc.returncode != 0:
        return {"ok": False, "error": (proc.stderr or "").strip()[:200], "rc": proc.returncode}
    uri = (proc.stdout or "").strip()
    data = Path(urllib.parse.urlparse(uri).path).read_bytes()
    return {"ok": True, "via": "xdg-portal", "bytes": len(data), "base64": base64.b64encode(data).decode()}


def urirun_bindings():
    return {"version": "urirun.bindings.v2", "bindings": {"screen://laptop/portal/query/capture": {
        "kind": "query", "adapter": "local-function", "ref": "gillm_capture:capture",
        "python": {"type": "python", "module": "gillm_capture", "export": "capture"},
        "inputSchema": {"type": "object", "properties": {}}, "uri": "screen://laptop/portal/query/capture"}}}
