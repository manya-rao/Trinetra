import { spawn } from 'child_process';
import http from 'http';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');
const screensDir = path.join(rootDir, 'docs', 'screens');
fs.mkdirSync(screensDir, { recursive: true });

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const DEBUG_PORT = 9222;
const FRONTEND_PORT = 5173;

function wait(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', (c) => (data += c));
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

async function main() {
  console.log('================================================================');
  console.log('TRINETRA: OVERFLOW MEASUREMENT (NO OVERFLOW-X HIDDEN) & SCREENS');
  console.log('================================================================\n');

  // 1. Start Vite Preview Server
  console.log('1. Starting Vite preview server on port', FRONTEND_PORT, '...');
  const viteProc = spawn('npx.cmd', ['vite', 'preview', '--port', String(FRONTEND_PORT)], {
    cwd: path.join(rootDir, 'frontend'),
    stdio: 'ignore',
    shell: true,
  });

  // Wait for Vite to respond
  let viteReady = false;
  for (let i = 0; i < 20; i++) {
    await wait(500);
    try {
      await new Promise((resolve, reject) => {
        const req = http.get(`http://127.0.0.1:${FRONTEND_PORT}`, (res) => {
          if (res.statusCode === 200) resolve(true);
          else reject(new Error('Status ' + res.statusCode));
        });
        req.on('error', reject);
      });
      viteReady = true;
      break;
    } catch {}
  }

  if (!viteReady) {
    console.error('Failed to start Vite preview server');
    viteProc.kill();
    process.exit(1);
  }
  console.log('✓ Vite preview server is UP at http://127.0.0.1:' + FRONTEND_PORT);

  // 2. Launch Edge Headless with CDP
  console.log('2. Launching headless Edge with remote debugging port', DEBUG_PORT, '...');
  const tempUserData = fs.mkdtempSync(path.join(os.tmpdir(), 'edge-cdp-'));
  const edgeProc = spawn(
    EDGE_PATH,
    [
      '--headless=new',
      `--remote-debugging-port=${DEBUG_PORT}`,
      `--user-data-dir=${tempUserData}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-gpu',
      'about:blank',
    ],
    { stdio: 'ignore' }
  );

  let versionInfo = null;
  for (let i = 0; i < 20; i++) {
    await wait(500);
    try {
      versionInfo = await fetchJson(`http://127.0.0.1:${DEBUG_PORT}/json/version`);
      if (versionInfo && versionInfo.webSocketDebuggerUrl) break;
    } catch {}
  }

  if (!versionInfo || !versionInfo.webSocketDebuggerUrl) {
    console.error('Failed to connect to Edge CDP');
    edgeProc.kill();
    viteProc.kill();
    process.exit(1);
  }
  console.log('✓ Edge CDP connected:', versionInfo.Browser);

  // Connect to the default page target from /json/list
  const targets = await fetchJson(`http://127.0.0.1:${DEBUG_PORT}/json/list`);
  const pageTarget = targets.find((t) => t.type === 'page') || targets[0];
  if (!pageTarget || !pageTarget.webSocketDebuggerUrl) {
    throw new Error('No page target found in Edge');
  }
  const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);

  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });

  let msgId = 1;
  const pending = new Map();
  ws.onmessage = (evt) => {
    const res = JSON.parse(evt.data);
    if (res.id && pending.has(res.id)) {
      pending.get(res.id)(res);
      pending.delete(res.id);
    }
  };

  function send(method, params = {}) {
    return new Promise((resolve) => {
      const id = msgId++;
      pending.set(id, resolve);
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  await send('Page.enable');
  await send('DOM.enable');
  await send('Runtime.enable');

  // 3. Overflow Measurements at 390, 768, 1280, 1920
  console.log('\n3. Measuring document.documentElement.scrollWidth vs clientWidth...');
  console.log('   (Note: body overflow-x: hidden has been removed; testing raw content geometry)\n');

  const widths = [390, 768, 1280, 1920];
  const overflowResults = [];

  for (const w of widths) {
    await send('Emulation.setDeviceMetricsOverride', {
      width: w,
      height: 900,
      deviceScaleFactor: 1,
      mobile: w < 768,
    });
    await send('Page.navigate', { url: `http://127.0.0.1:${FRONTEND_PORT}` });
    await wait(1200);

    const evalRes = await send('Runtime.evaluate', {
      expression: `({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        bodyScrollWidth: document.body.scrollWidth,
        bodyClientWidth: document.body.clientWidth
      })`,
      returnByValue: true,
    });

    const val = evalRes?.result?.result?.value || evalRes?.result?.value;
    if (!val) {
      console.error('evalRes:', JSON.stringify(evalRes));
      throw new Error('Failed to evaluate scroll metrics');
    }
    const delta = val.scrollWidth - val.clientWidth;
    overflowResults.push({
      'Viewport Width (px)': w,
      'documentElement.clientWidth': val.clientWidth,
      'documentElement.scrollWidth': val.scrollWidth,
      'Sideways Delta': delta + ' px',
      'Result': delta === 0 ? 'CLEAN (0px overflow)' : `OVERFLOW (${delta}px)`,
    });
  }

  console.table(overflowResults);

  // 4. Capture Screenshots of #top, #problem, #pipeline, #verify (passport state), #ladder at 390 and 1280
  console.log('\n4. Capturing screenshots for required sections at 390 and 1280 into docs/screens/...\n');
  const captureWidths = [390, 1280];

  for (const w of captureWidths) {
    console.log(`>>> Capturing for width ${w}px...`);
    await send('Emulation.setDeviceMetricsOverride', {
      width: w,
      height: 900,
      deviceScaleFactor: 1,
      mobile: w < 768,
    });
    await send('Page.navigate', { url: `http://127.0.0.1:${FRONTEND_PORT}` });
    await wait(1200);

    const sections = ['#top', '#problem', '#pipeline', '#ladder'];
    for (const secId of sections) {
      await send('Runtime.evaluate', {
        expression: `document.querySelector('${secId}')?.scrollIntoView({ behavior: 'instant', block: 'start' });`,
      });
      await wait(600);

      const shot = await send('Page.captureScreenshot', { format: 'png' });
      const filename = `${w}_${secId.replace('#', '')}.png`;
      const outPath = path.join(screensDir, filename);
      fs.writeFileSync(outPath, Buffer.from(shot.result.data, 'base64'));
      console.log(`  ✓ Saved ${filename} (${(fs.statSync(outPath).size / 1024).toFixed(1)} KB)`);
    }

    // Capture #verify in PASSPORT state
    // Scroll to #verify and trigger a demo card
    await send('Runtime.evaluate', {
      expression: `
        document.querySelector('#verify')?.scrollIntoView({ behavior: 'instant', block: 'start' });
        // Click the first demo button (Original) or second demo button (Modified)
        const demoBtns = document.querySelectorAll('#verify button');
        for (const b of demoBtns) {
          if (b.textContent && (b.textContent.includes('Original') || b.textContent.includes('MODIFIED'))) {
            b.click();
            break;
          }
        }
      `,
    });
    await wait(800);

    const shotPassport = await send('Page.captureScreenshot', { format: 'png' });
    const passFilename = `${w}_verify_passport.png`;
    const passPath = path.join(screensDir, passFilename);
    fs.writeFileSync(passPath, Buffer.from(shotPassport.result.data, 'base64'));
    console.log(`  ✓ Saved ${passFilename} (${(fs.statSync(passPath).size / 1024).toFixed(1)} KB)`);
  }

  // Cleanup
  ws.close();
  edgeProc.kill();
  viteProc.kill();
  try {
    fs.rmSync(tempUserData, { recursive: true, force: true });
  } catch {}

  console.log('\n✓ Overflow verification and screenshot capture complete!\n');
}

main().catch((err) => {
  console.error('Error during execution:', err);
  process.exit(1);
});
