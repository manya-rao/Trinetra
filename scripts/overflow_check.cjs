// overflow_check.cjs — CJS script to measure page overflow at 4 viewport widths
// and take screenshots. Run from repo root with:
//   node scripts/overflow_check.cjs
'use strict';
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

const REPO = path.join(__dirname, '..');
const FRONTEND = path.join(REPO, 'frontend');
const SCREENS = path.join(REPO, 'docs', 'screens');
const PORT = 5174;

if (!fs.existsSync(SCREENS)) fs.mkdirSync(SCREENS, { recursive: true });

// Start vite
const vite = spawn(
  path.join(FRONTEND, 'node_modules', '.bin', 'vite.cmd'),
  ['--port', String(PORT)],
  { cwd: FRONTEND, shell: true, stdio: ['ignore', 'pipe', 'pipe'] }
);
vite.stdout.on('data', d => process.stdout.write(String(d)));
vite.stderr.on('data', d => process.stderr.write(String(d)));

function waitForServer(port, timeout) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    function try1() {
      http.get('http://localhost:' + port, function(r) {
        r.resume(); resolve();
      }).on('error', function() {
        if (Date.now() - start > timeout) return reject(new Error('Server timeout'));
        setTimeout(try1, 600);
      });
    }
    try1();
  });
}

async function main() {
  console.log('Waiting for vite on port', PORT, '...');
  await waitForServer(PORT, 20000);
  console.log('Server is up. Launching Puppeteer...');

  const puppeteer = require(path.join(FRONTEND, 'node_modules', 'puppeteer'));
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const widths = [390, 768, 1280, 1920];
  const sections = ['top', 'problem', 'pipeline', 'verify', 'ladder'];
  const results = [];

  for (const w of widths) {
    const page = await browser.newPage();
    await page.setViewport({ width: w, height: 900 });
    await page.goto('http://localhost:' + PORT, { waitUntil: 'networkidle0', timeout: 20000 });
    await new Promise(r => setTimeout(r, 800));

    const overflow = await page.evaluate(function() {
      return {
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        diff: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      };
    });
    results.push({ width: w, ...overflow });
    const status = overflow.diff === 0 ? 'OK — no overflow' : 'OVERFLOW +' + overflow.diff + 'px';
    console.log('w=' + w + ': scrollWidth=' + overflow.scrollWidth + ' clientWidth=' + overflow.clientWidth + ' → ' + status);

    // Screenshots at 390 and 1280
    if (w === 390 || w === 1280) {
      for (const id of sections) {
        try {
          const el = await page.$('#' + id);
          if (el) {
            const fname = path.join(SCREENS, 'w' + w + '_' + id + '.png');
            await el.screenshot({ path: fname });
            console.log('  SCREENSHOT: docs/screens/w' + w + '_' + id + '.png');
          } else {
            console.log('  MISSING: #' + id + ' not found at w=' + w);
          }
        } catch (e) {
          console.error('  ERROR screenshot #' + id + ':', e.message);
        }
      }
    }
    await page.close();
  }

  console.log('\n=== OVERFLOW SUMMARY ===');
  for (const r of results) {
    const st = r.diff === 0 ? 'OK' : 'OVERFLOW +' + r.diff + 'px';
    console.log('  w=' + r.width + ': scrollWidth=' + r.scrollWidth + ' clientWidth=' + r.clientWidth + ' ' + st);
  }

  await browser.close();
  vite.kill();
  process.exit(0);
}

main().catch(function(e) {
  console.error('Fatal:', e.message);
  vite.kill();
  process.exit(1);
});
