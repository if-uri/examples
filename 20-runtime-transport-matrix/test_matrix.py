# Author: Tom Sapletta · https://tom.sapletta.com
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matrix, urirun, json


def test_language_x_transport_matrix():
    matrix.check_all.setup_polyglot_bin()
    for c in matrix.CONNECTORS:
        reg = urirun.compile_registry(matrix.check_all.emit_bindings(c))
        outs = []
        for t, fn in matrix.TRANSPORTS.items():
            env = fn(c["uri"], c["payload"], reg)
            ok = bool(env.get("ok")) or bool((matrix.connector_output(env) or {}).get("ok"))
            assert ok, f"{c['n']} failed over {t}"
            outs.append(json.dumps(matrix.connector_output(env), sort_keys=True))
        if c["det"]:                       # deterministic connectors: byte-identical across transports
            assert len(set(outs)) == 1, f"{c['n']} differs across transports: {outs}"
