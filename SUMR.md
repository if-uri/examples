# ifURI examples

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `examples`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: Makefile, testql(1), app.doql.less, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: examples;
  version: 0.1.0;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=./run_tests.sh;
}

workflow[name="site"] {
  trigger: manual;
  step-1: run cmd=python3 scripts/build_site.py _site;
}

workflow[name="deploy"] {
  trigger: manual;
  step-1: run cmd=bash scripts/deploy-plesk.sh;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
}
```

## Workflows

## Call Graph

*221 nodes · 273 edges · 23 modules · CC̄=3.5*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `main` *(in 12-full_e2e_connect_lab.scripts.assert_results)* | 38 ⚠ | 0 | 60 | **60** |
| `run_connector_routes` *(in 12-full_e2e_connect_lab.scripts.connector_checks)* | 7 | 1 | 47 | **48** |
| `build_registry` *(in 12-full_e2e_connect_lab.scripts.connector_checks)* | 1 | 2 | 38 | **40** |
| `normalize_flow` *(in 10-device_mesh_lab.controller)* | 20 ⚠ | 4 | 35 | **39** |
| `app_service_call` *(in 11-novnc_lan_flow.computer.browser_node)* | 22 ⚠ | 1 | 35 | **36** |
| `handler` *(in 10-device_mesh_lab.device_agent.DeviceAgent)* | 1 | 0 | 32 | **32** |
| `main` *(in 12-full_e2e_connect_lab.scripts.connector_checks)* | 20 ⚠ | 0 | 30 | **30** |
| `send_json` *(in 10-device_mesh_lab.mesh_env)* | 1 | 18 | 12 | **30** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/if-uri/examples
# generated in 0.10s
# nodes: 221 | edges: 273 | modules: 23
# CC̄=3.5

HUBS[20]:
  12-full_e2e_connect_lab.scripts.assert_results.main
    CC=38  in:0  out:60  total:60
  12-full_e2e_connect_lab.scripts.connector_checks.run_connector_routes
    CC=7  in:1  out:47  total:48
  12-full_e2e_connect_lab.scripts.connector_checks.build_registry
    CC=1  in:2  out:38  total:40
  10-device_mesh_lab.controller.normalize_flow
    CC=20  in:4  out:35  total:39
  11-novnc_lan_flow.computer.browser_node.app_service_call
    CC=22  in:1  out:35  total:36
  10-device_mesh_lab.device_agent.DeviceAgent.handler
    CC=1  in:0  out:32  total:32
  12-full_e2e_connect_lab.scripts.connector_checks.main
    CC=20  in:0  out:30  total:30
  10-device_mesh_lab.mesh_env.send_json
    CC=1  in:18  out:12  total:30
  11-novnc_lan_flow.computer.browser_node.json_response
    CC=1  in:18  out:12  total:30
  10-device_mesh_lab.device_agent.parse_browser_targets
    CC=19  in:1  out:26  total:27
  12-full_e2e_connect_lab.scripts.connector_checks.uri_run
    CC=2  in:23  out:4  total:27
  11-novnc_lan_flow.computer.browser_node.screenshot_page
    CC=10  in:1  out:26  total:27
  09-docker_uri_flow.orchestrator.flow_runner.parse_flow
    CC=24  in:1  out:26  total:27
  08-multi_transport.worker.serve_http
    CC=1  in:0  out:25  total:25
  07-transports.transport_lib.start_http_worker
    CC=1  in:1  out:24  total:25
  10-device_mesh_lab.device_agent.DeviceAgent.open_browser_in_novnc
    CC=9  in:0  out:24  total:24
  10-device_mesh_lab.controller.Handler.do_POST
    CC=12  in:0  out:24  total:24
  11-novnc_lan_flow.computer.browser_node.Handler.do_POST
    CC=9  in:0  out:23  total:23
  10-device_mesh_lab.www.app.escapeHtml
    CC=1  in:20  out:2  total:22
  06-html_uri_app.backend.Handler.do_GET
    CC=8  in:0  out:21  total:21

MODULES:
  05-generators.c.example  [2 funcs]
    main  CC=1  out:1
    puts  CC=1  out:0
  05-generators.go.example  [2 funcs]
    main  CC=4  out:3
    uriCommand  CC=4  out:4
  05-generators.php.example  [2 funcs]
    bindingFromFunction  CC=2  out:9
    schemaType  CC=2  out:3
  06-html_uri_app.app  [15 funcs]
    card  CC=2  out:2
    classFor  CC=1  out:2
    data  CC=2  out:1
    defaults  CC=8  out:5
    escapeHtml  CC=1  out:2
    iconFor  CC=2  out:3
    inputType  CC=2  out:2
    payloadDefaults  CC=4  out:0
    refreshLogs  CC=5  out:7
    renderActions  CC=5  out:5
  06-html_uri_app.backend  [13 funcs]
    do_GET  CC=8  out:21
    do_POST  CC=4  out:10
    log_message  CC=1  out:1
    add_log  CC=2  out:2
    binding_document  CC=1  out:2
    dispatch  CC=6  out:14
    dispatch_tool  CC=7  out:13
    env_bool  CC=1  out:2
    load_env  CC=6  out:10
    main  CC=5  out:10
  07-transports.transport_lib  [7 funcs]
    available_transports  CC=4  out:1
    grpc_available  CC=2  out:0
    run_inprocess  CC=2  out:1
    run_queue  CC=1  out:10
    run_via  CC=6  out:16
    serverless_handler  CC=1  out:2
    start_http_worker  CC=1  out:24
  08-multi_transport.worker  [2 funcs]
    serve_grpc  CC=1  out:2
    serve_http  CC=1  out:25
  09-docker_uri_flow.node-worker.server  [6 funcs]
    body  CC=2  out:1
    readBody  CC=2  out:4
    send  CC=1  out:4
    server  CC=10  out:4
    slug  CC=1  out:1
    slugify  CC=1  out:4
  09-docker_uri_flow.orchestrator.flow_runner  [16 funcs]
    get_path  CC=2  out:1
    json_get  CC=1  out:4
    json_post  CC=1  out:7
    load_registry  CC=3  out:4
    main  CC=3  out:5
    normalize_uri  CC=6  out:7
    parse_flow  CC=24  out:26
    parse_scalar  CC=3  out:2
    registry_has_uri  CC=4  out:9
    registry_route_count  CC=5  out:9
  09-docker_uri_flow.python-worker.server  [5 funcs]
    do_GET  CC=3  out:3
    do_POST  CC=6  out:11
    dispatch  CC=3  out:2
    normalize  CC=1  out:6
    summary  CC=1  out:2
  09-docker_uri_flow.shell-worker.server  [3 funcs]
    do_GET  CC=3  out:3
    do_POST  CC=6  out:11
    dispatch  CC=2  out:5
  10-device_mesh_lab.controller  [26 funcs]
    do_GET  CC=2  out:5
    do_OPTIONS  CC=1  out:1
    do_POST  CC=12  out:24
    append_step_if_missing  CC=7  out:6
    build_registry  CC=5  out:3
    discover_device  CC=6  out:9
    discover_mesh  CC=5  out:6
    execute_flow  CC=9  out:15
    fallback_flow  CC=1  out:4
    fallback_steps  CC=33  out:19
  10-device_mesh_lab.device_agent  [11 funcs]
    __init__  CC=3  out:3
    handler  CC=1  out:32
    log  CC=2  out:7
    open_browser_in_novnc  CC=9  out:24
    routes  CC=2  out:13
    build_novnc_browser_command  CC=1  out:2
    default_browser_targets  CC=2  out:2
    main  CC=1  out:6
    make_agent_from_env  CC=3  out:14
    object_schema  CC=2  out:0
  10-device_mesh_lab.mesh_env  [7 funcs]
    auth_headers  CC=2  out:1
    auth_token  CC=1  out:2
    check_auth  CC=2  out:2
    load_env  CC=9  out:10
    parse_peers  CC=8  out:14
    read_json  CC=3  out:5
    send_json  CC=1  out:12
  10-device_mesh_lab.www.app  [52 funcs]
    appendTimeline  CC=3  out:3
    data  CC=2  out:1
    defaultValueFor  CC=20  out:2
    description  CC=3  out:1
    deviceRows  CC=2  out:1
    escapeHtml  CC=1  out:2
    extractRunResult  CC=10  out:0
    filter  CC=3  out:1
    focusArea  CC=3  out:6
    focusTargetFor  CC=2  out:0
  11-novnc_lan_flow.computer.browser_node  [16 funcs]
    do_GET  CC=6  out:6
    do_OPTIONS  CC=1  out:1
    do_POST  CC=9  out:23
    log_message  CC=1  out:2
    app_service_call  CC=22  out:35
    current_url  CC=3  out:4
    ensure_session  CC=6  out:7
    json_response  CC=1  out:12
    log  CC=2  out:2
    main  CC=1  out:5
  11-novnc_lan_flow.orchestrator.run_flow  [6 funcs]
    collect_routes  CC=4  out:10
    fetch_json  CC=4  out:7
    main  CC=7  out:12
    run_step  CC=2  out:8
    target_from_uri  CC=2  out:2
    wait_health  CC=4  out:6
  12-full_e2e_connect_lab.registry-runtime.registry_server  [5 funcs]
    do_GET  CC=4  out:9
    discover  CC=4  out:9
    get_json  CC=2  out:4
    nodes  CC=4  out:6
    registry_document  CC=5  out:7
  12-full_e2e_connect_lab.scripts.assert_results  [2 funcs]
    load  CC=1  out:2
    main  CC=38  out:60
  12-full_e2e_connect_lab.scripts.connector_checks  [14 funcs]
    build_registry  CC=1  out:38
    emit_browser_control_bindings  CC=1  out:3
    emit_http_check_bindings  CC=1  out:3
    emit_time_tools_bindings  CC=1  out:3
    fetch_catalog  CC=1  out:6
    main  CC=20  out:30
    project_mcp_a2a  CC=1  out:4
    run  CC=4  out:2
    run_connector_routes  CC=7  out:47
    run_json  CC=2  out:3
  12-full_e2e_connect_lab.scripts.run_full_scenario  [1 funcs]
    print  CC=0  out:0
  13-simple_defaults.js.defaults  [6 funcs]
    boolean  CC=1  out:1
    connector  CC=2  out:13
    field  CC=2  out:1
    fullUri  CC=2  out:2
    integer  CC=1  out:1
    string  CC=1  out:1
  13-simple_defaults.python_connector  [2 funcs]
    bindings  CC=1  out:1
    main  CC=2  out:5

EDGES:
  06-html_uri_app.app.routeResponse → 06-html_uri_app.app.renderActions
  06-html_uri_app.app.routeResponse → 06-html_uri_app.app.renderForm
  06-html_uri_app.app.renderActions → 06-html_uri_app.app.classFor
  06-html_uri_app.app.renderActions → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.renderActions → 06-html_uri_app.app.iconFor
  06-html_uri_app.app.renderForm → 06-html_uri_app.app.schemaFor
  06-html_uri_app.app.renderForm → 06-html_uri_app.app.payloadDefaults
  06-html_uri_app.app.renderForm → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.required → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.defaults → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.inputType → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.refreshLogs → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.data → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.card → 06-html_uri_app.app.renderToolList
  06-html_uri_app.app.renderToolList → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.iconFor → 06-html_uri_app.app.classFor
  09-docker_uri_flow.node-worker.server.server → 09-docker_uri_flow.node-worker.server.send
  09-docker_uri_flow.node-worker.server.server → 09-docker_uri_flow.node-worker.server.readBody
  09-docker_uri_flow.node-worker.server.server → 09-docker_uri_flow.node-worker.server.slugify
  09-docker_uri_flow.node-worker.server.body → 09-docker_uri_flow.node-worker.server.send
  09-docker_uri_flow.node-worker.server.slug → 09-docker_uri_flow.node-worker.server.send
  10-device_mesh_lab.www.app.showView → 10-device_mesh_lab.www.app.setMenuActive
  10-device_mesh_lab.www.app.focusArea → 10-device_mesh_lab.www.app.showView
  10-device_mesh_lab.www.app.focusArea → 10-device_mesh_lab.www.app.setMenuActive
  10-device_mesh_lab.www.app.focusArea → 10-device_mesh_lab.www.app.focusTargetFor
  10-device_mesh_lab.www.app.recordActivity → 10-device_mesh_lab.www.app.renderActivityLog
  10-device_mesh_lab.www.app.routeBadge → 10-device_mesh_lab.www.app.isRouteSafe
  10-device_mesh_lab.www.app.renderDevices → 10-device_mesh_lab.www.app.filter
  10-device_mesh_lab.www.app.renderDevices → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.reachable → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.installable → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.novncUrlFor → 10-device_mesh_lab.www.app.novncEntryFor
  10-device_mesh_lab.www.app.renderNovnc → 10-device_mesh_lab.www.app.novncUrlFor
  10-device_mesh_lab.www.app.renderNovnc → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.url → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.status → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.renderRoutes → 10-device_mesh_lab.www.app.filter
  10-device_mesh_lab.www.app.renderRoutes → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.renderRoutes → 10-device_mesh_lab.www.app.routeBadge
  10-device_mesh_lab.www.app.filter → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.rows → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.renderRoutes
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.renderPayloadForm
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.setMenuActive
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.showJson
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.previewPayload
  10-device_mesh_lab.www.app.renderField → 10-device_mesh_lab.www.app.defaultValueFor
  10-device_mesh_lab.www.app.renderField → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.renderField → 10-device_mesh_lab.www.app.valueToInput
  10-device_mesh_lab.www.app.description → 10-device_mesh_lab.www.app.escapeHtml
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Integration (1)

**`Auto-generated from Python Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/if-uri/examples
# generated in 0.10s
# nodes: 221 | edges: 273 | modules: 23
# CC̄=3.5

