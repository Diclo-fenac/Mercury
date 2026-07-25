/**
 * Mercury Widget Build Script
 *
 * Produces:
 *   mercury-widget.js      – development, unminified (with comments)
 *   mercury-widget.min.js  – production, minified, no source map shipped
 *
 * Bundle budget: 30 KB gzip. Script will print warning if exceeded.
 */

import * as esbuild from 'esbuild';
import { gzipSync } from 'zlib';
import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const entry = join(__dir, 'src', 'index.js');
const GZIP_BUDGET_BYTES = 30 * 1024; // 30 KB

const sharedOptions = {
  entryPoints: [entry],
  bundle: true,
  format: 'iife',
  globalName: '__mercuryWidget__',
  platform: 'browser',
  target: ['es2018', 'chrome80', 'firefox75', 'safari13', 'edge80'],
  loader: { '.css': 'text' },
  define: {
    'process.env.NODE_ENV': '"production"',
  },
  legalComments: 'none',
};

// -- Development build --
await esbuild.build({
  ...sharedOptions,
  outfile: join(__dir, 'mercury-widget.js'),
  minify: false,
  sourcemap: 'inline',
});

// -- Production build --
await esbuild.build({
  ...sharedOptions,
  outfile: join(__dir, 'mercury-widget.min.js'),
  minify: true,
  sourcemap: false,
  metafile: true,
});

// -- Size report --
const minified = readFileSync(join(__dir, 'mercury-widget.min.js'));
const gzipped  = gzipSync(minified, { level: 9 });

const rawKB   = (minified.length  / 1024).toFixed(1);
const gzipKB  = (gzipped.length   / 1024).toFixed(1);

console.log('\n📦 Mercury Widget Build Report');
console.log(`   Raw:     ${rawKB} KB`);
console.log(`   Gzip:    ${gzipKB} KB`);

if (gzipped.length > GZIP_BUDGET_BYTES) {
  console.error(`\n❌ BUNDLE BUDGET EXCEEDED: ${gzipKB} KB gzip > 30 KB budget`);
  process.exit(1);
} else {
  console.log(`   ✅ Within 30 KB gzip budget`);
}

// Write a size badge JSON for CI consumption
writeFileSync(
  join(__dir, 'bundle-size.json'),
  JSON.stringify({ rawKB: parseFloat(rawKB), gzipKB: parseFloat(gzipKB), budget: 30 }, null, 2)
);
