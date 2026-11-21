import http from 'http';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distDir = path.resolve(__dirname, '../frontend/dist');

// Simple static server for frontend/dist
const server = http.createServer((req, res) => {
  let filePath = path.join(distDir, req.url === '/' ? 'index.html' : req.url);
  if (!fs.existsSync(filePath)) {
    filePath = path.join(distDir, 'index.html');
  }
  const ext = path.extname(filePath);
  const contentTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
  };
  const contentType = contentTypes[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(data);
    }
  });
});

await new Promise((resolve) => server.listen(4173, resolve));
console.log('Static server listening at http://localhost:4173');

import os from 'os';

const tmpUserDataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'edge-user-data-'));

const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const edgeProcess = spawn(edgePath, [
  '--headless=new',
  '--remote-debugging-port=9222',
  '--disable-gpu',
  '--no-sandbox',
  `--user-data-dir=${tmpUserDataDir}`,
  'http://localhost:4173',
]);

// Wait for CDP to be available
let wsUrl = null;
for (let i = 0; i < 30; i++) {
  await new Promise((r) => setTimeout(r, 300));
  try {
    const res = await fetch('http://127.0.0.1:9222/json');
    const data = await res.json();
    const page = data.find((item) => item.type === 'page' && item.webSocketDebuggerUrl);
    if (page) {
      wsUrl = page.webSocketDebuggerUrl;
      break;
    }
  } catch (e) {
    // waiting
  }
}

if (!wsUrl) {
  console.error('Failed to get WebSocket debugger URL from Edge');
  edgeProcess.kill();
  server.close();
  process.exit(1);
}

const ws = new WebSocket(wsUrl);
await new Promise((resolve, reject) => {
  ws.onopen = resolve;
  ws.onerror = reject;
});

let msgId = 1;
function sendCdp(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = msgId++;
    const handler = (evt) => {
      const resp = JSON.parse(evt.data);
      if (resp.id === id) {
        ws.removeEventListener('message', handler);
        if (resp.error) reject(resp.error);
        else resolve(resp.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

// Enable Page & Runtime
await sendCdp('Page.enable');
await sendCdp('Runtime.enable');

// Wait for page load
await new Promise((r) => setTimeout(r, 1000));

const testWidths = [390, 768, 1280, 1920];
const results = [];

for (const width of testWidths) {
  await sendCdp('Emulation.setDeviceMetricsOverride', {
    width,
    height: 900,
    deviceScaleFactor: 1,
    mobile: width < 768,
  });

  await new Promise((r) => setTimeout(r, 400));

  const evalRes = await sendCdp('Runtime.evaluate', {
    expression: `(() => {
      const cw = document.documentElement.clientWidth;
      const sw = document.documentElement.scrollWidth;
      const bw = document.body.scrollWidth;
      const maxScroll = Math.max(sw, bw);
      return {
        viewportWidth: window.innerWidth,
        clientWidth: cw,
        scrollWidth: maxScroll,
        overflow: maxScroll > cw,
        delta: maxScroll - cw
      };
    })()`,
    returnByValue: true,
  });

  results.push({
    testWidth: width,
    ...evalRes.result.value,
  });
}

console.log('\n--- VIEWPORT OVERFLOW CHECK RESULTS ---');
console.table(results);

const hasAnyOverflow = results.some((r) => r.overflow);
console.log(`Sideways scroll check: ${hasAnyOverflow ? 'FAILED (overflow detected)' : 'PASSED (no horizontal scroll)'}\n`);

// Also verify sequence metrics
const heroCheck = await sendCdp('Runtime.evaluate', {
  expression: `(() => {
    const hero = document.getElementById('top');
    const title = document.querySelector('h1');
    const hud = document.querySelector('[class*="border-b"]');
    return {
      heroFound: !!hero,
      heroHeight: hero ? hero.clientHeight : 0,
      titleText: title ? title.textContent : null,
      hudFound: !!hud
    };
  })()`,
  returnByValue: true,
});
console.log('Hero DOM Inspection:', heroCheck.result.value);

ws.close();
edgeProcess.kill();
server.close();
process.exit(hasAnyOverflow ? 1 : 0);
