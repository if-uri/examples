import { connector, string } from './defaults.mjs';

const demo = connector({ id: 'defaults-demo', scheme: 'demo', meta: { area: 'example' } });

demo.command('text/query/reverse', {
  fields: {
    text: string(),
    suffix: string({ default: '' }),
  },
  meta: { label: 'Reverse text' },
  argv: ({ text, suffix }) => [
    'node',
    '-e',
    'const [text, suffix] = process.argv.slice(1); console.log((text + suffix).split("").reverse().join(""))',
    text,
    suffix,
  ],
});

console.log(JSON.stringify(demo.bindings(), null, 2));
