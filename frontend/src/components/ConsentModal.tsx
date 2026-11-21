import React, { useEffect, useRef } from 'react';

interface ConsentModalProps {
  isOpen: boolean;
  targetUrl: string | null;
  providerName: string;
  lang: 'en' | 'hi';
  onConfirm: () => void;
  onClose: () => void;
}

export const ConsentModal: React.FC<ConsentModalProps> = ({
  isOpen,
  providerName,
  lang,
  onConfirm,
  onClose,
}) => {
  const modalRef = useRef<HTMLDivElement | null>(null);
  const confirmBtnRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      confirmBtnRef.current?.focus();
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose();
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="consent-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-void/80 backdrop-blur-sm animate-fade-in"
    >
      <div
        ref={modalRef}
        className="relative w-full max-w-md rounded-2xl border border-surface bg-void-2 p-6 shadow-2xl space-y-4"
      >
        <div className="flex items-center gap-3 pb-3 border-b border-surface/60">
          <span className="text-amber-400 font-mono text-xl">ℹ</span>
          <h3 id="consent-title" className="font-display text-base sm:text-lg font-bold text-text">
            {lang === 'en' ? 'Consent for External Search' : 'बाहरी खोज हेतु उपयोगकर्ता सहमति'}
          </h3>
        </div>

        <p className="text-xs sm:text-sm text-muted font-sans leading-relaxed">
          {lang === 'en'
            ? `You are about to open ${providerName}. This will open a third-party website in a new tab. Your image was processed locally and is NOT uploaded by Trinetra to third parties without your permission.`
            : `आप ${providerName} खोलने जा रहे हैं। यह नए टैब में बाहरी वेबसाइट खोलेगा। आपकी छवि स्थानीय रूप से जाँची गई है और त्रिनेत्र द्वारा इसे बिना आपकी अनुमति किसी को अपलोड नहीं किया जाता।`}
        </p>

        <div className="pt-3 border-t border-surface/60 flex items-center justify-end gap-3 font-mono text-xs">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded border border-surface bg-void text-muted hover:text-text transition-colors focus:outline-none focus:ring-1 focus:ring-accent"
          >
            {lang === 'en' ? 'Cancel' : 'रद्द करें'}
          </button>
          <button
            ref={confirmBtnRef}
            type="button"
            onClick={onConfirm}
            className="px-4 py-2 rounded border border-accent/60 bg-accent/20 text-accent font-semibold hover:bg-accent/30 transition-colors focus:outline-none focus:ring-2 focus:ring-accent"
          >
            {lang === 'en' ? 'I Consent, Proceed' : 'सहमति है, आगे बढ़ें'}
          </button>
        </div>
      </div>
    </div>
  );
};
