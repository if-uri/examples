# v2 binding generators

These examples show the same v2 binding contract generated from several
language-native declaration styles:

- `js/` - plain JavaScript helper, no transpiler
- `nodejs/` - Node.js script that writes a binding document
- `ts/` - TypeScript decorator-style declaration
- `php/` - PHP 8 attribute + reflection
- `go/` - Go typed descriptors and struct-like field definitions
- `c/` - C static descriptor emitting the same JSON contract

All examples generate the same shape:

```json
{
  "version": "urirun.bindings.v2",
  "bindings": {
    "scheme://target/resource/operation": {
      "kind": "command",
      "adapter": "argv-template",
      "inputSchema": {},
      "argv": []
    }
  }
}
```

The runtime does not care which language generated the file. It only consumes
the v2 JSON contract.

Run from the repository root:

```bash
./run_tests.sh
```

The smoke tests execute every installed language generator and validate the
generated binding document through `urirun validate`.
