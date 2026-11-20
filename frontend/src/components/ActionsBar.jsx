import React, { useState } from 'react';
import { RefreshCw, Share2, Copy, Check } from 'lucide-react';
import { strings, getTranslation } from '../strings';

export default function ActionsBar({ passport, lang, onReset, onOpenShareCard }) {
  const [copied, setCopied] = useState(false);

  const handleCopySummary = async () => {
    const summaryText = `Trinetra Provenance Passport\nVerdict: ${passport.verdict.toUpperCase()}\nConfidence: ${passport.confidence_band}\nSummary: ${passport.lang?.[lang] || passport.lang?.en || ''}\nVerify with Trinetra (Team Kinetix)`;
    try {
      await navigator.clipboard.writeText(summaryText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.warn('Clipboard write failed:', err);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
      <button
        type="button"
        onClick={onReset}
        className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 transition-colors"
      >
        <RefreshCw className="w-4 h-4 text-sky-400" />
        <span>{getTranslation(strings.ui.button_new_scan, lang)}</span>
      </button>

      <div className="flex items-center gap-2.5">
        <button
          type="button"
          onClick={handleCopySummary}
          className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl text-sm font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
        >
          {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          <span>{copied ? getTranslation(strings.ui.button_copied, lang) : getTranslation(strings.ui.button_copy_summary, lang)}</span>
        </button>

        <button
          type="button"
          onClick={onOpenShareCard}
          className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl text-sm font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-600/30 transition-colors"
        >
          <Share2 className="w-4 h-4" />
          <span>{getTranslation(strings.ui.button_share_card, lang)}</span>
        </button>
      </div>
    </div>
  );
}
