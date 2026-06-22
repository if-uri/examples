"""A urirun flow built from uri_tree routes across the just-installed connectors:
check a site (http-check) -> record the check (sqlite-context) -> open a ticket
(planfile). Emits/runs via urirun-flow.  `urirun-flow to-yaml ops_flow:flow`"""
import pathlib, yaml
from urirun_flow import Flow

TREE = yaml.safe_load((pathlib.Path(__file__).parent / "uri-tree.yaml").read_text())["uri_tree"]

def uri(connector, *path):
    node = TREE[connector]["schemes"][path[0]]
    for seg in ["host", *path[1:]]:
        node = node[seg]
    return node["uri"]                       # resolve a leaf URI from the tree

flow = Flow(task={"title": "site check -> log -> ticket"},
            registry="tools.registry.json",
            allow=["httpcheck://*", "check://*", "task://*"])
up    = flow.step(uri("http_check", "httpcheck", "http", "query", "status"),
                  id="up", payload={"url": "https://example.com"})
log   = flow.step(uri("sqlite_context_store", "check", "check", "command", "add"),
                  id="log", after=[up],
                  payload={"name": "example.com", "status_from": "up.result.value.status"})
flow.step(uri("planfile_tasks", "task", "ticket", "command", "create"),
          id="ticket", after=[log],
          payload={"title": "Follow up on example.com check"})

if __name__ == "__main__":
    print(flow.to_yaml())
