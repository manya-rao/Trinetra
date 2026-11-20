import React from 'react';
import { ShieldCheck, Globe, Cpu } from 'lucide-react';
import { getAvailableMocks } from '../api/client';

export default function Header({ lang, setLang, activeMock, setActiveMock, onReset }) {
  const mocks = getAvailableMocks();

  return (
    <header className="sticky top-0 z-40 bg-[#0c1017]/90 backdrop-blur-md border-b border-slate-800/80 px-4 py-3">
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-3">
        {/* Brand identity */}
        <button
          onClick={onReset}
          className="flex items-center gap-2.5 text-left group focus:outline-none focus:ring-2 focus:ring-sky-500 rounded-lg p-1 -m-1"
          aria-label="Trinetra Home"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 via-indigo-600 to-amber-500 p-[1px] shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#0c1017] rounded-[11px] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-sky-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                Trinetra
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-sky-950/80 text-sky-400 border border-sky-800/40">
                Kinetix
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Digital Trust & Provenance Passport
            </p>
          </div>
        </button>

        {/* Controls: Mock Selector (for review/demo) & Language Toggle */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Quick Mock Fixture Selector for judges/reviewers */}
          <div className="hidden md:flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 rounded-lg px-2 py-1">
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={activeMock || ''}
              onChange={(e) => setActiveMock(e.target.value)}
              aria-label="Demo Verdict Fixture"
              className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
            >
              {mocks.map((m) => (
                <option key={m} value={m} className="bg-slate-900 text-slate-200">
                  {m.replace(/_/g, ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Language Toggle EN / HI */}
          <div className="flex items-center bg-slate-900/90 p-0.5 rounded-lg border border-slate-800">
            <button
              onClick={() => setLang('en')}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                lang === 'en'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              aria-label="Switch to English"
            >
              EN
            </button>
            <button
              onClick={() => setLang('hi')}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                lang === 'hi'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              aria-label="Switch to Hindi"
            >
              हिंदी
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
