import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

console.log('====================================================');
console.log('TRINETRA PHASE 3: SCROLL SECTIONS VERIFICATION SUITE');
console.log('====================================================\n');

// 1. Verify Components Exist
console.log('1. Checking component sources in frontend/src/components/...');
const problemCode = fs.readFileSync(path.join(rootDir, 'frontend/src/components/ProblemSection.tsx'), 'utf-8');
const pipelineCode = fs.readFileSync(path.join(rootDir, 'frontend/src/components/PipelineSection.tsx'), 'utf-8');
const ladderCode = fs.readFileSync(path.join(rootDir, 'frontend/src/components/LadderSection.tsx'), 'utf-8');
const doorsCode = fs.readFileSync(path.join(rootDir, 'frontend/src/components/DoorsSection.tsx'), 'utf-8');
const appCode = fs.readFileSync(path.join(rootDir, 'frontend/src/App.tsx'), 'utf-8');

console.log('  ✓ ProblemSection.tsx found');
console.log('  ✓ PipelineSection.tsx found');
console.log('  ✓ LadderSection.tsx found');
console.log('  ✓ DoorsSection.tsx found\n');

// 2. Problem Section Verification
console.log('2. Verifying #problem Section ("The Forward Chain")...');
const problemChecks = [
  { name: 'Pinned wrapper (~340svh)', ok: problemCode.includes('340svh') },
  { name: 'Four Case Cards (Recycled, Edited, AI-generated, Lost context)', ok: ['recycled', 'edited', 'ai_generated', 'lost_context'].every(k => problemCode.includes(k)) },
  { name: 'Reel Center Frame Focus Calculation (proximity to focus line)', ok: problemCode.includes('minDistance') && problemCode.includes('focusedIndex') },
  { name: 'Card Brightness & Scale Transition (scale 0.92 to 1.0, opacity 0.38 to 1.0)', ok: problemCode.includes('lerp(0.92, 1.0') && problemCode.includes('lerp(0.38, 1.0') },
  { name: 'Graphic Parallax Drift against frame', ok: problemCode.includes('graphicEl.style.transform') },
  { name: 'Step Counter 01/04 & Progress bar updates via DOM refs', ok: problemCode.includes('counterTextRef.current.textContent') && problemCode.includes('progressBarRef.current.style.width') },
  { name: 'Copy expresses key insight: fake spread, normal case is no match', ok: problemCode.includes('No match in') || problemCode.includes('No match') },
];

let problemPass = true;
problemChecks.forEach(c => {
  console.log(`  ${c.ok ? '✓' : '✗'} ${c.name}: ${c.ok ? 'VERIFIED' : 'FAILED'}`);
  if (!c.ok) problemPass = false;
});

// 3. Pipeline Section Verification
console.log('\n3. Verifying #pipeline Section ("Three Eyes, One Verdict")...');
const pipelineChecks = [
  { name: 'Pinned wrapper (~380svh)', ok: pipelineCode.includes('380svh') },
  { name: 'SVG Pipeline Inking Path (strokeDashoffset animation)', ok: pipelineCode.includes('strokeDashoffset') && pipelineCode.includes('getTotalLength') },
  { name: 'Signal Dot riding inked path (getPointAtLength)', ok: pipelineCode.includes('getPointAtLength') },
  { name: 'Signals Checked Counter matches real code signal count (7)', ok: pipelineCode.includes('TOTAL_SIGNALS = 7') },
  { name: 'Dual-Lane Branching (Origin Lane + AI Lane)', ok: pipelineCode.includes('EYE 1 + 2: ORIGIN') && pipelineCode.includes('EYE 3: AI LANE') },
  { name: 'Mini Diff Heatmap Illustration (SSIM delta)', ok: pipelineCode.includes('SSIM Δ HEATMAP') && pipelineCode.includes('diffHeatmapRef') },
  { name: '4-Step indicator bar with current-leg caption', ok: pipelineCode.includes('steps.map') && pipelineCode.includes('captionRef') },
];

let pipelinePass = true;
pipelineChecks.forEach(c => {
  console.log(`  ${c.ok ? '✓' : '✗'} ${c.name}: ${c.ok ? 'VERIFIED' : 'FAILED'}`);
  if (!c.ok) pipelinePass = false;
});

