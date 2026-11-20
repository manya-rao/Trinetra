import React, { useState } from 'react';
import { Eye, ShieldAlert } from 'lucide-react';
import { strings, getTranslation } from '../strings';

export default function SuspiciousRegionView({ userImageUrl, suspiciousRegionsUrl, lang }) {
  const [showOverlay, setShowOverlay] = useState(true);

  if (!suspiciousRegionsUrl) return null;

  return (
    <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-4 sm:p-5 space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          <h3 className="font-semibold text-slate-100 text-sm sm:text-base">
            Synthesis Artifact Map
          </h3>
        </div>

        <button
          type="button"
          onClick={() => setShowOverlay(!showOverlay)}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border ${
            showOverlay
              ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
              : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-800'
          }`}
        >
          <Eye className="w-3.5 h-3.5" />
          <span>{showOverlay ? 'Hide Artifact Heatmap' : 'Show Artifact Heatmap'}</span>
        </button>
      </div>

      <div className="relative w-full aspect-[4/3] sm:aspect-[16/10] overflow-hidden rounded-xl bg-slate-950 border border-slate-800 shadow-inner">
        {/* Base user image */}
        <img
          src={userImageUrl || 'https://picsum.photos/seed/user_sample/600/400'}
          alt="Uploaded Analysis Target"
          className="w-full h-full object-cover"
        />

        {/* Heatmap overlay */}
        {showOverlay && (
          <img
            src={suspiciousRegionsUrl}
            alt="Suspicious Regions Heatmap"
            className="absolute inset-0 w-full h-full object-cover opacity-85 mix-blend-color-dodge pointer-events-none"
          />
        )}

        {/* Permanent Watermark / Badge */}
        <div className="absolute bottom-3 left-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-amber-500/40 flex items-center gap-2 shadow-lg">
          <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span className="text-xs font-medium text-amber-200">
            {getTranslation(strings.ui.suspicious_regions_label, lang)}
          </span>
        </div>
      </div>

      <p className="text-xs text-slate-400">
        Per-patch spatial noise residual & high-frequency anomalies are highlighted. These highlight inconsistencies for human review, not definitive proof.
      </p>
    </div>
  );
}
