import React, { useRef } from 'react';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface LadderSectionProps {
  lang: 'en' | 'hi';
}

interface LadderTier {
  level: string;
  verdictKey: string;
  titleEn: string;
  titleHi: string;
  verdictNameEn: string;
  verdictNameHi: string;
  color: string;
  rings: number;
  badgeEn: string;
  badgeHi: string;
  evidenceEn: string;
  evidenceHi: string;
  noteEn: string;
  noteHi: string;
}

export const LadderSection: React.FC<LadderSectionProps> = ({ lang }) => {
  const reducedMotion = useReducedMotion();

  const tiers: LadderTier[] = [
    {
      level: 'L1',
      verdictKey: 'ai_confirmed',
      titleEn: 'Level 1: Cryptographic Proof',
      titleHi: 'स्तर १: क्रिप्टोग्राफिक डिजिटल प्रमाण',
      verdictNameEn: 'AI-Generated (Confirmed)',
      verdictNameHi: 'एआई-निर्मित (पुष्ट)',
      color: '#EF4444',
      rings: 4,
      badgeEn: 'CONFIRMED ONLY',
      badgeHi: 'केवल पुष्ट',
      evidenceEn:
        'Valid cryptographically signed C2PA manifest or verifiable cryptographic generator watermark. The word "confirmed" appears ONLY at this level.',
      evidenceHi:
        'वैध रूप से हस्ताक्षरित C2PA घोषणापत्र या प्रमाणित एआई वॉटरमार्क। "पुष्ट" शब्द केवल इसी स्तर पर लागू होता है।',
      noteEn: 'Cryptographic ground truth · Zero ambiguity',
      noteHi: 'क्रिप्टोग्राफिक अचूक प्रमाण · शून्य अस्पष्टता',
    },
    {
      level: 'L2',
      verdictKey: 'modified',
      titleEn: 'Level 2: Index Match + Diff',
      titleHi: 'स्तर २: इंडेक्स मिलान एवं अंतर विश्लेषण',
      verdictNameEn: 'Modified / Original / Out of Context',
      verdictNameHi: 'संशोधित / मूल छवि / गलत संदर्भ',
      color: '#F59E0B',
      rings: 3,
      badgeEn: 'PROVENANCE ANCHORED',
      badgeHi: 'स्रोत आधारित',
      evidenceEn:
        'Direct match found in curated reference index via pHash/CLIP. SIFT/ORB homography alignment yields pixel delta; significant diffs flag "Modified", unedited images flag "Original" or "Out of Context" with date/source timeline.',
      evidenceHi:
        'pHash/CLIP द्वारा संदर्भ इंडेक्स में सीधा मिलान। SIFT/ORB अलाइनमेंट से पिक्सेल अंतर निकाला जाता है; बदलाव पर "संशोधित" तथा यथावत होने पर "मूल" या "गलत संदर्भ" दिया जाता है।',
      noteEn: 'Heatmap diff comparison · Curated demo archive',
      noteHi: 'हीटमैप तुलना · सत्यापित संग्रह',
    },
    {
      level: 'L3',
      verdictKey: 'likely_ai',
      titleEn: 'Level 3: Multi-Signal AI Consensus',
      titleHi: 'स्तर ३: बहु-संकेतक एआई सर्वसम्मति',
      verdictNameEn: 'Likely AI-Generated',
      verdictNameHi: 'संभावित एआई-निर्मित',
      color: '#F97316',
      rings: 2,
      badgeEn: 'LIKELIHOOD (NOT PROOF)',
      badgeHi: 'संभावना (प्रमाण नहीं)',
      evidenceEn:
        'OpenCLIP ViT-B-32 probe, FFT frequency power spectra, and Wavelet noise residual models all align and exceed high-confidence calibrated threshold (score > 0.9728).',
      evidenceHi:
        'OpenCLIP प्रोब, 2D FFT स्पेक्ट्रम और वेवलेट नॉइज़ मॉडल एकमत होकर उच्च सीमा (स्कोर > 0.9728) पार करते हैं।',
      noteEn: 'Statistically strong likelihood · Not definitive proof',
      noteHi: 'सांख्यिकीय रूप से मजबूत संकेत · अकाट्य प्रमाण नहीं',
    },
    {
      level: 'L4',
      verdictKey: 'inconclusive',
      titleEn: 'Level 4: Uncertainty Gate & Abstention',
      titleHi: 'स्तर ४: अनिश्चितता गेट एवं निष्पक्षता',
      verdictNameEn: 'Inconclusive',
      verdictNameHi: 'अनिर्णायक',
      color: '#64748B',
      rings: 1,
      badgeEn: 'ABSTAIN OVER GUESS',
      badgeHi: 'अटकलों से बचाव',
      evidenceEn:
        'Low resolution, WhatsApp/Telegram recompression (JPEG Q ≤ 75), screenshot artifacts, conflicting classifier signals, or novel held-out generators (e.g. Flux at 1.50% detection). Offers Google Lens & TinEye external search fallback.',
      evidenceHi:
        'कम रिज़ॉल्यूशन, व्हाट्सएप री-कम्प्रेशन (JPEG Q ≤ 75), स्क्रीनशॉट, विरोधी संकेत या अज्ञात जनरेटर। गूगल लेंस एवं टिनआई खोज विकल्प प्रदान करता है।',
      noteEn: 'Prefers false negatives over false accusations',
      noteHi: 'झूठे आरोप लगाने के बजाय निष्पक्ष रहना प्राथमिकता',
    },
  ];

  // 3D Card Tilt handler for hover/focus
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>, cardEl: HTMLDivElement) => {
    if (reducedMotion) return;
    const rect = cardEl.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    const rotX = -(y / (rect.height / 2)) * 8;
    const rotY = (x / (rect.width / 2)) * 8;
    cardEl.style.transform = `perspective(1000px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateY(-4px)`;
  };

  const handleMouseLeave = (cardEl: HTMLDivElement) => {
    if (reducedMotion) return;
    cardEl.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)';
  };

  return (
    <section
      id="ladder"
      className="relative w-full py-24 px-4 sm:px-8 bg-void border-t border-surface/50"
      aria-label="The Confirmation Ladder"
    >
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-3" data-reveal>
          <span className="font-mono text-xs text-accent tracking-widest uppercase block">
            {lang === 'en' ? '03 // Rigorous Epistemology' : '०३ // फोरेंसिक प्रमाण सीढ़ी'}
          </span>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-text">
            {lang === 'en' ? 'The Confirmation Ladder' : 'फोरेंसिक पुष्टि सीढ़ी'}
          </h2>
          <p className="text-sm sm:text-base text-muted font-sans leading-relaxed">
            {lang === 'en'
              ? 'Never guessing. Never claiming false certainty. Trinetra structures evidence into four strict tiers, reserving the word "confirmed" exclusively for verified cryptographic proof.'
              : 'कोई तुक्का नहीं। कोई झूठा दावा नहीं। त्रिनेत्र साक्ष्यों को चार कड़े स्तरों में विभाजित करता है, जहाँ "पुष्ट" शब्द केवल क्रिप्टोग्राफिक प्रमाण हेतु आरक्षित है।'}
          </p>
        </div>

        {/* Four Tier Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
          {tiers.map((tier) => (
            <CardItem
              key={tier.level}
              tier={tier}
              lang={lang}
              reducedMotion={reducedMotion}
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            />
          ))}
        </div>

        {/* Ladder Principle Footer */}
        <div className="rounded-xl border border-surface/80 bg-void-2/60 p-5 text-center font-mono text-xs text-muted max-w-3xl mx-auto space-y-1" data-reveal>
          <p className="text-accent">
            {lang === 'en'
              ? 'CORE TENET: Prefer false negatives over false accusations.'
              : 'मूल सिद्धांत: किसी निर्दोष छवि पर झूठा आरोप लगाने से बेहतर है अनिर्णायक रहना।'}
          </p>
          <p className="text-[11px] text-muted/70">
            {lang === 'en'
              ? 'Quiet signals read "No AI signs found, not proof". The system never presents likely_real_looking as a positive authenticity claim.'
              : 'शांत संकेतों पर "कोई एआई संकेत नहीं (प्रमाण नहीं)" दर्शाया जाता है। प्रणाली कभी भी इसे प्रामाणिकता का सकारात्मक दावा नहीं मानती।'}
          </p>
        </div>
      </div>
    </section>
  );
};

