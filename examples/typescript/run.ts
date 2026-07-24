const args = Bun.argv.slice(2);

if (args.length > 1 || (args.length === 1 && args[0] !== "--dry-run")) {
  console.error("usage: bun run run.ts [--dry-run]");
  process.exit(2);
}

const message = Bun.env.RUNWISP_EXAMPLE_MESSAGE;
console.log(args[0] === "--dry-run" ? `dry-run: ${message}` : message);
