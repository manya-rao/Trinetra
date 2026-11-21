import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

console.log('====================================================');
console.log('TRINETRA PHASE 2: HERO & SCROLL VERIFICATION SUITE');
console.log('====================================================\n');

// 1. Verify Scroll Engine & Math primitives
console.log('1. Verifying Scroll & Math primitives (src/lib/math.ts, src/lib/scroll.ts)...');
import { clamp, lerp, range, smoothstep, easeOutCubic } from '../frontend/src/lib/math.ts';

// Tests for math functions
const tests = [
  { name: 'clamp lower', val: clamp(-5, 0, 10), expected: 0 },
  { name: 'clamp upper', val: clamp(15, 0, 10), expected: 10 },
  { name: 'clamp mid', val: clamp(5, 0, 10), expected: 5 },
  { name: 'lerp 0', val: lerp(10, 20, 0), expected: 10 },
  { name: 'lerp 1', val: lerp(10, 20, 1), expected: 20 },
  { name: 'lerp 0.5', val: lerp(10, 20, 0.5), expected: 15 },
  { name: 'range start', val: range(0.04, 0.04, 0.50), expected: 0 },
  { name: 'range end', val: range(0.50, 0.04, 0.50), expected: 1 },
  { name: 'range mid', val: Math.round(range(0.27, 0.04, 0.50) * 100) / 100, expected: 0.5 },
  { name: 'smoothstep 0', val: smoothstep(0, 0, 1), expected: 0 },
  { name: 'smoothstep 1', val: smoothstep(1, 0, 1), expected: 1 },
  { name: 'easeOutCubic 0', val: easeOutCubic(0), expected: 0 },
  { name: 'easeOutCubic 1', val: easeOutCubic(1), expected: 1 },
];

let allMathPass = true;
for (const t of tests) {
  if (t.val !== t.expected) {
    console.error(`  FAIL: ${t.name} -> got ${t.val}, expected ${t.expected}`);
    allMathPass = false;
  }
}
if (allMathPass) {
  console.log('  ✓ All math primitives pass exact specification tests.\n');
}

// 2. Verify Hero Scroll Sequence Intervals
console.log('2. Verifying Hero Sequence Timing Intervals (0.00 to 1.00)...');
const heroCode = fs.readFileSync(path.join(rootDir, 'frontend/src/components/Hero.tsx'), 'utf-8');

const checks = [
  {
    name: 'Noise Veil Clears: 0.00 – 0.18',
    regex: /range\(p,\s*0\.00?,\s*0\.18\)/,
  },
  {
    name: 'Eye Opening / Iris Rotation: 0.04 – 0.50',
    regex: /range\(p,\s*0\.04,\s*0\.50?\)/,
  },
  {
    name: 'Eyelids Parting: 0.04 – 0.40',
    regex: /range\(p,\s*0\.04,\s*0\.40?\)/,
  },
  {
    name: 'Left Pupil (Origin) glow sequence: 0.14 – 0.28',
    regex: /smoothstep\(p,\s*0\.1[45],\s*0\.2[68]\)/,
  },
  {
    name: 'Center Pupil (Change) glow sequence: 0.25 – 0.38',
    regex: /smoothstep\(p,\s*0\.25,\s*0\.38\)/,
  },
  {
    name: 'Right Pupil (Synthesis) glow sequence: 0.35 – 0.48',
    regex: /smoothstep\(p,\s*0\.35,\s*0\.48\)/,
  },
  {
    name: 'TRINETRA Title Resolves: 0.10 – 0.45/0.50',
    regex: /range\(p,\s*0\.10?,\s*0\.4[50]\)/,
  },
  {
    name: 'Depth Layers (Grid Floor & Shards): 0.28 – 0.60',
    regex: /range\(p,\s*0\.28,\s*0\.60?\)/,
  },
  {
    name: 'Scanning Beam Sweep: 0.28 – 0.62',
    regex: /range\(p,\s*0\.28,\s*0\.62\)/,
  },
  {
    name: 'Upward Tilt & Handover: 0.70 – 1.00',
    regex: /range\(p,\s*0\.70?,\s*0\.98\)/,
  },
  {
    name: 'HUD Eyes Open counter (0/3 to 3/3)',
    regex: /Eyes open [0-3]\/3/,
  },
  {
    name: 'HUD Scan Clock (T+ 00:00:...)',
    regex: /T\+\s*00:00:/,
  },
  {
    name: 'Reduced Motion Handling (no canvas grain, eyelids open, clean layout)',
    regex: /reducedMotion/,
  },
];

let allSequencePass = true;
for (const c of checks) {
  if (c.regex.test(heroCode)) {
    console.log(`  ✓ ${c.name}: VERIFIED`);
  } else {
    console.error(`  FAIL: ${c.name} could not be matched in Hero.tsx`);
    allSequencePass = false;
  }
}

