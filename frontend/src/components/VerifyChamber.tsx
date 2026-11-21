import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Passport,
  analyzeImage,
  getMockFixture,
  getAvailableMocks,
  config,
  setMockMode,
} from '../api/client';
import {
  getVerdictStrings,
  getConfidenceBand,
  getReasonText,
  getEyeStatus,
  getUIStrings,
  getErrorStrings,
} from '../content';
import { ComparisonSlider } from './ComparisonSlider';
import { ConsentModal } from './ConsentModal';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface VerifyChamberProps {
  lang: 'en' | 'hi';
}

type Stage = 'idle' | 'analyzing' | 'passport';

export const VerifyChamber: React.FC<VerifyChamberProps> = ({ lang }) => {
  const [stage, setStage] = useState<Stage>('idle');
  const [passport, setPassport] = useState<Passport | null>(null);
  const [userImageUrl, setUserImageUrl] = useState<string | null>(null);
  const [hashOnly, setHashOnly] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [analyzingStep, setAnalyzingStep] = useState<number>(1);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [consentTarget, setConsentTarget] = useState<{ url: string; provider: string } | null>(null);
  const [isLiveApi, setIsLiveApi] = useState<boolean>(!config.useMock);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const dropZoneRef = useRef<HTMLDivElement | null>(null);
  const activeObjectUrlRef = useRef<string | null>(null);

  const reducedMotion = useReducedMotion();
  const ui = getUIStrings(lang);

  // Clean up object URLs to protect privacy and prevent memory leaks
  const cleanupUserImage = useCallback(() => {
    if (activeObjectUrlRef.current) {
      URL.revokeObjectURL(activeObjectUrlRef.current);
      activeObjectUrlRef.current = null;
    }
    setUserImageUrl(null);
  }, []);

  useEffect(() => {
    return () => {
      cleanupUserImage();
    };
  }, [cleanupUserImage]);

  // Handle Mock vs Real API toggle
  const toggleApiMode = (useReal: boolean) => {
    setMockMode(!useReal);
    setIsLiveApi(useReal);
  };

  // Analyzing step progression (does not fake completion; keeps looping or holding at step 3 until promise resolves)
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    if (stage === 'analyzing') {
      setAnalyzingStep(1);
      interval = setInterval(() => {
        setAnalyzingStep((prev) => (prev < 3 ? prev + 1 : 3));
      }, 700);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [stage]);

  // Image validation and upload dispatch
  const handleProcessFile = async (file: File) => {
    setErrorMsg(null);

    // Validate type
    if (!file.type.startsWith('image/')) {
      setErrorMsg(getErrorStrings('invalid_file', lang));
      return;
    }

    // Validate size (max 20MB)
    if (file.size > 20 * 1024 * 1024) {
      setErrorMsg(getErrorStrings('image_too_large', lang));
      return;
    }

    // Create temporary object URL for local display (never persisted)
    cleanupUserImage();
    const objUrl = URL.createObjectURL(file);
    activeObjectUrlRef.current = objUrl;
    setUserImageUrl(objUrl);

    setStage('analyzing');

    try {
      const result = await analyzeImage(file, {
        lang,
        hashOnly,
      });
      setPassport(result);
      setStage('passport');
    } catch (err: unknown) {
      const errorText = err instanceof Error ? err.message : String(err);
      console.warn('Analysis execution error:', errorText);
      setErrorMsg(
        `${getErrorStrings('network', lang)} (Backend offline or unreachable. You can test all 7 verdicts using the demo buttons below).`
      );
      setStage('idle');
    }
  };

  // Demo fixture loader
  const handleLoadDemo = (verdictKey: string) => {
    cleanupUserImage();
    setErrorMsg(null);
    const mock = getMockFixture(verdictKey);
    setPassport(mock);
    setStage('passport');
  };

  // Reset to idle
  const handleReset = () => {
    cleanupUserImage();
    setPassport(null);
    setErrorMsg(null);
    setStage('idle');
  };

  // Clipboard summary generator
  const handleCopySummary = async () => {
    if (!passport) return;
    const verdictInfo = getVerdictStrings(passport.verdict, lang);
    const summary = [
      `--- TRINETRA PROVENANCE PASSPORT ---`,
      `ID: ${passport.id}`,
      `Verdict: ${verdictInfo.headline} (${passport.verdict})`,
      `Confidence: ${getConfidenceBand(passport.confidence_band, lang)}`,
      `Eye 1 (Origin): ${passport.eyes.origin}`,
      `Eye 2 (Change): ${passport.eyes.change}`,
      `Eye 3 (Synthesis): ${passport.eyes.synthesis}`,
      passport.origin ? `Origin Match: ${passport.origin.source} (${passport.origin.date})` : `Origin: No known match in curated index`,
      `Scope: ${passport.scope_note[lang] || passport.scope_note.en}`,
      `Verified via Trinetra · Team Kinetix · Code for Innovex '26`,
    ].join('\n');

    try {
      await navigator.clipboard.writeText(summary);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2500);
    } catch {
      // Fallback
    }
  };

  // Web Share or card download
  const handleShareCard = async () => {
    if (!passport) return;
    const cardUrl = `/passport/${passport.id}/card.png?lang=${lang}`;
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Trinetra Passport: ${passport.id}`,
          text: `Provenance Passport verified by Trinetra: ${passport.verdict}`,
          url: cardUrl,
        });
        return;
      } catch {
        // user cancelled or share failed, fallback
      }
    }
    window.open(cardUrl, '_blank');
  };

  // Paste handling on window
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (stage !== 'idle') return;
      const items = e.clipboardData?.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith('image/')) {
          const file = items[i].getAsFile();
          if (file) {
            handleProcessFile(file);
            break;
          }
        }
      }
    };
    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [stage, lang, hashOnly]);

  return (
    <section
      id="verify"
      className="relative w-full py-20 px-4 sm:px-8 bg-void border-t border-surface/50"
      aria-label="Trinetra Verification Chamber"
    >
      <div className="max-w-5xl mx-auto space-y-10">
        {/* Section Header */}
        <div className="text-center space-y-3" data-reveal>
          <div className="inline-flex items-center gap-2 border border-accent/40 bg-void-2 px-3 py-1 rounded-full text-xs font-mono text-accent">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            <span>LIVE FORENSIC CHAMBER</span>
          </div>
          <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-text">
            {lang === 'en' ? 'Verify Image Provenance' : 'छवि प्रामाणिकता जांचें'}
          </h2>
          <p className="text-sm text-muted font-sans max-w-2xl mx-auto">
            {ui.appTagline}
          </p>

          {/* Real vs Mock API Switch */}
          <div className="pt-2 flex items-center justify-center gap-4 text-xs font-mono">
            <span className="text-muted">API Engine:</span>
            <button
              type="button"
              onClick={() => toggleApiMode(false)}
              className={`px-3 py-1 rounded border transition-colors ${
                !isLiveApi ? 'border-accent bg-accent/20 text-accent font-semibold' : 'border-surface bg-void-2 text-muted'
              }`}
            >
              Client Fixtures (Mock)
            </button>
            <button
              type="button"
              onClick={() => toggleApiMode(true)}
              className={`px-3 py-1 rounded border transition-colors ${
                isLiveApi ? 'border-accent bg-accent/20 text-accent font-semibold' : 'border-surface bg-void-2 text-muted'
              }`}
            >
              Real Backend (localhost:8000)
            </button>
          </div>
        </div>

        {/* Demo Result Switcher Row (Always Available) */}
        <div className="rounded-xl border border-surface bg-void-2/60 p-4 space-y-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-muted">
            <span className="text-accent font-semibold">
              {lang === 'en' ? 'TRY A PRE-COMPUTED SCENARIO (7 VERDICTS):' : 'पूर्वनिर्धारित परीक्षण परिणाम (७ निर्णय):'}
            </span>
            <span className="text-[10px] bg-void border border-surface px-2 py-0.5 rounded">
              PROTOTYPE · DEMO DATA
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {getAvailableMocks().map((mockKey) => {
              const vInfo = getVerdictStrings(mockKey, lang);
              const isActive = passport && passport.verdict === mockKey;
              return (
                <button
                  key={mockKey}
                  type="button"
                  onClick={() => handleLoadDemo(mockKey)}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-mono transition-all flex items-center gap-1.5 ${
                    isActive
                      ? 'border-accent bg-accent/20 text-text font-semibold ring-1 ring-accent'
                      : 'border-surface bg-void hover:border-accent/40 text-muted hover:text-text'
                  }`}
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{
                      backgroundColor:
                        vInfo.color === 'green'
                          ? '#10B981'
                          : vInfo.color === 'amber'
                          ? '#F59E0B'
                          : vInfo.color === 'red'
                          ? '#EF4444'
                          : vInfo.color === 'orange'
                          ? '#F97316'
                          : '#64748B',
                    }}
                  />
                  <span>{vInfo.headline}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Error Notification */}
        {errorMsg && (
          <div
            role="alert"
            className="rounded-xl border border-red-500/50 bg-red-500/10 p-4 text-xs font-mono text-red-200 flex items-start gap-3"
          >
            <span className="text-base">⚠</span>
            <div className="flex-1 leading-relaxed">{errorMsg}</div>
            <button
              type="button"
              onClick={() => setErrorMsg(null)}
              className="text-red-400 hover:text-red-200 font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {/* STATE 1: IDLE DROPZONE */}
        {stage === 'idle' && (
          <div className="space-y-6">
            <div
              ref={dropZoneRef}
              tabIndex={0}
              role="button"
              aria-label={ui.dropZoneTitle}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  fileInputRef.current?.click();
                }
              }}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragOver(false);
                const droppedFiles = e.dataTransfer.files;
                if (droppedFiles && droppedFiles.length > 0) {
                  handleProcessFile(droppedFiles[0]);
                }
              }}
              className={`relative rounded-2xl border-2 border-dashed p-10 sm:p-14 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent ${
                isDragOver
                  ? 'border-accent bg-accent/10 scale-[1.01]'
                  : 'border-surface hover:border-accent/60 bg-void-2/60 hover:bg-void-2'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleProcessFile(e.target.files[0]);
                  }
                }}
              />

              {/* Forensic Aperture Mark */}
              <div className="w-16 h-16 rounded-full border border-accent/40 bg-void flex items-center justify-center mb-4 text-accent">
                <svg viewBox="0 0 24 24" className="w-8 h-8 stroke-current" fill="none">
                  <path d="M 4 16 L 4 20 L 8 20" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M 20 16 L 20 20 L 16 20" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M 4 8 L 4 4 L 8 4" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M 20 8 L 20 4 L 16 4" strokeWidth="1.5" strokeLinecap="round" />
                  <circle cx="12" cy="12" r="3" strokeWidth="1.5" />
                  <line x1="12" y1="5" x2="12" y2="7" strokeWidth="1.5" />
                  <line x1="12" y1="17" x2="12" y2="19" strokeWidth="1.5" />
                </svg>
              </div>

              <h3 className="font-display text-lg sm:text-xl font-bold text-text mb-1">
                {ui.dropZoneTitle}
              </h3>
              <p className="text-xs sm:text-sm text-muted font-sans max-w-md">
                {ui.dropZoneSub}
              </p>

              <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-xs font-mono text-muted/70">
                <span className="px-2.5 py-1 rounded bg-void border border-surface">{ui.pasteHint}</span>
                <span>&bull;</span>
                <span className="px-2.5 py-1 rounded bg-void border border-surface">JPEG · PNG · WEBP (≤ 20MB)</span>
              </div>
            </div>

            {/* Privacy Controls & Android / WhatsApp Hint */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl border border-surface bg-void-2/40 text-xs font-mono">
              <label className="flex items-center gap-2 cursor-pointer text-muted hover:text-text select-none">
                <input
                  type="checkbox"
                  checked={hashOnly}
                  onChange={(e) => setHashOnly(e.target.checked)}
                  className="rounded border-surface text-accent focus:ring-accent bg-void w-4 h-4"
                />
                <span>{ui.privacyHashOnly}</span>
              </label>

              <div className="text-[11px] text-accent/80 font-sans">
                {ui.shareWhatsappHint}
              </div>
            </div>

            <p className="text-[11px] text-muted/60 text-center font-mono">
              {ui.privacyDisclaimer}
            </p>
          </div>
        )}

        {/* STATE 2: ANALYZING PROGRESS */}
        {stage === 'analyzing' && (
          <div
            role="status"
            aria-live="polite"
            className="rounded-2xl border border-surface bg-void-2 p-10 sm:p-14 flex flex-col items-center justify-center text-center space-y-8 shadow-2xl"
          >
            {/* Sequential Three Eyes Light-up Animation */}
            <div className="flex items-center gap-6 sm:gap-10">
              {/* Eye 1 */}
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`w-14 h-14 sm:w-16 sm:h-16 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${
                    analyzingStep >= 1
                      ? 'border-accent bg-accent/20 text-accent shadow-[0_0_20px_#19D3C5]'
                      : 'border-surface bg-void text-muted/40'
                  }`}
                >
                  <span className="font-mono text-sm font-bold">01</span>
                </div>
                <span className="font-mono text-[11px] text-muted">ORIGIN</span>
              </div>

              {/* Link Line */}
              <div className={`w-8 sm:w-12 h-0.5 ${analyzingStep >= 2 ? 'bg-accent' : 'bg-surface'}`} />

              {/* Eye 2 */}
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`w-14 h-14 sm:w-16 sm:h-16 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${
                    analyzingStep >= 2
                      ? 'border-amber-400 bg-amber-400/20 text-amber-300 shadow-[0_0_20px_#F59E0B]'
                      : 'border-surface bg-void text-muted/40'
                  }`}
                >
                  <span className="font-mono text-sm font-bold">02</span>
                </div>
                <span className="font-mono text-[11px] text-muted">CHANGE</span>
              </div>

              {/* Link Line */}
              <div className={`w-8 sm:w-12 h-0.5 ${analyzingStep >= 3 ? 'bg-orange-500' : 'bg-surface'}`} />

              {/* Eye 3 */}
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`w-14 h-14 sm:w-16 sm:h-16 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${
                    analyzingStep >= 3
                      ? 'border-orange-500 bg-orange-500/20 text-orange-400 shadow-[0_0_20px_#F97316]'
                      : 'border-surface bg-void text-muted/40'
                  }`}
                >
                  <span className="font-mono text-sm font-bold">03</span>
                </div>
                <span className="font-mono text-[11px] text-muted">SYNTHESIS</span>
              </div>
            </div>

            {/* Current Analysis Step Description */}
            <div className="space-y-2 max-w-md">
              <h3 className="font-display text-lg font-bold text-text">
                {ui.analyzingTitle}
              </h3>
              <p className="font-mono text-xs text-accent">
                {analyzingStep === 1 && ui.analyzingEye1}
                {analyzingStep === 2 && ui.analyzingEye2}
                {analyzingStep === 3 && ui.analyzingEye3}
              </p>
            </div>

            {!reducedMotion && (
              <div className="w-48 h-1 bg-surface rounded-full overflow-hidden">
                <div className="h-full bg-accent animate-pulse w-full" />
              </div>
            )}
          </div>
        )}

        {/* STATE 3: PROVENANCE PASSPORT VIEW */}
        {stage === 'passport' && passport && (
          <div className="rounded-2xl border border-surface bg-void-2/95 shadow-2xl p-6 sm:p-10 space-y-8">
            {/* Header / ID & Badges */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-surface/60">
              <div className="flex items-center gap-3">
                <span className="font-display text-lg font-bold text-text tracking-wide">
                  PROVENANCE PASSPORT
                </span>
                <span className="font-mono text-xs text-muted border border-surface px-2 py-0.5 rounded bg-void">
                  {passport.id}
                </span>
              </div>

              <div className="flex items-center gap-2 font-mono text-[11px]">
                {passport.demo_data && (
                  <span className="px-2.5 py-0.5 rounded border border-amber-500/40 bg-amber-500/15 text-amber-300 font-semibold">
                    DEMO DATA
                  </span>
                )}
                {!isLiveApi && (
                  <span className="px-2.5 py-0.5 rounded border border-accent/40 bg-accent/15 text-accent">
                    PROTOTYPE - MOCK DATA
                  </span>
                )}
              </div>
            </div>

            {/* 1. Verdict Banner */}
            {(() => {
              const vInfo = getVerdictStrings(passport.verdict, lang);
              const colorMap: Record<string, { bg: string; border: string; text: string }> = {
                green: { bg: 'bg-emerald-500/15', border: 'border-emerald-500/50', text: 'text-emerald-400' },
                amber: { bg: 'bg-amber-500/15', border: 'border-amber-500/50', text: 'text-amber-400' },
                red: { bg: 'bg-red-500/15', border: 'border-red-500/50', text: 'text-red-400' },
                orange: { bg: 'bg-orange-500/15', border: 'border-orange-500/50', text: 'text-orange-400' },
                'grey-blue': { bg: 'bg-slate-500/15', border: 'border-slate-500/50', text: 'text-slate-400' },
                teal: { bg: 'bg-teal-500/15', border: 'border-teal-500/50', text: 'text-teal-400' },
              };
              const c = colorMap[vInfo.color] || colorMap['grey-blue'];

              return (
                <div className={`rounded-xl border p-5 sm:p-6 space-y-2 ${c.bg} ${c.border}`}>
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <span className={`w-3 h-3 rounded-full ${c.text.replace('text-', 'bg-')}`} />
                      <h3 className={`font-display text-xl sm:text-2xl font-bold tracking-tight ${c.text}`}>
                        {vInfo.headline}
                      </h3>
                    </div>
                    <span className="font-mono text-xs text-muted border border-surface px-2 py-0.5 rounded bg-void/80">
                      {getConfidenceBand(passport.confidence_band, lang)}
                    </span>
                  </div>
                  <p className="text-xs sm:text-sm text-text/90 font-sans leading-relaxed">
                    {vInfo.detail}
                  </p>
                </div>
              );
            })()}

            {/* 2. Three Eyes Status Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Eye 1 */}
              {(() => {
                const eye1 = getEyeStatus('eye1', passport.eyes.origin, lang);
                return (
                  <div className="p-4 rounded-xl border border-surface bg-void space-y-1">
                    <span className="font-mono text-[10px] text-accent tracking-wider uppercase block">
                      {eye1.name}
                    </span>
                    <div className="font-sans text-sm font-bold text-text">
                      {eye1.statusText}
                    </div>
                    <p className="text-[11px] text-muted font-sans">{eye1.subtitle}</p>
                  </div>
                );
              })()}

              {/* Eye 2 */}
              {(() => {
                const eye2 = getEyeStatus('eye2', passport.eyes.change, lang);
                return (
                  <div className="p-4 rounded-xl border border-surface bg-void space-y-1">
                    <span className="font-mono text-[10px] text-amber-400 tracking-wider uppercase block">
                      {eye2.name}
                    </span>
                    <div className="font-sans text-sm font-bold text-text">
                      {eye2.statusText}
                    </div>
                    <p className="text-[11px] text-muted font-sans">{eye2.subtitle}</p>
                  </div>
                );
              })()}

              {/* Eye 3 */}
              {(() => {
                const eye3 = getEyeStatus('eye3', passport.eyes.synthesis, lang);
                return (
                  <div className="p-4 rounded-xl border border-surface bg-void space-y-1">
                    <span className="font-mono text-[10px] text-orange-400 tracking-wider uppercase block">
                      {eye3.name}
                    </span>
                    <div className="font-sans text-sm font-bold text-text">
                      {eye3.statusText}
                    </div>
                    <p className="text-[11px] text-muted font-sans">{eye3.subtitle}</p>
                  </div>
                );
              })()}
            </div>

            {/* 3. Evidence Panel: Origin Timeline OR Reasons List */}
            <div className="space-y-4">
              <h4 className="font-display text-sm font-semibold tracking-wider text-muted uppercase">
                {lang === 'en' ? 'FORENSIC EVIDENCE & ATTRIBUTION' : 'फोरेंसिक साक्ष्य एवं स्रोत विवरण'}
              </h4>

              {passport.origin ? (
                /* Origin Matched Timeline */
                <div className="rounded-xl border border-surface bg-void p-5 space-y-3 font-mono text-xs">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-surface/60 pb-2">
                    <span className="text-accent font-semibold">VERIFIED ORIGIN ARCHIVE</span>
                    <span className="text-muted">SOURCE DATE: {passport.origin.date}</span>
                  </div>
                  <div className="space-y-1 text-sm font-sans">
                    <span className="text-muted text-xs block">Source Publication:</span>
                    <span className="text-text font-semibold">{passport.origin.source}</span>
                  </div>
                  <div className="space-y-1 text-xs font-sans text-muted">
                    <span className="block text-muted/80">Archived Context Claim:</span>
                    <p className="italic text-text/90">
                      &quot;{lang === 'en' ? passport.origin.claim_en : passport.origin.claim_hi}&quot;
                    </p>
                  </div>
                  {passport.origin.factcheck_url && (
                    <div className="pt-2">
                      <a
                        href={passport.origin.factcheck_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-accent hover:underline text-xs"
                      >
                        <span>View archived record source</span>
                        <span>↗</span>
                      </a>
                    </div>
                  )}
                </div>
              ) : (
                /* No match in index notice (Normal case!) */
                <div className="rounded-xl border border-surface bg-void p-4 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-mono text-muted">
                    <span className="w-2 h-2 rounded-full bg-slate-400" />
                    <span className="font-semibold">
                      {lang === 'en' ? 'NO MATCH IN REFERENCE INDEX' : 'संदर्भ इंडेक्स में कोई पूर्व मिलान नहीं'}
                    </span>
                  </div>
                  <p className="text-xs text-muted font-sans leading-relaxed">
                    {lang === 'en'
                      ? 'This is the standard case for unique or un-indexed imagery. Evaluation proceeded directly to Eye 3 AI synthesis analysis.'
                      : 'यह अप्रकाशित या नई छवियों के लिए सामान्य बात है। विश्लेषण सीधे तृतीय नेत्र एआई संश्लेषण द्वारा किया गया।'}
                  </p>
                </div>
              )}

              {/* Reasons Breakdown */}
              {passport.reasons && passport.reasons.length > 0 && (
                <div className="space-y-2">
                  <span className="font-mono text-xs text-muted block">
                    {lang === 'en' ? 'Observed Signals:' : 'विश्लेषित संकेत:'}
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {passport.reasons.map((r, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg border border-surface/80 bg-void/60 text-xs font-sans text-muted flex items-start gap-2"
                      >
                        <span className="text-accent font-mono text-sm leading-none">•</span>
                        <span>{getReasonText(r.key, lang)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Special Guidance Notes */}
              {passport.verdict === 'inconclusive' && (
                <div className="p-3.5 rounded-lg border border-slate-500/40 bg-slate-500/10 text-xs font-mono text-slate-300">
                  {lang === 'en'
                    ? 'Evidence is weak, so we abstain rather than guess.'
                    : 'साक्ष्य अपर्याप्त हैं, अतः प्रणाली अटकलें लगाने के बजाय अनिर्णायक रहना चुनती है।'}
                </div>
              )}
              {passport.verdict === 'likely_ai' && (
                <div className="p-3.5 rounded-lg border border-orange-500/40 bg-orange-500/10 text-xs font-mono text-orange-300">
                  {lang === 'en'
                    ? 'This is a likelihood based on image signals, not proof.'
                    : 'यह छवि के सांख्यिकीय संकेतों पर आधारित संभावना है, पूर्ण प्रमाण नहीं।'}
                </div>
              )}
            </div>

            {/* 4. Comparison Slider — only when both origin AND diff exist */}
            {passport.origin && passport.diff ? (
              <div className="space-y-3 pt-4 border-t border-surface/60">
                <h4 className="font-display text-sm font-semibold tracking-wider text-muted uppercase">
                  {lang === 'en' ? 'VISUAL COMPARISON SLIDER' : 'दृश्य तुलना स्लाइडर'}
                </h4>
                <ComparisonSlider
                  userImageUrl={userImageUrl}
                  originalThumbUrl={passport.origin.thumb_url || null}
                  changedRegions={passport.diff.changed_regions}
                  hasSuspiciousOverlay={Boolean(passport.suspicious_regions_url)}
                  lang={lang}
                />
              </div>
            ) : userImageUrl ? (
              /* No origin match — show submitted image with suspicious-regions overlay only */
              <div className="space-y-3 pt-4 border-t border-surface/60">
                <h4 className="font-display text-sm font-semibold tracking-wider text-muted uppercase">
                  {lang === 'en' ? 'SUBMITTED IMAGE' : 'प्रस्तुत छवि'}
                </h4>
                <div className="relative w-full h-64 sm:h-80 md:h-96 rounded-xl border border-surface overflow-hidden bg-void flex items-center justify-center">
                  <img
                    src={userImageUrl}
                    alt="Submitted Image"
                    className="w-full h-full object-contain pointer-events-none"
                  />
                  {passport.suspicious_regions_url && (
                    <div className="absolute top-3 left-3 bg-orange-500/90 text-void font-mono text-[10px] font-bold px-2 py-0.5 rounded shadow pointer-events-none">
                      {lang === 'en'
                        ? 'Suspicious regions, not proof'
                        : 'संभावित संदेहास्पद क्षेत्र (प्रमाण नहीं)'}
                    </div>
                  )}
                  <span className="absolute bottom-3 left-3 font-mono text-[10px] bg-void/80 text-accent px-2 py-0.5 rounded border border-surface pointer-events-none">
                    {lang === 'en' ? 'SUBMITTED' : 'प्रस्तुत छवि'}
                  </span>
                </div>
              </div>
            ) : null}

            {/* 5. Scope Note & External Search */}
            <div className="p-4 rounded-xl border border-surface bg-void space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-accent font-semibold">{ui.scopeNoteHeading}</span>
                <span className="text-muted">HONEST BOUNDARY</span>
              </div>
              <p className="text-xs text-muted font-sans leading-relaxed">
                {passport.scope_note[lang] || passport.scope_note.en}
              </p>
              <div className="flex flex-wrap gap-3 pt-1">
                <button
                  type="button"
                  onClick={() =>
                    setConsentTarget({
                      url: passport.external_search?.lens || 'https://lens.google.com/',
                      provider: 'Google Lens',
                    })
                  }
                  className="px-3 py-1.5 rounded border border-surface bg-void-2 text-xs font-mono text-muted hover:text-text hover:border-accent/60 transition-colors flex items-center gap-1.5"
                >
                  <span>Google Lens Search</span>
                  <span>↗</span>
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setConsentTarget({
                      url: passport.external_search?.tineye || 'https://tineye.com/',
                      provider: 'TinEye Reverse Search',
                    })
                  }
                  className="px-3 py-1.5 rounded border border-surface bg-void-2 text-xs font-mono text-muted hover:text-text hover:border-accent/60 transition-colors flex items-center gap-1.5"
                >
                  <span>TinEye Reverse Search</span>
                  <span>↗</span>
                </button>
              </div>
            </div>

            {/* 6. Action Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-6 border-t border-surface/60">
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={handleShareCard}
                  className="px-4 py-2 rounded-lg border border-accent/60 bg-accent/15 text-accent text-xs font-mono uppercase tracking-wider font-semibold hover:bg-accent/25 transition-colors focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  {ui.buttonShareCard}
                </button>

                <button
                  type="button"
                  onClick={handleCopySummary}
                  className="px-4 py-2 rounded-lg border border-surface bg-void text-xs font-mono text-muted hover:text-text hover:border-surface/80 transition-colors focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  {copySuccess ? ui.buttonCopied : ui.buttonCopySummary}
                </button>
              </div>

              <button
                type="button"
                onClick={handleReset}
                className="px-4 py-2 rounded-lg border border-surface bg-void-2 text-xs font-mono text-accent hover:border-accent/60 transition-colors"
              >
                {ui.buttonNewScan}
              </button>
            </div>
          </div>
        )}

        {/* External Search Consent Dialog */}
        <ConsentModal
          isOpen={Boolean(consentTarget)}
          targetUrl={consentTarget?.url || null}
          providerName={consentTarget?.provider || 'Third Party'}
          lang={lang}
          onConfirm={() => {
            if (consentTarget?.url) {
              window.open(consentTarget.url, '_blank', 'noopener,noreferrer');
            }
            setConsentTarget(null);
          }}
          onClose={() => setConsentTarget(null)}
        />
      </div>
    </section>
  );
};
