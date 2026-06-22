#!/usr/bin/env node
// Pretend this is your EXISTING Node notification function — a different runtime,
// a different library ecosystem. urirun gives it the SAME shop:// URI surface as
// the Python module, with no rewrite.
const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, tok, i, a) => {
    if (tok.startsWith("--")) acc.push([tok.slice(2), a[i + 1]]);
    return acc;
  }, []),
);

const result = { sent: true, channel: "email", to: args.to ?? "", message: args.msg ?? "" };
process.stdout.write(JSON.stringify(result) + "\n");