HUBS[20]:
  12-full_e2e_connect_lab.scripts.assert_results.main
    CC=38  in:0  out:60  total:60
  12-full_e2e_connect_lab.scripts.connector_checks.run_connector_routes
    CC=7  in:1  out:47  total:48
  12-full_e2e_connect_lab.scripts.connector_checks.build_registry
    CC=1  in:2  out:38  total:40
  10-device_mesh_lab.controller.normalize_flow
    CC=20  in:4  out:35  total:39
  11-novnc_lan_flow.computer.browser_node.app_service_call
    CC=22  in:1  out:35  total:36
  10-device_mesh_lab.device_agent.DeviceAgent.handler
    CC=1  in:0  out:32  total:32
  12-full_e2e_connect_lab.scripts.connector_checks.main
    CC=20  in:0  out:30  total:30
  10-device_mesh_lab.mesh_env.send_json
    CC=1  in:18  out:12  total:30
  11-novnc_lan_flow.computer.browser_node.json_response
    CC=1  in:18  out:12  total:30
  10-device_mesh_lab.device_agent.parse_browser_targets
    CC=19  in:1  out:26  total:27
  12-full_e2e_connect_lab.scripts.connector_checks.uri_run
    CC=2  in:23  out:4  total:27
  11-novnc_lan_flow.computer.browser_node.screenshot_page
    CC=10  in:1  out:26  total:27
  09-docker_uri_flow.orchestrator.flow_runner.parse_flow
    CC=24  in:1  out:26  total:27
  08-multi_transport.worker.serve_http
    CC=1  in:0  out:25  total:25
  07-transports.transport_lib.start_http_worker
    CC=1  in:1  out:24  total:25
  10-device_mesh_lab.device_agent.DeviceAgent.open_browser_in_novnc
    CC=9  in:0  out:24  total:24
  10-device_mesh_lab.controller.Handler.do_POST
    CC=12  in:0  out:24  total:24
  11-novnc_lan_flow.computer.browser_node.Handler.do_POST
    CC=9  in:0  out:23  total:23
  10-device_mesh_lab.www.app.escapeHtml
    CC=1  in:20  out:2  total:22
  06-html_uri_app.backend.Handler.do_GET
    CC=8  in:0  out:21  total:21

MODULES:
  05-generators.c.example  [2 funcs]
    main  CC=1  out:1
    puts  CC=1  out:0
  05-generators.go.example  [2 funcs]
    main  CC=4  out:3
    uriCommand  CC=4  out:4
  05-generators.php.example  [2 funcs]
    bindingFromFunction  CC=2  out:9
    schemaType  CC=2  out:3
  06-html_uri_app.app  [15 funcs]
    card  CC=2  out:2
    classFor  CC=1  out:2
    data  CC=2  out:1
    defaults  CC=8  out:5
    escapeHtml  CC=1  out:2
    iconFor  CC=2  out:3
    inputType  CC=2  out:2
    payloadDefaults  CC=4  out:0
    refreshLogs  CC=5  out:7
    renderActions  CC=5  out:5
  06-html_uri_app.backend  [13 funcs]
    do_GET  CC=8  out:21
    do_POST  CC=4  out:10
    log_message  CC=1  out:1
    add_log  CC=2  out:2
    binding_document  CC=1  out:2
    dispatch  CC=6  out:14
    dispatch_tool  CC=7  out:13
    env_bool  CC=1  out:2
    load_env  CC=6  out:10
    main  CC=5  out:10
  07-transports.transport_lib  [7 funcs]
    available_transports  CC=4  out:1
    grpc_available  CC=2  out:0
    run_inprocess  CC=2  out:1
    run_queue  CC=1  out:10
    run_via  CC=6  out:16
    serverless_handler  CC=1  out:2
    start_http_worker  CC=1  out:24
  08-multi_transport.worker  [2 funcs]
    serve_grpc  CC=1  out:2
    serve_http  CC=1  out:25
  09-docker_uri_flow.node-worker.server  [6 funcs]
    body  CC=2  out:1
    readBody  CC=2  out:4
    send  CC=1  out:4
    server  CC=10  out:4
    slug  CC=1  out:1
    slugify  CC=1  out:4
  09-docker_uri_flow.orchestrator.flow_runner  [16 funcs]
    get_path  CC=2  out:1
    json_get  CC=1  out:4
    json_post  CC=1  out:7
    load_registry  CC=3  out:4
    main  CC=3  out:5
    normalize_uri  CC=6  out:7
    parse_flow  CC=24  out:26
    parse_scalar  CC=3  out:2
    registry_has_uri  CC=4  out:9
    registry_route_count  CC=5  out:9
  09-docker_uri_flow.python-worker.server  [5 funcs]
    do_GET  CC=3  out:3
    do_POST  CC=6  out:11
    dispatch  CC=3  out:2
    normalize  CC=1  out:6
    summary  CC=1  out:2
  09-docker_uri_flow.shell-worker.server  [3 funcs]
    do_GET  CC=3  out:3
    do_POST  CC=6  out:11
    dispatch  CC=2  out:5
  10-device_mesh_lab.controller  [26 funcs]
    do_GET  CC=2  out:5
    do_OPTIONS  CC=1  out:1
    do_POST  CC=12  out:24
    append_step_if_missing  CC=7  out:6
    build_registry  CC=5  out:3
    discover_device  CC=6  out:9
    discover_mesh  CC=5  out:6
    execute_flow  CC=9  out:15
    fallback_flow  CC=1  out:4
    fallback_steps  CC=33  out:19
  10-device_mesh_lab.device_agent  [11 funcs]
    __init__  CC=3  out:3
    handler  CC=1  out:32
    log  CC=2  out:7
    open_browser_in_novnc  CC=9  out:24
    routes  CC=2  out:13
    build_novnc_browser_command  CC=1  out:2
    default_browser_targets  CC=2  out:2
    main  CC=1  out:6
    make_agent_from_env  CC=3  out:14
    object_schema  CC=2  out:0
  10-device_mesh_lab.mesh_env  [7 funcs]
    auth_headers  CC=2  out:1
    auth_token  CC=1  out:2
    check_auth  CC=2  out:2
    load_env  CC=9  out:10
    parse_peers  CC=8  out:14
    read_json  CC=3  out:5
    send_json  CC=1  out:12
  10-device_mesh_lab.www.app  [52 funcs]
    appendTimeline  CC=3  out:3
    data  CC=2  out:1
    defaultValueFor  CC=20  out:2
    description  CC=3  out:1
    deviceRows  CC=2  out:1
    escapeHtml  CC=1  out:2
    extractRunResult  CC=10  out:0
    filter  CC=3  out:1
    focusArea  CC=3  out:6
    focusTargetFor  CC=2  out:0
  11-novnc_lan_flow.computer.browser_node  [16 funcs]
    do_GET  CC=6  out:6
    do_OPTIONS  CC=1  out:1
    do_POST  CC=9  out:23
    log_message  CC=1  out:2
    app_service_call  CC=22  out:35
    current_url  CC=3  out:4
    ensure_session  CC=6  out:7
    json_response  CC=1  out:12
    log  CC=2  out:2
    main  CC=1  out:5
  11-novnc_lan_flow.orchestrator.run_flow  [6 funcs]
    collect_routes  CC=4  out:10
    fetch_json  CC=4  out:7
    main  CC=7  out:12
    run_step  CC=2  out:8
    target_from_uri  CC=2  out:2
    wait_health  CC=4  out:6
  12-full_e2e_connect_lab.registry-runtime.registry_server  [5 funcs]
    do_GET  CC=4  out:9
    discover  CC=4  out:9
    get_json  CC=2  out:4
    nodes  CC=4  out:6
    registry_document  CC=5  out:7
  12-full_e2e_connect_lab.scripts.assert_results  [2 funcs]
    load  CC=1  out:2
    main  CC=38  out:60
  12-full_e2e_connect_lab.scripts.connector_checks  [14 funcs]
    build_registry  CC=1  out:38
    emit_browser_control_bindings  CC=1  out:3
    emit_http_check_bindings  CC=1  out:3
    emit_time_tools_bindings  CC=1  out:3
    fetch_catalog  CC=1  out:6
    main  CC=20  out:30
    project_mcp_a2a  CC=1  out:4
    run  CC=4  out:2
    run_connector_routes  CC=7  out:47
    run_json  CC=2  out:3
  12-full_e2e_connect_lab.scripts.run_full_scenario  [1 funcs]
    print  CC=0  out:0
  13-simple_defaults.js.defaults  [6 funcs]
    boolean  CC=1  out:1
    connector  CC=2  out:13
    field  CC=2  out:1
    fullUri  CC=2  out:2
    integer  CC=1  out:1
    string  CC=1  out:1
  13-simple_defaults.python_connector  [2 funcs]
    bindings  CC=1  out:1
    main  CC=2  out:5

EDGES:
  06-html_uri_app.app.routeResponse → 06-html_uri_app.app.renderActions
  06-html_uri_app.app.routeResponse → 06-html_uri_app.app.renderForm
  06-html_uri_app.app.renderActions → 06-html_uri_app.app.classFor
  06-html_uri_app.app.renderActions → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.renderActions → 06-html_uri_app.app.iconFor
  06-html_uri_app.app.renderForm → 06-html_uri_app.app.schemaFor
  06-html_uri_app.app.renderForm → 06-html_uri_app.app.payloadDefaults
  06-html_uri_app.app.renderForm → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.required → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.defaults → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.inputType → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.refreshLogs → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.data → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.card → 06-html_uri_app.app.renderToolList
  06-html_uri_app.app.renderToolList → 06-html_uri_app.app.escapeHtml
  06-html_uri_app.app.iconFor → 06-html_uri_app.app.classFor
  09-docker_uri_flow.node-worker.server.server → 09-docker_uri_flow.node-worker.server.send
  09-docker_uri_flow.node-worker.server.server → 09-docker_uri_flow.node-worker.server.readBody
  09-docker_uri_flow.node-worker.server.server → 09-docker_uri_flow.node-worker.server.slugify
  09-docker_uri_flow.node-worker.server.body → 09-docker_uri_flow.node-worker.server.send
  09-docker_uri_flow.node-worker.server.slug → 09-docker_uri_flow.node-worker.server.send
  10-device_mesh_lab.www.app.showView → 10-device_mesh_lab.www.app.setMenuActive
  10-device_mesh_lab.www.app.focusArea → 10-device_mesh_lab.www.app.showView
  10-device_mesh_lab.www.app.focusArea → 10-device_mesh_lab.www.app.setMenuActive
  10-device_mesh_lab.www.app.focusArea → 10-device_mesh_lab.www.app.focusTargetFor
  10-device_mesh_lab.www.app.recordActivity → 10-device_mesh_lab.www.app.renderActivityLog
  10-device_mesh_lab.www.app.routeBadge → 10-device_mesh_lab.www.app.isRouteSafe
  10-device_mesh_lab.www.app.renderDevices → 10-device_mesh_lab.www.app.filter
  10-device_mesh_lab.www.app.renderDevices → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.reachable → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.installable → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.novncUrlFor → 10-device_mesh_lab.www.app.novncEntryFor
  10-device_mesh_lab.www.app.renderNovnc → 10-device_mesh_lab.www.app.novncUrlFor
  10-device_mesh_lab.www.app.renderNovnc → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.url → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.status → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.renderRoutes → 10-device_mesh_lab.www.app.filter
  10-device_mesh_lab.www.app.renderRoutes → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.renderRoutes → 10-device_mesh_lab.www.app.routeBadge
  10-device_mesh_lab.www.app.filter → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.rows → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.renderRoutes
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.renderPayloadForm
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.setMenuActive
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.showJson
  10-device_mesh_lab.www.app.selectRoute → 10-device_mesh_lab.www.app.previewPayload
  10-device_mesh_lab.www.app.renderField → 10-device_mesh_lab.www.app.defaultValueFor
  10-device_mesh_lab.www.app.renderField → 10-device_mesh_lab.www.app.escapeHtml
  10-device_mesh_lab.www.app.renderField → 10-device_mesh_lab.www.app.valueToInput
  10-device_mesh_lab.www.app.description → 10-device_mesh_lab.www.app.escapeHtml
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 125f 60653L | json:49,python:19,shell:14,javascript:11,yml:5,txt:3,yaml:2,toml:1,go:1,typescript:1,php:1,c:1 | 2026-06-21
# generated in 0.02s
# CC̅=3.5 | critical:14/348 | dups:5 | cycles:0

