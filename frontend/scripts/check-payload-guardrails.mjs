import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';

const SRC_DIR = path.resolve(process.cwd(), 'src');
const TARGET_EXTENSIONS = new Set(['.ts', '.vue']);
const EXCLUDE_SUFFIXES = ['.bak'];

const PARTIAL_ENTITY_PATTERN = /Partial\s*<\s*(Task|Todo|Timeline|Profile)\s*>/g;
const SPREAD_UPDATE_PATTERN = /(taskService|todoService|timelineService|profileService)\.update\([\s\S]{0,260}?\{[\s\S]{0,260}?\.\.\./g;

const violations = [];

const shouldScan = (filePath) => {
  const ext = path.extname(filePath);
  if (!TARGET_EXTENSIONS.has(ext)) return false;
  return !EXCLUDE_SUFFIXES.some((suffix) => filePath.endsWith(suffix));
};

const collectFiles = async (dir) => {
  const entries = await readdir(dir, { withFileTypes: true });
  const all = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      all.push(...await collectFiles(fullPath));
      continue;
    }
    if (shouldScan(fullPath)) all.push(fullPath);
  }

  return all;
};

const lineOfIndex = (text, index) => text.slice(0, index).split('\n').length;

const scanPattern = (content, filePath, pattern, message) => {
  for (const match of content.matchAll(pattern)) {
    const idx = match.index ?? 0;
    violations.push({
      filePath,
      line: lineOfIndex(content, idx),
      message,
      snippet: match[0].replace(/\s+/g, ' ').trim().slice(0, 140),
    });
  }
};

const main = async () => {
  const files = await collectFiles(SRC_DIR);

  for (const filePath of files) {
    const content = await readFile(filePath, 'utf8');
    scanPattern(
      content,
      filePath,
      PARTIAL_ENTITY_PATTERN,
      'Disallowed update payload type: Partial<Entity>. Use explicit Update*Payload types.'
    );
    scanPattern(
      content,
      filePath,
      SPREAD_UPDATE_PATTERN,
      'Disallowed spread object sent into service.update(...). Use payload mappers instead.'
    );
  }

  if (violations.length === 0) {
    console.log('Payload guardrails: PASS');
    process.exit(0);
  }

  console.error('Payload guardrails: FAIL');
  for (const v of violations) {
    const rel = path.relative(process.cwd(), v.filePath).replaceAll('\\\\', '/');
    console.error(`- ${rel}:${v.line} ${v.message}`);
    console.error(`  ${v.snippet}`);
  }

  process.exit(1);
};

main().catch((error) => {
  console.error('Payload guardrails: ERROR');
  console.error(error);
  process.exit(1);
});
