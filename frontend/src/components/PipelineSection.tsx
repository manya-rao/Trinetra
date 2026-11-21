import React, { useEffect, useRef } from 'react';
import { onFrame } from '../lib/scroll';
import { pinProgress, range, lerp, clamp } from '../lib/math';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface PipelineSectionProps {
  lang: 'en' | 'hi';
}

export const PipelineSection: React.FC<PipelineSectionProps> = ({ lang }) => {
  const sectionRef = useRef<HTMLElement | null>(null);
  const pathInkingRef = useRef<SVGPathElement | null>(null);
  const signalDotRef = useRef<SVGCircleElement | null>(null);
  const signalsCountRef = useRef<HTMLSpanElement | null>(null);
  const captionRef = useRef<HTMLParagraphElement | null>(null);
  const stepIndicatorsRef = useRef<(HTMLDivElement | null)[]>([]);
  const diffHeatmapRef = useRef<HTMLDivElement | null>(null);

  const reducedMotion = useReducedMotion();

  // Total signal families derived directly from code (ml/features, backend/app):
  // 1. pHash, 2. OpenCLIP, 3. C2PA, 4. SIFT/SSIM Diff, 5. Frequency FFT, 6. Wavelet Noise, 7. EXIF/JPEG Quantization
  const TOTAL_SIGNALS = 7;

  const steps = [
    {
      num: '01',
      titleEn: 'Input & Ingestion',
      titleHi: 'छवि इनपुट एवं फिंगरप्रिंट',
      descEn: 'The image is ingested; client extracts perceptual hash (pHash 64-bit) and OpenCLIP ViT-B-32 visual probe vector.',
      descHi: 'छवि प्राप्त की जाती है; पर्सेप्टुअल हैश (pHash) और OpenCLIP ViT-B-32 विज़ुअल प्रोब वेक्टर तैयार किया जाता है।',
    },
    {
      num: '02',
      titleEn: 'Signed-Proof Verification',
      titleHi: 'डिजिटल हस्ताक्षर सत्यापन (C2PA)',
      descEn: 'Inspects embedded cryptographic Content Credentials (C2PA). If signed and verified as AI-generated, immediately issues L1 Confirmed.',
      descHi: 'क्रिप्टोग्राफिक C2PA सामग्री क्रेडेंशियल्स की जांच। यदि हस्ताक्षरित और पुष्ट है, तो सीधे L1 पुष्ट पासपोर्ट जारी किया जाता है।',
    },
    {
      num: '03',
      titleEn: 'Dual-Lane Dispatch',
      titleHi: 'द्वि-मार्गी विश्लेषण (मूल स्रोत बनाम एआई)',
      descEn: 'Origin Lane matches against curated reference index + computes SSIM diff heatmap. If unmatched, AI Lane executes FFT frequency + noise fusion.',
      descHi: 'ओरिजिन लेन इंडेक्स से मिलान कर SSIM डिफ़ हीटमैप बनाती है। यदि मैच नहीं मिलता, तो एआई लेन FFT आवृत्ति और नॉइज़ फ़्यूज़न चलाती है।',
    },
    {
      num: '04',
      titleEn: 'Consensus & Passport',
      titleHi: 'सर्वसम्मति एवं प्रोवेनेंस पासपोर्ट',
      descEn: 'Aggregator resolves signals across Three Eyes via the Confirmation Ladder, strictly routing inconclusive cases rather than guessing.',
      descHi: 'एग्रीगेटर तीनों आँखों के संकेतों को पुष्टि सीढ़ी के आधार पर संयोजित कर स्पष्ट पासपोर्ट जारी करता है।',
    },
  ];

  useEffect(() => {
    if (reducedMotion) return;

    const unsubscribe = onFrame(() => {
      if (!sectionRef.current) return;
      const { p, inView } = pinProgress(sectionRef.current);
      if (!inView) return;

      // Inking SVG Path progress
      const path = pathInkingRef.current;
      if (path) {
        const totalLen = path.getTotalLength();
        const strokeDash = totalLen * (1 - p);
        path.style.strokeDashoffset = `${strokeDash.toFixed(1)}px`;

        // Signal Dot riding the path
        if (signalDotRef.current) {
          const pt = path.getPointAtLength(p * totalLen);
          signalDotRef.current.setAttribute('cx', pt.x.toFixed(1));
          signalDotRef.current.setAttribute('cy', pt.y.toFixed(1));
          signalDotRef.current.style.opacity = p > 0.02 && p < 0.98 ? '1' : '0.4';
        }
      }

      // Real signals checked counter (0 -> 7)
      const currentSignals = Math.min(TOTAL_SIGNALS, Math.floor(p * (TOTAL_SIGNALS + 0.9)));
      if (signalsCountRef.current) {
        signalsCountRef.current.textContent = `${currentSignals} / ${TOTAL_SIGNALS}`;
      }

      // Step indicator (4 steps across progress 0.0 - 1.0)
      const activeStep = clamp(Math.floor(p * 4), 0, 3);
      stepIndicatorsRef.current.forEach((el, idx) => {
        if (!el) return;
        if (idx === activeStep) {
          el.classList.add('border-accent', 'bg-accent/15', 'text-text');
          el.classList.remove('border-surface', 'bg-void-2/60', 'text-muted');
        } else {
          el.classList.remove('border-accent', 'bg-accent/15', 'text-text');
          el.classList.add('border-surface', 'bg-void-2/60', 'text-muted');
        }
      });

      // Update current leg caption
      if (captionRef.current) {
        captionRef.current.textContent = lang === 'en' ? steps[activeStep].descEn : steps[activeStep].descHi;
      }

      // Mini Diff Heatmap reveal during Step 3 (0.45 – 0.85)
      if (diffHeatmapRef.current) {
        const pDiff = range(p, 0.45, 0.75);
        diffHeatmapRef.current.style.opacity = pDiff > 0 ? lerp(0.2, 1, pDiff).toFixed(2) : '0';
        diffHeatmapRef.current.style.transform = `scale(${lerp(0.9, 1, pDiff).toFixed(2)})`;
      }
    });

    return () => unsubscribe();
  }, [reducedMotion, lang, steps]);

  return (
    <section
      id="pipeline"
      ref={sectionRef}
      className="relative w-full h-[380svh] bg-void border-t border-surface/50"
      aria-label="Three Eyes Pipeline Architecture"
    >
      {/* Sticky Pinned Viewport */}
      <div className="sticky top-0 h-screen w-full overflow-hidden flex flex-col justify-between py-12 px-4 sm:px-8 max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-surface/40">
          <div>
            <span className="font-mono text-xs text-accent tracking-widest uppercase block mb-1">
              {lang === 'en' ? '02 // Autonomous Provenance Architecture' : '०२ // स्वायत्त प्रोवेनेंस आर्किटेक्चर'}
            </span>
            <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight text-text">
              {lang === 'en' ? 'Three Eyes, one verdict.' : 'तीन आँखें, एक अचूक निर्णय।'}
            </h2>
            <p className="mt-1 text-xs sm:text-sm text-muted font-sans max-w-2xl">
              {lang === 'en'
                ? 'Every submitted image flows through a deterministic forensic pipeline: verifiable signatures first, then index-anchored origin diffs, then multi-feature synthetic detection.'
                : 'प्रत्येक छवि एक सुव्यवस्थित फोरेंसिक पाइपलाइन से गुजरती है: पहले डिजिटल हस्ताक्षर, फिर मूल स्रोत अंतर, और अंत में बहु-संकेतक कृत्रिम पहचान।'}
            </p>
          </div>

          {/* Real Counter: Signals checked */}
          <div className="flex items-center gap-3 border border-surface bg-void-2 px-4 py-2 rounded-lg font-mono text-xs">
            <span className="text-muted">SIGNALS CHECKED:</span>
            <span ref={signalsCountRef} className="text-accent font-semibold text-sm">
              0 / {TOTAL_SIGNALS}
            </span>
          </div>
        </div>

        {/* Central Pipeline Schematic (SVG path inking + branching) */}
        <div className="relative flex-1 flex items-center justify-center my-4 overflow-hidden">
          <div className="w-full max-w-5xl h-72 sm:h-80 md:h-96 relative flex items-center justify-center">
            {/* SVG Pipeline Canvas */}
            <svg
              viewBox="0 0 900 360"
              className="w-full h-full overflow-visible"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Background Pipeline Guideline (Faint) */}
              <path
                d="M 50 180 L 180 180 L 320 180 C 400 180 430 90 520 90 L 680 90 C 740 90 770 180 820 180"
                stroke="#12254A"
                strokeWidth="4"
                strokeLinecap="round"
              />
              <path
                d="M 320 180 C 400 180 430 270 520 270 L 680 270 C 740 270 770 180 820 180"
                stroke="#12254A"
                strokeWidth="4"
                strokeLinecap="round"
              />

              {/* Inked Pipeline Path (animated via strokeDashoffset) */}
              <path
                ref={pathInkingRef}
                d="M 50 180 L 180 180 L 320 180 C 400 180 430 90 520 90 L 680 90 C 740 90 770 180 820 180"
                stroke="#19D3C5"
                strokeWidth="3.5"
                strokeLinecap="round"
                style={{
                  strokeDasharray: '1200',
                  strokeDashoffset: reducedMotion ? '0' : '1200',
                  transition: 'stroke-dashoffset 0.05s linear',
                }}
              />
              <path
                d="M 320 180 C 400 180 430 270 520 270 L 680 270 C 740 270 770 180 820 180"
                stroke="#F97316"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeDasharray="4 6"
                strokeOpacity="0.8"
              />

              {/* Inked Signal Dot */}
              <circle
                ref={signalDotRef}
                cx="50"
                cy="180"
                r="7"
                fill="#19D3C5"
                style={{
                  filter: 'drop-shadow(0 0 10px #19D3C5)',
                  opacity: reducedMotion ? '1' : '0.4',
                }}
              />

              {/* Node 1: Input */}
              <g transform="translate(50, 180)">
                <circle cx="0" cy="0" r="18" fill="#0B1B3A" stroke="#19D3C5" strokeWidth="1.5" />
                <circle cx="0" cy="0" r="6" fill="#19D3C5" />
                <text x="0" y="34" textAnchor="middle" fill="#EAF1FF" fontSize="10" fontFamily="IBM Plex Mono">
                  IMAGE INPUT
                </text>
              </g>

              {/* Node 2: Fingerprint */}
              <g transform="translate(180, 180)">
                <circle cx="0" cy="0" r="16" fill="#0B1B3A" stroke="#19D3C5" strokeWidth="1.5" />
                <text x="0" y="4" textAnchor="middle" fill="#19D3C5" fontSize="11" fontWeight="bold" fontFamily="IBM Plex Mono">
                  #
                </text>
                <text x="0" y="34" textAnchor="middle" fill="#EAF1FF" fontSize="10" fontFamily="IBM Plex Mono">
                  pHASH + CLIP
                </text>
              </g>

              {/* Node 3: C2PA Proof */}
              <g transform="translate(320, 180)">
                <circle cx="0" cy="0" r="16" fill="#0B1B3A" stroke="#EF4444" strokeWidth="1.5" />
                <text x="0" y="4" textAnchor="middle" fill="#EF4444" fontSize="10" fontWeight="bold" fontFamily="IBM Plex Mono">
                  L1
                </text>
                <text x="0" y="-24" textAnchor="middle" fill="#EF4444" fontSize="9" fontFamily="IBM Plex Mono">
                  C2PA SIGNED
                </text>
                <text x="0" y="34" textAnchor="middle" fill="#EAF1FF" fontSize="10" fontFamily="IBM Plex Mono">
                  PROOF CHECK
                </text>
              </g>

              {/* Branch Node Top: Eye 1 & 2 (Origin & Diff Lane) */}
              <g transform="translate(560, 90)">
                <rect x="-60" y="-20" width="120" height="40" rx="6" fill="#0B1B3A" stroke="#F59E0B" strokeWidth="1.5" />
                <text x="0" y="-3" textAnchor="middle" fill="#F59E0B" fontSize="10" fontWeight="bold" fontFamily="IBM Plex Mono">
                  EYE 1 + 2: ORIGIN
                </text>
                <text x="0" y="12" textAnchor="middle" fill="#A9B8D6" fontSize="9" fontFamily="IBM Plex Mono">
                  Index + SSIM Diff
                </text>
              </g>

              {/* Branch Node Bottom: Eye 3 (AI Lane) */}
              <g transform="translate(560, 270)">
                <rect x="-60" y="-20" width="120" height="40" rx="6" fill="#0B1B3A" stroke="#F97316" strokeWidth="1.5" />
                <text x="0" y="-3" textAnchor="middle" fill="#F97316" fontSize="10" fontWeight="bold" fontFamily="IBM Plex Mono">
                  EYE 3: AI LANE
                </text>
                <text x="0" y="12" textAnchor="middle" fill="#A9B8D6" fontSize="9" fontFamily="IBM Plex Mono">
                  FFT + Wavelet Gate
                </text>
              </g>

              {/* Node 4: Verdict Aggregator */}
              <g transform="translate(820, 180)">
                <polygon points="0,-22 22,0 0,22 -22,0" fill="#0B1B3A" stroke="#19D3C5" strokeWidth="2" />
                <circle cx="0" cy="0" r="5" fill="#19D3C5" />
                <text x="0" y="38" textAnchor="middle" fill="#19D3C5" fontSize="10" fontWeight="bold" fontFamily="IBM Plex Mono">
                  PASSPORT
                </text>
              </g>
            </svg>

            {/* Mini Illustration: Diff Heatmap (SSIM delta) */}
            <div
              ref={diffHeatmapRef}
              className="absolute right-4 top-2 sm:top-6 w-48 sm:w-56 p-3 rounded-lg border border-amber-500/40 bg-void-2/95 shadow-2xl pointer-events-none transition-opacity"
              style={{ opacity: reducedMotion ? 1 : 0 }}
            >
              <div className="flex items-center justify-between text-[10px] font-mono text-muted border-b border-surface/80 pb-1 mb-2">
                <span className="text-amber-400 font-semibold">EYE 2 DIFF</span>
                <span>SSIM Δ HEATMAP</span>
              </div>
              <div className="relative h-20 rounded bg-void border border-surface/80 flex items-center justify-center overflow-hidden">
                {/* Background grid */}
                <div
                  className="absolute inset-0 opacity-20"
                  style={{
                    backgroundImage: 'linear-gradient(#F59E0B 1px, transparent 1px), linear-gradient(90deg, #F59E0B 1px, transparent 1px)',
                    backgroundSize: '10px 10px',
                  }}
                />
                {/* Simulated Heatmap changed region */}
                <div className="absolute w-14 h-12 rounded border-2 border-amber-400 bg-amber-500/30 flex items-center justify-center animate-pulse">
                  <span className="text-[8px] font-mono text-amber-200">SPLICED</span>
                </div>
              </div>
              <p className="mt-1.5 text-[9px] font-mono text-muted text-center">
                SIFT alignment &bull; pixel-level delta
              </p>
            </div>
          </div>
        </div>

        {/* 4-Step Indicator Bar + Current Leg Caption */}
        <div className="border-t border-surface/40 pt-4 space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
            {steps.map((st, i) => (
              <div
                key={st.num}
                ref={(el) => {
                  stepIndicatorsRef.current[i] = el;
                }}
                className={`p-2.5 rounded-lg border text-xs font-mono transition-all duration-200 ${
                  i === 0 ? 'border-accent bg-accent/15 text-text' : 'border-surface bg-void-2/60 text-muted'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-accent">STEP {st.num}</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-accent/80" />
                </div>
                <div className="font-semibold text-[11px] truncate">{lang === 'en' ? st.titleEn : st.titleHi}</div>
              </div>
            ))}
          </div>

          <div className="bg-void-2/80 border border-surface/60 rounded-lg p-3 flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-accent animate-ping flex-shrink-0" />
            <p ref={captionRef} className="text-xs sm:text-sm font-sans text-muted leading-relaxed">
              {lang === 'en' ? steps[0].descEn : steps[0].descHi}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