HEALTH[15]:
  🔴 DUP   5 classes duplicated
  🟡 CC    defaultValueFor CC=20 (limit:15)
  🟡 CC    renderDevices CC=15 (limit:15)
  🟡 CC    reachable CC=15 (limit:15)
  🟡 CC    renderField CC=15 (limit:15)
  🟡 CC    main CC=20 (limit:15)
  🟡 CC    parse_flow CC=24 (limit:15)
  🟡 CC    main CC=38 (limit:15)
  🟡 CC    parse_browser_targets CC=19 (limit:15)
  🟡 CC    dispatch CC=27 (limit:15)
  🟡 CC    fallback_steps CC=33 (limit:15)
  🟡 CC    postprocess_flow CC=20 (limit:15)
  🟡 CC    normalize_flow CC=20 (limit:15)
  🟡 CC    app_service_call CC=22 (limit:15)
  🟡 CC    md CC=28 (limit:15)

REFACTOR[2]:
  1. rm duplicates  (-5 dup classes)
  2. split 14 high-CC methods  (CC>15)

PIPELINES[133]:
  [1] Src [bindings]: bindings
      PURITY: 100% pure
  [2] Src [routeResponse]: routeResponse → renderActions → classFor
      PURITY: 100% pure
  [3] Src [button]: button
      PURITY: 100% pure
  [4] Src [result]: result
      PURITY: 100% pure
  [5] Src [required]: required → escapeHtml
      PURITY: 100% pure
  [6] Src [defaults]: defaults → escapeHtml
      PURITY: 100% pure
  [7] Src [inputType]: inputType → escapeHtml
      PURITY: 100% pure
  [8] Src [payloadFromForm]: payloadFromForm
      PURITY: 100% pure
  [9] Src [refreshLogs]: refreshLogs → escapeHtml
      PURITY: 100% pure
  [10] Src [data]: data → escapeHtml
      PURITY: 100% pure
  [11] Src [manifest]: manifest
      PURITY: 100% pure
  [12] Src [card]: card → renderToolList → escapeHtml
      PURITY: 100% pure
  [13] Src [key]: key
      PURITY: 100% pure
  [14] Src [http]: http
      PURITY: 100% pure
  [15] Src [fs]: fs
      PURITY: 100% pure
  [16] Src [path]: path
      PURITY: 100% pure
  [17] Src [bindings]: bindings
      PURITY: 100% pure
  [18] Src [data]: data
      PURITY: 100% pure
  [19] Src [server]: server → send
      PURITY: 100% pure
  [20] Src [body]: body → send
      PURITY: 100% pure
  [21] Src [slug]: slug → send
      PURITY: 100% pure
  [22] Src [selectedRoute]: selectedRoute
      PURITY: 100% pure
  [23] Src [focusArea]: focusArea → showView → setMenuActive
      PURITY: 100% pure
  [24] Src [target]: target
      PURITY: 100% pure
  [25] Src [reachable]: reachable → escapeHtml
      PURITY: 100% pure
  [26] Src [installable]: installable → escapeHtml
      PURITY: 100% pure
  [27] Src [url]: url → escapeHtml
      PURITY: 100% pure
  [28] Src [status]: status → escapeHtml
      PURITY: 100% pure
  [29] Src [rows]: rows → escapeHtml
      PURITY: 100% pure
  [30] Src [selectRoute]: selectRoute → renderRoutes → filter → escapeHtml
      PURITY: 100% pure
  [31] Src [description]: description → escapeHtml
      PURITY: 100% pure
  [32] Src [inputType]: inputType → escapeHtml
      PURITY: 100% pure
  [33] Src [step]: step → escapeHtml
      PURITY: 100% pure
  [34] Src [required]: required → escapeHtml
      PURITY: 100% pure
  [35] Src [trimmed]: trimmed
      PURITY: 100% pure
  [36] Src [li]: li → escapeHtml
      PURITY: 100% pure
  [37] Src [frontendRows]: frontendRows → escapeHtml
      PURITY: 100% pure
  [38] Src [deviceRows]: deviceRows → escapeHtml
      PURITY: 100% pure
  [39] Src [groups]: groups → routeByUri
      PURITY: 100% pure
  [40] Src [data]: data → showJson
      PURITY: 100% pure
  [41] Src [runNlFlow]: runNlFlow → recordActivity → renderActivityLog → escapeHtml
      PURITY: 100% pure
  [42] Src [prompt]: prompt → recordActivity → renderActivityLog → escapeHtml
      PURITY: 100% pure
  [43] Src [runSelectedRoute]: runSelectedRoute → payloadFromForm → parsePayloadValue
      PURITY: 100% pure
  [44] Src [row]: row → recordActivity → renderActivityLog → escapeHtml
      PURITY: 100% pure
  [45] Src [echo_message]: echo_message
      PURITY: 100% pure
  [46] Src [transcode]: transcode
      PURITY: 100% pure
  [47] Src [shell_echo]: shell_echo
      PURITY: 100% pure
  [48] Src [main]: main
      PURITY: 100% pure
  [49] Src [greet]: greet
      PURITY: 100% pure
  [50] Src [document]: document
      PURITY: 100% pure

LAYERS:
  scripts/                        CC̄=12.7   ←in:0  →out:0
  │ !! build_site                 138L  0C    3m  CC=28     ←0
  │ deploy-plesk.sh             21L  0C    0m  CC=0.0    ←0
  │
  11-novnc_lan_flow/              CC̄=4.6    ←in:0  →out:0  ×DUP
  │ !! smoke-output.json          663L  0C    0m  CC=0.0    ←0
  │ !! browser_node               331L  1C   17m  CC=22     ←1  ×DUP
  │ run_flow                   279L  0C    6m  CC=7      ←0
  │ flow-result.json           276L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml         123L  0C    0m  CC=0.0    ←0
  │ smoke.sh                    94L  0C    1m  CC=0.0    ←0
  │ registry.json               65L  0C    0m  CC=0.0    ←0
  │ Makefile                    45L  0C    0m  CC=0.0    ←0
  │ runtime-config.js           13L  0C    0m  CC=0.0    ←0
  │ routes.txt                  12L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   9L  0C    0m  CC=0.0    ←0
  │
  12-full_e2e_connect_lab/        CC̄=4.1    ←in:0  →out:0
  │ !! connectors-result.json   25765L  0C    0m  CC=0.0    ←0
  │ !! connectors-install-registry.json  8163L  0C    0m  CC=0.0    ←0
  │ !! connectors-registry.json  8163L  0C    0m  CC=0.0    ←0
  │ !! monitor-bindings.json     2150L  0C    0m  CC=0.0    ←0
  │ !! task-bindings.json        1838L  0C    0m  CC=0.0    ←0
  │ !! agents.json               1590L  0C    0m  CC=0.0    ←0
  │ !! nodes.json                1066L  0C    0m  CC=0.0    ←0
  │ !! connectors-catalog.json    842L  0C    0m  CC=0.0    ←0
  │ !! data-bindings.json         725L  0C    0m  CC=0.0    ←0
  │ flow-result.json           476L  0C    0m  CC=0.0    ←0
  │ !! connector_checks           409L  0C   15m  CC=20     ←1
  │ registry-runtime.json      266L  0C    0m  CC=0.0    ←0
  │ routes.json                260L  0C    0m  CC=0.0    ←0
  │ !! assert_results             116L  0C    2m  CC=38     ←0
  │ registry_server            105L  1C    7m  CC=5      ←0
  │ browser-control-bindings.json    96L  0C    0m  CC=0.0    ←0
  │ run_full_scenario.sh        92L  0C    4m  CC=0.0    ←10
  │ docker-compose.yml          60L  0C    0m  CC=0.0    ←0
  │ http-check-bindings.json    47L  0C    0m  CC=0.0    ←0
  │ public_smoke.sh             40L  0C    1m  CC=0.0    ←0
  │ connectors-install-routes.txt    39L  0C    0m  CC=0.0    ←0
  │ time-tools-bindings.json    39L  0C    0m  CC=0.0    ←0
  │ user_scenario.yaml          26L  0C    0m  CC=0.0    ←0
  │ Makefile                    25L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  17L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T214509Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T211850Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260620T001713Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T233508Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T234253Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T233741Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T234757Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T230901Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T215253Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T221603Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260620T004537Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T213510Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T222801Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T230706Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260620T000445Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260619T224704Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ example.test-20260620T005133Z.dns-backup.json    13L  0C    0m  CC=0.0    ←0
  │ connectors-policy.json       7L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   7L  0C    0m  CC=0.0    ←0
  │
  10-device_mesh_lab/             CC̄=4.0    ←in:2  →out:5
  │ !! device_agent               608L  1C   23m  CC=27     ←2
  │ !! app.js                     562L  0C   91m  CC=20     ←4
  │ !! controller                 490L  1C   28m  CC=33     ←0
  │ mesh_env                    78L  0C    7m  CC=9      ←2
  │ runtime-config.js           13L  0C    1m  CC=2      ←0
  │
  09-docker_uri_flow/             CC̄=3.3    ←in:0  →out:0  ×DUP
  │ !! registry.json             1069L  0C    0m  CC=0.0    ←0
  │ !! bindings.v2.json           521L  0C    0m  CC=0.0    ←0
  │ !! flow_runner                221L  0C   16m  CC=24     ←0
  │ server                      71L  1C    7m  CC=6      ←0  ×DUP
  │ server                      67L  1C    5m  CC=6      ←2  ×DUP
  │ server.js                   55L  0C   11m  CC=10     ←1
  │ docker-compose.yml          48L  0C    0m  CC=0.0    ←0
  │ cross_service_report.yaml    39L  0C    0m  CC=0.0    ←0
  │ docker-compose.test.yml     34L  0C    0m  CC=0.0    ←0
  │ bindings.json               31L  0C    0m  CC=0.0    ←0
  │ generate_registry.sh        29L  0C    0m  CC=0.0    ←0
  │ Makefile                    20L  0C    0m  CC=0.0    ←0
  │ routes.txt                  20L  0C    0m  CC=0.0    ←0
  │ bindings.json               20L  0C    0m  CC=0.0    ←0
  │ bindings.json               18L  0C    0m  CC=0.0    ←0
  │ run.sh                      16L  0C    1m  CC=0.0    ←0
  │ run_tests.sh                16L  0C    1m  CC=0.0    ←0
  │ write_report.sh             12L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  12L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  10L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   9L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   9L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   7L  0C    0m  CC=0.0    ←0
  │ package.json                 6L  0C    0m  CC=0.0    ←0
  │
  06-html_uri_app/                CC̄=3.1    ←in:0  →out:13  !! split  ×DUP
  │ backend                    230L  1C   18m  CC=8      ←0  ×DUP
  │ app.js                     170L  0C   24m  CC=10     ←0
  │ bindings.json               74L  0C    0m  CC=0.0    ←0
  │ test.mjs                    16L  0C    2m  CC=1      ←1
  │ run.sh                       8L  0C    0m  CC=0.0    ←0
  │
  07-transports/                  CC̄=2.7    ←in:0  →out:0
  │ transport_lib              155L  0C    8m  CC=6      ←0
  │ scan_and_run                52L  0C    1m  CC=6      ←0
  │ registry.bindings.json      28L  0C    0m  CC=0.0    ←0
  │ demo                        18L  0C    0m  CC=0.0    ←0
  │ Makefile                     9L  0C    0m  CC=0.0    ←0
  │
  05-generators/                  CC̄=1.5    ←in:0  →out:0
  │ example.go                  83L  4C    2m  CC=4      ←0
  │ decorators.ts               65L  1C    5m  CC=1      ←0
  │ example.php                 64L  1C    4m  CC=2      ←0
  │ uri-command.mjs             47L  0C    8m  CC=4      ←0
  │ generate-bindings.mjs       28L  0C    3m  CC=2      ←0
  │ example.c                   25L  0C    2m  CC=1      ←0
  │ example.mjs                 20L  0C    2m  CC=1      ←0
  │
  13-simple_defaults/             CC̄=1.3    ←in:0  →out:1
  │ defaults.mjs                52L  0C   10m  CC=2      ←0
  │ python_connector            40L  0C    3m  CC=2      ←0
  │ example.mjs                 23L  0C    1m  CC=1      ←0
  │
  08-multi_transport/             CC̄=1.0    ←in:0  →out:2
  │ worker                      80L  0C    3m  CC=2      ←0
  │ web-bindings.json           36L  0C    0m  CC=0.0    ←0
  │ docker-compose.test.yml     33L  0C    0m  CC=0.0    ←0
  │ rpc-bindings.json           24L  0C    0m  CC=0.0    ←0
  │ run_tests.sh                16L  0C    1m  CC=0.0    ←0
  │ Dockerfile                  15L  0C    0m  CC=0.0    ←0
  │ Makefile                     7L  0C    0m  CC=0.0    ←0
  │
  02-decorators/                  CC̄=1.0    ←in:0  →out:0
  │ example                     28L  0C    3m  CC=1      ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ run_tests.sh                92L  0C    1m  CC=0.0    ←0
  │ project.sh                  66L  0C    0m  CC=0.0    ←0
  │ Makefile                    14L  0C    0m  CC=0.0    ←0
  │ tree.sh                      4L  0C    0m  CC=0.0    ←0
  │
  03-artifacts/                   CC̄=0.0    ←in:0  →out:0
  │ urirun.manifest.json        18L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   9L  0C    0m  CC=0.0    ←0
  │ deploy.sh                    6L  0C    0m  CC=0.0    ←0
  │ pyproject.toml               6L  0C    0m  CC=0.0    ←0
  │ package.json                 6L  0C    0m  CC=0.0    ←0
  │ Makefile                     5L  0C    0m  CC=0.0    ←0
  │
  01-json/                        CC̄=0.0    ←in:0  →out:0
  │ bindings.v2.example.json   151L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                                                                     06-html_uri_app                11-novnc_lan_flow.computer                    10-device_mesh_lab.www           12-full_e2e_connect_lab.scripts           09-docker_uri_flow.shell-worker                        10-device_mesh_lab          09-docker_uri_flow.python-worker            09-docker_uri_flow.node-worker  12-full_e2e_connect_lab.registry-runtime                        08-multi_transport           09-docker_uri_flow.orchestrator            11-novnc_lan_flow.orchestrator                        13-simple_defaults
                           06-html_uri_app                                        ──                                        10                                                                                   1                                         1                                         1                                                                                                                                                                                                                                                                                                        !! fan-out
                11-novnc_lan_flow.computer                                       ←10                                        ──                                                                                   2                                                                                   1                                                                                                                                                                                                                                                                                                        hub
                    10-device_mesh_lab.www                                                                                                                            ──                                                                                  ←5                                        ←2                                        ←5                                                                                                                                                                                                                                                              hub
           12-full_e2e_connect_lab.scripts                                        ←1                                        ←2                                                                                  ──                                                                                  ←3                                                                                                                                                                      ←2                                        ←1                                        ←1                                        ←1  hub
           09-docker_uri_flow.shell-worker                                        ←1                                                                                   5                                                                                  ──                                                                                  ←1                                                                                                                                                                                                                                                            
                        10-device_mesh_lab                                        ←1                                        ←1                                         2                                         3                                                                                  ──                                                                                                                                                                                                                                                                                                      
          09-docker_uri_flow.python-worker                                                                                                                             5                                                                                   1                                                                                  ──                                                                                                                                                                                                                                                            
            09-docker_uri_flow.node-worker                                                                                                                                                                                                                                                                                                                                              ──                                        ←4                                                                                                                                                                        
  12-full_e2e_connect_lab.registry-runtime                                                                                                                                                                                                                                                                                                                                               4                                        ──                                                                                                                                                                        
                        08-multi_transport                                                                                                                                                                       2                                                                                                                                                                                                                                                          ──                                                                                                                              
           09-docker_uri_flow.orchestrator                                                                                                                                                                       1                                                                                                                                                                                                                                                                                                    ──                                                                                    
            11-novnc_lan_flow.orchestrator                                                                                                                                                                       1                                                                                                                                                                                                                                                                                                                                              ──                                          
                        13-simple_defaults                                                                                                                                                                       1                                                                                                                                                                                                                                                                                                                                                                                        ──
  CYCLES: none
  HUB: 11-novnc_lan_flow.computer/ (fan-in=10)
  HUB: 12-full_e2e_connect_lab.scripts/ (fan-in=11)
  HUB: 10-device_mesh_lab.www/ (fan-in=12)
  SMELL: 06-html_uri_app/ fan-out=13 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 142 groups | 33f 6672L | 2026-06-21

