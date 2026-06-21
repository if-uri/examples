# ifURI examples

ifURI examples

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `examples`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: Makefile, testql(1), app.doql.less, project/(3 analysis files)

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

## Interfaces

### testql Scenarios

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# Converted 8 assertions from pytest
ASSERT[8]{field, operator, expected}:
  env.error.type, ==, "schema"
  env.request.uri, ==, "python://python-worker/text/normalize"
  normalized.result.normalized, ==, "supplier report"
  slug.result.slug, ==, "supplier-report-june-2026"
  env.error.type, ==, "schema"
  env.request.uri, ==, "python://python-worker/text/normalize"
  normalized.result.normalized, ==, "supplier report"
  slug.result.slug, ==, "supplier-report-june-2026"
```

## Workflows

## Configuration

```yaml
project:
  name: examples
  version: 0.0.0
  env: local
```

## Deployment

```bash markpact:run
pip install examples

# development install
pip install -e .[dev]
```

## Makefile Targets

- `test`
- `help`
- `site`
- `deploy`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# examples | 56f 7901L | python:32,shell:14,javascript:5,css:2,go:1,typescript:1,less:1 | 2026-06-21
# stats: 187 func | 24 cls | 56 mod | CC̄=4.4 | critical:16 | cycles:0
# alerts[5]: CC main=38; CC fallback_steps=33; CC md=28; CC parse_flow=24; CC app_service_call=22
# hotspots[5]: main fan=24; start_http_worker fan=19; serve_http fan=19; run_e2e fan=19; screenshot_page fan=16
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[56]:
  02-decorators/example.py,29
  03-artifacts/deploy.sh,7
  04-python/test_adopt.py,104
  04-python/test_mcp_a2a.py,143
  04-python/test_urihandler_v2.py,316
  05-generators/go/example.go,84
  05-generators/ts/decorators.ts,66
  06-html_uri_app/app.js,171
  06-html_uri_app/backend.py,231
  06-html_uri_app/run.sh,9
  06-html_uri_app/styles.css,293
  07-transports/demo.py,19
  07-transports/scan_and_run.py,53
  07-transports/test_transports.py,53
  07-transports/transport_lib.py,156
  08-multi_transport/run_multi_test.py,109
  08-multi_transport/run_tests.sh,17
  08-multi_transport/worker.py,81
  09-docker_uri_flow/generate_registry.sh,30
  09-docker_uri_flow/node-worker/server.js,56
  09-docker_uri_flow/orchestrator/flow_runner.py,222
  09-docker_uri_flow/python-worker/server.py,72
  09-docker_uri_flow/run.sh,17
  09-docker_uri_flow/run_tests.sh,17
  09-docker_uri_flow/shell-worker/server.py,68
  09-docker_uri_flow/shell-worker/write_report.sh,13
  09-docker_uri_flow/test_flow_e2e.py,103
  09-docker_uri_flow/test_flow_runner.py,112
  09-docker_uri_flow/test_service_adapter.py,111
  09-docker_uri_flow/tester/run_compose_test.py,83
  10-device_mesh_lab/controller.py,491
  10-device_mesh_lab/device_agent.py,609
  10-device_mesh_lab/mesh_env.py,79
  10-device_mesh_lab/tests/device_agent_policy.py,52
  10-device_mesh_lab/tests/gui_smoke.py,428
  10-device_mesh_lab/www/app.js,563
  10-device_mesh_lab/www/runtime-config.js,14
  10-device_mesh_lab/www/styles.css,704
  11-novnc_lan_flow/computer/browser_node.py,332
  11-novnc_lan_flow/dashboard/runtime-config.js,14
  11-novnc_lan_flow/orchestrator/run_flow.py,280
  11-novnc_lan_flow/scripts/smoke.sh,95
  12-full_e2e_connect_lab/registry-runtime/registry_server.py,106
  12-full_e2e_connect_lab/scripts/assert_results.py,117
  12-full_e2e_connect_lab/scripts/connector_checks.py,410
  12-full_e2e_connect_lab/scripts/public_smoke.sh,41
  12-full_e2e_connect_lab/scripts/run_full_scenario.sh,93
  13-simple_defaults/python_connector.py,41
  14-llm-uri-agent/agent.py,108
  14-llm-uri-agent/tools.py,124
  app.doql.less,30
  project.sh,66
  run_tests.sh,93
  scripts/build_site.py,139
  scripts/deploy-plesk.sh,22
  tree.sh,5
D:
  02-decorators/example.py:
    e: echo_message,transcode,shell_echo
    echo_message(text)
    transcode(input;output;width;height)
    shell_echo(text)
  04-python/test_adopt.py:
    e: SpreadArgsTests,PythonPackageAdoptionTests,NpmPackageAdoptionTests,InitTests,CliTests
    SpreadArgsTests: test_spread_array_param_expands_into_argv(0),test_spread_defaults_to_empty(0),test_validate_accepts_spread_placeholder(0)
    PythonPackageAdoptionTests: test_console_scripts_become_passthrough_commands(0),test_adopted_command_runs_with_passthrough_args(0)
    NpmPackageAdoptionTests: test_bin_field_becomes_npx_command(0)
    InitTests: test_init_builds_binding_document_from_project(0)
    CliTests: test_add_python_package_compile_and_run(0)
  04-python/test_mcp_a2a.py:
    e: registry,McpProjectionTests,A2aCardTests,McpServerTests,BackendInteropTests
    McpProjectionTests: setUp(0),test_mcp_manifest_exposes_tools_with_json_schema(0),test_tool_index_maps_back_to_uris(0),test_call_tool_dry_run_renders_command(0),test_call_unknown_tool_raises(0)
    A2aCardTests: test_agent_card_lists_skills(0)
    McpServerTests: test_jsonrpc_roundtrip_over_streams(0)
    BackendInteropTests: test_backend_serves_mcp_tools_and_calls(0)
    registry()
  04-python/test_urihandler_v2.py:
    e: DecoratorTests,SchemaRuntimeTests,ArtifactAdoptionTests,HtmlAppTests
    DecoratorTests: test_decorator_generates_schema_and_argv_runtime(0),test_shell_decorator_executes_only_when_shell_policy_allows_it(0)
    SchemaRuntimeTests: setUp(0),test_json_schema_defaults_are_applied_before_rendering(0),test_missing_required_input_is_schema_error(0),test_shell_binding_is_real_shell_runtime_when_allowed(0),test_document_validation_catches_unresolved_placeholders(0)
    ArtifactAdoptionTests: test_artifact_scan_builds_v2_bindings_from_common_standards(0),test_cli_scan_validate_compile_and_run(0),test_cli_add_pypi_and_command_binding_in_one_line(0)
    HtmlAppTests: test_html_backend_dispatches_v2_runtime(0)
  06-html_uri_app/backend.py:
    e: load_env,env_bool,read_json,binding_document,registry,routes,add_log,recent_logs,json_response,execute_policy,dispatch,dispatch_tool,main,Handler
    Handler: log_message(1),do_GET(0),do_POST(0),read_body(0),serve_static(1)
    load_env(path)
    env_bool(name;default)
    read_json(path)
    binding_document()
    registry()
    routes()
    add_log(event;detail;source)
    recent_logs(limit)
    json_response(handler;status;payload)
    execute_policy(uri;allow_shell)
    dispatch(body)
    dispatch_tool(body)
    main()
  07-transports/demo.py:
  07-transports/scan_and_run.py:
    e: main
    main(argv)
  07-transports/test_transports.py:
    e: test_all_transports_agree,test_schema_validation_is_uniform,test_scan_and_run_cli
    test_all_transports_agree()
    test_schema_validation_is_uniform()
    test_scan_and_run_cli()
  07-transports/transport_lib.py:
    e: build_registry,run_inprocess,run_queue,serverless_handler,start_http_worker,run_via,grpc_available,available_transports
    build_registry()
    run_inprocess(uri;payload;registry;mode)
    run_queue(uri;payload;registry;timeout)
    serverless_handler(event;registry)
    start_http_worker(registry;host)
    run_via(transport;uri;payload;registry)
    grpc_available()
    available_transports()
  08-multi_transport/run_multi_test.py:
    e: http_get,wait_http,wait_grpc,route_key,detect_conflicts,main
    http_get(url)
    wait_http(host;port;timeout)
    wait_grpc(host;timeout)
    route_key(uri)
    detect_conflicts(sources)
    main()
  08-multi_transport/worker.py:
    e: discovery,serve_http,serve_grpc
    discovery()
    serve_http()
    serve_grpc()
  09-docker_uri_flow/orchestrator/flow_runner.py:
    e: parse_scalar,parse_flow,get_path,resolve_payload,service_url,route_key,normalize_uri,registry_has_uri,registry_route_count,load_registry,validate_flow_registry,json_get,json_post,wait_for_services,run_flow,main
    parse_scalar(value)
    parse_flow(path)
    get_path(data;dotted)
    resolve_payload(payload;results)
    service_url(uri)
    route_key(uri)
    normalize_uri(uri)
    registry_has_uri(registry;uri)
    registry_route_count(registry)
    load_registry(path)
    validate_flow_registry(flow;registry)
    json_get(url)
    json_post(url;payload)
    wait_for_services(uris)
    run_flow(flow)
    main(argv)
  09-docker_uri_flow/python-worker/server.py:
    e: response,normalize,summary,dispatch,Handler
    Handler: log_message(1),do_GET(0),do_POST(0)
    response(handler;status;payload)
    normalize(payload)
    summary(payload)
    dispatch(uri;payload)
  09-docker_uri_flow/shell-worker/server.py:
    e: response,dispatch,Handler
    Handler: log_message(1),do_GET(0),do_POST(0)
    response(handler;status;payload)
    dispatch(uri;payload)
  09-docker_uri_flow/test_flow_e2e.py:
    e: load_runner,free_port,start,wait_health,run_e2e,test_cross_service_flow_runs_without_docker
    load_runner()
    free_port()
    start(cmd;port;extra_env)
    wait_health(port;timeout)
    run_e2e()
    test_cross_service_flow_runs_without_docker()
  09-docker_uri_flow/test_flow_runner.py:
    e: load_runner,test_parse_compact_uri_flow,test_registry_uri_lookup,test_registry_uri_lookup_prefers_full_uri_index,test_registry_dispatch_distinguishes_targets_with_same_segments
    load_runner()
    test_parse_compact_uri_flow()
    test_registry_uri_lookup()
    test_registry_uri_lookup_prefers_full_uri_index()
    test_registry_dispatch_distinguishes_targets_with_same_segments()
  09-docker_uri_flow/test_service_adapter.py:
    e: registry,free_port,wait_health,test_dry_run_plans_the_http_call_without_network,test_schema_validation_runs_before_dispatch,test_unknown_uri_is_a_registry_error,test_service_dispatch_calls_live_workers
    registry()
    free_port()
    wait_health(port;timeout)
    test_dry_run_plans_the_http_call_without_network()
    test_schema_validation_runs_before_dispatch()
    test_unknown_uri_is_a_registry_error()
    test_service_dispatch_calls_live_workers()
  09-docker_uri_flow/tester/run_compose_test.py:
    e: get,wait_healthy,main
    get(url)
    wait_healthy(host;timeout)
    main()
  10-device_mesh_lab/controller.py:
    e: json_get,json_post,slug,target_from_uri,route_binding,is_safe_route,discover_device,discover_mesh,build_registry,registry_route_count,route_summary,fallback_steps,fallback_flow,append_step_if_missing,postprocess_flow,json_from_text,normalize_flow,llm_messages,generate_with_litellm,generate_flow,execute_flow,nl_flow,main,Handler
    Handler: __init__(0),end_headers(0),do_OPTIONS(0),do_GET(0),do_POST(0)
    json_get(url;timeout)
    json_post(url;payload;timeout)
    slug(value)
    target_from_uri(uri)
    route_binding(route)
    is_safe_route(route)
    discover_device(name;base_url)
    discover_mesh()
    build_registry(routes)
    registry_route_count(registry)
    route_summary(routes)
    fallback_steps(prompt;routes)
    fallback_flow(prompt;routes;reason)
    append_step_if_missing(flow;uri;payload)
    postprocess_flow(flow;prompt;routes)
    json_from_text(text)
    normalize_flow(flow;allowed_uris)
    llm_messages(prompt;routes;devices)
    generate_with_litellm(prompt;routes;devices)
    generate_flow(prompt;mesh)
    execute_flow(flow;mesh;registry)
    nl_flow(prompt;execute)
    main()
  10-device_mesh_lab/device_agent.py:
    e: object_schema,default_browser_targets,browser_target_from_spec,parse_browser_targets,build_novnc_browser_command,make_agent_from_env,main,DeviceAgent
    DeviceAgent: __init__(6),log(2),recent_logs(1),append_note(1),routes(0),device_card(0),browser_target(0),installable(0),processes(2),safe_command(2),open_browser_on_host(2),open_browser_in_novnc(2),open_browser(1),dispatch(2),handler(0),serve(2)
    object_schema(properties;required)
    default_browser_targets()
    browser_target_from_spec(name;spec)
    parse_browser_targets(value)
    build_novnc_browser_command(url)
    make_agent_from_env()
    main()
  10-device_mesh_lab/mesh_env.py:
    e: load_env,parse_peers,auth_token,auth_headers,check_auth,read_json,send_json
    load_env()
    parse_peers(value)
    auth_token()
    auth_headers()
    check_auth(headers)
    read_json(handler)
    send_json(handler;status;payload)
  10-device_mesh_lab/tests/device_agent_policy.py:
    e: main
    main()
  10-device_mesh_lab/tests/gui_smoke.py:
    e: route,free_port,find_chrome,recv_exact,wait_for_debugger,wait_for_page_ready,main,DemoHandler,ThreadedHTTPServer,WebSocket,CDP
    DemoHandler: __init__(0),log_message(1),send_json(1),do_GET(0),do_POST(0)
    ThreadedHTTPServer:
    WebSocket: __init__(1),send_json(1),recv_json(0),close(0)
    CDP: __init__(1),call(2),close(0)
    route(uri;title;properties;required)
    free_port()
    find_chrome()
    recv_exact(sock;length)
    wait_for_debugger(port)
    wait_for_page_ready(cdp)
    main()
  11-novnc_lan_flow/computer/browser_node.py:
    e: log,json_response,route_kind,webdriver,wait_for_webdriver,ensure_session,current_url,open_page,safe_name,screenshot_page,app_service_call,route_call,main,Handler
    Handler: log_message(1),do_OPTIONS(0),do_GET(0),do_POST(0)
    log(event;detail)
    json_response(handler;status;payload)
    route_kind(uri)
    webdriver(method;path;payload;timeout)
    wait_for_webdriver(timeout)
    ensure_session()
    current_url(session_id)
    open_page(payload)
    safe_name(value)
    screenshot_page(payload)
    app_service_call(uri;payload)
    route_call(uri;payload)
    main()
  11-novnc_lan_flow/orchestrator/run_flow.py:
    e: target_from_uri,fetch_json,wait_health,collect_routes,run_step,main
    target_from_uri(uri)
    fetch_json(url;payload;timeout)
    wait_health(target;timeout)
    collect_routes(targets)
    run_step(step)
    main()
  12-full_e2e_connect_lab/registry-runtime/registry_server.py:
    e: nodes,get_json,discover,registry_document,send,Handler
    Handler: do_GET(0),log_message(1)
    nodes()
    get_json(url;timeout)
    discover()
    registry_document()
    send(handler;payload;status)
  12-full_e2e_connect_lab/scripts/assert_results.py:
    e: load,main
    load(path)
    main()
  12-full_e2e_connect_lab/scripts/connector_checks.py:
    e: run,run_json,write_json,fetch_catalog,emit_http_check_bindings,emit_time_tools_bindings,emit_browser_control_bindings,build_registry,uri_run,result_ok,run_connector_routes,project_mcp_a2a,test_grpc_transport,summarize_catalog,main
    run(args)
    run_json(args)
    write_json(path;data)
    fetch_catalog()
    emit_http_check_bindings()
    emit_time_tools_bindings()
    emit_browser_control_bindings()
    build_registry()
    uri_run(uri;payload)
    result_ok(envelope)
    run_connector_routes()
    project_mcp_a2a()
    test_grpc_transport()
    summarize_catalog(catalog;route_results)
    main()
  13-simple_defaults/python_connector.py:
    e: upper,bindings,main
    upper(text;suffix)
    bindings()
    main()
  14-llm-uri-agent/agent.py:
    e: load_registry,action_space,plan,run_step,main
    load_registry()
    action_space(registry)
    plan(goal;routes)
    run_step(registry;step)
    main(argv)
  14-llm-uri-agent/tools.py:
    e: emit,_route,bindings,now,http_status,_chrome_bin,browser_dom,log_event,main
    emit(payload)
    _route(uri;argv;properties;label)
    bindings()
    now()
    http_status(url)
    _chrome_bin()
    browser_dom(url;max_chars)
    log_event(event;detail)
    main(argv)
  scripts/build_site.py:
    e: md,page,first_title_desc
    md(text)
    page(title;body;depth)
    first_title_desc(readme)
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('examples', '0.0.0', 'python').

% ── Project Files ────────────────────────────────────────
project_file('02-decorators/example.py', 29, 'python').
project_file('03-artifacts/deploy.sh', 7, 'shell').
project_file('04-python/test_adopt.py', 104, 'python').
project_file('04-python/test_mcp_a2a.py', 143, 'python').
project_file('04-python/test_urihandler_v2.py', 316, 'python').
project_file('05-generators/go/example.go', 84, 'go').
project_file('05-generators/ts/decorators.ts', 66, 'typescript').
project_file('06-html_uri_app/app.js', 171, 'javascript').
project_file('06-html_uri_app/backend.py', 231, 'python').
project_file('06-html_uri_app/run.sh', 9, 'shell').
project_file('06-html_uri_app/styles.css', 293, 'css').
project_file('07-transports/demo.py', 19, 'python').
project_file('07-transports/scan_and_run.py', 53, 'python').
project_file('07-transports/test_transports.py', 53, 'python').
project_file('07-transports/transport_lib.py', 156, 'python').
project_file('08-multi_transport/run_multi_test.py', 109, 'python').
project_file('08-multi_transport/run_tests.sh', 17, 'shell').
project_file('08-multi_transport/worker.py', 81, 'python').
project_file('09-docker_uri_flow/generate_registry.sh', 30, 'shell').
project_file('09-docker_uri_flow/node-worker/server.js', 56, 'javascript').
project_file('09-docker_uri_flow/orchestrator/flow_runner.py', 222, 'python').
project_file('09-docker_uri_flow/python-worker/server.py', 72, 'python').
project_file('09-docker_uri_flow/run.sh', 17, 'shell').
project_file('09-docker_uri_flow/run_tests.sh', 17, 'shell').
project_file('09-docker_uri_flow/shell-worker/server.py', 68, 'python').
project_file('09-docker_uri_flow/shell-worker/write_report.sh', 13, 'shell').
project_file('09-docker_uri_flow/test_flow_e2e.py', 103, 'python').
project_file('09-docker_uri_flow/test_flow_runner.py', 112, 'python').
project_file('09-docker_uri_flow/test_service_adapter.py', 111, 'python').
project_file('09-docker_uri_flow/tester/run_compose_test.py', 83, 'python').
project_file('10-device_mesh_lab/controller.py', 491, 'python').
project_file('10-device_mesh_lab/device_agent.py', 609, 'python').
project_file('10-device_mesh_lab/mesh_env.py', 79, 'python').
project_file('10-device_mesh_lab/tests/device_agent_policy.py', 52, 'python').
project_file('10-device_mesh_lab/tests/gui_smoke.py', 428, 'python').
project_file('10-device_mesh_lab/www/app.js', 563, 'javascript').
project_file('10-device_mesh_lab/www/runtime-config.js', 14, 'javascript').
project_file('10-device_mesh_lab/www/styles.css', 704, 'css').
project_file('11-novnc_lan_flow/computer/browser_node.py', 332, 'python').
project_file('11-novnc_lan_flow/dashboard/runtime-config.js', 14, 'javascript').
project_file('11-novnc_lan_flow/orchestrator/run_flow.py', 280, 'python').
project_file('11-novnc_lan_flow/scripts/smoke.sh', 95, 'shell').
project_file('12-full_e2e_connect_lab/registry-runtime/registry_server.py', 106, 'python').
project_file('12-full_e2e_connect_lab/scripts/assert_results.py', 117, 'python').
project_file('12-full_e2e_connect_lab/scripts/connector_checks.py', 410, 'python').
project_file('12-full_e2e_connect_lab/scripts/public_smoke.sh', 41, 'shell').
project_file('12-full_e2e_connect_lab/scripts/run_full_scenario.sh', 93, 'shell').
project_file('13-simple_defaults/python_connector.py', 41, 'python').
project_file('14-llm-uri-agent/agent.py', 108, 'python').
project_file('14-llm-uri-agent/tools.py', 124, 'python').
project_file('app.doql.less', 30, 'less').
project_file('project.sh', 66, 'shell').
project_file('run_tests.sh', 93, 'shell').
project_file('scripts/build_site.py', 139, 'python').
project_file('scripts/deploy-plesk.sh', 22, 'shell').
project_file('tree.sh', 5, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('02-decorators/example.py', 'echo_message', 1, 1, 1).
python_function('02-decorators/example.py', 'transcode', 4, 1, 1).
python_function('02-decorators/example.py', 'shell_echo', 1, 1, 1).
python_function('04-python/test_mcp_a2a.py', 'registry', 0, 1, 3).
python_function('06-html_uri_app/backend.py', 'load_env', 1, 6, 7).
python_function('06-html_uri_app/backend.py', 'env_bool', 2, 1, 2).
python_function('06-html_uri_app/backend.py', 'read_json', 1, 1, 2).
python_function('06-html_uri_app/backend.py', 'binding_document', 0, 1, 2).
python_function('06-html_uri_app/backend.py', 'registry', 0, 1, 2).
python_function('06-html_uri_app/backend.py', 'routes', 0, 4, 4).
python_function('06-html_uri_app/backend.py', 'add_log', 3, 2, 2).
python_function('06-html_uri_app/backend.py', 'recent_logs', 1, 1, 1).
python_function('06-html_uri_app/backend.py', 'json_response', 3, 1, 8).
python_function('06-html_uri_app/backend.py', 'execute_policy', 2, 1, 0).
python_function('06-html_uri_app/backend.py', 'dispatch', 1, 6, 8).
python_function('06-html_uri_app/backend.py', 'dispatch_tool', 1, 7, 7).
python_function('06-html_uri_app/backend.py', 'main', 0, 5, 9).
python_function('07-transports/scan_and_run.py', 'main', 1, 6, 10).
python_function('07-transports/test_transports.py', 'test_all_transports_agree', 0, 4, 4).
python_function('07-transports/test_transports.py', 'test_schema_validation_is_uniform', 0, 5, 3).
python_function('07-transports/test_transports.py', 'test_scan_and_run_cli', 0, 2, 3).
python_function('07-transports/transport_lib.py', 'build_registry', 0, 1, 3).
python_function('07-transports/transport_lib.py', 'run_inprocess', 4, 2, 1).
python_function('07-transports/transport_lib.py', 'run_queue', 4, 1, 7).
python_function('07-transports/transport_lib.py', 'serverless_handler', 2, 1, 2).
python_function('07-transports/transport_lib.py', 'start_http_worker', 2, 1, 19).
python_function('07-transports/transport_lib.py', 'run_via', 4, 6, 13).
python_function('07-transports/transport_lib.py', 'grpc_available', 0, 2, 0).
python_function('07-transports/transport_lib.py', 'available_transports', 0, 4, 1).
python_function('08-multi_transport/run_multi_test.py', 'http_get', 1, 1, 4).
python_function('08-multi_transport/run_multi_test.py', 'wait_http', 3, 3, 4).
python_function('08-multi_transport/run_multi_test.py', 'wait_grpc', 2, 3, 4).
python_function('08-multi_transport/run_multi_test.py', 'route_key', 1, 1, 3).
python_function('08-multi_transport/run_multi_test.py', 'detect_conflicts', 1, 5, 5).
python_function('08-multi_transport/run_multi_test.py', 'main', 0, 7, 12).
python_function('08-multi_transport/worker.py', 'discovery', 0, 2, 1).
python_function('08-multi_transport/worker.py', 'serve_http', 0, 1, 19).
python_function('08-multi_transport/worker.py', 'serve_grpc', 0, 1, 2).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'parse_scalar', 1, 3, 2).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'parse_flow', 1, 24, 12).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'get_path', 2, 2, 1).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'resolve_payload', 2, 4, 4).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'service_url', 1, 5, 6).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'route_key', 1, 5, 5).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'normalize_uri', 1, 6, 6).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'registry_has_uri', 2, 4, 5).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'registry_route_count', 1, 5, 4).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'load_registry', 1, 3, 4).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'validate_flow_registry', 2, 5, 3).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'json_get', 1, 1, 4).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'json_post', 2, 1, 7).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'wait_for_services', 1, 5, 7).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'run_flow', 1, 8, 10).
python_function('09-docker_uri_flow/orchestrator/flow_runner.py', 'main', 1, 3, 5).
python_function('09-docker_uri_flow/python-worker/server.py', 'response', 3, 1, 8).
python_function('09-docker_uri_flow/python-worker/server.py', 'normalize', 1, 1, 6).
python_function('09-docker_uri_flow/python-worker/server.py', 'summary', 1, 1, 2).
python_function('09-docker_uri_flow/python-worker/server.py', 'dispatch', 2, 3, 2).
python_function('09-docker_uri_flow/shell-worker/server.py', 'response', 3, 1, 8).
python_function('09-docker_uri_flow/shell-worker/server.py', 'dispatch', 2, 2, 3).
python_function('09-docker_uri_flow/test_flow_e2e.py', 'load_runner', 0, 1, 3).
python_function('09-docker_uri_flow/test_flow_e2e.py', 'free_port', 0, 1, 3).
python_function('09-docker_uri_flow/test_flow_e2e.py', 'start', 3, 2, 4).
python_function('09-docker_uri_flow/test_flow_e2e.py', 'wait_health', 2, 4, 4).
python_function('09-docker_uri_flow/test_flow_e2e.py', 'run_e2e', 0, 11, 19).
python_function('09-docker_uri_flow/test_flow_e2e.py', 'test_cross_service_flow_runs_without_docker', 0, 1, 1).
python_function('09-docker_uri_flow/test_flow_runner.py', 'load_runner', 0, 1, 3).
python_function('09-docker_uri_flow/test_flow_runner.py', 'test_parse_compact_uri_flow', 0, 4, 2).
python_function('09-docker_uri_flow/test_flow_runner.py', 'test_registry_uri_lookup', 0, 4, 3).
python_function('09-docker_uri_flow/test_flow_runner.py', 'test_registry_uri_lookup_prefers_full_uri_index', 0, 5, 4).
python_function('09-docker_uri_flow/test_flow_runner.py', 'test_registry_dispatch_distinguishes_targets_with_same_segments', 0, 3, 2).
python_function('09-docker_uri_flow/test_service_adapter.py', 'registry', 0, 2, 4).
python_function('09-docker_uri_flow/test_service_adapter.py', 'free_port', 0, 1, 3).
python_function('09-docker_uri_flow/test_service_adapter.py', 'wait_health', 2, 4, 4).
python_function('09-docker_uri_flow/test_service_adapter.py', 'test_dry_run_plans_the_http_call_without_network', 0, 4, 3).
python_function('09-docker_uri_flow/test_service_adapter.py', 'test_schema_validation_runs_before_dispatch', 0, 3, 2).
python_function('09-docker_uri_flow/test_service_adapter.py', 'test_unknown_uri_is_a_registry_error', 0, 3, 2).
python_function('09-docker_uri_flow/test_service_adapter.py', 'test_service_dispatch_calls_live_workers', 0, 10, 13).
python_function('09-docker_uri_flow/tester/run_compose_test.py', 'get', 1, 1, 4).
python_function('09-docker_uri_flow/tester/run_compose_test.py', 'wait_healthy', 2, 3, 4).
python_function('09-docker_uri_flow/tester/run_compose_test.py', 'main', 0, 9, 7).
python_function('10-device_mesh_lab/controller.py', 'json_get', 2, 1, 6).
python_function('10-device_mesh_lab/controller.py', 'json_post', 3, 3, 8).
python_function('10-device_mesh_lab/controller.py', 'slug', 1, 2, 3).
python_function('10-device_mesh_lab/controller.py', 'target_from_uri', 1, 1, 1).
python_function('10-device_mesh_lab/controller.py', 'route_binding', 1, 2, 2).
python_function('10-device_mesh_lab/controller.py', 'is_safe_route', 1, 4, 4).
python_function('10-device_mesh_lab/controller.py', 'discover_device', 2, 6, 4).
python_function('10-device_mesh_lab/controller.py', 'discover_mesh', 0, 5, 5).
python_function('10-device_mesh_lab/controller.py', 'build_registry', 1, 5, 3).
python_function('10-device_mesh_lab/controller.py', 'registry_route_count', 1, 3, 3).
python_function('10-device_mesh_lab/controller.py', 'route_summary', 1, 3, 3).
python_function('10-device_mesh_lab/controller.py', 'fallback_steps', 2, 33, 10).
python_function('10-device_mesh_lab/controller.py', 'fallback_flow', 3, 1, 4).
python_function('10-device_mesh_lab/controller.py', 'append_step_if_missing', 3, 7, 6).
python_function('10-device_mesh_lab/controller.py', 'postprocess_flow', 3, 20, 8).
python_function('10-device_mesh_lab/controller.py', 'json_from_text', 1, 5, 7).
python_function('10-device_mesh_lab/controller.py', 'normalize_flow', 2, 20, 9).
python_function('10-device_mesh_lab/controller.py', 'llm_messages', 3, 4, 4).
python_function('10-device_mesh_lab/controller.py', 'generate_with_litellm', 3, 4, 9).
python_function('10-device_mesh_lab/controller.py', 'generate_flow', 2, 6, 7).
python_function('10-device_mesh_lab/controller.py', 'execute_flow', 3, 9, 8).
python_function('10-device_mesh_lab/controller.py', 'nl_flow', 2, 4, 8).
python_function('10-device_mesh_lab/controller.py', 'main', 0, 1, 8).
python_function('10-device_mesh_lab/device_agent.py', 'object_schema', 2, 2, 0).
python_function('10-device_mesh_lab/device_agent.py', 'default_browser_targets', 0, 2, 2).
python_function('10-device_mesh_lab/device_agent.py', 'browser_target_from_spec', 2, 3, 3).
python_function('10-device_mesh_lab/device_agent.py', 'parse_browser_targets', 1, 19, 12).
python_function('10-device_mesh_lab/device_agent.py', 'build_novnc_browser_command', 1, 1, 2).
python_function('10-device_mesh_lab/device_agent.py', 'make_agent_from_env', 0, 3, 8).
python_function('10-device_mesh_lab/device_agent.py', 'main', 0, 1, 5).
python_function('10-device_mesh_lab/mesh_env.py', 'load_env', 0, 9, 6).
python_function('10-device_mesh_lab/mesh_env.py', 'parse_peers', 1, 8, 8).
python_function('10-device_mesh_lab/mesh_env.py', 'auth_token', 0, 1, 2).
python_function('10-device_mesh_lab/mesh_env.py', 'auth_headers', 0, 2, 1).
python_function('10-device_mesh_lab/mesh_env.py', 'check_auth', 1, 2, 2).
python_function('10-device_mesh_lab/mesh_env.py', 'read_json', 1, 3, 5).
python_function('10-device_mesh_lab/mesh_env.py', 'send_json', 3, 1, 8).
python_function('10-device_mesh_lab/tests/device_agent_policy.py', 'main', 0, 17, 8).
python_function('10-device_mesh_lab/tests/gui_smoke.py', 'route', 4, 4, 0).
python_function('10-device_mesh_lab/tests/gui_smoke.py', 'free_port', 0, 1, 5).
python_function('10-device_mesh_lab/tests/gui_smoke.py', 'find_chrome', 0, 5, 3).
python_function('10-device_mesh_lab/tests/gui_smoke.py', 'recv_exact', 2, 3, 5).
python_function('10-device_mesh_lab/tests/gui_smoke.py', 'wait_for_debugger', 1, 5, 7).
python_function('10-device_mesh_lab/tests/gui_smoke.py', 'wait_for_page_ready', 1, 5, 6).
python_function('10-device_mesh_lab/tests/gui_smoke.py', 'main', 0, 5, 24).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'log', 2, 2, 2).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'json_response', 3, 1, 8).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'route_kind', 1, 2, 0).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'webdriver', 4, 7, 8).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'wait_for_webdriver', 1, 3, 4).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'ensure_session', 0, 6, 4).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'current_url', 1, 3, 4).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'open_page', 1, 3, 7).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'safe_name', 1, 2, 2).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'screenshot_page', 1, 10, 16).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'app_service_call', 2, 22, 8).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'route_call', 2, 9, 10).
python_function('11-novnc_lan_flow/computer/browser_node.py', 'main', 0, 1, 5).
python_function('11-novnc_lan_flow/orchestrator/run_flow.py', 'target_from_uri', 1, 2, 1).
python_function('11-novnc_lan_flow/orchestrator/run_flow.py', 'fetch_json', 3, 4, 7).
python_function('11-novnc_lan_flow/orchestrator/run_flow.py', 'wait_health', 2, 4, 5).
python_function('11-novnc_lan_flow/orchestrator/run_flow.py', 'collect_routes', 1, 4, 8).
python_function('11-novnc_lan_flow/orchestrator/run_flow.py', 'run_step', 1, 2, 6).
python_function('11-novnc_lan_flow/orchestrator/run_flow.py', 'main', 0, 7, 11).
python_function('12-full_e2e_connect_lab/registry-runtime/registry_server.py', 'nodes', 0, 4, 4).
python_function('12-full_e2e_connect_lab/registry-runtime/registry_server.py', 'get_json', 2, 2, 4).
python_function('12-full_e2e_connect_lab/registry-runtime/registry_server.py', 'discover', 0, 4, 7).
python_function('12-full_e2e_connect_lab/registry-runtime/registry_server.py', 'registry_document', 0, 5, 4).
python_function('12-full_e2e_connect_lab/registry-runtime/registry_server.py', 'send', 3, 1, 8).
python_function('12-full_e2e_connect_lab/scripts/assert_results.py', 'load', 1, 1, 2).
python_function('12-full_e2e_connect_lab/scripts/assert_results.py', 'main', 0, 38, 13).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'run', 1, 4, 2).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'run_json', 1, 2, 3).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'write_json', 2, 1, 3).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'fetch_catalog', 0, 1, 6).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'emit_http_check_bindings', 0, 1, 3).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'emit_time_tools_bindings', 0, 1, 3).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'emit_browser_control_bindings', 0, 1, 3).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'build_registry', 0, 1, 7).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'uri_run', 2, 2, 4).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'result_ok', 1, 1, 2).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'run_connector_routes', 0, 7, 3).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'project_mcp_a2a', 0, 1, 2).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'test_grpc_transport', 0, 2, 10).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'summarize_catalog', 2, 13, 4).
python_function('12-full_e2e_connect_lab/scripts/connector_checks.py', 'main', 0, 20, 16).
python_function('13-simple_defaults/python_connector.py', 'upper', 2, 1, 1).
python_function('13-simple_defaults/python_connector.py', 'bindings', 0, 1, 1).
python_function('13-simple_defaults/python_connector.py', 'main', 0, 2, 5).
python_function('14-llm-uri-agent/agent.py', 'load_registry', 0, 1, 3).
python_function('14-llm-uri-agent/agent.py', 'action_space', 1, 6, 4).
python_function('14-llm-uri-agent/agent.py', 'plan', 2, 8, 2).
python_function('14-llm-uri-agent/agent.py', 'run_step', 2, 3, 4).
python_function('14-llm-uri-agent/agent.py', 'main', 1, 10, 13).
python_function('14-llm-uri-agent/tools.py', 'emit', 1, 1, 2).
python_function('14-llm-uri-agent/tools.py', '_route', 4, 2, 0).
python_function('14-llm-uri-agent/tools.py', 'bindings', 0, 1, 2).
python_function('14-llm-uri-agent/tools.py', 'now', 0, 1, 2).
python_function('14-llm-uri-agent/tools.py', 'http_status', 1, 3, 5).
python_function('14-llm-uri-agent/tools.py', '_chrome_bin', 0, 3, 1).
python_function('14-llm-uri-agent/tools.py', 'browser_dom', 2, 4, 7).
python_function('14-llm-uri-agent/tools.py', 'log_event', 2, 1, 5).
python_function('14-llm-uri-agent/tools.py', 'main', 1, 10, 12).
python_function('scripts/build_site.py', 'md', 1, 28, 12).
python_function('scripts/build_site.py', 'page', 3, 2, 1).
python_function('scripts/build_site.py', 'first_title_desc', 1, 8, 4).

% ── Python Classes ───────────────────────────────────────
python_class('04-python/test_adopt.py', 'SpreadArgsTests').
python_method('SpreadArgsTests', 'test_spread_array_param_expands_into_argv', 0, 1, 6).
python_method('SpreadArgsTests', 'test_spread_defaults_to_empty', 0, 1, 4).
python_method('SpreadArgsTests', 'test_validate_accepts_spread_placeholder', 0, 1, 3).
python_class('04-python/test_adopt.py', 'PythonPackageAdoptionTests').
python_method('PythonPackageAdoptionTests', 'test_console_scripts_become_passthrough_commands', 0, 4, 4).
python_method('PythonPackageAdoptionTests', 'test_adopted_command_runs_with_passthrough_args', 0, 2, 6).
python_class('04-python/test_adopt.py', 'NpmPackageAdoptionTests').
python_method('NpmPackageAdoptionTests', 'test_bin_field_becomes_npx_command', 0, 1, 7).
python_class('04-python/test_adopt.py', 'InitTests').
python_method('InitTests', 'test_init_builds_binding_document_from_project', 0, 1, 3).
python_class('04-python/test_adopt.py', 'CliTests').
python_method('CliTests', 'test_add_python_package_compile_and_run', 0, 1, 6).
python_class('04-python/test_mcp_a2a.py', 'McpProjectionTests').
python_method('McpProjectionTests', 'setUp', 0, 1, 1).
python_method('McpProjectionTests', 'test_mcp_manifest_exposes_tools_with_json_schema', 0, 2, 4).
python_method('McpProjectionTests', 'test_tool_index_maps_back_to_uris', 0, 1, 3).
python_method('McpProjectionTests', 'test_call_tool_dry_run_renders_command', 0, 1, 4).
python_method('McpProjectionTests', 'test_call_unknown_tool_raises', 0, 1, 2).
python_class('04-python/test_mcp_a2a.py', 'A2aCardTests').
python_method('A2aCardTests', 'test_agent_card_lists_skills', 0, 3, 7).
python_class('04-python/test_mcp_a2a.py', 'McpServerTests').
python_method('McpServerTests', 'test_jsonrpc_roundtrip_over_streams', 0, 2, 13).
python_class('04-python/test_mcp_a2a.py', 'BackendInteropTests').
python_method('BackendInteropTests', 'test_backend_serves_mcp_tools_and_calls', 0, 5, 26).
python_class('04-python/test_urihandler_v2.py', 'DecoratorTests').
python_method('DecoratorTests', 'test_decorator_generates_schema_and_argv_runtime', 0, 1, 8).
python_method('DecoratorTests', 'test_shell_decorator_executes_only_when_shell_policy_allows_it', 0, 1, 8).
python_class('04-python/test_urihandler_v2.py', 'SchemaRuntimeTests').
python_method('SchemaRuntimeTests', 'setUp', 0, 1, 3).
python_method('SchemaRuntimeTests', 'test_json_schema_defaults_are_applied_before_rendering', 0, 1, 2).
python_method('SchemaRuntimeTests', 'test_missing_required_input_is_schema_error', 0, 1, 4).
python_method('SchemaRuntimeTests', 'test_shell_binding_is_real_shell_runtime_when_allowed', 0, 1, 4).
python_method('SchemaRuntimeTests', 'test_document_validation_catches_unresolved_placeholders', 0, 1, 3).
python_class('04-python/test_urihandler_v2.py', 'ArtifactAdoptionTests').
python_method('ArtifactAdoptionTests', 'test_artifact_scan_builds_v2_bindings_from_common_standards', 0, 2, 5).
python_method('ArtifactAdoptionTests', 'test_cli_scan_validate_compile_and_run', 0, 1, 6).
python_method('ArtifactAdoptionTests', 'test_cli_add_pypi_and_command_binding_in_one_line', 0, 1, 6).
python_class('04-python/test_urihandler_v2.py', 'HtmlAppTests').
python_method('HtmlAppTests', 'test_html_backend_dispatches_v2_runtime', 0, 5, 23).
python_class('06-html_uri_app/backend.py', 'Handler').
python_method('Handler', 'log_message', 1, 1, 1).
python_method('Handler', 'do_GET', 0, 8, 14).
python_method('Handler', 'do_POST', 0, 4, 6).
python_method('Handler', 'read_body', 0, 3, 5).
python_method('Handler', 'serve_static', 1, 7, 13).
python_class('09-docker_uri_flow/python-worker/server.py', 'Handler').
python_method('Handler', 'log_message', 1, 1, 0).
python_method('Handler', 'do_GET', 0, 3, 1).
python_method('Handler', 'do_POST', 0, 6, 8).
python_class('09-docker_uri_flow/shell-worker/server.py', 'Handler').
python_method('Handler', 'log_message', 1, 1, 0).
python_method('Handler', 'do_GET', 0, 3, 1).
python_method('Handler', 'do_POST', 0, 6, 8).
python_class('10-device_mesh_lab/controller.py', 'Handler').
python_method('Handler', '__init__', 0, 1, 3).
python_method('Handler', 'end_headers', 0, 1, 3).
python_method('Handler', 'do_OPTIONS', 0, 1, 1).
python_method('Handler', 'do_GET', 0, 2, 5).
python_method('Handler', 'do_POST', 0, 12, 13).
python_class('10-device_mesh_lab/device_agent.py', 'DeviceAgent').
python_method('DeviceAgent', '__init__', 6, 3, 3).
python_method('DeviceAgent', 'log', 2, 2, 6).
python_method('DeviceAgent', 'recent_logs', 1, 4, 5).
python_method('DeviceAgent', 'append_note', 1, 1, 6).
python_method('DeviceAgent', 'routes', 0, 2, 2).
python_method('DeviceAgent', 'device_card', 0, 1, 6).
python_method('DeviceAgent', 'browser_target', 0, 2, 1).
python_method('DeviceAgent', 'installable', 0, 1, 0).
python_method('DeviceAgent', 'processes', 2, 6, 7).
python_method('DeviceAgent', 'safe_command', 2, 4, 4).
python_method('DeviceAgent', 'open_browser_on_host', 2, 2, 2).
python_method('DeviceAgent', 'open_browser_in_novnc', 2, 9, 14).
python_method('DeviceAgent', 'open_browser', 1, 3, 3).
python_method('DeviceAgent', 'dispatch', 2, 27, 15).
python_method('DeviceAgent', 'handler', 0, 1, 14).
python_method('DeviceAgent', 'serve', 2, 2, 4).
python_class('10-device_mesh_lab/tests/gui_smoke.py', 'DemoHandler').
python_method('DemoHandler', '__init__', 0, 1, 3).
python_method('DemoHandler', 'log_message', 1, 1, 0).
python_method('DemoHandler', 'send_json', 1, 4, 8).
python_method('DemoHandler', 'do_GET', 0, 2, 4).
python_method('DemoHandler', 'do_POST', 0, 5, 9).
python_class('10-device_mesh_lab/tests/gui_smoke.py', 'ThreadedHTTPServer').
python_class('10-device_mesh_lab/tests/gui_smoke.py', 'WebSocket').
python_method('WebSocket', '__init__', 1, 1, 10).
python_method('WebSocket', 'send_json', 1, 4, 11).
python_method('WebSocket', 'recv_json', 0, 9, 7).
python_method('WebSocket', 'close', 0, 1, 1).
python_class('10-device_mesh_lab/tests/gui_smoke.py', 'CDP').
python_method('CDP', '__init__', 1, 1, 1).
python_method('CDP', 'call', 2, 5, 4).
python_method('CDP', 'close', 0, 1, 1).
python_class('11-novnc_lan_flow/computer/browser_node.py', 'Handler').
python_method('Handler', 'log_message', 1, 1, 2).
python_method('Handler', 'do_OPTIONS', 0, 1, 1).
python_method('Handler', 'do_GET', 0, 6, 3).
python_method('Handler', 'do_POST', 0, 9, 13).
python_class('12-full_e2e_connect_lab/registry-runtime/registry_server.py', 'Handler').
python_method('Handler', 'do_GET', 0, 4, 4).
python_method('Handler', 'log_message', 1, 1, 0).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────
makefile_target('test', '').
makefile_target('help', '').
makefile_target('site', '').
makefile_target('deploy', '').

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
```

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

## Intent

ifURI examples
