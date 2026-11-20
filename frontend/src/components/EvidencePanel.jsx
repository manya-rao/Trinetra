import React from 'react';
import {
  ExternalLink,
  Calendar,
  CheckCircle,
  FileCheck2,
  Cpu,
  Waves,
  Sparkles,
  Info
} from 'lucide-react';
import { getTranslation } from '../strings';

const REASON_ICONS = {
  spectrum_peaks: Waves,
  noise_uniform: Cpu,
  no_camera_metadata: Info,
  clip_ai_signal: Sparkles,
  low_resolution: Info,
  heavy_compression: Info,
  signals_disagree: Info,
  generator_tag_found: Cpu
};

export default function EvidencePanel({ passport, lang }) {
  const origin = passport.origin;
  const reasons = passport.reasons || [];
  const c2pa = passport.c2pa;

  return (
    <div className="space-y-4">
      {/* 1. Origin Evidence Card (if origin match exists) */}
      {origin && (
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-4 sm:p-5 space-y-3">
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-5 h-5 text-emerald-400" />
            <h3 className="font-semibold text-slate-100 text-sm sm:text-base">
              Earliest Verified Origin Match
            </h3>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 items-start">
            {origin.thumb_url && (
              <img
                src={origin.thumb_url}
                alt="Source Thumbnail"
                className="w-24 h-24 sm:w-28 sm:h-28 object-cover rounded-xl border border-slate-800 shrink-0 bg-slate-950"
              />
            )}
            <div className="space-y-2 flex-1">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="text-sm font-bold text-slate-200">
                  {origin.source}
                </span>
                {origin.date && (
                  <span className="inline-flex items-center gap-1 text-xs text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded">
                    <Calendar className="w-3 h-3" />
                    <span>{origin.date}</span>
                  </span>
                )}
              </div>

              <p className="text-xs sm:text-sm text-slate-300">
                {lang === 'hi' ? origin.claim_hi || origin.claim_en : origin.claim_en}
              </p>

              {origin.factcheck_url && (
                <a
                  href={origin.factcheck_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-sky-400 hover:text-sky-300 transition-colors pt-1"
                >
                  <span>View Fact-Checker Report</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 2. C2PA Cryptographic Content Credentials (if present) */}
      {c2pa && c2pa.status !== 'none' && (
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-4 sm:p-5 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-sky-400" />
              <h3 className="font-semibold text-slate-100 text-sm sm:text-base">
                C2PA Content Credentials
              </h3>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-xs font-semibold border ${
                c2pa.status === 'valid'
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                  : 'bg-red-500/15 text-red-300 border-red-500/30'
              }`}
            >
              {c2pa.status.toUpperCase()}
            </span>
          </div>

          <div className="text-xs sm:text-sm text-slate-300 space-y-1">
            {c2pa.issuer && (
              <p>
                <span className="text-slate-400">Cryptographic Issuer:</span>{' '}
                <strong className="text-slate-200">{c2pa.issuer}</strong>
              </p>
            )}
            {c2pa.ai_generated !== undefined && (
              <p>
                <span className="text-slate-400">Generative Manifest Assertion:</span>{' '}
                <strong className={c2pa.ai_generated ? 'text-orange-300' : 'text-emerald-300'}>
                  {c2pa.ai_generated ? 'AI-Created Media Declared' : 'Authentic Camera Capture Declared'}
                </strong>
              </p>
            )}
          </div>
        </div>
      )}

      {/* 3. Forensic Evidence Reasons List */}
      {reasons.length > 0 && (
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-4 sm:p-5 space-y-3">
          <h3 className="font-semibold text-slate-100 text-sm sm:text-base">
            Forensic Synthesis Evidence
          </h3>

          <ul className="space-y-2.5">
            {reasons.map((r, idx) => {
              const IconComp = REASON_ICONS[r.key] || Info;
              const text = lang === 'hi' ? r.hi || r.en : r.en;
              return (
                <li
                  key={idx}
                  className="flex items-start gap-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800/80"
                >
                  <div className="p-1.5 rounded-lg bg-sky-950/60 text-sky-400 shrink-0 mt-0.5">
                    <IconComp className="w-4 h-4" />
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                      {r.key.replace(/_/g, ' ')}
                    </span>
                    <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
                      {text}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
