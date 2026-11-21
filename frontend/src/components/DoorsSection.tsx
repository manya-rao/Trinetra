import React from 'react';

interface DoorsSectionProps {
  lang: 'en' | 'hi';
}

interface DoorCard {
  id: string;
  badge: string;
  titleEn: string;
  titleHi: string;
  descEn: string;
  descHi: string;
  availability: string;
  iconSvg: () => React.ReactNode;
}

export const DoorsSection: React.FC<DoorsSectionProps> = ({ lang }) => {
  const doors: DoorCard[] = [
    {
      id: 'pwa',
      badge: 'INTEGRATED PWA',
      titleEn: 'System Share Target',
      titleHi: 'सिस्टम शेयर टार्गेट (PWA)',
      descEn:
        'Install Trinetra directly onto Android or desktop. Share any image directly from WhatsApp, Telegram, or gallery straight into Trinetra for an instant Passport.',
      descHi:
        'सीधे एंड्रॉइड या डेस्कटॉप पर इंस्टॉल करें। व्हाट्सएप, टेलीग्राम या गैलरी से सीधे शेयर कर तुरंत प्रोवेनेंस पासपोर्ट प्राप्त करें।',
      availability: 'PRODUCTION READY',
      iconSvg: () => (
        <svg viewBox="0 0 48 48" className="w-8 h-8 stroke-accent" fill="none">
          <rect x="12" y="6" width="24" height="36" rx="4" strokeWidth="2" />
          <line x1="20" y1="36" x2="28" y2="36" strokeWidth="2" strokeLinecap="round" />
          <path d="M 24 16 L 24 26 M 20 20 L 24 16 L 28 20" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
    },
    {
      id: 'telegram',
      badge: 'PROOF OF CONCEPT',
      titleEn: 'Telegram Verification Bot',
      titleHi: 'टेलीग्राम सत्यापन बॉट',
      descEn:
        'Forward any suspect media in group chats or DM to @TrinetraVerifyBot. Runs the exact same Three Eyes pipeline and replies with summary and card image.',
      descHi:
        'ग्रुप चैट या निजी संदेश में किसी भी संदिग्ध मीडिया को फॉरवर्ड करें। वही त्रिनेत्र पाइपलाइन चलाकर कार्ड व सारांश के साथ उत्तर देता है।',
      availability: 'POC WORKING · WA FUTURE SCOPE',
      iconSvg: () => (
        <svg viewBox="0 0 48 48" className="w-8 h-8 stroke-accent" fill="none">
          <circle cx="24" cy="24" r="18" strokeWidth="2" />
          <path d="M 14 24 L 34 16 L 28 32 L 23 26 L 19 28 Z" strokeWidth="2" strokeLinejoin="round" />
        </svg>
      ),
    },
    {
      id: 'extension',
      badge: 'ON DEMAND',
      titleEn: 'Chrome Forensic Extension',
      titleHi: 'क्रोम फोरेंसिक एक्सटेंशन',
      descEn:
        'Right-click any web photo on Twitter, Reddit, or news feeds -> "Inspect with Trinetra". Overlays the provenance passport without leaving your tab.',
      descHi:
        'ट्विटर, रेडिट या समाचार पृष्ठों पर किसी भी तस्वीर पर राइट-क्लिक करें -> "त्रिनेत्र से जांचें"। उसी टैब में पासपोर्ट प्रदर्शित करता है।',
      availability: 'CHROME MANIFEST V3',
      iconSvg: () => (
        <svg viewBox="0 0 48 48" className="w-8 h-8 stroke-accent" fill="none">
          <circle cx="24" cy="24" r="18" strokeWidth="2" />
          <circle cx="24" cy="24" r="7" strokeWidth="2" />
          <line x1="24" y1="6" x2="24" y2="17" strokeWidth="2" />
          <line x1="10" y1="31" x2="19" y2="26" strokeWidth="2" />
          <line x1="38" y1="31" x2="29" y2="26" strokeWidth="2" />
        </svg>
      ),
    },
    {
      id: 'ios_shortcut',
      badge: 'SHARE SHEET',
      titleEn: 'iOS Shortcut & Mobile Web',
      titleHi: 'आईओएस शॉर्टकट एवं मोबाइल वेब',
      descEn:
        'Add to iOS Share Sheet via Siri Shortcut or use standalone Safari PWA. Direct image paste and camera roll integration with full privacy sandbox.',
      descHi:
        'सिरी शॉर्टकट द्वारा आईओएस शेयर शीट में जोड़ें या सफारी PWA उपयोग करें। पूर्ण गोपनीयता के साथ सीधा पेस्ट और कैमरा रोल समर्थन।',
      availability: 'STANDALONE WEB + SHORTCUT',
      iconSvg: () => (
        <svg viewBox="0 0 48 48" className="w-8 h-8 stroke-accent" fill="none">
          <rect x="8" y="10" width="32" height="28" rx="6" strokeWidth="2" />
          <circle cx="24" cy="24" r="5" strokeWidth="2" />
          <path d="M 14 16 L 18 16" strokeWidth="2" strokeLinecap="round" />
        </svg>
      ),
    },
  ];

  return (
    <section
      id="doors"
      className="relative w-full py-24 px-4 sm:px-8 bg-void border-t border-surface/50"
      aria-label="One Engine, Many Doors - Platform Distribution"
    >
      <div className="max-w-7xl mx-auto space-y-16">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-3" data-reveal>
          <span className="font-mono text-xs text-accent tracking-widest uppercase block">
            {lang === 'en' ? '04 // Universal Accessibility' : '०४ // सार्वभौमिक पहुंच'}
          </span>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-text">
            {lang === 'en' ? 'One engine, many doors.' : 'एक इंजन, अनेक द्वार।'}
          </h2>
          <p className="text-sm sm:text-base text-muted font-sans leading-relaxed">
            {lang === 'en'
              ? 'Misinformation travels through chat apps, social feeds, and mobile browsers. Trinetra meets users where they already are, without requiring app store friction.'
              : 'दुष्प्रचार चैट ऐप्स, सोशल मीडिया और मोबाइल ब्राउज़र के माध्यम से फैलता है। त्रिनेत्र उपयोगकर्ताओं तक वहीं पहुंचता है जहाँ वे पहले से मौजूद हैं।'}
          </p>
        </div>

        {/* Four Doors Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {doors.map((door) => (
            <div
              key={door.id}
              data-reveal
              className="rounded-xl border border-surface bg-void-2/80 backdrop-blur-md p-6 flex flex-col justify-between hover:border-accent/60 transition-all duration-300 group shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-surface/60 mb-4">
                  <span className="font-mono text-[9px] tracking-wider text-accent border border-accent/40 bg-accent/10 px-2 py-0.5 rounded">
                    {door.badge}
                  </span>
                  <div className="p-1 rounded bg-surface/50 group-hover:bg-accent/10 transition-colors">
                    {door.iconSvg()}
                  </div>
                </div>

                <h3 className="font-sans text-base font-bold text-text group-hover:text-accent transition-colors">
                  {lang === 'en' ? door.titleEn : door.titleHi}
                </h3>
                <p className="mt-2 text-xs text-muted font-sans leading-relaxed">
                  {lang === 'en' ? door.descEn : door.descHi}
                </p>
              </div>

              <div className="mt-6 pt-3 border-t border-surface/40 font-mono text-[10px] text-muted/70 flex items-center justify-between">
                <span>{door.availability}</span>
                <span className="w-1.5 h-1.5 rounded-full bg-accent" />
              </div>
            </div>
          ))}
        </div>

        {/* Honest Limits Panel */}
        <div
          data-reveal
          className="rounded-2xl border border-surface/90 bg-void-2/90 backdrop-blur-md p-6 sm:p-8 max-w-4xl mx-auto shadow-2xl space-y-4"
        >
          <div className="flex items-center gap-3 border-b border-surface/60 pb-3">
            <span className="text-amber-400 font-mono text-base">⚠</span>
            <h3 className="font-display text-base sm:text-lg font-semibold text-text tracking-wide">
              {lang === 'en' ? 'Honest Forensic Limitations' : 'फोरेंसिक प्रणाली की ईमानदार सीमाएँ'}
            </h3>
            <span className="ml-auto font-mono text-[10px] text-muted border border-surface px-2 py-0.5 rounded">
              TRANSPARENCY REPORT
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans text-muted leading-relaxed">
            <div className="p-3.5 rounded-lg border border-surface/60 bg-void/60 space-y-1.5">
              <span className="font-mono text-[11px] text-accent block font-semibold">
                1. CURATED FACT-CHECK INDEX
              </span>
              <p>
                {lang === 'en'
                  ? 'Eye 1 (Origin) matches against a small curated reference index of known debunked records, NEVER claiming to search the entire internet.'
                  : 'आई १ (ओरिजिन) केवल सत्यापित संदर्भ इंडेक्स से मिलान करती है, कभी भी संपूर्ण इंटरनेट खोजने का झूठा दावा नहीं करती।'}
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-surface/60 bg-void/60 space-y-1.5">
              <span className="font-mono text-[11px] text-amber-400 block font-semibold">
                2. COMPRESSION & NOVEL GENERATORS
              </span>
              <p>
                {lang === 'en'
                  ? 'Heavy compression (WhatsApp JPEG Q ≤ 75) destroys high frequencies. Held-out novel generators (Flux at 1.50% detection from benchmark ml/RESULTS.md) are honestly routed to Inconclusive.'
                  : 'अत्यधिक कम्प्रेशन (JPEG Q ≤ 75) फ़्रीक्वेंसी विवरण नष्ट कर देता है। अज्ञात जनरेटर (Flux पर 1.50% पहचान दर) को ईमानदारी से अनिर्णायक में भेजा जाता है।'}
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-surface/60 bg-void/60 space-y-1.5">
              <span className="font-mono text-[11px] text-orange-400 block font-semibold">
                3. ABSTAIN RATHER THAN GUESS
              </span>
              <p>
                {lang === 'en'
                  ? 'Eye 3 ships ONLY as likely_ai or inconclusive. Quiet signals read "No AI signs found, not proof". The system never outputs a positive authenticity claim.'
                  : 'आई ३ केवल likely_ai या अनिर्णायक निर्णय देती है। शांत संकेत "कोई एआई संकेत नहीं (प्रमाण नहीं)" दर्शाते हैं, कभी झूठी पुष्टि नहीं करते।'}
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-surface/60 bg-void/60 space-y-1.5">
              <span className="font-mono text-[11px] text-green-400 block font-semibold">
                4. ZERO PASSIVE SURVEILLANCE
              </span>
              <p>
                {lang === 'en'
                  ? 'Trinetra never auto-scans private chats or backgrounds. All evaluations are explicitly initiated by the user on a specific suspicious image.'
                  : 'त्रिनेत्र कभी भी निजी चैट को स्वतः स्कैन नहीं करता। सभी विश्लेषण उपयोगकर्ता द्वारा किसी विशेष संदिग्ध छवि पर स्वेच्छा से किए जाते हैं।'}
              </p>
            </div>
          </div>
        </div>

        {/* Global Footer */}
        <footer className="pt-12 border-t border-surface/50 text-center font-mono text-xs text-muted/70 space-y-2">
          <p className="text-text font-semibold tracking-wider">
            Trinetra: Digital Trust &amp; Cybersecurity · Kinetix · Code for Innovex &apos;26
          </p>
          <p className="text-[11px]">
            Theme: Navyug — A New Era · Track: Misinformation &amp; Provenance
          </p>
        </footer>
      </div>
    </section>
  );
};
