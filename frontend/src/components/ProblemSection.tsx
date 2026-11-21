import React, { useEffect, useRef } from 'react';
import { onFrame } from '../lib/scroll';
import { pinProgress, lerp, clamp } from '../lib/math';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface ProblemSectionProps {
  lang: 'en' | 'hi';
}

interface ProblemCard {
  id: string;
  tag: string;
  titleEn: string;
  titleHi: string;
  descEn: string;
  descHi: string;
  color: string;
  renderIllustration: () => React.ReactNode;
}

export const ProblemSection: React.FC<ProblemSectionProps> = ({ lang }) => {
  const sectionRef = useRef<HTMLElement | null>(null);
  const trackRef = useRef<HTMLDivElement | null>(null);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);
  const graphicRefs = useRef<(HTMLDivElement | null)[]>([]);
  const counterTextRef = useRef<HTMLSpanElement | null>(null);
  const progressBarRef = useRef<HTMLDivElement | null>(null);

  const reducedMotion = useReducedMotion();

  const cards: ProblemCard[] = [
    {
      id: 'recycled',
      tag: 'OUT OF CONTEXT',
      titleEn: 'A real photo, a new claim',
      titleHi: 'वास्तविक तस्वीर, नया भ्रामक दावा',
      descEn:
        'An authentic photograph from an old event is resurfaced with a fabricated caption. AI detectors report it as 100% natural because the camera sensor physics are genuine.',
      descHi:
        'किसी पुरानी घटना की वास्तविक तस्वीर को झूठे कैप्शन के साथ पुनः फैलाया जाता है। एआई डिटेक्टर इसे प्राकृतिक बताते हैं क्योंकि कैमरे के संकेत असली होते हैं।',
      color: '#F59E0B',
      renderIllustration: () => (
        <svg viewBox="0 0 320 180" className="w-full h-full" fill="none">
          {/* Newspaper / Archived Photo Frame */}
          <rect x="20" y="20" width="160" height="120" rx="4" stroke="#A9B8D6" strokeWidth="1" strokeOpacity="0.4" fill="#0B1B3A" />
          <path d="M 30 110 L 70 60 L 110 95 L 140 70 L 170 110 Z" fill="#12254A" stroke="#19D3C5" strokeWidth="1" strokeOpacity="0.6" />
          <circle cx="65" cy="50" r="10" fill="#19D3C5" fillOpacity="0.4" />
          <rect x="30" y="125" width="80" height="6" rx="2" fill="#A9B8D6" fillOpacity="0.3" />
          <text x="30" y="38" fill="#19D3C5" fontSize="9" fontFamily="IBM Plex Mono">ARCHIVE: 2021</text>
          
          {/* Misleading Forward Arrow and Stamp */}
          <path d="M 170 80 Q 210 60 230 85" stroke="#F59E0B" strokeWidth="2" strokeDasharray="3 3" />
          <polygon points="232,80 238,88 228,89" fill="#F59E0B" />
          
          <rect x="180" y="70" width="120" height="75" rx="6" stroke="#F59E0B" strokeWidth="1.5" fill="#060D1F" />
          <rect x="190" y="85" width="100" height="8" rx="2" fill="#EF4444" fillOpacity="0.6" />
          <rect x="190" y="100" width="70" height="6" rx="2" fill="#A9B8D6" fillOpacity="0.4" />
          <text x="190" y="130" fill="#F59E0B" fontSize="9" fontFamily="IBM Plex Mono">CLAIM: &quot;TODAY&quot;</text>
        </svg>
      ),
    },
    {
      id: 'edited',
      tag: 'MODIFIED / SPLICED',
      titleEn: 'One object quietly removed',
      titleHi: 'एक वस्तु को गुपचुप हटा दिया गया',
      descEn:
        'Content-aware inpainting or selective splicing alters the truth of an image while preserving the surrounding original frame. Frequency transforms alone miss targeted local edits.',
      descHi:
        'इनपेंटिंग या चुनिंदा एडिटिंग से तस्वीर की सच्चाई बदल दी जाती है जबकि बाकी हिस्सा मूल रहता है। केवल वैश्विक फ़्रीक्वेंसी विश्लेषण स्थानीय बदलावों को नहीं पकड़ पाता।',
      color: '#F59E0B',
      renderIllustration: () => (
        <svg viewBox="0 0 320 180" className="w-full h-full" fill="none">
          <rect x="30" y="25" width="260" height="130" rx="6" stroke="#A9B8D6" strokeWidth="1" strokeOpacity="0.4" fill="#0B1B3A" />
          {/* Background mountain lines */}
          <path d="M 40 130 L 100 70 L 160 120 L 220 65 L 280 130" stroke="#12254A" strokeWidth="2" />
          {/* Cutout Spliced Bounding Box */}
          <rect x="120" y="55" width="80" height="70" rx="3" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="4 4" fill="#060D1F" />
          {/* Missing object dashed outline */}
          <circle cx="160" cy="85" r="16" stroke="#F59E0B" strokeWidth="1" strokeDasharray="2 2" strokeOpacity="0.6" />
          <path d="M 148 115 L 172 115" stroke="#F59E0B" strokeWidth="1.5" />
          <text x="160" y="112" textAnchor="middle" fill="#F59E0B" fontSize="8" fontFamily="IBM Plex Mono">REMOVED</text>
          {/* Scan alignment points */}
          <circle cx="120" cy="55" r="3" fill="#19D3C5" />
          <circle cx="200" cy="55" r="3" fill="#19D3C5" />
          <circle cx="120" cy="125" r="3" fill="#19D3C5" />
          <circle cx="200" cy="125" r="3" fill="#19D3C5" />
        </svg>
      ),
    },
    {
      id: 'ai_generated',
      tag: 'SYNTHETIC GENERATION',
      titleEn: 'A scene that never existed',
      titleHi: 'एक दृश्य जो कभी था ही नहीं',
      descEn:
        'Diffusion models synthesize photorealistic humans and events from scratch. Subtle frequency anomalies and noise pattern uniformities betray their algorithmic origin.',
      descHi:
        'डिफ्यूज़न मॉडल पूरी तरह काल्पनिक यथार्थवादी तस्वीरों को रचते हैं। सूक्ष्म फ़्रीक्वेंसी असंगतताएँ और अस्वाभाविक शोर पैटर्न उनकी कृत्रिम उत्पत्ति को उजागर करते हैं।',
      color: '#F97316',
      renderIllustration: () => (
        <svg viewBox="0 0 320 180" className="w-full h-full" fill="none">
          {/* Latent diffusion grid */}
          <rect x="30" y="25" width="260" height="130" rx="6" stroke="#F97316" strokeWidth="1" strokeOpacity="0.4" fill="#0B1B3A" />
          {/* Concentric synthetic rings */}
          <circle cx="160" cy="90" r="55" stroke="#F97316" strokeWidth="0.75" strokeDasharray="4 6" strokeOpacity="0.5" />
          <circle cx="160" cy="90" r="38" stroke="#F97316" strokeWidth="1" strokeDasharray="2 4" strokeOpacity="0.7" />
          <circle cx="160" cy="90" r="20" stroke="#F97316" strokeWidth="1.2" strokeOpacity="0.9" />
          
          {/* Spectral peaks */}
          <line x1="80" y1="90" x2="240" y2="90" stroke="#F97316" strokeWidth="0.5" strokeOpacity="0.4" />
          <line x1="160" y1="35" x2="160" y2="145" stroke="#F97316" strokeWidth="0.5" strokeOpacity="0.4" />
          
          <rect x="125" y="78" width="70" height="24" rx="4" fill="#060D1F" stroke="#F97316" strokeWidth="1" />
          <text x="160" y="93" textAnchor="middle" fill="#F97316" fontSize="9" fontFamily="IBM Plex Mono">SYNTHETIC</text>
        </svg>
      ),
    },
    {
      id: 'lost_context',
      tag: 'STRIPPED METADATA',
      titleEn: 'Screenshots strip the evidence',
      titleHi: 'स्क्रीनशॉट सारे प्रमाण मिटा देते हैं',
      descEn:
        'Recompression over WhatsApp and screenshotting strip all EXIF metadata and obliterate high-frequency cues. Honest provenance systems must abstain rather than falsely accuse.',
      descHi:
        'व्हाट्सएप पर बार-बार री-कम्प्रेशन और स्क्रीनशॉट लेने से EXIF डेटा नष्ट हो जाता है। एक ईमानदार प्रणाली झूठा आरोप लगाने के बजाय अनिर्णायक रहना चुनती है।',
      color: '#64748B',
      renderIllustration: () => (
        <svg viewBox="0 0 320 180" className="w-full h-full" fill="none">
          {/* Smartphone Frame */}
          <rect x="80" y="20" width="160" height="140" rx="12" stroke="#64748B" strokeWidth="1.5" fill="#0B1B3A" />
          <rect x="95" y="35" width="130" height="100" rx="4" stroke="#64748B" strokeWidth="0.8" strokeDasharray="2 2" fill="#060D1F" />
          {/* EXIF Data Strip shredder */}
          <g transform="translate(105, 50)">
            <text x="0" y="10" fill="#EF4444" fontSize="8" fontFamily="IBM Plex Mono">EXIF: [STRIPPED]</text>
            <text x="0" y="24" fill="#64748B" fontSize="8" fontFamily="IBM Plex Mono">JPEG Q: ≤ 75</text>
            <text x="0" y="38" fill="#64748B" fontSize="8" fontFamily="IBM Plex Mono">CAMERA: UNKNOWN</text>
            <line x1="0" y1="46" x2="110" y2="46" stroke="#EF4444" strokeWidth="1" strokeDasharray="2 2" />
            <text x="0" y="60" fill="#A9B8D6" fontSize="8" fontFamily="IBM Plex Mono">STATUS: GATED</text>
          </g>
        </svg>
      ),
    },
  ];

  useEffect(() => {
    if (reducedMotion) return;

    const unsubscribe = onFrame(() => {
      if (!sectionRef.current || !trackRef.current) return;
      const { p, inView, rect } = pinProgress(sectionRef.current);
      if (!inView) return;

      const track = trackRef.current;
      const trackWidth = track.scrollWidth;
      const viewWidth = rect.width;
      const maxScroll = Math.max(0, trackWidth - viewWidth + 80);

      // Slide reel horizontally with scroll
      const currentX = -p * maxScroll;
      track.style.transform = `translateX(${currentX.toFixed(1)}px)`;

      // Update card focus state based on proximity to center focus line
      const focusX = viewWidth * 0.45;
      const totalCards = cards.length;
      let focusedIndex = 0;
      let minDistance = Infinity;

      cardRefs.current.forEach((cardEl, idx) => {
        if (!cardEl) return;
        const cardBox = cardEl.getBoundingClientRect();
        const cardCenter = cardBox.left + cardBox.width / 2;
        const dist = Math.abs(cardCenter - focusX);

        if (dist < minDistance) {
          minDistance = dist;
          focusedIndex = idx;
        }

        // Focused card is bright; others dim and scale down
        const factor = clamp(1 - dist / (viewWidth * 0.6), 0, 1);
        const scale = lerp(0.92, 1.0, factor);
        const opacity = lerp(0.38, 1.0, factor);
        cardEl.style.transform = `scale(${scale.toFixed(3)})`;
        cardEl.style.opacity = opacity.toFixed(2);

        // Graphic inside card drifts against frame
        const graphicEl = graphicRefs.current[idx];
        if (graphicEl) {
          const drift = lerp(-12, 12, factor);
          graphicEl.style.transform = `translateY(${drift.toFixed(1)}px)`;
        }
      });

      // Update 01/04 Counter and Progress Bar directly on refs
      if (counterTextRef.current) {
        counterTextRef.current.textContent = `0${focusedIndex + 1} / 0${totalCards}`;
      }
      if (progressBarRef.current) {
        const pct = ((focusedIndex + 1) / totalCards) * 100;
        progressBarRef.current.style.width = `${pct.toFixed(1)}%`;
      }
    });

    return () => unsubscribe();
  }, [reducedMotion, cards.length]);

  return (
    <section
      id="problem"
      ref={sectionRef}
      className="relative w-full h-[340svh] bg-void border-t border-surface/50"
      aria-label="The Forward Chain - Problem Statement"
    >
      {/* Pinned Sticky Viewport */}
      <div className="sticky top-0 h-screen w-full overflow-hidden flex flex-col justify-between py-16 px-4 sm:px-8 max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-surface/40">
          <div className="max-w-2xl">
            <span className="font-mono text-xs text-accent tracking-widest uppercase block mb-1">
              {lang === 'en' ? '01 // The Forward Chain' : '०१ // फ़ॉरवर्ड शृंखला'}
            </span>
            <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight text-text">
              {lang === 'en'
                ? 'Fake images spread faster than the truth.'
                : 'झूठी छवियां सच से कहीं अधिक तेजी से फैलती हैं।'}
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-muted font-sans leading-relaxed">
              {lang === 'en'
                ? 'Most misinformation is an authentic photo repurposed in the wrong context or a lightly edited real image that AI detectors cannot see. In Trinetra, "No match in index" is the normal case and still delivers a valid Passport.'
                : 'अधिकांश दुष्प्रचार असली तस्वीर को गलत संदर्भ में दिखाना या हल्के रूप से संपादित करना होता है जिसे एआई पकड़ नहीं पाता। त्रिनेत्र में "इंडेक्स में कोई मैच न होना" सामान्य बात है और तब भी मान्य पासपोर्ट प्रदान किया जाता है।'}
            </p>
          </div>

          {/* Reel Progress & Counter */}
          <div className="flex flex-col items-start md:items-end gap-2 font-mono text-xs">
            <div className="flex items-center gap-3">
              <span className="text-muted uppercase tracking-wider text-[11px]">CASE STUDY</span>
              <span ref={counterTextRef} className="text-accent font-semibold text-sm">
                01 / 04
              </span>
            </div>
            <div className="w-36 h-1 bg-surface rounded-full overflow-hidden">
              <div ref={progressBarRef} className="h-full bg-accent transition-all duration-150" style={{ width: '25%' }} />
            </div>
          </div>
        </div>

        {/* Sliding Reel Stage */}
        <div className="relative flex-1 flex items-center overflow-hidden my-4">
          <div
            ref={trackRef}
            className="flex items-center gap-6 sm:gap-8 will-change-transform"
            style={{ transform: 'translateX(0px)' }}
          >
            {cards.map((card, i) => (
              <div
                key={card.id}
                ref={(el) => {
                  cardRefs.current[i] = el;
                }}
                className="w-72 sm:w-88 md:w-96 flex-shrink-0 rounded-xl border border-surface bg-void-2/80 backdrop-blur-md p-5 sm:p-6 shadow-xl transition-transform duration-75"
                style={{
                  opacity: i === 0 ? 1 : 0.4,
                  transform: i === 0 ? 'scale(1)' : 'scale(0.92)',
                }}
              >
                {/* Card Tag */}
                <div className="flex items-center justify-between pb-3 border-b border-surface/60 mb-4">
                  <span
                    className="font-mono text-[10px] tracking-wider px-2 py-0.5 rounded border"
                    style={{
                      borderColor: `${card.color}60`,
                      color: card.color,
                      backgroundColor: `${card.color}15`,
                    }}
                  >
                    {card.tag}
                  </span>
                  <span className="font-mono text-[11px] text-muted">0{i + 1}</span>
                </div>

                {/* Graphic Container with Parallax Drift */}
                <div
                  ref={(el) => {
                    graphicRefs.current[i] = el;
                  }}
                  className="w-full h-40 rounded-lg bg-void border border-surface/60 overflow-hidden p-2 flex items-center justify-center transition-transform duration-75"
                >
                  {card.renderIllustration()}
                </div>

                {/* Card Title & Description */}
                <div className="mt-5 space-y-2">
                  <h3 className="font-sans text-base sm:text-lg font-semibold text-text">
                    {lang === 'en' ? card.titleEn : card.titleHi}
                  </h3>
                  <p className="text-xs sm:text-sm text-muted font-sans leading-relaxed">
                    {lang === 'en' ? card.descEn : card.descHi}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Reel Hint */}
        <div className="flex items-center justify-between text-[11px] font-mono text-muted/60 pt-3 border-t border-surface/40">
          <span>FOCUS LINE ALIGNED</span>
          <span className="text-accent/80">SCROLL DOWN TO PROGRESS CARDS →</span>
        </div>
      </div>
    </section>
  );
};