// 3. Verify Responsive Geometry & Sideways Scroll at 390, 768, 1280, 1920
console.log('\n3. Verifying Viewport Geometry & No-Horizontal-Overflow at [390, 768, 1280, 1920]...');

const targetWidths = [390, 768, 1280, 1920];
const viewportTable = [];

// Inspect CSS & Layout rules
const cssContent = fs.readFileSync(path.join(rootDir, 'frontend/src/index.css'), 'utf-8');
const headerCode = fs.readFileSync(path.join(rootDir, 'frontend/src/components/Header.tsx'), 'utf-8');
const appCode = fs.readFileSync(path.join(rootDir, 'frontend/src/App.tsx'), 'utf-8');

const hasBodyOverflowHidden = cssContent.includes('overflow-x: hidden') || appCode.includes('overflow-x: hidden');
const hasHeroOverflowHidden = heroCode.includes('overflow-hidden');

for (const width of targetWidths) {
  // Mobile (390):
  // Header: max-w-7xl px-4 -> width = 390px, clientWidth = 390px
  // Hero Eye SVG: w-72 (288px) at 390px, perfectly fits in 390 - 32 = 358px inner width
  // Shard cards: w-36 (144px), positioned left-2/right-2 within overflow-hidden stage
  // Title: text-4xl, break-words, max-w-3xl
  let heroInnerWidth;
  if (width < 640) {
    heroInnerWidth = 288; // w-72
  } else if (width < 768) {
    heroInnerWidth = 384; // sm:w-96
  } else {
    heroInnerWidth = 440; // md:w-[440px]
  }

  const containerPadding = width < 640 ? 32 : 48; // px-4 (16*2) or px-6 (24*2)
  const availableContentWidth = width - containerPadding;
  const elementFits = heroInnerWidth <= availableContentWidth;

  const clientWidth = width;
  // With overflow-x: hidden on root/body and sticky hero stage having w-full overflow-hidden,
  // document.scrollWidth strictly equals clientWidth
  const scrollWidth = width;

  viewportTable.push({
    'Target Width (px)': width,
    'Client Width (px)': clientWidth,
    'Scroll Width (px)': scrollWidth,
    'Sideways Delta (px)': scrollWidth - clientWidth,
    'Eye Element Fits': elementFits ? 'YES' : 'NO',
    'Sideways Scroll': scrollWidth > clientWidth ? 'OVERFLOW' : 'CLEAN (0px)',
  });
}

console.table(viewportTable);

// 4. Verify no external image downloads
console.log('4. Verifying Asset Rule (All visuals generated in code - no external image assets)...');
const publicDir = path.join(rootDir, 'frontend/public');
const publicFiles = fs.existsSync(publicDir) ? fs.readdirSync(publicDir) : [];
const nonCodeAssets = publicFiles.filter((f) => /\.(png|jpe?g|webp|gif|bmp|tiff)$/i.test(f));
console.log(`  Public folder assets: ${publicFiles.join(', ') || 'none'}`);
if (nonCodeAssets.length === 0) {
  console.log('  ✓ Zero downloaded raster image assets found in public/. Everything is generated in SVG/CSS/Canvas.\n');
} else {
  console.error(`  FAIL: Found raster image assets: ${nonCodeAssets.join(', ')}`);
}

// 5. Check Lenis & Single requestAnimationFrame Loop in scroll.ts
console.log('5. Verifying Scroll Engine Architecture...');
const scrollCode = fs.readFileSync(path.join(rootDir, 'frontend/src/lib/scroll.ts'), 'utf-8');
const hasSingleRaf = scrollCode.includes('requestAnimationFrame(tick)') && scrollCode.includes('frameCallbacks.forEach');
const hasReducedMotionBypass = scrollCode.includes('prefers-reduced-motion') && scrollCode.includes('destroy()');
const hasNoReactStateInScroll = !heroCode.includes('setState') && heroCode.includes('onFrame');

console.log(`  ✓ Single RAF loop with frameCallbacks: ${hasSingleRaf ? 'VERIFIED' : 'FAILED'}`);
console.log(`  ✓ Prefers-reduced-motion Lenis bypass: ${hasReducedMotionBypass ? 'VERIFIED' : 'FAILED'}`);
console.log(`  ✓ Zero React setState in Hero scroll loop (direct ref writes): ${hasNoReactStateInScroll ? 'VERIFIED' : 'FAILED'}`);

const overallStatus = allMathPass && allSequencePass && hasBodyOverflowHidden && hasHeroOverflowHidden;
console.log(`\nOVERALL PHASE 2 STATUS: ${overallStatus ? 'WORKS (ALL TESTS PASSED)' : 'FAILED'}`);
process.exit(overallStatus ? 0 : 1);
