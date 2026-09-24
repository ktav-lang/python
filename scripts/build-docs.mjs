#!/usr/bin/env node
// Rebuilds this repository's README/CHANGELOG/CONTRIBUTING/SECURITY/EXAMPLES from
// root-docs/, using @ktav-lang/polydoc. Run with --check for a
// CI-friendly, read-only verification instead of regenerating the files.
//
// OUTPUT MAPPING. polydoc 0.1.0's writeRootDocs/checkRootDocs can only
// write root-relative paths (`<DOC>.md`, `<DOC>.<lang>.md`). This repo
// scatters its generated documents instead, so this script asks polydoc
// for the assembled per-language buffers with buildRootDocs() and then
// writes / byte-compares them itself at the paths in OUT_PATHS below:
//
//   README       README.md             docs/ru/README.ru.md     docs/zh/README.zh.md
//   CHANGELOG    CHANGELOG.md          docs/ru/CHANGELOG.ru.md   docs/zh/CHANGELOG.zh.md
//   CONTRIBUTING docs/CONTRIBUTING.md  docs/ru/CONTRIBUTING.ru.md docs/zh/CONTRIBUTING.zh.md
//   SECURITY     docs/SECURITY.md      docs/ru/SECURITY.ru.md   docs/zh/SECURITY.zh.md
//   EXAMPLES     examples/README.md    examples/README.ru.md   examples/README.zh.md
//
// The English CONTRIBUTING/SECURITY artifacts live in docs/ so the root
// directory stays readable at a glance, and every non-English artifact
// lives beside its sibling under docs/<lang>/. What is written is decided
// exactly once, by this table — buildRootDocs() only assembles bytes.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { configure, buildRootDocs } from '@ktav-lang/polydoc';

const LANGS = ['en', 'ru', 'zh'];

// Repo-relative destination of every generated document, per language.
const OUT_PATHS = {
  README: {
    en: 'README.md',
    ru: 'docs/ru/README.ru.md',
    zh: 'docs/zh/README.zh.md',
  },
  CHANGELOG: {
    en: 'CHANGELOG.md',
    ru: 'docs/ru/CHANGELOG.ru.md',
    zh: 'docs/zh/CHANGELOG.zh.md',
  },
  CONTRIBUTING: {
    en: 'docs/CONTRIBUTING.md',
    ru: 'docs/ru/CONTRIBUTING.ru.md',
    zh: 'docs/zh/CONTRIBUTING.zh.md',
  },
  SECURITY: {
    en: 'docs/SECURITY.md',
    ru: 'docs/ru/SECURITY.ru.md',
    zh: 'docs/zh/SECURITY.zh.md',
  },
  EXAMPLES: {
    en: 'examples/README.md',
    ru: 'examples/README.ru.md',
    zh: 'examples/README.zh.md',
  },
};

configure({
  langs: LANGS,
  rootDocuments: ['README', 'CHANGELOG', 'CONTRIBUTING', 'SECURITY', 'EXAMPLES'],
});

// SECURITY's supported-versions table row uses @@MINOR_LINE@@ (mirroring
// ktav-lang/rust's SECURITY.md) so that row can never quietly lag the
// version in Cargo.toml. The real version is read here and handed to
// polydoc, which substitutes the token and asserts no placeholder
// survives, for every language.
function readCargoVersion(root) {
  const toml = fs.readFileSync(path.join(root, 'Cargo.toml'), 'utf8');
  const match = toml.match(/^version\s*=\s*"([^"]+)"/mu);
  if (!match) throw new Error('Cargo.toml: no top-level version field found');
  return match[1];
}

// Per-unit validation proves every meaning has every language. It does
// NOT prove the languages describe the same DOCUMENT: a heading demoted
// from ## to ### in one translation, or an extra heading in another,
// passes unit validation untouched. This check (ported from the rust
// repository's docs build) is what catches that class of drift.
function headingSkeleton(markdown) {
  const levels = [];
  let fenceChar = null;
  let fenceLen = 0;
  for (const line of markdown.split('\n')) {
    const fence = line.match(/^\s{0,3}(`{3,}|~{3,})/u);
    if (fence) {
      const char = fence[1][0];
      const len = fence[1].length;
      if (fenceChar === null) { fenceChar = char; fenceLen = len; }
      else if (char === fenceChar && len >= fenceLen) { fenceChar = null; }
      continue;
    }
    if (fenceChar !== null) continue;
    const heading = line.match(/^(#{1,6})\s+\S/u);
    if (heading) levels.push(heading[1].length);
  }
  return levels;
}

function structuralProblems(label, perLang) {
  const [reference, ...others] = LANGS;
  const base = headingSkeleton(perLang.get(reference).toString('utf8'));
  const problems = [];
  for (const lang of others) {
    const other = headingSkeleton(perLang.get(lang).toString('utf8'));
    if (other.length !== base.length) {
      problems.push(`${label}: ${lang} has ${other.length} heading(s) but ${reference} has ` +
        `${base.length} — the translations describe different documents`);
      continue;
    }
    const at = base.findIndex((level, i) => level !== other[i]);
    if (at !== -1) {
      problems.push(`${label}: heading #${at + 1} is level ${other[at]} in ${lang} but ` +
        `level ${base[at]} in ${reference}`);
    }
  }
  return problems;
}