SUMMARY:
  files_scanned: 33
  total_lines:   6672
  dup_groups:    142
  dup_fragments: 290
  saved_lines:   2471
  scan_ms:       2058

HOTSPOTS[7] (files with most duplication):
  10-device_mesh_lab/device_agent.py  dup=576L  groups=24  frags=24  (8.6%)
  _site/10-device_mesh_lab/device_agent.py  dup=576L  groups=24  frags=24  (8.6%)
  10-device_mesh_lab/controller.py  dup=402L  groups=25  frags=25  (6.0%)
  _site/10-device_mesh_lab/controller.py  dup=402L  groups=25  frags=25  (6.0%)
  12-full_e2e_connect_lab/scripts/connector_checks.py  dup=350L  groups=12  frags=14  (5.2%)
  _site/12-full_e2e_connect_lab/scripts/connector_checks.py  dup=350L  groups=12  frags=14  (5.2%)
  11-novnc_lan_flow/computer/browser_node.py  dup=234L  groups=14  frags=14  (3.5%)

DUPLICATES[142] (ranked by impact):
  [69be9d2dc0b22042] !! EXAC  routes  L=114 N=2 saved=114 sim=1.00
      10-device_mesh_lab/device_agent.py:192-305  (routes)
      _site/10-device_mesh_lab/device_agent.py:192-305  (routes)
  [01d0f16764749e12] !! EXAC  run_connector_routes  L=111 N=2 saved=111 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:148-258  (run_connector_routes)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:148-258  (run_connector_routes)
  [d75072a96d87e93c] ! EXAC  main  L=98 N=2 saved=98 sim=1.00
      12-full_e2e_connect_lab/scripts/assert_results.py:15-112  (main)
      _site/12-full_e2e_connect_lab/scripts/assert_results.py:15-112  (main)
  [1db8e95a160a7266] ! EXAC  open_browser_in_novnc  L=68 N=2 saved=68 sim=1.00
      10-device_mesh_lab/device_agent.py:398-465  (open_browser_in_novnc)
      _site/10-device_mesh_lab/device_agent.py:398-465  (open_browser_in_novnc)
  [66d956965e2c74fc] ! EXAC  main  L=67 N=2 saved=67 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:339-405  (main)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:339-405  (main)
  [c3dd9c583859a60e] ! EXAC  fallback_steps  L=58 N=2 saved=58 sim=1.00
      10-device_mesh_lab/controller.py:140-197  (fallback_steps)
      _site/10-device_mesh_lab/controller.py:140-197  (fallback_steps)
  [64af2882eea11da3] ! EXAC  app_service_call  L=55 N=2 saved=55 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:206-260  (app_service_call)
      _site/11-novnc_lan_flow/computer/browser_node.py:206-260  (app_service_call)
  [e9774a4d0b8a637f] ! EXAC  handler  L=52 N=2 saved=52 sim=1.00
      10-device_mesh_lab/device_agent.py:522-573  (handler)
      _site/10-device_mesh_lab/device_agent.py:522-573  (handler)
  [147928cf7e6743e9] ! EXAC  parse_flow  L=49 N=2 saved=49 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:22-70  (parse_flow)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:22-70  (parse_flow)
  [49f26202cd168674] ! EXAC  build_novnc_browser_command  L=47 N=2 saved=47 sim=1.00
      10-device_mesh_lab/device_agent.py:87-133  (build_novnc_browser_command)
      _site/10-device_mesh_lab/device_agent.py:87-133  (build_novnc_browser_command)
  [dff326e03a7a6ba3] ! EXAC  build_registry  L=47 N=2 saved=47 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:88-134  (build_registry)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:88-134  (build_registry)
  [83c8eb67ddbae959] ! EXAC  test_grpc_transport  L=47 N=2 saved=47 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:267-313  (test_grpc_transport)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:267-313  (test_grpc_transport)
  [1cdaacabf78eb042] ! EXAC  normalize_flow  L=43 N=2 saved=43 sim=1.00
      10-device_mesh_lab/controller.py:270-312  (normalize_flow)
      _site/10-device_mesh_lab/controller.py:270-312  (normalize_flow)
  [a28b24d71479ef10] ! STRU  emit_http_check_bindings  L=8 N=6 saved=40 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:58-65  (emit_http_check_bindings)
      12-full_e2e_connect_lab/scripts/connector_checks.py:68-75  (emit_time_tools_bindings)
      12-full_e2e_connect_lab/scripts/connector_checks.py:78-85  (emit_browser_control_bindings)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:58-65  (emit_http_check_bindings)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:68-75  (emit_time_tools_bindings)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:78-85  (emit_browser_control_bindings)
  [7ad782d3381b6a0e] ! EXAC  start_http_worker  L=33 N=2 saved=33 sim=1.00
      07-transports/transport_lib.py:76-108  (start_http_worker)
      _site/07-transports/transport_lib.py:76-108  (start_http_worker)
  [45f340716cd80ce3] ! EXAC  ensure_session  L=33 N=2 saved=33 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:113-145  (ensure_session)
      _site/11-novnc_lan_flow/computer/browser_node.py:113-145  (ensure_session)
  [0f7c1d0b2bf66ba2] ! EXAC  serve_http  L=31 N=2 saved=31 sim=1.00
      08-multi_transport/worker.py:39-69  (serve_http)
      _site/08-multi_transport/worker.py:39-69  (serve_http)
  [c6bc700b9202c42e]   EXAC  postprocess_flow  L=30 N=2 saved=30 sim=1.00
      10-device_mesh_lab/controller.py:225-254  (postprocess_flow)
      _site/10-device_mesh_lab/controller.py:225-254  (postprocess_flow)
  [dc4d5586968e7846]   EXAC  installable  L=30 N=2 saved=30 sim=1.00
      10-device_mesh_lab/device_agent.py:323-352  (installable)
      _site/10-device_mesh_lab/device_agent.py:323-352  (installable)
  [1382976c55d8ffff]   EXAC  parse_browser_targets  L=29 N=2 saved=29 sim=1.00
      10-device_mesh_lab/device_agent.py:56-84  (parse_browser_targets)
      _site/10-device_mesh_lab/device_agent.py:56-84  (parse_browser_targets)
  [e49cff6e205822b6]   EXAC  dispatch  L=29 N=2 saved=29 sim=1.00
      10-device_mesh_lab/device_agent.py:492-520  (dispatch)
      _site/10-device_mesh_lab/device_agent.py:492-520  (dispatch)
  [6383d3f2a07c922c]   EXAC  screenshot_page  L=29 N=2 saved=29 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:175-203  (screenshot_page)
      _site/11-novnc_lan_flow/computer/browser_node.py:175-203  (screenshot_page)
  [b5af7fa4f56a9f21]   EXAC  make_handler  L=28 N=2 saved=28 sim=1.00
      07-transports/transport_lib.py:77-104  (make_handler)
      _site/07-transports/transport_lib.py:77-104  (make_handler)
  [f434d0e66b7adbd5]   EXAC  run_via  L=27 N=2 saved=27 sim=1.00
      07-transports/transport_lib.py:114-140  (run_via)
      _site/07-transports/transport_lib.py:114-140  (run_via)
  [b04a632e9e4f79ce]   EXAC  llm_messages  L=27 N=2 saved=27 sim=1.00
      10-device_mesh_lab/controller.py:315-341  (llm_messages)
      _site/10-device_mesh_lab/controller.py:315-341  (llm_messages)
  [9adb30d1951350ce]   EXAC  main  L=26 N=2 saved=26 sim=1.00
      07-transports/scan_and_run.py:23-48  (main)
      _site/07-transports/scan_and_run.py:23-48  (main)
  [8f83c265747e2de9]   EXAC  discover_device  L=25 N=2 saved=25 sim=1.00
      10-device_mesh_lab/controller.py:72-96  (discover_device)
      _site/10-device_mesh_lab/controller.py:72-96  (discover_device)
  [e3cf3327b4b3163a]   EXAC  do_POST  L=25 N=2 saved=25 sim=1.00
      10-device_mesh_lab/controller.py:446-470  (do_POST)
      _site/10-device_mesh_lab/controller.py:446-470  (do_POST)
  [71a6b41e428d0a5e]   EXAC  registry_document  L=25 N=2 saved=25 sim=1.00
      12-full_e2e_connect_lab/registry-runtime/registry_server.py:49-73  (registry_document)
      _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py:49-73  (registry_document)
  [432bb098a0d952ba]   EXAC  do_GET  L=24 N=2 saved=24 sim=1.00
      06-html_uri_app/backend.py:145-168  (do_GET)
      _site/06-html_uri_app/backend.py:145-168  (do_GET)
  [0ea86459b4cfe4ba]   EXAC  execute_flow  L=24 N=2 saved=24 sim=1.00
      10-device_mesh_lab/controller.py:384-407  (execute_flow)
      _site/10-device_mesh_lab/controller.py:384-407  (execute_flow)
  [b64fdc47caad31cd]   EXAC  open_browser  L=24 N=2 saved=24 sim=1.00
      10-device_mesh_lab/device_agent.py:467-490  (open_browser)
      _site/10-device_mesh_lab/device_agent.py:467-490  (open_browser)
  [3f007f8cc27a7f38]   EXAC  dispatch  L=22 N=2 saved=22 sim=1.00
      06-html_uri_app/backend.py:98-119  (dispatch)
      _site/06-html_uri_app/backend.py:98-119  (dispatch)
  [adcbcce722c5fe8d]   EXAC  _send  L=7 N=4 saved=21 sim=1.00
      07-transports/transport_lib.py:82-88  (_send)
      08-multi_transport/worker.py:44-50  (_send)
      _site/07-transports/transport_lib.py:82-88  (_send)
      _site/08-multi_transport/worker.py:44-50  (_send)
  [8caacb912f08722e]   EXAC  do_POST  L=21 N=2 saved=21 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:298-318  (do_POST)
      _site/11-novnc_lan_flow/computer/browser_node.py:298-318  (do_POST)
  [e587783ba85be9d2]   EXAC  summarize_catalog  L=21 N=2 saved=21 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:316-336  (summarize_catalog)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:316-336  (summarize_catalog)
  [bfc435fc38efa7db]   EXAC  main  L=20 N=2 saved=20 sim=1.00
      06-html_uri_app/backend.py:207-226  (main)
      _site/06-html_uri_app/backend.py:207-226  (main)
  [21314c8961dae93c]   EXAC  run_flow  L=19 N=2 saved=19 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:191-209  (run_flow)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:191-209  (run_flow)
  [6dfebe44aa82c9f1]   EXAC  do_GET  L=19 N=2 saved=19 sim=1.00
      10-device_mesh_lab/device_agent.py:535-553  (do_GET)
      _site/10-device_mesh_lab/device_agent.py:535-553  (do_GET)
  [1d90d6c1bd15b13a]   EXAC  webdriver  L=19 N=2 saved=19 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:79-97  (webdriver)
      _site/11-novnc_lan_flow/computer/browser_node.py:79-97  (webdriver)
  [4920fe15ccae2d54]   EXAC  collect_routes  L=19 N=2 saved=19 sim=1.00
      11-novnc_lan_flow/orchestrator/run_flow.py:220-238  (collect_routes)
      _site/11-novnc_lan_flow/orchestrator/run_flow.py:220-238  (collect_routes)
  [8d8c719de35fe055]   EXAC  generate_with_litellm  L=18 N=2 saved=18 sim=1.00
      10-device_mesh_lab/controller.py:344-361  (generate_with_litellm)
      _site/10-device_mesh_lab/controller.py:344-361  (generate_with_litellm)
  [9304122e74b562a1]   EXAC  generate_flow  L=18 N=2 saved=18 sim=1.00
      10-device_mesh_lab/controller.py:364-381  (generate_flow)
      _site/10-device_mesh_lab/controller.py:364-381  (generate_flow)
  [f58a6444ee5fe8e2]   EXAC  main  L=18 N=2 saved=18 sim=1.00
      11-novnc_lan_flow/orchestrator/run_flow.py:258-275  (main)
      _site/11-novnc_lan_flow/orchestrator/run_flow.py:258-275  (main)
  [8a771b93305e6379]   EXAC  discover  L=18 N=2 saved=18 sim=1.00
      12-full_e2e_connect_lab/registry-runtime/registry_server.py:29-46  (discover)
      _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py:29-46  (discover)
  [e0b517f6d492fa9e]   EXAC  dispatch  L=17 N=2 saved=17 sim=1.00
      09-docker_uri_flow/shell-worker/server.py:25-41  (dispatch)
      _site/09-docker_uri_flow/shell-worker/server.py:25-41  (dispatch)
  [f63f80b5015a841c]   EXAC  __init__  L=17 N=2 saved=17 sim=1.00
      10-device_mesh_lab/device_agent.py:137-153  (__init__)
      _site/10-device_mesh_lab/device_agent.py:137-153  (__init__)
  [afd212c4eda94230]   EXAC  wait_for_services  L=16 N=2 saved=16 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:173-188  (wait_for_services)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:173-188  (wait_for_services)
  [2bc50b639283b96e]   EXAC  dispatch_tool  L=15 N=2 saved=15 sim=1.00
      06-html_uri_app/backend.py:122-136  (dispatch_tool)
      _site/06-html_uri_app/backend.py:122-136  (dispatch_tool)
  [9ee67aa0199f695a]   EXAC  serve_static  L=15 N=2 saved=15 sim=1.00
      06-html_uri_app/backend.py:190-204  (serve_static)
      _site/06-html_uri_app/backend.py:190-204  (serve_static)
  [96e9911f8516908c]   EXAC  nl_flow  L=15 N=2 saved=15 sim=1.00
      10-device_mesh_lab/controller.py:410-424  (nl_flow)
      _site/10-device_mesh_lab/controller.py:410-424  (nl_flow)
  [c09ee0f330d04403]   EXAC  make_agent_from_env  L=15 N=2 saved=15 sim=1.00
      10-device_mesh_lab/device_agent.py:581-595  (make_agent_from_env)
      _site/10-device_mesh_lab/device_agent.py:581-595  (make_agent_from_env)
  [ecdaeddbaf6bc42d]   EXAC  processes  L=15 N=2 saved=15 sim=1.00
      10-device_mesh_lab/device_agent.py:354-368  (processes)
      _site/10-device_mesh_lab/device_agent.py:354-368  (processes)
  [c9289c5e9acd639f]   EXAC  open_page  L=15 N=2 saved=15 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:153-167  (open_page)
      _site/11-novnc_lan_flow/computer/browser_node.py:153-167  (open_page)
  [5a4d7396cdfd6c47]   EXAC  run_step  L=15 N=2 saved=15 sim=1.00
      11-novnc_lan_flow/orchestrator/run_flow.py:241-255  (run_step)
      _site/11-novnc_lan_flow/orchestrator/run_flow.py:241-255  (run_step)
  [702206f3a0dea8bb]   EXAC  run_queue  L=14 N=2 saved=14 sim=1.00
      07-transports/transport_lib.py:50-63  (run_queue)
      _site/07-transports/transport_lib.py:50-63  (run_queue)
  [f6c2711a33ff613d]   EXAC  main  L=14 N=2 saved=14 sim=1.00
      10-device_mesh_lab/controller.py:473-486  (main)
      _site/10-device_mesh_lab/controller.py:473-486  (main)
  [5bac0d43c5759aea]   EXAC  safe_command  L=14 N=2 saved=14 sim=1.00
      10-device_mesh_lab/device_agent.py:370-383  (safe_command)
      _site/10-device_mesh_lab/device_agent.py:370-383  (safe_command)
  [619d9326ceccdf63]   EXAC  do_POST  L=14 N=2 saved=14 sim=1.00
      10-device_mesh_lab/device_agent.py:555-568  (do_POST)
      _site/10-device_mesh_lab/device_agent.py:555-568  (do_POST)
  [f25a16447d0bc4a4]   EXAC  parse_peers  L=14 N=2 saved=14 sim=1.00
      10-device_mesh_lab/mesh_env.py:30-43  (parse_peers)
      _site/10-device_mesh_lab/mesh_env.py:30-43  (parse_peers)
  [917d8587531254e2]   EXAC  route_call  L=14 N=2 saved=14 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:263-276  (route_call)
      _site/11-novnc_lan_flow/computer/browser_node.py:263-276  (route_call)
  [95868e767b5c1efe]   EXAC  do_POST  L=13 N=2 saved=13 sim=1.00
      06-html_uri_app/backend.py:170-182  (do_POST)
      _site/06-html_uri_app/backend.py:170-182  (do_POST)
  [3d495216039e39c8]   EXAC  service_url  L=13 N=2 saved=13 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:90-102  (service_url)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:90-102  (service_url)
  [9000c08e82a83f30]   EXAC  log  L=13 N=2 saved=13 sim=1.00
      10-device_mesh_lab/device_agent.py:155-167  (log)
      _site/10-device_mesh_lab/device_agent.py:155-167  (log)
  [43781593e7d48b40]   EXAC  load_env  L=13 N=2 saved=13 sim=1.00
      10-device_mesh_lab/mesh_env.py:15-27  (load_env)
      _site/10-device_mesh_lab/mesh_env.py:15-27  (load_env)
  [5a7ff067345a256f]   EXAC  discover_mesh  L=12 N=2 saved=12 sim=1.00
      10-device_mesh_lab/controller.py:99-110  (discover_mesh)
      _site/10-device_mesh_lab/controller.py:99-110  (discover_mesh)
  [ee8fc1cc792a3b92]   EXAC  route_summary  L=12 N=2 saved=12 sim=1.00
      10-device_mesh_lab/controller.py:126-137  (route_summary)
      _site/10-device_mesh_lab/controller.py:126-137  (route_summary)
  [f9771b6228b37b60]   EXAC  append_step_if_missing  L=12 N=2 saved=12 sim=1.00
      10-device_mesh_lab/controller.py:211-222  (append_step_if_missing)
      _site/10-device_mesh_lab/controller.py:211-222  (append_step_if_missing)
  [2b0aff66365792c8]   EXAC  device_card  L=12 N=2 saved=12 sim=1.00
      10-device_mesh_lab/device_agent.py:307-318  (device_card)
      _site/10-device_mesh_lab/device_agent.py:307-318  (device_card)
  [f6aecf287cb68d0d]   EXAC  open_browser_on_host  L=12 N=2 saved=12 sim=1.00
      10-device_mesh_lab/device_agent.py:385-396  (open_browser_on_host)
      _site/10-device_mesh_lab/device_agent.py:385-396  (open_browser_on_host)
  [dc6db96e07a3ed30]   EXAC  wait_health  L=12 N=2 saved=12 sim=1.00
      11-novnc_lan_flow/orchestrator/run_flow.py:206-217  (wait_health)
      _site/11-novnc_lan_flow/orchestrator/run_flow.py:206-217  (wait_health)
  [584acb8fd093e0dd]   EXAC  do_GET  L=12 N=2 saved=12 sim=1.00
      12-full_e2e_connect_lab/registry-runtime/registry_server.py:87-98  (do_GET)
      _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py:87-98  (do_GET)
  [92579cd8e453d4a3]   EXAC  routes  L=11 N=2 saved=11 sim=1.00
      06-html_uri_app/backend.py:55-65  (routes)
      _site/06-html_uri_app/backend.py:55-65  (routes)
  [47accdf766b5b304]   EXAC  route_binding  L=11 N=2 saved=11 sim=1.00
      10-device_mesh_lab/controller.py:54-64  (route_binding)
      _site/10-device_mesh_lab/controller.py:54-64  (route_binding)
  [736e2f548dee1d93]   EXAC  json_from_text  L=11 N=2 saved=11 sim=1.00
      10-device_mesh_lab/controller.py:257-267  (json_from_text)
      _site/10-device_mesh_lab/controller.py:257-267  (json_from_text)
  [9dfc6e53258f8a35]   EXAC  append_note  L=11 N=2 saved=11 sim=1.00
      10-device_mesh_lab/device_agent.py:180-190  (append_note)
      _site/10-device_mesh_lab/device_agent.py:180-190  (append_note)
  [fff92108cc147bec]   EXAC  wait_for_webdriver  L=11 N=2 saved=11 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:100-110  (wait_for_webdriver)
      _site/11-novnc_lan_flow/computer/browser_node.py:100-110  (wait_for_webdriver)
  [e0246bed1ebba275]   EXAC  do_GET  L=11 N=2 saved=11 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:286-296  (do_GET)
      _site/11-novnc_lan_flow/computer/browser_node.py:286-296  (do_GET)
  [6280520d06464a75]   EXAC  run  L=11 N=2 saved=11 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:26-36  (run)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:26-36  (run)
  [cff493113a62e4ad]   EXAC  registry_route_count  L=10 N=2 saved=10 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:131-140  (registry_route_count)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:131-140  (registry_route_count)
  [2cb9ab82c8947850]   EXAC  recent_logs  L=10 N=2 saved=10 sim=1.00
      10-device_mesh_lab/device_agent.py:169-178  (recent_logs)
      _site/10-device_mesh_lab/device_agent.py:169-178  (recent_logs)
  [fbdf403e23e1da9f]   EXAC  send_json  L=10 N=2 saved=10 sim=1.00
      10-device_mesh_lab/mesh_env.py:69-78  (send_json)
      _site/10-device_mesh_lab/mesh_env.py:69-78  (send_json)
  [b661cc4397526c9a]   EXAC  json_response  L=10 N=2 saved=10 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:63-72  (json_response)
      _site/11-novnc_lan_flow/computer/browser_node.py:63-72  (json_response)
  [5b869fb350aa94c8]   EXAC  fetch_json  L=10 N=2 saved=10 sim=1.00
      11-novnc_lan_flow/orchestrator/run_flow.py:194-203  (fetch_json)
      _site/11-novnc_lan_flow/orchestrator/run_flow.py:194-203  (fetch_json)
  [f9f49cca20a3be57]   EXAC  load_env  L=9 N=2 saved=9 sim=1.00
      06-html_uri_app/backend.py:28-36  (load_env)
      _site/06-html_uri_app/backend.py:28-36  (load_env)
  [dc4e453e5605d20a]   EXAC  json_post  L=9 N=2 saved=9 sim=1.00
      10-device_mesh_lab/controller.py:34-42  (json_post)
      _site/10-device_mesh_lab/controller.py:34-42  (json_post)
  [d487a1b1a13a6fb9]   EXAC  fallback_flow  L=9 N=2 saved=9 sim=1.00
      10-device_mesh_lab/controller.py:200-208  (fallback_flow)
      _site/10-device_mesh_lab/controller.py:200-208  (fallback_flow)
  [9d934db3435ea1f9]   EXAC  object_schema  L=9 N=2 saved=9 sim=1.00
      10-device_mesh_lab/device_agent.py:23-31  (object_schema)
      _site/10-device_mesh_lab/device_agent.py:23-31  (object_schema)
  [a474649c6f1ffb89]   EXAC  resolve_payload  L=8 N=2 saved=8 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:80-87  (resolve_payload)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:80-87  (resolve_payload)
  [3f8cd880d9569ea6]   EXAC  do_GET  L=8 N=2 saved=8 sim=1.00
      09-docker_uri_flow/shell-worker/server.py:48-55  (do_GET)
      _site/09-docker_uri_flow/shell-worker/server.py:48-55  (do_GET)
  [d12a3831451d1350]   EXAC  do_POST  L=8 N=2 saved=8 sim=1.00
      09-docker_uri_flow/shell-worker/server.py:57-64  (do_POST)
      _site/09-docker_uri_flow/shell-worker/server.py:57-64  (do_POST)
  [c67184284f1bbbce]   EXAC  nodes  L=8 N=2 saved=8 sim=1.00
      12-full_e2e_connect_lab/registry-runtime/registry_server.py:14-21  (nodes)
      _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py:14-21  (nodes)
  [50e5a3e349f60ff5]   EXAC  send  L=8 N=2 saved=8 sim=1.00
      12-full_e2e_connect_lab/registry-runtime/registry_server.py:76-83  (send)
      _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py:76-83  (send)
  [6aeab07f40a9fac1]   EXAC  json_response  L=7 N=2 saved=7 sim=1.00
      06-html_uri_app/backend.py:81-87  (json_response)
      _site/06-html_uri_app/backend.py:81-87  (json_response)
  [2f40890489960f67]   EXAC  do_POST  L=7 N=2 saved=7 sim=1.00
      07-transports/transport_lib.py:96-102  (do_POST)
      _site/07-transports/transport_lib.py:96-102  (do_POST)
  [d96bb165cb33a44b]   EXAC  do_GET  L=7 N=2 saved=7 sim=1.00
      08-multi_transport/worker.py:52-58  (do_GET)
      _site/08-multi_transport/worker.py:52-58  (do_GET)
  [a2aaf5d98a34d13b]   EXAC  do_POST  L=7 N=2 saved=7 sim=1.00
      08-multi_transport/worker.py:60-66  (do_POST)
      _site/08-multi_transport/worker.py:60-66  (do_POST)
  [fec3c7cd0fa6c593]   EXAC  normalize_uri  L=7 N=2 saved=7 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:113-119  (normalize_uri)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:113-119  (normalize_uri)
  [76f0770d711aeab8]   EXAC  registry_has_uri  L=7 N=2 saved=7 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:122-128  (registry_has_uri)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:122-128  (registry_has_uri)
  [a7f5249b488f0ca2]   EXAC  load_registry  L=7 N=2 saved=7 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:143-149  (load_registry)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:143-149  (load_registry)
  [7ddcf858f51d006b]   EXAC  validate_flow_registry  L=7 N=2 saved=7 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:152-158  (validate_flow_registry)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:152-158  (validate_flow_registry)
  [6caf3f65e898549f]   EXAC  response  L=7 N=2 saved=7 sim=1.00
      09-docker_uri_flow/shell-worker/server.py:16-22  (response)
      _site/09-docker_uri_flow/shell-worker/server.py:16-22  (response)
  [73795bbbf5c2b29b]   EXAC  main  L=7 N=2 saved=7 sim=1.00
      10-device_mesh_lab/device_agent.py:598-604  (main)
      _site/10-device_mesh_lab/device_agent.py:598-604  (main)
  [a9604e6b8ad6ac5a]   EXAC  main  L=7 N=2 saved=7 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:321-327  (main)
      _site/11-novnc_lan_flow/computer/browser_node.py:321-327  (main)
  [d8bb4dbaafb8fb70]   EXAC  add_log  L=6 N=2 saved=6 sim=1.00
      06-html_uri_app/backend.py:68-73  (add_log)
      _site/06-html_uri_app/backend.py:68-73  (add_log)
  [55e69ca9bb1abbee]   EXAC  execute_policy  L=6 N=2 saved=6 sim=1.00
      06-html_uri_app/backend.py:90-95  (execute_policy)
      _site/06-html_uri_app/backend.py:90-95  (execute_policy)
  [a7f643c11f7dc127]   EXAC  grpc_available  L=6 N=2 saved=6 sim=1.00
      07-transports/transport_lib.py:146-151  (grpc_available)
      _site/07-transports/transport_lib.py:146-151  (grpc_available)
  [e17bfb1ffabe166f]   EXAC  route_key  L=6 N=2 saved=6 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:105-110  (route_key)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:105-110  (route_key)
  [b7b22164527111ba]   EXAC  main  L=6 N=2 saved=6 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:212-217  (main)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:212-217  (main)
  [c6a6c6989956f203]   EXAC  do_GET  L=6 N=2 saved=6 sim=1.00
      10-device_mesh_lab/controller.py:439-444  (do_GET)
      _site/10-device_mesh_lab/controller.py:439-444  (do_GET)
  [c0b3d726b4aa80cf]   EXAC  browser_target_from_spec  L=6 N=2 saved=6 sim=1.00
      10-device_mesh_lab/device_agent.py:48-53  (browser_target_from_spec)
      _site/10-device_mesh_lab/device_agent.py:48-53  (browser_target_from_spec)
  [dec9d211ee005efe]   EXAC  run_json  L=6 N=2 saved=6 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:39-44  (run_json)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:39-44  (run_json)
  [a7472d1fa8d210ae]   EXAC  read_body  L=5 N=2 saved=5 sim=1.00
      06-html_uri_app/backend.py:184-188  (read_body)
      _site/06-html_uri_app/backend.py:184-188  (read_body)
  [4c938d5b6ed85818]   EXAC  do_GET  L=5 N=2 saved=5 sim=1.00
      07-transports/transport_lib.py:90-94  (do_GET)
      _site/07-transports/transport_lib.py:90-94  (do_GET)
  [97d72af47b5da733]   EXAC  discovery  L=5 N=2 saved=5 sim=1.00
      08-multi_transport/worker.py:32-36  (discovery)
      _site/08-multi_transport/worker.py:32-36  (discovery)
  [70d231959da1a57f]   EXAC  serve_grpc  L=5 N=2 saved=5 sim=1.00
      08-multi_transport/worker.py:72-76  (serve_grpc)
      _site/08-multi_transport/worker.py:72-76  (serve_grpc)
  [9249685c6f285dc2]   EXAC  parse_scalar  L=5 N=2 saved=5 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:15-19  (parse_scalar)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:15-19  (parse_scalar)
  [e92b0ce21ca177c7]   EXAC  get_path  L=5 N=2 saved=5 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:73-77  (get_path)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:73-77  (get_path)
  [f87a21eff79df87b]   EXAC  json_post  L=5 N=2 saved=5 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:166-170  (json_post)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:166-170  (json_post)
  [23101421c9739ca4]   EXAC  build_registry  L=5 N=2 saved=5 sim=1.00
      10-device_mesh_lab/controller.py:113-117  (build_registry)
      _site/10-device_mesh_lab/controller.py:113-117  (build_registry)
  [932abff75efd1dce]   EXAC  _authorized  L=5 N=2 saved=5 sim=1.00
      10-device_mesh_lab/device_agent.py:529-533  (_authorized)
      _site/10-device_mesh_lab/device_agent.py:529-533  (_authorized)
  [8941d8306b405fcd]   EXAC  check_auth  L=5 N=2 saved=5 sim=1.00
      10-device_mesh_lab/mesh_env.py:55-59  (check_auth)
      _site/10-device_mesh_lab/mesh_env.py:55-59  (check_auth)
  [4cadc0c754a692d9]   EXAC  read_json  L=5 N=2 saved=5 sim=1.00
      10-device_mesh_lab/mesh_env.py:62-66  (read_json)
      _site/10-device_mesh_lab/mesh_env.py:62-66  (read_json)
  [3ae61375e9c32bcb]   EXAC  uri_run  L=5 N=2 saved=5 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:137-141  (uri_run)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:137-141  (uri_run)
  [8327b2f1f3a915be]   EXAC  json_get  L=4 N=2 saved=4 sim=1.00
      10-device_mesh_lab/controller.py:28-31  (json_get)
      _site/10-device_mesh_lab/controller.py:28-31  (json_get)
  [823e86fce8dda074]   EXAC  registry_route_count  L=4 N=2 saved=4 sim=1.00
      10-device_mesh_lab/controller.py:120-123  (registry_route_count)
      _site/10-device_mesh_lab/controller.py:120-123  (registry_route_count)
  [7b7b2b835be4f159]   EXAC  end_headers  L=4 N=2 saved=4 sim=1.00
      10-device_mesh_lab/controller.py:431-434  (end_headers)
      _site/10-device_mesh_lab/controller.py:431-434  (end_headers)
  [013a9ef6fe424ddd]   EXAC  serve  L=4 N=2 saved=4 sim=1.00
      10-device_mesh_lab/device_agent.py:575-578  (serve)
      _site/10-device_mesh_lab/device_agent.py:575-578  (serve)
  [2fe3e7559afd9cea]   EXAC  fetch_catalog  L=4 N=2 saved=4 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:52-55  (fetch_catalog)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:52-55  (fetch_catalog)
  [7a9755ba2a4c94fc]   EXAC  project_mcp_a2a  L=4 N=2 saved=4 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:261-264  (project_mcp_a2a)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:261-264  (project_mcp_a2a)
  [b3ef1406de5613d4]   EXAC  recent_logs  L=3 N=2 saved=3 sim=1.00
      06-html_uri_app/backend.py:76-78  (recent_logs)
      _site/06-html_uri_app/backend.py:76-78  (recent_logs)
  [40a4cf6dc9eb88bc]   EXAC  consumer  L=3 N=2 saved=3 sim=1.00
      07-transports/transport_lib.py:54-56  (consumer)
      _site/07-transports/transport_lib.py:54-56  (consumer)
  [61123e31adfca20d]   EXAC  json_get  L=3 N=2 saved=3 sim=1.00
      09-docker_uri_flow/orchestrator/flow_runner.py:161-163  (json_get)
      _site/09-docker_uri_flow/orchestrator/flow_runner.py:161-163  (json_get)
  [1ed0961add26c18a]   EXAC  slug  L=3 N=2 saved=3 sim=1.00
      10-device_mesh_lab/controller.py:45-47  (slug)
      _site/10-device_mesh_lab/controller.py:45-47  (slug)
  [2a2d1edddc37da92]   EXAC  is_safe_route  L=3 N=2 saved=3 sim=1.00
      10-device_mesh_lab/controller.py:67-69  (is_safe_route)
      _site/10-device_mesh_lab/controller.py:67-69  (is_safe_route)
  [3be4d4010222af4b]   EXAC  auth_headers  L=3 N=2 saved=3 sim=1.00
      10-device_mesh_lab/mesh_env.py:50-52  (auth_headers)
      _site/10-device_mesh_lab/mesh_env.py:50-52  (auth_headers)
  [cc61cf7c2816fdd8]   EXAC  log  L=3 N=2 saved=3 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:58-60  (log)
      _site/11-novnc_lan_flow/computer/browser_node.py:58-60  (log)
  [852a0235289a1239]   EXAC  current_url  L=3 N=2 saved=3 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:148-150  (current_url)
      _site/11-novnc_lan_flow/computer/browser_node.py:148-150  (current_url)
  [d8d5c3249ccd27b5]   EXAC  safe_name  L=3 N=2 saved=3 sim=1.00
      11-novnc_lan_flow/computer/browser_node.py:170-172  (safe_name)
      _site/11-novnc_lan_flow/computer/browser_node.py:170-172  (safe_name)
  [69a524668be61def]   EXAC  target_from_uri  L=3 N=2 saved=3 sim=1.00
      11-novnc_lan_flow/orchestrator/run_flow.py:189-191  (target_from_uri)
      _site/11-novnc_lan_flow/orchestrator/run_flow.py:189-191  (target_from_uri)
  [6fdad1e4dd046e5c]   EXAC  get_json  L=3 N=2 saved=3 sim=1.00
      12-full_e2e_connect_lab/registry-runtime/registry_server.py:24-26  (get_json)
      _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py:24-26  (get_json)
  [cb9d6c548dc8d4fb]   EXAC  write_json  L=3 N=2 saved=3 sim=1.00
      12-full_e2e_connect_lab/scripts/connector_checks.py:47-49  (write_json)
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py:47-49  (write_json)

