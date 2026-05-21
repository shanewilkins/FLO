import ELK from 'elkjs/lib/elk.bundled.js';

const readStdin = async () => {
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }
  return input;
};

try {
  const raw = await readStdin();
  const payload = JSON.parse(raw || '{}');
  const elk = new ELK();
  const result = await elk.layout(payload);
  process.stdout.write(JSON.stringify(result));
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(message);
  process.exitCode = 1;
}