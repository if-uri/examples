"""Typed form (urirun-flow) of web-recon.flow.yaml — `urirun-flow to-yaml web_recon.flow:flow`
emits the same YAML; `urirun-flow run web_recon.flow:flow --execute` runs it.
Install: pip install urirun-flow"""
from urirun_flow import Flow

URL = "https://example.com"
flow = Flow(task={"title": "Web recon — is it up, read the page, log it"},
            registry="tools.bindings.json",
            allow=["httpcheck://*", "browser://*", "log://*", "time://*"])
up = flow.step("httpcheck://host/url/query/status", id="up", payload={"url": URL})
read = flow.step("browser://chrome/page/query/dom", id="read",
                 payload={"url": URL, "max": 400}, after=[up])
flow.step("log://host/run/command/write", id="audit",
          payload={"event": "recon", "detail": "read example.com"}, after=[read])
