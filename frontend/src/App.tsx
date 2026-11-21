import { useEffect, useState } from 'react';
import { initScroll } from './lib/scroll';
import { useReveals } from './hooks/useReveals';
import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { ProblemSection } from './components/ProblemSection';
import { PipelineSection } from './components/PipelineSection';
import { VerifyChamber } from './components/VerifyChamber';
import { LadderSection } from './components/LadderSection';
import { DoorsSection } from './components/DoorsSection';

export default function App() {
  const [lang, setLang] = useState<'en' | 'hi'>('en');

  useEffect(() => {
    const cleanupScroll = initScroll();
    return () => cleanupScroll();
  }, []);

  useReveals();

  const handleToggleLang = () => {
    setLang((prev) => (prev === 'en' ? 'hi' : 'en'));
  };

  return (
    <div className="relative min-h-screen bg-void text-text selection:bg-accent/20 selection:text-accent font-sans">
      <Header lang={lang} onToggleLang={handleToggleLang} />

      <main>
        {/* Section #top: The Hero (Open the Eye) */}
        <Hero lang={lang} />

        {/* Section #problem: The Forward Chain (Horizontal Reel) */}
        <ProblemSection lang={lang} />

        {/* Section #pipeline: Three Eyes, One Verdict (Inking SVG Pipeline) */}
        <PipelineSection lang={lang} />

        {/* Section #verify: Interactive Provenance Verification Chamber */}
        <VerifyChamber lang={lang} />

        {/* Section #ladder: The Confirmation Ladder (L1 to L4 3D Tilt Cards) */}
        <LadderSection lang={lang} />

        {/* Section #doors: Universal Distribution & Honest Limits */}
        <DoorsSection lang={lang} />
      </main>
    </div>
  );
}
