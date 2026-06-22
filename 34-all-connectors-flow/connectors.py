# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Every urirun-connector-* (Python ones here), with: the pip-installable dir name,
# the python module, and a representative route to prove it works. `route=None`
# means the connector is config-gated (needs creds / a device / a project) — we
# install + validate it, but don't run a route. The polyglot connectors
# (base64/php, hash/go, uuid/js) are covered by example 19 (they need their own
# toolchains, not pip), so this YAML-flow sweep focuses on the pip-installable set.

from __future__ import annotations

# name : (python module, route or None, payload, note)
CONNECTORS = {
    "time-tools":      ("urirun_connector_time_tools",     "time://host/clock/query/now", {}, "current time"),
    "mcp-filesystem":  ("urirun_connector_mcp_filesystem", "fs://host/dir/query/list", {"path": "."}, "list a dir"),
    "http-check":      ("urirun_connector_http_check",     "httpcheck://host/http/query/status", {"url": "https://example.com"}, "HTTP status (network)"),
    "domain-monitor":  ("urirun_connector_domain_monitor", "monitor://host/dns/query/current",
                        {"domain": "example.com", "current_records": [{"Name": "@", "Type": "A", "Address": "203.0.113.10"}]}, "DNS diff"),
    "get-node":        ("urirun_connector_get_node",       "node://get/installer/query/script", {}, "installer script"),
    "sqlite-context":  ("urirun_connector_sqlite_context", "log://host/logs/query/recent", {"limit": 5}, "recent logs"),
    "browser-control": ("urirun_connector_browser_control", "browser://chrome/page/query/text", {"url": "https://example.com", "max": 80}, "read page (Chrome)"),
    # config-gated: installed + validated, not run (need creds / device / project / key / extra deps)
    "email":           ("urirun_connector_email",           None, {}, "IMAP/SMTP creds"),
    "mqtt":            ("urirun_connector_mqtt",             None, {}, "needs paho-mqtt + a broker"),
    "ksef":            ("urirun_connector_ksef",            None, {}, "live MF KSeF API"),
    "planfile":        ("urirun_connector_planfile",        None, {}, "needs a planfile project"),
    "namecheap-dns":   ("urirun_connector_namecheap_dns",   None, {}, "Namecheap API creds"),
    "llm":             ("urirun_connector_llm",             None, {}, "LLM API key / Ollama"),
    "kvm":             ("urirun_connector_kvm",             None, {}, "KVM device"),
    "flow-repair":     ("urirun_connector_flow_repair",     None, {}, "needs a registry + LLM"),
}