REFACTOR[142] (ranked by priority):
  [1] ◐ extract_class      → utils/routes.py
      WHY: 2 occurrences of 114-line block across 2 files — saves 114 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [2] ◐ extract_module     → utils/run_connector_routes.py
      WHY: 2 occurrences of 111-line block across 2 files — saves 111 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [3] ◐ extract_module     → utils/main.py
      WHY: 2 occurrences of 98-line block across 2 files — saves 98 lines
      FILES: 12-full_e2e_connect_lab/scripts/assert_results.py, _site/12-full_e2e_connect_lab/scripts/assert_results.py
  [4] ◐ extract_class      → utils/open_browser_in_novnc.py
      WHY: 2 occurrences of 68-line block across 2 files — saves 68 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [5] ◐ extract_module     → utils/main.py
      WHY: 2 occurrences of 67-line block across 2 files — saves 67 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [6] ◐ extract_module     → utils/fallback_steps.py
      WHY: 2 occurrences of 58-line block across 2 files — saves 58 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [7] ◐ extract_module     → utils/app_service_call.py
      WHY: 2 occurrences of 55-line block across 2 files — saves 55 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [8] ◐ extract_class      → utils/handler.py
      WHY: 2 occurrences of 52-line block across 2 files — saves 52 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [9] ◐ extract_function   → utils/parse_flow.py
      WHY: 2 occurrences of 49-line block across 2 files — saves 49 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [10] ◐ extract_function   → utils/build_novnc_browser_command.py
      WHY: 2 occurrences of 47-line block across 2 files — saves 47 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [11] ◐ extract_function   → utils/build_registry.py
      WHY: 2 occurrences of 47-line block across 2 files — saves 47 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [12] ◐ extract_function   → utils/test_grpc_transport.py
      WHY: 2 occurrences of 47-line block across 2 files — saves 47 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [13] ◐ extract_function   → utils/normalize_flow.py
      WHY: 2 occurrences of 43-line block across 2 files — saves 43 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [14] ○ extract_function   → utils/emit_http_check_bindings.py
      WHY: 6 occurrences of 8-line block across 2 files — saves 40 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [15] ◐ extract_function   → utils/start_http_worker.py
      WHY: 2 occurrences of 33-line block across 2 files — saves 33 lines
      FILES: 07-transports/transport_lib.py, _site/07-transports/transport_lib.py
  [16] ◐ extract_function   → utils/ensure_session.py
      WHY: 2 occurrences of 33-line block across 2 files — saves 33 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [17] ◐ extract_function   → utils/serve_http.py
      WHY: 2 occurrences of 31-line block across 2 files — saves 31 lines
      FILES: 08-multi_transport/worker.py, _site/08-multi_transport/worker.py
  [18] ○ extract_function   → utils/postprocess_flow.py
      WHY: 2 occurrences of 30-line block across 2 files — saves 30 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [19] ○ extract_class      → utils/installable.py
      WHY: 2 occurrences of 30-line block across 2 files — saves 30 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [20] ○ extract_function   → utils/parse_browser_targets.py
      WHY: 2 occurrences of 29-line block across 2 files — saves 29 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [21] ○ extract_class      → utils/dispatch.py
      WHY: 2 occurrences of 29-line block across 2 files — saves 29 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [22] ○ extract_function   → utils/screenshot_page.py
      WHY: 2 occurrences of 29-line block across 2 files — saves 29 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [23] ○ extract_function   → utils/make_handler.py
      WHY: 2 occurrences of 28-line block across 2 files — saves 28 lines
      FILES: 07-transports/transport_lib.py, _site/07-transports/transport_lib.py
  [24] ○ extract_function   → utils/run_via.py
      WHY: 2 occurrences of 27-line block across 2 files — saves 27 lines
      FILES: 07-transports/transport_lib.py, _site/07-transports/transport_lib.py
  [25] ○ extract_function   → utils/llm_messages.py
      WHY: 2 occurrences of 27-line block across 2 files — saves 27 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [26] ○ extract_function   → utils/main.py
      WHY: 2 occurrences of 26-line block across 2 files — saves 26 lines
      FILES: 07-transports/scan_and_run.py, _site/07-transports/scan_and_run.py
  [27] ○ extract_function   → utils/discover_device.py
      WHY: 2 occurrences of 25-line block across 2 files — saves 25 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [28] ○ extract_class      → utils/do_POST.py
      WHY: 2 occurrences of 25-line block across 2 files — saves 25 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [29] ○ extract_function   → utils/registry_document.py
      WHY: 2 occurrences of 25-line block across 2 files — saves 25 lines
      FILES: 12-full_e2e_connect_lab/registry-runtime/registry_server.py, _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py
  [30] ○ extract_class      → utils/do_GET.py
      WHY: 2 occurrences of 24-line block across 2 files — saves 24 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [31] ○ extract_function   → utils/execute_flow.py
      WHY: 2 occurrences of 24-line block across 2 files — saves 24 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [32] ○ extract_class      → utils/open_browser.py
      WHY: 2 occurrences of 24-line block across 2 files — saves 24 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [33] ○ extract_function   → utils/dispatch.py
      WHY: 2 occurrences of 22-line block across 2 files — saves 22 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [34] ● extract_class      → utils/_send.py
      WHY: 4 occurrences of 7-line block across 4 files — saves 21 lines
      FILES: 07-transports/transport_lib.py, 08-multi_transport/worker.py, _site/07-transports/transport_lib.py, _site/08-multi_transport/worker.py
  [35] ○ extract_class      → utils/do_POST.py
      WHY: 2 occurrences of 21-line block across 2 files — saves 21 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [36] ○ extract_function   → utils/summarize_catalog.py
      WHY: 2 occurrences of 21-line block across 2 files — saves 21 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [37] ○ extract_function   → utils/main.py
      WHY: 2 occurrences of 20-line block across 2 files — saves 20 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [38] ○ extract_function   → utils/run_flow.py
      WHY: 2 occurrences of 19-line block across 2 files — saves 19 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [39] ○ extract_class      → utils/do_GET.py
      WHY: 2 occurrences of 19-line block across 2 files — saves 19 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [40] ○ extract_function   → utils/webdriver.py
      WHY: 2 occurrences of 19-line block across 2 files — saves 19 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [41] ○ extract_function   → utils/collect_routes.py
      WHY: 2 occurrences of 19-line block across 2 files — saves 19 lines
      FILES: 11-novnc_lan_flow/orchestrator/run_flow.py, _site/11-novnc_lan_flow/orchestrator/run_flow.py
  [42] ○ extract_function   → utils/generate_with_litellm.py
      WHY: 2 occurrences of 18-line block across 2 files — saves 18 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [43] ○ extract_function   → utils/generate_flow.py
      WHY: 2 occurrences of 18-line block across 2 files — saves 18 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [44] ○ extract_function   → utils/main.py
      WHY: 2 occurrences of 18-line block across 2 files — saves 18 lines
      FILES: 11-novnc_lan_flow/orchestrator/run_flow.py, _site/11-novnc_lan_flow/orchestrator/run_flow.py
  [45] ○ extract_function   → utils/discover.py
      WHY: 2 occurrences of 18-line block across 2 files — saves 18 lines
      FILES: 12-full_e2e_connect_lab/registry-runtime/registry_server.py, _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py
  [46] ○ extract_function   → utils/dispatch.py
      WHY: 2 occurrences of 17-line block across 2 files — saves 17 lines
      FILES: 09-docker_uri_flow/shell-worker/server.py, _site/09-docker_uri_flow/shell-worker/server.py
  [47] ○ extract_class      → utils/__init__.py
      WHY: 2 occurrences of 17-line block across 2 files — saves 17 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [48] ○ extract_function   → utils/wait_for_services.py
      WHY: 2 occurrences of 16-line block across 2 files — saves 16 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [49] ○ extract_function   → utils/dispatch_tool.py
      WHY: 2 occurrences of 15-line block across 2 files — saves 15 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [50] ○ extract_class      → utils/serve_static.py
      WHY: 2 occurrences of 15-line block across 2 files — saves 15 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [51] ○ extract_function   → utils/nl_flow.py
      WHY: 2 occurrences of 15-line block across 2 files — saves 15 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [52] ○ extract_function   → utils/make_agent_from_env.py
      WHY: 2 occurrences of 15-line block across 2 files — saves 15 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [53] ○ extract_class      → utils/processes.py
      WHY: 2 occurrences of 15-line block across 2 files — saves 15 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [54] ○ extract_function   → utils/open_page.py
      WHY: 2 occurrences of 15-line block across 2 files — saves 15 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [55] ○ extract_function   → utils/run_step.py
      WHY: 2 occurrences of 15-line block across 2 files — saves 15 lines
      FILES: 11-novnc_lan_flow/orchestrator/run_flow.py, _site/11-novnc_lan_flow/orchestrator/run_flow.py
  [56] ○ extract_function   → utils/run_queue.py
      WHY: 2 occurrences of 14-line block across 2 files — saves 14 lines
      FILES: 07-transports/transport_lib.py, _site/07-transports/transport_lib.py
  [57] ○ extract_function   → utils/main.py
      WHY: 2 occurrences of 14-line block across 2 files — saves 14 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [58] ○ extract_class      → utils/safe_command.py
      WHY: 2 occurrences of 14-line block across 2 files — saves 14 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [59] ○ extract_class      → utils/do_POST.py
      WHY: 2 occurrences of 14-line block across 2 files — saves 14 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [60] ○ extract_function   → utils/parse_peers.py
      WHY: 2 occurrences of 14-line block across 2 files — saves 14 lines
      FILES: 10-device_mesh_lab/mesh_env.py, _site/10-device_mesh_lab/mesh_env.py
  [61] ○ extract_function   → utils/route_call.py
      WHY: 2 occurrences of 14-line block across 2 files — saves 14 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [62] ○ extract_class      → utils/do_POST.py
      WHY: 2 occurrences of 13-line block across 2 files — saves 13 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [63] ○ extract_function   → utils/service_url.py
      WHY: 2 occurrences of 13-line block across 2 files — saves 13 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [64] ○ extract_class      → utils/log.py
      WHY: 2 occurrences of 13-line block across 2 files — saves 13 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [65] ○ extract_function   → utils/load_env.py
      WHY: 2 occurrences of 13-line block across 2 files — saves 13 lines
      FILES: 10-device_mesh_lab/mesh_env.py, _site/10-device_mesh_lab/mesh_env.py
  [66] ○ extract_function   → utils/discover_mesh.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [67] ○ extract_function   → utils/route_summary.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [68] ○ extract_function   → utils/append_step_if_missing.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [69] ○ extract_class      → utils/device_card.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [70] ○ extract_class      → utils/open_browser_on_host.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [71] ○ extract_function   → utils/wait_health.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: 11-novnc_lan_flow/orchestrator/run_flow.py, _site/11-novnc_lan_flow/orchestrator/run_flow.py
  [72] ○ extract_class      → utils/do_GET.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: 12-full_e2e_connect_lab/registry-runtime/registry_server.py, _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py
  [73] ○ extract_function   → utils/routes.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [74] ○ extract_function   → utils/route_binding.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [75] ○ extract_function   → utils/json_from_text.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [76] ○ extract_class      → utils/append_note.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [77] ○ extract_function   → utils/wait_for_webdriver.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [78] ○ extract_class      → utils/do_GET.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [79] ○ extract_function   → utils/run.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [80] ○ extract_function   → utils/registry_route_count.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [81] ○ extract_class      → utils/recent_logs.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [82] ○ extract_function   → utils/send_json.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: 10-device_mesh_lab/mesh_env.py, _site/10-device_mesh_lab/mesh_env.py
  [83] ○ extract_function   → utils/json_response.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [84] ○ extract_function   → utils/fetch_json.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: 11-novnc_lan_flow/orchestrator/run_flow.py, _site/11-novnc_lan_flow/orchestrator/run_flow.py
  [85] ○ extract_function   → utils/load_env.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [86] ○ extract_function   → utils/json_post.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [87] ○ extract_function   → utils/fallback_flow.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [88] ○ extract_function   → utils/object_schema.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [89] ○ extract_function   → utils/resolve_payload.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [90] ○ extract_class      → utils/do_GET.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: 09-docker_uri_flow/shell-worker/server.py, _site/09-docker_uri_flow/shell-worker/server.py
  [91] ○ extract_class      → utils/do_POST.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: 09-docker_uri_flow/shell-worker/server.py, _site/09-docker_uri_flow/shell-worker/server.py
  [92] ○ extract_function   → utils/nodes.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: 12-full_e2e_connect_lab/registry-runtime/registry_server.py, _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py
  [93] ○ extract_function   → utils/send.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: 12-full_e2e_connect_lab/registry-runtime/registry_server.py, _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py
  [94] ○ extract_function   → utils/json_response.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [95] ○ extract_class      → utils/do_POST.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 07-transports/transport_lib.py, _site/07-transports/transport_lib.py
  [96] ○ extract_class      → utils/do_GET.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 08-multi_transport/worker.py, _site/08-multi_transport/worker.py
  [97] ○ extract_class      → utils/do_POST.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 08-multi_transport/worker.py, _site/08-multi_transport/worker.py
  [98] ○ extract_function   → utils/normalize_uri.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [99] ○ extract_function   → utils/registry_has_uri.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [100] ○ extract_function   → utils/load_registry.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [101] ○ extract_function   → utils/validate_flow_registry.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [102] ○ extract_function   → utils/response.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 09-docker_uri_flow/shell-worker/server.py, _site/09-docker_uri_flow/shell-worker/server.py
  [103] ○ extract_function   → utils/main.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [104] ○ extract_function   → utils/main.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [105] ○ extract_function   → utils/add_log.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [106] ○ extract_function   → utils/execute_policy.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [107] ○ extract_function   → utils/grpc_available.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: 07-transports/transport_lib.py, _site/07-transports/transport_lib.py
  [108] ○ extract_function   → utils/route_key.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [109] ○ extract_function   → utils/main.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [110] ○ extract_class      → utils/do_GET.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [111] ○ extract_function   → utils/browser_target_from_spec.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [112] ○ extract_function   → utils/run_json.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [113] ○ extract_class      → utils/read_body.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [114] ○ extract_class      → utils/do_GET.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 07-transports/transport_lib.py, _site/07-transports/transport_lib.py
  [115] ○ extract_function   → utils/discovery.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 08-multi_transport/worker.py, _site/08-multi_transport/worker.py
  [116] ○ extract_function   → utils/serve_grpc.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 08-multi_transport/worker.py, _site/08-multi_transport/worker.py
  [117] ○ extract_function   → utils/parse_scalar.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [118] ○ extract_function   → utils/get_path.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [119] ○ extract_function   → utils/json_post.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [120] ○ extract_function   → utils/build_registry.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [121] ○ extract_class      → utils/_authorized.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [122] ○ extract_function   → utils/check_auth.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 10-device_mesh_lab/mesh_env.py, _site/10-device_mesh_lab/mesh_env.py
  [123] ○ extract_function   → utils/read_json.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 10-device_mesh_lab/mesh_env.py, _site/10-device_mesh_lab/mesh_env.py
  [124] ○ extract_function   → utils/uri_run.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [125] ○ extract_function   → utils/json_get.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [126] ○ extract_function   → utils/registry_route_count.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [127] ○ extract_class      → utils/end_headers.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [128] ○ extract_class      → utils/serve.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: 10-device_mesh_lab/device_agent.py, _site/10-device_mesh_lab/device_agent.py
  [129] ○ extract_function   → utils/fetch_catalog.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [130] ○ extract_function   → utils/project_mcp_a2a.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  [131] ○ extract_function   → utils/recent_logs.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 06-html_uri_app/backend.py, _site/06-html_uri_app/backend.py
  [132] ○ extract_function   → utils/consumer.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 07-transports/transport_lib.py, _site/07-transports/transport_lib.py
  [133] ○ extract_function   → utils/json_get.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 09-docker_uri_flow/orchestrator/flow_runner.py, _site/09-docker_uri_flow/orchestrator/flow_runner.py
  [134] ○ extract_function   → utils/slug.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [135] ○ extract_function   → utils/is_safe_route.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 10-device_mesh_lab/controller.py, _site/10-device_mesh_lab/controller.py
  [136] ○ extract_function   → utils/auth_headers.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 10-device_mesh_lab/mesh_env.py, _site/10-device_mesh_lab/mesh_env.py
  [137] ○ extract_function   → utils/log.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [138] ○ extract_function   → utils/current_url.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [139] ○ extract_function   → utils/safe_name.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 11-novnc_lan_flow/computer/browser_node.py, _site/11-novnc_lan_flow/computer/browser_node.py
  [140] ○ extract_function   → utils/target_from_uri.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 11-novnc_lan_flow/orchestrator/run_flow.py, _site/11-novnc_lan_flow/orchestrator/run_flow.py
  [141] ○ extract_function   → utils/get_json.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 12-full_e2e_connect_lab/registry-runtime/registry_server.py, _site/12-full_e2e_connect_lab/registry-runtime/registry_server.py
  [142] ○ extract_function   → utils/write_json.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: 12-full_e2e_connect_lab/scripts/connector_checks.py, _site/12-full_e2e_connect_lab/scripts/connector_checks.py

