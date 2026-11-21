// Overflow check script: measures scrollWidth vs clientWidth at 390/768/1280/1920
// and takes screenshots of key sections at 390 and 1280.
import { createServer } from 'http';
import { exec, spawn } from 'child_process';
import { mkdirSync, existsSync } from 'fs';
import { join } from 'path';

const REPO = 'C:/cloud/Desktop/Trinetra-repo';
const SCREENS_DIR = join(REPO, 'docs/screens');
const FRONTEND = join(REPO, 'frontend');
const PORT = 5174;

if (!existsSync(SCREENS_DIR)) mkdirSync(SCREENS_DIR, { recursive: true });

// Start vite
const vite = spawn('node_modules/.bin/vite.cmd', ['--port', String(PORT)], {
  cwd: FRONTEND,
  shell: true,
  stdio: 'pipe',
});
vite.stderr.on('data', d => process.stderr.write(d));

function waitForServer(url, timeout) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const tryOnce = () => {
      import('http').then(({ default: http }) => {
        const req = http.get(url, r => { r.resume(); resolve(); });
        req.on('error', e => {
          if (Date.now() - start > timeout) return reject(e);
          setTimeout(tryOnce, 600);
        });
        req.setTimeout(1000, () => { req.destroy(); setTimeout(tryOnce, 600); });
      });
    };
    tryOnce();
  });
}

async function run() {
  console.log('Waiting for vite on port', PORT, '...');
  await waitForServer(`http://localhost:${PORT}`, 20000);
  console.log('Server is up.');

  const { default: puppeteer } = await import(
    join(FRONTEND, 'node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js')
      .replace(/\\/g, '/')
  );

  // Try standard puppeteer launch
  let browser;
  try {
    // Use dynamic import for puppeteer from node_modules
    const pMod = await import(`file:///${join(FRONTEND, 'node_modules/puppeteer').replace(/\\/g, '/')}/lib/esm/puppeteer/puppeteer.js`);
    browser = await pMod.default.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  } catch (e) {
    console.error('Puppeteer launch failed:', e.message);
    vite.kill();
    process.exit(1);
  }

  const widths = [390, 768, 1280, 1920];
  const sections = ['top', 'problem', 'pipeline', 'verify', 'ladder'];
  const results = [];

  for (const w of widths) {
    const page = await browser.newPage();
    await page.setViewport({ width: w, height: 900 });
    await page.goto(`http://localhost:${PORT}`, { waitUntil: 'networkidle0', timeout: 20000 });
    await new Promise(r => setTimeout(r, 600));

    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    }));
    results.push({ width: w, ...overflow });
    console.log(`w=${w}: scrollWidth=${overflow.scrollWidth} clientWidth=${overflow.clientWidth} overflow=${overflow.overflow}px`);

    // Screenshots at 390 and 1280
    if (w === 390 || w === 1280) {
      for (const id of sections) {
        try {
          const el = await page.$(`#${id}`);
          if (el) {
            const fname = join(SCREENS_DIR, `w${w}_${id}.png`);
            await el.screenshot({ path: fname });
            console.log(`SCREENSHOT: docs/screens/w${w}_${id}.png`);
          } else {
            console.log(`MISSING SECTION #${id} at w=${w}`);
          }
        } catch (e) {
          console.error(`Screenshot error #${id} w=${w}:`, e.message);
        }
      }
    }
    await page.close();
  }

  console.log('\n=== OVERFLOW SUMMARY ===');
  for (const r of results) {
    const status = r.overflow === 0 ? 'OK' : `OVERFLOW +${r.overflow}px`;
    console.log(`  w=${r.width}: scrollWidth=${r.scrollWidth} clientWidth=${r.clientWidth} → ${status}`);
  }

  await browser.close();
  vite.kill();
  process.exit(0);
}

run().catch(e => {
  console.error('Fatal:', e);
  vite.kill();
  process.exit(1);
});
