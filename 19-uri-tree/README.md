# 19 · uri_tree — connectors as a YAML URI tree

Install a set of connectors with one line, then view their URIs as a **tree**
(`scheme → host → path → {uri}`) and build flows by navigating it.

## Install the connectors

```bash
curl -fsSL 'https://connect.ifuri.com/install?connectors=planfile,sqlite-context,domain-monitor,http-check,time-tools,namecheap-dns,grpc-transport,browser-control' | bash
```

The `/install` endpoint turns the comma-separated selection into a bash script that
`pip install`s the urirun runtime plus each `urirun-connector-*` package.

## The uri_tree

`build_uri_tree.py` reads the same selection from the live
[connect.ifuri.com](https://connect.ifuri.com) catalog and emits `uri-tree.yaml` —
each connector's routes nested as a tree:

```yaml
uri_tree:
  planfile_tasks:
    status: available
    verified: true
    category: Planning
    description: "Plan, group and execute daily tasks through task:// and planfile:// URI commands."
    schemes:
      task:
        host:
          tickets: { query: { list: { uri: "task://host/tickets/query/list" } } }
          ticket:
            query: { next: { uri: "task://host/ticket/query/next" }, … }
            command: { create: { uri: "task://host/ticket/command/create" }, … }
      planfile:
        host:
          dsl: { command: { run: { uri: "planfile://host/dsl/command/run" } } }
```

```bash
python build_uri_tree.py                         # the 8 connectors above -> uri-tree.yaml
python build_uri_tree.py http-check time-tools   # any selection
```

Singular vs plural is meaningful and preserved verbatim — `ticket` (a single
resource) and `tickets` (the collection), `record`/`records`, `check`/`checks` — they
are distinct path segments, so they stay distinct branches.

**8 connectors · 39 URI leaves** across `task, planfile, data, artifact, check, log,
monitor, browser, flow, httpcheck, time, dns, transport`.

## Build a flow by navigating the tree

`ops_flow.py` resolves leaves from `uri-tree.yaml` and composes them with
[urirun-flow](https://github.com/if-uri/urirun-flow) — check a site, record it, open a
ticket, across three connectors:

```
up     -> httpcheck://host/http/query/status     (http-check)
log     -> check://host/check/command/add          (sqlite-context)
ticket  -> task://host/ticket/command/create       (planfile)
```

```bash
make tree                                  # regenerate uri-tree.yaml
python ops_flow.py                         # emit the flow YAML
urirun-flow run ops_flow:flow --execute    # run it (needs the connectors installed)
```

The tree is the index; the flow is one path through it.
