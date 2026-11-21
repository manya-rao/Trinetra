import React, { useEffect, useRef } from 'react';
import { onFrame, scrollToHash } from '../lib/scroll';
import { pinProgress, range, lerp, smoothstep, easeOutCubic } from '../lib/math';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface HeroProps {
  lang: 'en' | 'hi';
}

export const Hero: React.FC<HeroProps> = ({ lang }) => {
  const sectionRef = useRef<HTMLElement | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const veilRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const titleContainerRef = useRef<HTMLDivElement | null>(null);
  const eyeLidUpperRef = useRef<SVGPathElement | null>(null);
  const eyeLidLowerRef = useRef<SVGPathElement | null>(null);
  const irisRingsRef = useRef<SVGGElement | null>(null);
  const pupilLeftRef = useRef<SVGCircleElement | null>(null);
  const pupilCenterRef = useRef<SVGCircleElement | null>(null);
  const pupilRightRef = useRef<SVGCircleElement | null>(null);
  const shardsContainerRef = useRef<HTMLDivElement | null>(null);
  const gridFloorRef = useRef<HTMLDivElement | null>(null);
  const scanBeamRef = useRef<HTMLDivElement | null>(null);
  const hudClockRef = useRef<HTMLSpanElement | null>(null);
  const hudEyesRef = useRef<HTMLSpanElement | null>(null);
  const hudScrollHintRef = useRef<HTMLDivElement | null>(null);

  const reducedMotion = useReducedMotion();

  // Noise Canvas setup
  useEffect(() => {
    if (reducedMotion) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let width = 0;
    let height = 0;

    const handleResize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = canvas.parentElement?.clientWidth || window.innerWidth;
      height = canvas.parentElement?.clientHeight || window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.scale(dpr, dpr);
    };

    handleResize();
    const ro = new ResizeObserver(handleResize);
    ro.observe(canvas.parentElement || document.body);

    let lastNoiseTime = 0;
    const renderNoise = (t: number) => {
      // Throttle noise generation to ~24fps to keep CPU usage low
      if (t - lastNoiseTime > 40 && canvas.width > 0 && canvas.height > 0) {
        lastNoiseTime = t;
        const w = Math.min(width, 400);
        const h = Math.min(height, 300);
        const imgData = ctx.createImageData(w, h);
        const buffer = new Uint32Array(imgData.data.buffer);
        const len = buffer.length;
        for (let i = 0; i < len; i++) {
          if (Math.random() < 0.12) {
            // Monochromatic grain with occasional teal pixel
            const isTeal = Math.random() < 0.08;
            buffer[i] = isTeal ? 0xffc5d319 : (Math.random() < 0.5 ? 0x66ffffff : 0x33000000);
          } else {
            buffer[i] = 0x00000000;
          }
        }
        ctx.clearRect(0, 0, width, height);
        // Draw scaled
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = w;
        tempCanvas.height = h;
        const tempCtx = tempCanvas.getContext('2d');
        if (tempCtx) {
          tempCtx.putImageData(imgData, 0, 0);
          ctx.drawImage(tempCanvas, 0, 0, width, height);
        }
      }
      animId = requestAnimationFrame(renderNoise);
    };

    animId = requestAnimationFrame(renderNoise);

    return () => {
      cancelAnimationFrame(animId);
      ro.disconnect();
    };
  }, [reducedMotion]);

  // Frame Loop subscription (writing directly to DOM refs, NO React state updates)
  useEffect(() => {
    if (reducedMotion) return;

    let startTime = performance.now();

    const unsubscribe = onFrame((time) => {
      if (!sectionRef.current) return;
      const { p, inView } = pinProgress(sectionRef.current);
      if (!inView) return;

      // Update HUD Scan Clock: T+ 00:00:SS.m
      if (hudClockRef.current) {
        const elapsed = Math.floor((time - startTime) / 100);
        const secs = Math.floor(elapsed / 10) % 60;
        const tenths = elapsed % 10;
        const secsStr = secs < 10 ? `0${secs}` : `${secs}`;
        hudClockRef.current.textContent = `T+ 00:00:${secsStr}.${tenths}`;
      }

      // 1. Noise Veil: 0.00 – 0.18
      const veilOpacity = 1 - range(p, 0.00, 0.18);
      if (veilRef.current) {
        veilRef.current.style.opacity = veilOpacity.toFixed(3);
        veilRef.current.style.pointerEvents = veilOpacity > 0.05 ? 'auto' : 'none';
        veilRef.current.style.display = veilOpacity <= 0 ? 'none' : 'flex';
      }

      // 2. Eye Opening: 0.04 – 0.50
      // Iris rings rotation and 3D tilt
      const pEye = range(p, 0.04, 0.50);
      if (irisRingsRef.current) {
        const rot = pEye * 90;
        const tiltX = lerp(20, 0, easeOutCubic(pEye));
        irisRingsRef.current.style.transform = `rotateX(${tiltX.toFixed(2)}deg) rotate(${rot.toFixed(1)}deg)`;
      }

      // Eyelids parting (0.04 - 0.40)
      const pLids = easeOutCubic(range(p, 0.04, 0.40));
      if (eyeLidUpperRef.current) {
        // Move upper lid up by up to 90px
        eyeLidUpperRef.current.style.transform = `translateY(${(-pLids * 85).toFixed(1)}px)`;
      }
      if (eyeLidLowerRef.current) {
        // Move lower lid down by up to 90px
        eyeLidLowerRef.current.style.transform = `translateY(${(pLids * 85).toFixed(1)}px)`;
      }

      // Pupils glow in sequence
      // Left (Origin): 0.15 - 0.28
      const pLeft = smoothstep(p, 0.14, 0.26);
      if (pupilLeftRef.current) {
        pupilLeftRef.current.style.opacity = lerp(0.2, 1, pLeft).toFixed(2);
        pupilLeftRef.current.style.filter = `drop-shadow(0 0 ${lerp(0, 12, pLeft)}px #19D3C5)`;
      }

      // Center (Change): 0.25 - 0.38
      const pCenter = smoothstep(p, 0.25, 0.38);
      if (pupilCenterRef.current) {
        pupilCenterRef.current.style.opacity = lerp(0.2, 1, pCenter).toFixed(2);
        pupilCenterRef.current.style.filter = `drop-shadow(0 0 ${lerp(0, 16, pCenter)}px #19D3C5)`;
      }

      // Right (Synthesis): 0.35 - 0.48
      const pRight = smoothstep(p, 0.35, 0.48);
      if (pupilRightRef.current) {
        pupilRightRef.current.style.opacity = lerp(0.2, 1, pRight).toFixed(2);
        pupilRightRef.current.style.filter = `drop-shadow(0 0 ${lerp(0, 12, pRight)}px #19D3C5)`;
      }

      // HUD "Eyes open 1/3 .. 3/3"
      if (hudEyesRef.current) {
        if (p < 0.15) {
          hudEyesRef.current.textContent = 'Eyes open 0/3';
        } else if (p < 0.26) {
          hudEyesRef.current.textContent = 'Eyes open 1/3 (Origin)';
        } else if (p < 0.36) {
          hudEyesRef.current.textContent = 'Eyes open 2/3 (Change)';
        } else {
          hudEyesRef.current.textContent = 'Eyes open 3/3 (Synthesis)';
        }
      }

      // 3. TRINETRA Title resolves: 0.10 – 0.50
      const pTitle = range(p, 0.10, 0.45);
      if (titleContainerRef.current) {
        const spacing = lerp(0.5, 0.18, easeOutCubic(pTitle));
        const blur = lerp(10, 0, pTitle);
        const opacity = smoothstep(p, 0.10, 0.32);
        titleContainerRef.current.style.letterSpacing = `${spacing.toFixed(2)}em`;
        titleContainerRef.current.style.filter = `blur(${blur.toFixed(1)}px)`;
        titleContainerRef.current.style.opacity = opacity.toFixed(2);
      }

      // 4. Depth layers close in: 0.28 – 0.60
      const pDepth = range(p, 0.28, 0.60);
      if (gridFloorRef.current) {
        gridFloorRef.current.style.opacity = smoothstep(p, 0.26, 0.42).toFixed(2);
        gridFloorRef.current.style.transform = `perspective(800px) rotateX(70deg) translateY(${lerp(60, 0, pDepth).toFixed(1)}px)`;
      }

      // Drifting shards
      if (shardsContainerRef.current) {
        const shardOpacity = smoothstep(p, 0.28, 0.44);
        shardsContainerRef.current.style.opacity = shardOpacity.toFixed(2);
        const drift = lerp(40, -40, pDepth);
        shardsContainerRef.current.style.transform = `translateY(${drift.toFixed(1)}px)`;
      }

      // Scanning beam
      if (scanBeamRef.current) {
        const pBeam = range(p, 0.28, 0.62);
        if (pBeam > 0 && pBeam < 1) {
          scanBeamRef.current.style.opacity = smoothstep(pBeam, 0, 0.2).toFixed(2);
          scanBeamRef.current.style.transform = `translateY(${lerp(-50, 450, pBeam).toFixed(1)}px)`;
        } else {
          scanBeamRef.current.style.opacity = '0';
        }
      }

      // 5. Handover / Tilt away upward: 0.70 – 1.00
      const pExit = range(p, 0.70, 0.98);
      if (stageRef.current) {
        const rotX = lerp(0, 22, easeOutCubic(pExit));
        const translateY = -lerp(0, 140, easeOutCubic(pExit));
        const scale = lerp(1, 0.92, pExit);
        const opacity = 1 - smoothstep(p, 0.82, 0.98);
        stageRef.current.style.transform = `perspective(1200px) rotateX(${rotX.toFixed(2)}deg) translateY(${translateY.toFixed(1)}px) scale(${scale.toFixed(3)})`;
        stageRef.current.style.opacity = opacity.toFixed(3);
      }

      // Scroll hint fades out early
      if (hudScrollHintRef.current) {
        const hintOpacity = 1 - range(p, 0.05, 0.25);
        hudScrollHintRef.current.style.opacity = hintOpacity.toFixed(2);
      }
    });

    return () => unsubscribe();
  }, [reducedMotion]);

  return (
    <section
      id="top"
      ref={sectionRef}
      className="relative w-full h-[440svh] bg-void selection:bg-accent/20"
      aria-label="Trinetra Hero - Open the Eye"
    >
      {/* Sticky Stage Container */}
      <div className="sticky top-0 h-screen w-full overflow-hidden flex flex-col justify-between pt-16 pb-6 px-4 sm:px-6">
        {/* HUD Overlay - Top Bar */}
        <div className="relative z-40 max-w-7xl mx-auto w-full flex items-center justify-between text-xs font-mono text-muted/80 border-b border-surface/40 pb-2">
          {/* Top Left: Scan Clock */}
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-ping" />
            <span ref={hudClockRef}>T+ 00:00:00.0</span>
          </div>

          {/* Top Center: System Tag */}
          <div className="hidden sm:flex items-center gap-2 text-[11px] text-accent/80 tracking-widest uppercase">
            <span>[ SYSTEM: ACTIVE ]</span>
            <span>·</span>
            <span>PROVENANCE PASSPORT L1–L4</span>
          </div>

          {/* Top Right: Eyes Open Counter */}
          <div className="flex items-center gap-2">
            <span
              ref={hudEyesRef}
              className="text-accent/90 border border-surface px-2 py-0.5 rounded bg-void-2/60"
            >
              {reducedMotion ? 'Eyes open 3/3' : 'Eyes open 0/3'}
            </span>
          </div>
        </div>

        {/* 3D Perspective Stage */}
        <div
          ref={stageRef}
          className="relative flex-1 w-full max-w-6xl mx-auto flex flex-col items-center justify-center preserve-3d transition-transform duration-75"
          style={{ perspective: '1200px' }}
        >
          {/* 3D Perspective Grid Floor */}
          <div
            ref={gridFloorRef}
            className="absolute -bottom-24 w-full h-80 pointer-events-none opacity-0"
            style={{
              backgroundImage:
                'linear-gradient(to right, rgba(25, 211, 197, 0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(25, 211, 197, 0.08) 1px, transparent 1px)',
              backgroundSize: '40px 40px',
              maskImage: 'radial-gradient(ellipse at 50% 100%, black 30%, transparent 80%)',
              WebkitMaskImage: 'radial-gradient(ellipse at 50% 100%, black 30%, transparent 80%)',
            }}
          />

          {/* Scanning Beam (Sweeping line) */}
          <div
            ref={scanBeamRef}
            className="absolute left-0 right-0 h-1 pointer-events-none opacity-0 z-30"
            style={{
              background: 'linear-gradient(90deg, transparent, #19D3C5 50%, transparent)',
              boxShadow: '0 0 20px 2px #19D3C5',
            }}
          />

          {/* Central Eye Construct: Large SVG Iris + Eyelids + Three Eyes */}
          <div className="relative w-72 h-72 sm:w-96 sm:h-96 md:w-[440px] md:h-[440px] flex items-center justify-center">
            {/* SVG Eye Architecture */}
            <svg
              viewBox="0 0 500 500"
              className="w-full h-full overflow-visible"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <defs>
                <radialGradient id="irisGrad" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#19D3C5" stopOpacity="0.25" />
                  <stop offset="70%" stopColor="#0B1B3A" stopOpacity="0.6" />
                  <stop offset="100%" stopColor="#060D1F" stopOpacity="0" />
                </radialGradient>
                <filter id="tealGlow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="8" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Rotating Concentric Iris Rings */}
              <g ref={irisRingsRef} className="origin-center transition-transform">
                {/* Outer radar ticks */}
                <circle cx="250" cy="250" r="230" stroke="#19D3C5" strokeWidth="0.75" strokeOpacity="0.2" strokeDasharray="3 9" />
                <circle cx="250" cy="250" r="200" stroke="#19D3C5" strokeWidth="1" strokeOpacity="0.3" strokeDasharray="6 6" />
                <circle cx="250" cy="250" r="160" stroke="#19D3C5" strokeWidth="1.2" strokeOpacity="0.35" />
                <circle cx="250" cy="250" r="120" stroke="#19D3C5" strokeWidth="0.75" strokeOpacity="0.4" strokeDasharray="2 12" />
                <circle cx="250" cy="250" r="80" stroke="#19D3C5" strokeWidth="1" strokeOpacity="0.25" />

                {/* Aperture blades */}
                {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, i) => (
                  <line
                    key={i}
                    x1="250"
                    y1="250"
                    x2={250 + 200 * Math.cos((angle * Math.PI) / 180)}
                    y2={250 + 200 * Math.sin((angle * Math.PI) / 180)}
                    stroke="#19D3C5"
                    strokeWidth="0.5"
                    strokeOpacity="0.18"
                  />
                ))}

                {/* Iris Glow Fill */}
                <circle cx="250" cy="250" r="140" fill="url(#irisGrad)" />
              </g>

              {/* Connecting Triangulation lines between the Three Eyes */}
              <line x1="150" y1="270" x2="250" y2="190" stroke="#19D3C5" strokeWidth="1.5" strokeOpacity="0.6" strokeDasharray="4 4" />
              <line x1="250" y1="190" x2="350" y2="270" stroke="#19D3C5" strokeWidth="1.5" strokeOpacity="0.6" strokeDasharray="4 4" />
              <line x1="150" y1="270" x2="350" y2="270" stroke="#19D3C5" strokeWidth="1" strokeOpacity="0.4" strokeDasharray="2 4" />

              {/* EYE 1: Left (Origin) */}
              <g id="eye-origin">
                <circle cx="150" cy="270" r="32" stroke="#19D3C5" strokeWidth="1.5" strokeOpacity="0.7" fill="#0B1B3A" />
                <circle cx="150" cy="270" r="16" stroke="#19D3C5" strokeWidth="1" strokeOpacity="0.4" />
                <circle
                  ref={pupilLeftRef}
                  cx="150"
                  cy="270"
                  r="9"
                  fill="#19D3C5"
                  opacity={reducedMotion ? 1 : 0.2}
                />
                <text x="150" y="320" textAnchor="middle" fill="#A9B8D6" fontSize="11" fontFamily="IBM Plex Mono" letterSpacing="0.05em">
                  EYE 1 · ORIGIN
                </text>
              </g>

              {/* EYE 2: Centre (Change - larger & raised) */}
              <g id="eye-change">
                <path
                  d="M 190 190 Q 250 120 310 190 Q 250 260 190 190 Z"
                  stroke="#19D3C5"
                  strokeWidth="2"
                  strokeOpacity="0.9"
                  fill="#0B1B3A"
                />
                <circle cx="250" cy="190" r="26" stroke="#19D3C5" strokeWidth="1.2" strokeOpacity="0.5" />
                <circle
                  ref={pupilCenterRef}
                  cx="250"
                  cy="190"
                  r="13"
                  fill="#19D3C5"
                  opacity={reducedMotion ? 1 : 0.2}
                />
                <text x="250" y="145" textAnchor="middle" fill="#19D3C5" fontSize="12" fontWeight="600" fontFamily="IBM Plex Mono" letterSpacing="0.08em">
                  EYE 2 · CHANGE
                </text>
              </g>

              {/* EYE 3: Right (Synthesis) */}
              <g id="eye-synthesis">
                <circle cx="350" cy="270" r="32" stroke="#19D3C5" strokeWidth="1.5" strokeOpacity="0.7" fill="#0B1B3A" />
                <circle cx="350" cy="270" r="16" stroke="#19D3C5" strokeWidth="1" strokeOpacity="0.4" />
                <circle
                  ref={pupilRightRef}
                  cx="350"
                  cy="270"
                  r="9"
                  fill="#19D3C5"
                  opacity={reducedMotion ? 1 : 0.2}
                />
                <text x="350" y="320" textAnchor="middle" fill="#A9B8D6" fontSize="11" fontFamily="IBM Plex Mono" letterSpacing="0.05em">
                  EYE 3 · SYNTHESIS
                </text>
              </g>

              {/* Eyelids (Parting mechanism) */}
              {!reducedMotion && (
                <>
                  {/* Upper Eyelid */}
                  <path
                    ref={eyeLidUpperRef}
                    d="M 60 250 C 140 100 360 100 440 250 C 380 180 120 180 60 250 Z"
                    fill="#060D1F"
                    stroke="#19D3C5"
                    strokeWidth="1.5"
                    strokeOpacity="0.6"
                    className="transition-transform"
                  />
                  {/* Lower Eyelid */}
                  <path
                    ref={eyeLidLowerRef}
                    d="M 60 250 C 140 400 360 400 440 250 C 380 320 120 320 60 250 Z"
                    fill="#060D1F"
                    stroke="#19D3C5"
                    strokeWidth="1.5"
                    strokeOpacity="0.6"
                    className="transition-transform"
                  />
                </>
              )}
            </svg>
          </div>

          {/* Drifting Shard Cards (0.28 – 0.60 depth layers) */}
          <div
            ref={shardsContainerRef}
            className="absolute inset-0 pointer-events-none opacity-0 flex items-center justify-center"
          >
            {/* Shard 1: Recycled Copy */}
            <div
              className="absolute left-2 sm:left-8 top-1/4 w-36 sm:w-44 p-3 rounded-lg border border-surface bg-void-2/90 backdrop-blur-md shadow-2xl"
              style={{
                transform: 'rotateY(16deg) rotateX(-8deg) translateZ(40px)',
              }}
            >
              <div className="flex items-center justify-between border-b border-surface/80 pb-1.5 mb-2 text-[10px] font-mono text-muted">
                <span>SHARD // 01</span>
                <span className="text-accent">ORIGIN</span>
              </div>
              <div className="h-16 rounded bg-void flex items-center justify-center p-1.5 overflow-hidden">
                <svg viewBox="0 0 100 50" className="w-full h-full stroke-accent/70" fill="none">
                  <path d="M5 25 Q 25 5 50 25 T 95 25" strokeWidth="1.5" />
                  <path d="M5 32 Q 25 12 50 32 T 95 32" strokeWidth="1" strokeDasharray="2 2" strokeOpacity="0.5" />
                </svg>
              </div>
              <p className="mt-2 text-[11px] font-mono text-text">Recycled image</p>
              <p className="text-[9px] text-muted font-sans">Matched to index original</p>
            </div>

            {/* Shard 2: Edited Patch */}
            <div
              className="absolute right-2 sm:right-8 top-1/3 w-36 sm:w-44 p-3 rounded-lg border border-amber-500/40 bg-void-2/90 backdrop-blur-md shadow-2xl"
              style={{
                transform: 'rotateY(-18deg) rotateX(12deg) translateZ(70px)',
              }}
            >
              <div className="flex items-center justify-between border-b border-surface/80 pb-1.5 mb-2 text-[10px] font-mono text-muted">
                <span>SHARD // 02</span>
                <span className="text-amber-400">CHANGE</span>
              </div>
              <div className="h-16 rounded bg-void flex items-center justify-center p-1.5 relative overflow-hidden">
                <div className="absolute inset-2 border border-dashed border-amber-400/60 rounded bg-amber-500/10 flex items-center justify-center">
                  <span className="text-[9px] font-mono text-amber-300">SSIM DIFF</span>
                </div>
              </div>
              <p className="mt-2 text-[11px] font-mono text-text">Spliced region</p>
              <p className="text-[9px] text-muted font-sans">Local pixel delta heatmap</p>
            </div>

            {/* Shard 3: Synthetic Grain — centred horizontally to avoid overlap at all widths */}
            <div
              className="absolute bottom-4 sm:bottom-10 w-40 sm:w-48 p-3 rounded-lg border border-orange-500/40 bg-void-2/90 backdrop-blur-md shadow-2xl"
              style={{
                left: '50%',
                transform: 'translateX(-50%) rotateY(8deg) rotateX(-16deg) translateZ(50px)',
              }}
            >
              <div className="flex items-center justify-between border-b border-surface/80 pb-1.5 mb-2 text-[10px] font-mono text-muted">
                <span>SHARD // 03</span>
                <span className="text-orange-400">SYNTHESIS</span>
              </div>
              <div className="h-16 rounded bg-void flex items-center justify-center p-1.5 overflow-hidden">
                <svg viewBox="0 0 100 50" className="w-full h-full stroke-orange-400/80" fill="none">
                  <circle cx="50" cy="25" r="20" strokeWidth="0.8" strokeDasharray="3 3" />
                  <circle cx="50" cy="25" r="12" strokeWidth="1" />
                  <circle cx="50" cy="25" r="4" fill="#F97316" />
                </svg>
              </div>
              <p className="mt-2 text-[11px] font-mono text-text">Synthetic residual</p>
              <p className="text-[9px] text-muted font-sans">OpenCLIP + Noise fusion</p>
            </div>
          </div>

          {/* Title and Tagline (Resolves between depth layers 0.10 – 0.50) */}
          <div
            ref={titleContainerRef}
            className="relative z-20 text-center mt-4 sm:mt-6 px-4 max-w-3xl"
            style={
              reducedMotion
                ? { letterSpacing: '0.18em', opacity: 1, filter: 'none' }
                : { letterSpacing: '0.5em', opacity: 0, filter: 'blur(10px)' }
            }
          >
            <p className="font-mono text-xs sm:text-sm uppercase tracking-widest text-accent mb-2">
              {lang === 'en' ? 'Digital Trust & Cybersecurity · Team Kinetix' : 'डिजिटल ट्रस्ट एवं साइबर सुरक्षा · टीम काइनेटिक्स'}
            </p>
            <h1 className="font-display text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-text drop-shadow-[0_0_35px_rgba(25,211,197,0.25)]">
              TRINETRA
            </h1>
            <p className="mt-3 text-sm sm:text-base md:text-lg text-muted max-w-2xl mx-auto font-sans leading-relaxed">
              {lang === 'en'
                ? 'Share any suspicious image and get a Provenance Passport in seconds: where it came from, what was changed, and whether it is likely AI-made.'
                : 'किसी भी संदिग्ध तस्वीर को साझा करें और सेकंडों में प्रोवेनेंस पासपोर्ट प्राप्त करें: यह कहाँ से आई, क्या बदला गया, और क्या यह एआई द्वारा बनाई गई है।'}
            </p>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-2 sm:gap-4 text-xs font-mono text-muted/90">
              <span className="px-2.5 py-1 rounded border border-surface bg-void-2/60">
                Eye 1: <strong className="text-text font-normal">Origin</strong>
              </span>
              <span className="text-surface">/</span>
              <span className="px-2.5 py-1 rounded border border-surface bg-void-2/60">
                Eye 2: <strong className="text-text font-normal">Change</strong>
              </span>
              <span className="text-surface">/</span>
              <span className="px-2.5 py-1 rounded border border-surface bg-void-2/60">
                Eye 3: <strong className="text-text font-normal">Synthesis</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Digital Noise Veil (0.00 – 0.18) */}
        {!reducedMotion && (
          <div
            ref={veilRef}
            className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-void/90 backdrop-blur-md transition-opacity pointer-events-auto"
          >
            <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
            <div className="relative z-10 text-center px-4 max-w-lg space-y-4">
              <div className="inline-flex items-center gap-2 border border-accent/40 bg-void-2/80 px-3 py-1.5 rounded-full text-xs font-mono text-accent">
                <span className="w-2 h-2 rounded-full bg-accent animate-ping" />
                {lang === 'en' ? 'Digital Trust & Cybersecurity' : 'डिजिटल ट्रस्ट एवं साइबर सुरक्षा'}
              </div>
              <h2 className="font-display text-2xl sm:text-3xl font-semibold tracking-wider text-text">
                NAVYUG — A NEW ERA
              </h2>
              <p className="text-xs sm:text-sm font-mono text-muted animate-pulse">
                {lang === 'en' ? '↓ Scroll to clear the noise & open the eye' : '↓ शोर साफ करने और आँख खोलने के लिए स्क्रॉल करें'}
              </p>
            </div>
          </div>
        )}

        {/* HUD Overlay - Bottom Bar (Corner brackets + Scroll hint) */}
        <div className="relative z-40 max-w-7xl mx-auto w-full flex items-center justify-between text-xs font-mono text-muted/70 pt-2 border-t border-surface/40">
          {/* Bottom Left Corner Bracket */}
          <div className="flex items-center gap-1.5">
            <span className="text-accent/60 font-mono text-sm">⎣</span>
            <span className="text-[11px]">SYS_ID: KINETIX_26</span>
          </div>

          {/* Bottom Center Scroll Hint */}
          <div
            ref={hudScrollHintRef}
            className="flex flex-col items-center gap-1 text-accent text-[11px] tracking-widest uppercase cursor-pointer"
            onClick={() => scrollToHash('#problem')}
          >
            <span>{lang === 'en' ? 'Scroll to explore' : 'अन्वेषण के लिए स्क्रॉल करें'}</span>
            <span className="animate-bounce text-sm">↓</span>
          </div>

          {/* Bottom Right Corner Bracket */}
          <div className="flex items-center gap-1.5">
            <span className="text-[11px]">THEME: NAVYUG</span>
            <span className="text-accent/60 font-mono text-sm">⎦</span>
          </div>
        </div>
      </div>
    </section>
  );
};