QUICK_WINS[95] (low risk, high savings — do first):
  [14] extract_function   saved=40L  → utils/emit_http_check_bindings.py
      FILES: connector_checks.py, connector_checks.py
  [18] extract_function   saved=30L  → utils/postprocess_flow.py
      FILES: controller.py, controller.py
  [19] extract_class      saved=30L  → utils/installable.py
      FILES: device_agent.py, device_agent.py
  [20] extract_function   saved=29L  → utils/parse_browser_targets.py
      FILES: device_agent.py, device_agent.py
  [21] extract_class      saved=29L  → utils/dispatch.py
      FILES: device_agent.py, device_agent.py
  [22] extract_function   saved=29L  → utils/screenshot_page.py
      FILES: browser_node.py, browser_node.py
  [23] extract_function   saved=28L  → utils/make_handler.py
      FILES: transport_lib.py, transport_lib.py
  [24] extract_function   saved=27L  → utils/run_via.py
      FILES: transport_lib.py, transport_lib.py
  [25] extract_function   saved=27L  → utils/llm_messages.py
      FILES: controller.py, controller.py
  [26] extract_function   saved=26L  → utils/main.py
      FILES: scan_and_run.py, scan_and_run.py

DEPENDENCY_RISK[142] (duplicates spanning multiple packages):
  _send  packages=3  files=4
      07-transports/transport_lib.py
      08-multi_transport/worker.py
      _site/07-transports/transport_lib.py
      _site/08-multi_transport/worker.py
  routes  packages=2  files=2
      10-device_mesh_lab/device_agent.py
      _site/10-device_mesh_lab/device_agent.py
  run_connector_routes  packages=2  files=2
      12-full_e2e_connect_lab/scripts/connector_checks.py
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  main  packages=2  files=2
      12-full_e2e_connect_lab/scripts/assert_results.py
      _site/12-full_e2e_connect_lab/scripts/assert_results.py
  open_browser_in_novnc  packages=2  files=2
      10-device_mesh_lab/device_agent.py
      _site/10-device_mesh_lab/device_agent.py
  main  packages=2  files=2
      12-full_e2e_connect_lab/scripts/connector_checks.py
      _site/12-full_e2e_connect_lab/scripts/connector_checks.py
  fallback_steps  packages=2  files=2
      10-device_mesh_lab/controller.py
      _site/10-device_mesh_lab/controller.py