interface CardItemProps {
  tier: LadderTier;
  lang: 'en' | 'hi';
  reducedMotion: boolean;
  onMouseMove: (e: React.MouseEvent<HTMLDivElement>, el: HTMLDivElement) => void;
  onMouseLeave: (el: HTMLDivElement) => void;
}

const CardItem: React.FC<CardItemProps> = ({ tier, lang, reducedMotion, onMouseMove, onMouseLeave }) => {
  const cardRef = useRef<HTMLDivElement | null>(null);

  return (
    <div
      ref={cardRef}
      data-reveal
      tabIndex={0}
      onMouseMove={(e) => cardRef.current && onMouseMove(e, cardRef.current)}
      onMouseLeave={() => cardRef.current && onMouseLeave(cardRef.current)}
      onFocus={() => {
        if (!reducedMotion && cardRef.current) {
          cardRef.current.style.transform = 'perspective(1000px) translateY(-6px)';
        }
      }}
      onBlur={() => {
        if (!reducedMotion && cardRef.current) {
          cardRef.current.style.transform = 'perspective(1000px) translateY(0px)';
        }
      }}
      className="relative rounded-2xl border border-surface bg-void-2/90 backdrop-blur-md p-6 sm:p-8 flex flex-col justify-between transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-accent hover:border-accent/60 shadow-xl group"
      style={{
        boxShadow: `0 10px 30px -10px ${tier.color}15`,
      }}
    >
      <div>
        {/* Top Header: Level & Orbit Graphic */}
        <div className="flex items-center justify-between pb-4 border-b border-surface/60 mb-6">
          <div className="flex items-center gap-3">
            <span
              className="font-mono text-xl sm:text-2xl font-bold px-3 py-1 rounded border"
              style={{
                color: tier.color,
                borderColor: `${tier.color}60`,
                backgroundColor: `${tier.color}15`,
              }}
            >
              {tier.level}
            </span>
            <div>
              <span className="font-mono text-[10px] uppercase tracking-wider block" style={{ color: tier.color }}>
                {lang === 'en' ? tier.badgeEn : tier.badgeHi}
              </span>
              <h3 className="font-sans text-base sm:text-lg font-bold text-text">
                {lang === 'en' ? tier.titleEn : tier.titleHi}
              </h3>
            </div>
          </div>

          {/* Orbit-Ring Graphic (rings = strength of evidence) */}
          <div className="w-16 h-16 relative flex items-center justify-center">
            <svg viewBox="0 0 80 80" className="w-full h-full" fill="none">
              {/* Outer rings based on evidence tier count */}
              {Array.from({ length: 4 }).map((_, i) => {
                const r = 36 - i * 8;
                const isPresent = i < tier.rings;
                return (
                  <circle
                    key={i}
                    cx="40"
                    cy="40"
                    r={r}
                    stroke={isPresent ? tier.color : '#12254A'}
                    strokeWidth={isPresent ? '1.5' : '1'}
                    strokeOpacity={isPresent ? 0.9 - i * 0.15 : 0.3}
                    strokeDasharray={isPresent && i === tier.rings - 1 && tier.rings < 4 ? '3 3' : 'none'}
                  />
                );
              })}
              {/* Center evidence core */}
              <circle cx="40" cy="40" r="5" fill={tier.color} />
            </svg>
          </div>
        </div>

        {/* Verdict Badge */}
        <div className="mb-4">
          <span
            className="inline-flex items-center gap-2 font-mono text-xs px-3 py-1 rounded-full font-semibold border"
            style={{
              borderColor: `${tier.color}60`,
              color: tier.color,
              backgroundColor: `${tier.color}15`,
            }}
          >
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: tier.color }} />
            {lang === 'en' ? tier.verdictNameEn : tier.verdictNameHi}
          </span>
        </div>

        {/* Evidence Description */}
        <p className="text-xs sm:text-sm text-muted font-sans leading-relaxed">
          {lang === 'en' ? tier.evidenceEn : tier.evidenceHi}
        </p>
      </div>

      {/* Footer Note */}
      <div className="mt-6 pt-4 border-t border-surface/40 flex items-center justify-between text-[11px] font-mono text-muted/80">
        <span>{lang === 'en' ? tier.noteEn : tier.noteHi}</span>
        <span style={{ color: tier.color }}>{tier.rings}/4 RINGS</span>
      </div>
    </div>
  );
};
