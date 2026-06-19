# 13 - simple defaults

This example shows the ergonomic target for connector authors:

- declare the connector once,
- use short URI paths inside the connector,
- derive JSON Schema from language-native declarations,
- export the same `urirun.bindings.v2` document for registry, MCP and A2A.

## Python

```python
import urirun

connector = urirun.connector("defaults-demo", scheme="demo")

@connector.command("text/query/upper")
def upper(text: str, suffix: str = ""):
    return ["python3", "-c", "import sys; print((sys.argv[1] + sys.argv[2]).upper())", "{text}", "{suffix}"]

bindings = connector.bindings()
```

The full route becomes:

```text
demo://host/text/query/upper
```

`text` is required because it has no default. `suffix` is optional because the
function signature has a default value.

Run:

```bash
python3 python_connector.py > /tmp/defaults.bindings.json
urirun validate /tmp/defaults.bindings.json
urirun compile /tmp/defaults.bindings.json --out /tmp/defaults.registry.json
```

## JavaScript

The JS helper mirrors the same convention:

```js
const demo = connector({ id: 'defaults-demo', scheme: 'demo' });

demo.command('text/query/reverse', {
  fields: { text: string(), suffix: string({ default: '' }) },
  argv: ({ text, suffix }) => ['node', '-e', '...', text, suffix],
});

console.log(JSON.stringify(demo.bindings(), null, 2));
```

Run:

```bash
node js/example.mjs > /tmp/defaults-js.bindings.json
urirun validate /tmp/defaults-js.bindings.json
```

## Convention

| Input | Default |
| --- | --- |
| connector id | stable package id, for example `defaults-demo` |
| scheme | explicit when needed, otherwise id without dashes |
| target | `host` |
| route path | connector-local path, for example `text/query/upper` |
| metadata | `meta.connector` is filled automatically |
| schema required fields | parameters without default values |
