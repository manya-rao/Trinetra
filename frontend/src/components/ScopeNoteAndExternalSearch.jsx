import React, { useState } from 'react';
import { Search, Globe2 } from 'lucide-react';
import { strings, getTranslation } from '../strings';
import ConsentModal from './ConsentModal';

export default function ScopeNoteAndExternalSearch({ passport, lang }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedEngine, setSelectedEngine] = useState('Google Lens');

  const lensUrl = passport.external_search?.lens || '#';
  const tineyeUrl = passport.external_search?.tineye || '#';

  const handleOpenConsent = (engineName) => {
    setSelectedEngine(engineName);
    setModalOpen(true);
  };

  const handleProceed = () => {
    setModalOpen(false);
    const targetUrl = selectedEngine === 'Google Lens' ? lensUrl : tineyeUrl;
    if (targetUrl && targetUrl !== '#') {
      window.open(targetUrl, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <>
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-4 sm:p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Globe2 className="w-5 h-5 text-sky-400" />
          <h3 className="font-semibold text-slate-100 text-sm sm:text-base">
            {getTranslation(strings.ui.scope_note_heading, lang)}
          </h3>
        </div>

        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
          {getTranslation(passport.scope_note || strings.ui.scope_note, lang)}
        </p>

        <div className="pt-2 flex flex-wrap gap-2.5">
          <button
            type="button"
            onClick={() => handleOpenConsent('Google Lens')}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors shadow-sm"
          >
            <Search className="w-4 h-4 text-sky-400" />
            <span>Search with Google Lens</span>
          </button>

          <button
            type="button"
            onClick={() => handleOpenConsent('TinEye')}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors shadow-sm"
          >
            <Search className="w-4 h-4 text-amber-400" />
            <span>Search with TinEye</span>
          </button>
        </div>
      </div>

      <ConsentModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleProceed}
        targetEngine={selectedEngine}
      />
    </>
  );
}
