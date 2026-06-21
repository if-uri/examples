# 17 — flows: usage scenarios in txt, bash and YAML

A **flow** is an ordered list of URI steps (`query` reads, `command` mutates),
gated by policy and chaining prior results. The same scenarios appear in three
forms so you can pick the one that fits:

- **`scenarios.txt`** — human/LLM-readable catalog (step-id · uri · payload · `<- dep`).
- **`flow-*.sh`** — runnable bash (plain `urirun run` chains).
- **`*.flow.yaml`** + **`run_flow.py`** — declarative flow files executed by a tiny runner.
- **`*.flow.py`** (typed) — author the flow in typed Python with
  [`urirun-flow`](https://github.com/if-uri/urirun-flow) (Pydantic): `urirun-flow to-yaml
  web_recon.flow:flow` emits the YAML above, `urirun-flow run … --execute` runs it.

```bash
make setup                 # generate the registries the flows reference
make local                 # scenario 1 — offline (timestamp + audit log)
make web                   # scenario 2 — httpcheck + real Chrome DOM + log
make declarative           # scenario 3 — drive httpbin from a TOML spec
make ksef                  # scenario 5 — KSeF challenge+send (dry-run, no secret)
make test                  # offline CI test
```

## YAML flow shape

```yaml
task: { title: "..." }
registry: tools.bindings.json          # a bindings or registry path (relative)
allow: [ "time://*", "log://*" ]        # policy globs
secretAllow: [ "getv://TOKEN" ]         # secret:// references this flow may resolve
steps:
  - id: stamp
    uri: time://host/clock/query/now
    payload: {}
  - id: audit
    uri: log://host/run/command/write
    payload: { event: "demo", url_from: "stamp.result.url" }   # _from chains a prior result
    depends_on: [ stamp ]
```

`run_flow.py <flow> [--execute] [--allow GLOB] [--secret-allow GLOB]`. Default is
**dry-run** — nothing executes, no secret resolves, the plan is printed. `query`
steps run freely with `--execute`; `command` steps need an `--allow` glob, so the
same flow is safe to dry-run and explicit to execute.

## Scenarios

| # | Scenario | URIs | Needs |
|---|----------|------|-------|
| 1 | local audit | `time://` → `log://` | nothing (offline) |
| 2 | web recon | `httpcheck://` → `browser://chrome` → `log://` | network + Chrome |
| 3 | declarative HTTP | `httpbin://...` (from a TOML spec) | network |
| 4 | secret call | `sdemo://...` with `Bearer {getv:DEMO_TOKEN}` | see `../16-secrets` |
| 5 | KSeF | `ksef://test/auth/challenge` → `.../send` | dry-run safe |
| 6 | LLM agent | planner picks the URIs | see `../14-llm-uri-agent` |

Every step is a URI + payload + policy decision — auditable, replayable, and the
same surface an LLM, MCP client or A2A peer would drive.
