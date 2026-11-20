import React from 'react';
import { ExternalLink, ShieldAlert, X } from 'lucide-react';
import { strings, getTranslation } from '../strings';

export default function ConsentModal({ isOpen, onClose, onConfirm, targetEngine = 'Google Lens' }) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="consent-title"
    >
      <div className="bg-[#151c28] border border-slate-700 rounded-2xl max-w-md w-full p-5 sm:p-6 shadow-2xl space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5 text-amber-400">
            <ShieldAlert className="w-6 h-6 shrink-0" />
            <h3 id="consent-title" className="text-base sm:text-lg font-bold text-white">
              {getTranslation(strings.ui.consent_modal_title)}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-slate-300 leading-relaxed">
          {getTranslation(strings.ui.consent_modal_body)}
        </p>

        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
          Target Service: <span className="font-semibold text-slate-200">{targetEngine}</span>.
          Trinetra will not send your identity or private session data.
        </div>

        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors"
          >
            {getTranslation(strings.ui.button_cancel)}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-600/30 flex items-center gap-1.5 transition-colors"
          >
            <span>{getTranslation(strings.ui.button_proceed)}</span>
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