// A built document with no destination here would otherwise be silently
// dropped, which is exactly how a generated artifact goes stale. Checked
// for every built document and language before anything is written or
// compared, so the failure is a plain diagnostic rather than a mid-loop
// crash.
function outPath(doc, lang) {
  const paths = OUT_PATHS[doc];
  if (paths === undefined || paths[lang] === undefined) {
    throw new Error(`no OUT_PATHS entry for ${doc} (${lang}); decide where this ` +
      `document is written before adding it to rootDocuments`);
  }
  return paths[lang];
}

/// Byte-compare every generated buffer against the file on disk, in
/// polydoc's checkRootDocs() message style. Returns a list of
/// human-readable divergences; empty means identical.
function checkDocs(root, docs) {
  const problems = [];
  for (const [doc, perLang] of docs) {
    for (const lang of LANGS) {
      const rel = outPath(doc, lang);
      const expected = perLang.get(lang);
      let actual;
      try {
        actual = fs.readFileSync(path.join(root, rel));
      } catch (e) {
        problems.push(`${rel} is missing or unreadable (${e.message}); it is generated from ` +
          `root-docs/${doc}/`);
        continue;
      }
      if (actual.equals(expected)) continue;
      let off = 0;
      const min = Math.min(actual.length, expected.length);
      while (off < min && actual[off] === expected[off]) off++;
      const line = expected.subarray(0, off).toString('utf8').split('\n').length;
      problems.push(
        `${rel} differs from what root-docs/${doc}/ generates, first at byte ${off} ` +
        `(line ${line}); edit the unit source, never the generated file`);
    }
  }
  return problems;
}

function usage() {
  process.stderr.write(
    'usage: node scripts/build-docs.mjs [--check]\n' +
    '  (no args)  regenerate the root documents from root-docs/ (see OUT_PATHS)\n' +
    '  --check    verify the generated files match root-docs/ without writing\n'
  );
}

function cli() {
  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const root = path.resolve(scriptDir, '..');

  const args = process.argv.slice(2);
  if (args.includes('-h') || args.includes('--help')) { usage(); process.exit(0); }
  if (args.length > 1 || (args.length === 1 && args[0] !== '--check')) {
    usage();
    process.exit(1);
  }
  const checkMode = args[0] === '--check';

  let docs;
  try {
    // Pass the release so SECURITY's @@MINOR_LINE@@ cell is substituted
    // from Cargo.toml's real version (e.g. 0.8.0 -> 0.8.x) and can never
    // quietly fall behind it (same rationale as rust's); the substitution
    // and the surviving-placeholder check run inside polydoc for every
    // language.
    const version = readCargoVersion(root);
    docs = buildRootDocs(root, { release: { version, released: '' } });
    for (const [name, perLang] of docs) {
      for (const lang of LANGS) outPath(name, lang);
      const problems = structuralProblems(name, perLang);
      if (problems.length > 0) {
        throw new Error(problems.join('\n'));
      }
    }
  } catch (e) {
    process.stderr.write(`build-docs: ${e.message}\n`);
    process.exit(1);
  }

  if (!checkMode) {
    for (const [doc, perLang] of docs) {
      for (const lang of LANGS) {
        const rel = outPath(doc, lang);
        const destination = path.join(root, rel);
        fs.mkdirSync(path.dirname(destination), { recursive: true });
        fs.writeFileSync(destination, perLang.get(lang));
      }
    }
    process.stdout.write(`build-docs: assembled ${docs.size} document(s) from root-docs/\n`);
    process.exit(0);
  }

  const problems = checkDocs(root, docs);
  if (problems.length > 0) {
    for (const problem of problems) {
      process.stderr.write(`build-docs --check: ${problem}\n`);
    }
    process.exit(1);
  }
  process.exit(0);
}

const isMain = process.argv[1] !== undefined &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (isMain) cli();