EFFORT_ESTIMATE (total ≈ 196.5h):
  hard   routes                              saved=114L  ~684min
  hard   run_connector_routes                saved=111L  ~666min
  hard   main                                saved=98L  ~588min
  hard   open_browser_in_novnc               saved=68L  ~408min
  hard   main                                saved=67L  ~402min
  hard   fallback_steps                      saved=58L  ~348min
  hard   app_service_call                    saved=55L  ~330min
  hard   handler                             saved=52L  ~312min
  hard   parse_flow                          saved=49L  ~294min
  hard   build_novnc_browser_command         saved=47L  ~282min
  ... +132 more (~7476min)

METRICS-TARGET:
  dup_groups:  142 → 0
  saved_lines: 2471 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 0 func | 1f | 2026-06-21
# generated in 0.00s

NEXT[2] (ranked by impact):
  [1] !! SPLIT           10-device_mesh_lab/device_agent.py
      WHY: 608L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [2] !! SPLIT           _site/10-device_mesh_lab/device_agent.py
      WHY: 608L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[2]:
  ⚠ Splitting 10-device_mesh_lab/device_agent.py may break 0 import paths
  ⚠ Splitting _site/10-device_mesh_lab/device_agent.py may break 0 import paths

METRICS-TARGET:
  CC̄:          0.0 → ≤0.0
  max-CC:      0 → ≤0
  god-modules: 2 → 0
  high-CC(≥15): 0 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  (first run — no previous data)
```

## Intent

ifURI examples
