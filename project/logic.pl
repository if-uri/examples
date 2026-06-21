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
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, './run_tests.sh').
sumd_workflow('site', 'manual').
sumd_workflow_step('site', 1, 'python3 scripts/build_site.py _site').
sumd_workflow('deploy', 'manual').
sumd_workflow_step('deploy', 1, 'bash scripts/deploy-plesk.sh').

