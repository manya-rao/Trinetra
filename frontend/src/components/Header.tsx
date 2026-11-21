import React, { useState } from 'react';
import { scrollToHash } from '../lib/scroll';

interface HeaderProps {
  lang: 'en' | 'hi';
  onToggleLang: () => void;
}

export const Header: React.FC<HeaderProps> = ({ lang, onToggleLang }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { id: '#problem', label: lang === 'en' ? 'Problem' : 'समस्या' },
    { id: '#pipeline', label: lang === 'en' ? 'Pipeline' : 'पाइपलाइन' },
    { id: '#verify', label: lang === 'en' ? 'Verify' : 'जाँचें' },
    { id: '#ladder', label: lang === 'en' ? 'Ladder' : 'प्रमाण सीढ़ी' },
    { id: '#doors', label: lang === 'en' ? 'Doors' : 'प्लेटफ़ॉर्म' },
  ];

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, hash: string) => {
    e.preventDefault();
    scrollToHash(hash);
    setMobileMenuOpen(false);
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-void/80 backdrop-blur-md border-b border-surface/60 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Crescent-free mark: Three-Eye logo + TRINETRA wordmark */}
        <a
          href="#top"
          onClick={(e) => handleNavClick(e, '#top')}
          className="flex items-center gap-3 group focus:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-md py-1 px-1.5"
          aria-label="Trinetra Home"
        >
          {/* Three Eyes SVG mark */}
          <div className="relative w-9 h-6 flex items-center justify-center">
            <svg viewBox="0 0 44 24" className="w-full h-full" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Connecting baseline */}
              <line x1="6" y1="12" x2="38" y2="12" stroke="#19D3C5" strokeWidth="1" strokeOpacity="0.4" strokeDasharray="2 2" />
              
              {/* Eye 1 (Left - Origin) */}
              <circle cx="9" cy="12" r="5" stroke="#19D3C5" strokeWidth="1.2" strokeOpacity="0.8" />
              <circle cx="9" cy="12" r="2" fill="#19D3C5" />
              
              {/* Eye 2 (Centre - Change, larger & raised) */}
              <path d="M 16 9 Q 22 2 28 9 Q 22 16 16 9 Z" stroke="#19D3C5" strokeWidth="1.4" fill="#0B1B3A" />
              <circle cx="22" cy="9" r="2.5" fill="#19D3C5" />
              
              {/* Eye 3 (Right - Synthesis) */}
              <circle cx="35" cy="12" r="5" stroke="#19D3C5" strokeWidth="1.2" strokeOpacity="0.8" />
              <circle cx="35" cy="12" r="2" fill="#19D3C5" />
            </svg>
          </div>

          <div className="flex flex-col">
            <span className="font-display tracking-[0.22em] text-base font-semibold text-text group-hover:text-accent transition-colors">
              TRINETRA
            </span>
            <span className="font-mono text-[9px] uppercase tracking-wider text-muted -mt-0.5">
              TEAM KINETIX
            </span>
          </div>
        </a>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-6" aria-label="Main Navigation">
          {navLinks.map((link) => (
            <a
              key={link.id}
              href={link.id}
              onClick={(e) => handleNavClick(e, link.id)}
              className="text-sm font-sans text-muted hover:text-text hover:border-b-2 hover:border-accent pb-0.5 transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-accent rounded-sm"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Right Actions: Lang Toggle + CTA */}
        <div className="flex items-center gap-3">
          {/* Language Toggle */}
          <button
            type="button"
            onClick={onToggleLang}
            className="flex items-center gap-1 text-xs font-mono px-2.5 py-1.5 rounded border border-surface bg-void-2 hover:border-accent/60 text-muted hover:text-text transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            aria-label={`Switch language. Current: ${lang === 'en' ? 'English' : 'Hindi'}`}
          >
            <span className={lang === 'en' ? 'text-accent font-semibold' : ''}>EN</span>
            <span className="text-surface">|</span>
            <span className={lang === 'hi' ? 'text-accent font-semibold font-hindi' : 'font-hindi'}>हिं</span>
          </button>

          {/* Verify an image CTA */}
          <button
            type="button"
            onClick={() => scrollToHash('#verify')}
            className="hidden sm:inline-flex items-center gap-2 bg-accent/10 border border-accent/60 hover:bg-accent/20 hover:border-accent text-accent text-xs font-mono tracking-wider uppercase px-3.5 py-2 rounded transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
            {lang === 'en' ? 'Verify Image' : 'छवि जाँचें'}
          </button>

          {/* Mobile Menu Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded text-muted hover:text-text hover:bg-surface focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-surface bg-void-2/95 backdrop-blur-lg px-4 pt-2 pb-6 space-y-3">
          <nav className="flex flex-col space-y-2">
            {navLinks.map((link) => (
              <a
                key={link.id}
                href={link.id}
                onClick={(e) => handleNavClick(e, link.id)}
                className="text-base font-sans text-muted hover:text-accent px-3 py-2 rounded-md hover:bg-surface/50 transition-colors"
              >
                {link.label}
              </a>
            ))}
            <button
              type="button"
              onClick={() => {
                scrollToHash('#verify');
                setMobileMenuOpen(false);
              }}
              className="w-full mt-2 inline-flex justify-center items-center gap-2 bg-accent/15 border border-accent text-accent text-sm font-mono tracking-wider uppercase px-4 py-2.5 rounded"
            >
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
              {lang === 'en' ? 'Verify an Image' : 'छवि जाँचें'}
            </button>
          </nav>
        </div>
      )}
    </header>
  );
};
