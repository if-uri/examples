export function string(options = {}) {
  return field('string', options);
}

export function integer(options = {}) {
  return field('integer', options);
}

export function boolean(options = {}) {
  return field('boolean', options);
}

function field(type, options) {
  const { required, ...schema } = options;
  return { schema: { type, ...schema }, required: required ?? !Object.hasOwn(schema, 'default') };
}

export function connector({ id, scheme = id.replaceAll('-', ''), target = 'host', meta = {} }) {
  const commands = [];
  const fullUri = (route) => (route.includes('://') ? route : `${scheme}://${target}/${route.replace(/^\/+/, '')}`);

  return {
    uri: fullUri,
    command(route, { fields = {}, argv, kind = 'command', adapter = 'argv-template', meta: routeMeta = {} }) {
      const uri = fullUri(route);
      const placeholders = Object.fromEntries(Object.keys(fields).map((name) => [name, `{${name}}`]));
      const properties = Object.fromEntries(Object.entries(fields).map(([name, spec]) => [name, spec.schema]));
      const required = Object.entries(fields)
        .filter(([, spec]) => spec.required)
        .map(([name]) => name);

      commands.push({
        uri,
        kind,
        adapter,
        inputSchema: { type: 'object', required, properties, additionalProperties: false },
        argv: argv(placeholders),
        meta: { connector: id, ...meta, ...routeMeta },
      });
      return uri;
    },
    bindings() {
      return {
        version: 'urirun.bindings.v2',
        bindings: Object.fromEntries(commands.map((binding) => [binding.uri, binding])),
      };
    },
  };
}
