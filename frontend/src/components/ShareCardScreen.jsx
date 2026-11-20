import React, { useState } from 'react';
import { ArrowLeft, Download, Share2, Check, ShieldCheck } from 'lucide-react';
import { config } from '../api/client';
import { strings, getTranslation } from '../strings';

export default function ShareCardScreen({ passport, lang, onBack }) {
  const [shared, setShared] = useState(false);

  // In real backend, GET /passport/{id}/card.png?lang=en|hi
  // In mock/fallback, generate visually formatted client card
  const cardUrl = `${config.apiUrl}/passport/${passport.id}/card.png?lang=${lang}`;

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Trinetra Provenance Passport - ${passport.verdict.toUpperCase()}`,
          text: `Verified image provenance with Trinetra. Verdict: ${passport.verdict}.`,
          url: window.location.href
        });
        setShared(true);
        setTimeout(() => setShared(false), 2000);
      } catch (err) {
        console.warn('Web Share failed/cancelled:', err);
      }
    } else {
      // Fallback: download card or copy link
      await navigator.clipboard.writeText(window.location.href);
      setShared(true);
      setTimeout(() => setShared(false), 2000);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-5 py-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Passport</span>
        </button>

        <span className="text-xs font-semibold text-sky-400">
          Passport ID: {passport.id}
        </span>
      </div>

      {/* Shareable Card Preview Canvas/Card */}
      <div className="rounded-3xl bg-gradient-to-b from-[#1b2434] to-[#121824] border border-slate-700/80 p-6 shadow-2xl space-y-5 text-center relative overflow-hidden">
        {/* Decorative background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-48 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center justify-center gap-2">
          <ShieldCheck className="w-6 h-6 text-sky-400" />
          <span className="font-extrabold text-lg text-white tracking-tight">TRINETRA</span>
        </div>

        <div className="space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            PROVENANCE PASSPORT
          </span>
          <h2 className="text-2xl font-black text-white uppercase tracking-tight">
            {passport.verdict.replace(/_/g, ' ')}
          </h2>
          <p className="text-xs text-sky-300">
            Confidence: {passport.confidence_band.toUpperCase()}
          </p>
        </div>

        {/* Three Eyes mini-summary */}
        <div className="grid grid-cols-3 gap-2 py-3 border-y border-slate-800 text-left">
          <div className="space-y-0.5">
            <span className="text-[10px] text-slate-400 font-bold block">EYE 1: ORIGIN</span>
            <span className="text-xs font-bold text-slate-200 capitalize">{passport.eyes.origin}</span>
          </div>
          <div className="space-y-0.5">
            <span className="text-[10px] text-slate-400 font-bold block">EYE 2: CHANGE</span>
            <span className="text-xs font-bold text-slate-200 capitalize">{passport.eyes.change}</span>
          </div>
          <div className="space-y-0.5">
            <span className="text-[10px] text-slate-400 font-bold block">EYE 3: SYNTH</span>
            <span className="text-xs font-bold text-slate-200 capitalize">{passport.eyes.synthesis}</span>
          </div>
        </div>

        <p className="text-xs text-slate-300 italic px-2 leading-relaxed">
          "{passport.lang?.[lang] || passport.lang?.en}"
        </p>

        <div className="pt-2 text-[11px] text-slate-400">
          Team Kinetix | Code for Innovex '26 (Navyug)
        </div>
      </div>

      {/* Share / Download Buttons */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleShare}
          className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-sm shadow-lg shadow-sky-600/30 transition-colors"
        >
          {shared ? <Check className="w-4 h-4 text-emerald-300" /> : <Share2 className="w-4 h-4" />}
          <span>{shared ? 'Shared / Link Copied!' : 'Share Passport Card'}</span>
        </button>

        <a
          href={cardUrl}
          download={`trinetra_passport_${passport.id}.png`}
          target="_blank"
          rel="noreferrer"
          className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          title="Download PNG"
        >
          <Download className="w-5 h-5" />
        </a>
      </div>
    </div>
  );
}
