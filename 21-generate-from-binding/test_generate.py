# Author: Tom Sapletta · https://tom.sapletta.com
import ast, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate, urirun


def test_generates_typed_artifacts_from_binding():
    sys.path.insert(0, str(generate.ROOT / "urirun-connector-domain-monitor"))
    import urirun_connector_domain_monitor as conn
    reg = urirun.compile_registry(conn.urirun_bindings())
    rs = list(generate.routes(reg))
    assert rs, "no routes"
    proto = generate.gen_proto(rs)
    assert proto.count("returns (RunResult)") == len(rs)  # one rpc per route
    assert "message RunResult" in proto
    oa = generate.gen_openapi(rs)
    assert len(oa["paths"]) == len(rs) and oa["openapi"].startswith("3.")
    ast.parse(generate.gen_client(rs))                     # client is valid Python