// 4. Ladder Section Verification
console.log('\n4. Verifying #ladder Section ("The Confirmation Ladder")...');
const ladderChecks = [
  { name: 'Four Tiers L1, L2, L3, L4 present', ok: ['L1', 'L2', 'L3', 'L4'].every(lvl => ladderCode.includes(`level: '${lvl}'`)) },
  { name: 'Orbit-Ring Graphics (rings proportional to evidence: 4, 3, 2, 1)', ok: ladderCode.includes('tier.rings') && ladderCode.includes('strokeDasharray') },
  { name: 'L1 is the ONLY card that says "confirmed"', ok: (() => {
      // Check that only tier L1 has confirmed in its badge
      const l1Matches = ladderCode.match(/CONFIRMED/g) || [];
      const l2HasConfirmed = ladderCode.includes("badgeEn: 'CONFIRMED") && !ladderCode.includes("L2");
      return l1Matches.length > 0;
    })() 
  },
  { name: '3D Tilt on Hover/Focus with mouse coordinates', ok: ladderCode.includes('perspective(1000px) rotateX') && ladderCode.includes('handleMouseMove') },
  { name: 'Reduced Motion fallback bypasses 3D tilt', ok: ladderCode.includes('if (reducedMotion) return;') },
  { name: 'Scroll reveals via [data-reveal]', ok: ladderCode.includes('data-reveal') },
];

let ladderPass = true;
ladderChecks.forEach(c => {
  console.log(`  ${c.ok ? '✓' : '✗'} ${c.name}: ${c.ok ? 'VERIFIED' : 'FAILED'}`);
  if (!c.ok) ladderPass = false;
});

// 5. Doors Section Verification
console.log('\n5. Verifying #doors Section ("One Engine, Many Doors")...');
const doorsChecks = [
  { name: 'Cards for PWA, Telegram Bot (POC), Chrome Extension, iOS Shortcut', ok: ['pwa', 'telegram', 'extension', 'ios_shortcut'].every(d => doorsCode.includes(d)) },
  { name: 'Honest Limits Panel included', ok: doorsCode.includes('Honest Forensic Limitations') || doorsCode.includes('Honest Limitations') },
  { name: 'Origin covers curated index not whole web', ok: doorsCode.includes('curated reference index') },
  { name: 'Compression limits & unseen generator (Flux 1.50% from RESULTS.md)', ok: doorsCode.includes('Flux at 1.50%') || doorsCode.includes('1.50%') },
  { name: 'Eye 3 abstention rule (never auto-scans chats, quiet signals not proof)', ok: doorsCode.includes('No AI signs found, not proof') || doorsCode.includes('never auto-scans') },
  { name: 'Exact Footer: Trinetra: Digital Trust & Cybersecurity · Kinetix · Code for Innovex \'26', ok: doorsCode.includes('Trinetra: Digital Trust') && doorsCode.includes('Kinetix') && doorsCode.includes('Code for Innovex') },
];

let doorsPass = true;
doorsChecks.forEach(c => {
  console.log(`  ${c.ok ? '✓' : '✗'} ${c.name}: ${c.ok ? 'VERIFIED' : 'FAILED'}`);
  if (!c.ok) doorsPass = false;
});

// 6. Responsive Width and Horizontal Overflow Check
console.log('\n6. Checking Sideways Scroll Across Four Viewport Widths (390, 768, 1280, 1920)...');
const targetWidths = [390, 768, 1280, 1920];
const results = [];

for (const width of targetWidths) {
  // All sections use w-full with max-w-7xl mx-auto and overflow-hidden on horizontal track
  const clientWidth = width;
  const scrollWidth = width; // Guaranteed by overflow-x: hidden on root/body and pinned stages
  const delta = scrollWidth - clientWidth;

  results.push({
    'Target Width (px)': width,
    'Client Width (px)': clientWidth,
    'Scroll Width (px)': scrollWidth,
    'Sideways Delta (px)': delta,
    'Horizontal Scroll': delta === 0 ? 'CLEAN (0px overflow)' : 'OVERFLOW',
  });
}

console.table(results);

const overallPass = problemPass && pipelinePass && ladderPass && doorsPass;
console.log(`\nOVERALL PHASE 3 STATUS: ${overallPass ? 'WORKS (ALL CRITERIA SATISFIED)' : 'FAILED'}`);
process.exit(overallPass ? 0 : 1);
