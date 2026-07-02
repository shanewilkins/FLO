import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const resolveElkSpecifiers = () => {
  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const fromScriptNodeModules = path.resolve(
    scriptDir,
    '../../../../node_modules/elkjs/lib/elk.bundled.js'
  );
  const fromCwdNodeModules = path.resolve(
    process.cwd(),
    'node_modules/elkjs/lib/elk.bundled.js'
  );
  const explicitPath = process.env.FLO_ELKJS_PATH;

  const specifiers = ['elkjs/lib/elk.bundled.js'];
  if (explicitPath) {
    specifiers.push(pathToFileURL(path.resolve(explicitPath)).href);
  }
  specifiers.push(pathToFileURL(fromScriptNodeModules).href);
  specifiers.push(pathToFileURL(fromCwdNodeModules).href);
  return specifiers;
};

const loadElk = async () => {
  const attempts = [];
  for (const specifier of resolveElkSpecifiers()) {
    try {
      const mod = await import(specifier);
      if (mod?.default) {
        return mod.default;
      }
      attempts.push(`Loaded '${specifier}' but no default export was found.`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      attempts.push(`Failed '${specifier}': ${message}`);
    }
  }
  throw new Error(`Unable to resolve elkjs runtime. ${attempts.join(' ')}`);
};

const readStdin = async () => {
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }
  return input;
};

try {
  const ELK = await loadElk();
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