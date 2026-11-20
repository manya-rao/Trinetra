import React, { useState, useEffect } from 'react';
import { Compass, GitCompare, Cpu, CheckCircle } from 'lucide-react';
import { strings, getTranslation } from '../strings';

export default function AnalyzingScreen({ lang }) {
  const [activeStep, setActiveStep] = useState(1);

  useEffect(() => {
    const t1 = setTimeout(() => setActiveStep(2), 500);
    const t2 = setTimeout(() => setActiveStep(3), 1000);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, []);

  const steps = [
    {
      step: 1,
      title: getTranslation(strings.eyes.eye1.name, lang),
      sub: getTranslation(strings.ui.analyzing_eye1, lang),
      icon: Compass,
      color: 'text-sky-400'
    },
    {
      step: 2,
      title: getTranslation(strings.eyes.eye2.name, lang),
      sub: getTranslation(strings.ui.analyzing_eye2, lang),
      icon: GitCompare,
      color: 'text-amber-400'
    },
    {
      step: 3,
      title: getTranslation(strings.eyes.eye3.name, lang),
      sub: getTranslation(strings.ui.analyzing_eye3, lang),
      icon: Cpu,
      color: 'text-purple-400'
    }
  ];

  return (
    <div className="py-12 sm:py-16 max-w-md mx-auto text-center space-y-8 animate-fade-in">
      <div className="relative inline-flex items-center justify-center">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-sky-600 via-indigo-600 to-amber-500 p-[2px] animate-spin-slow">
          <div className="w-full h-full bg-[#0c1017] rounded-[22px] flex items-center justify-center">
            <Cpu className="w-10 h-10 text-sky-400 animate-pulse" />
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="text-xl sm:text-2xl font-bold text-white">
          {getTranslation(strings.ui.analyzing_title, lang)}
        </h2>
        <p className="text-xs sm:text-sm text-slate-400">
          Synthesizing multi-modal provenance signals across the Three Eyes
        </p>
      </div>

      {/* Sequential Eye Progress */}
      <div className="space-y-3 text-left">
        {steps.map((s) => {
          const isDone = activeStep > s.step;
          const isCurrent = activeStep === s.step;
          const IconComp = s.icon;

          return (
            <div
              key={s.step}
              className={`p-3.5 rounded-xl border transition-all ${
                isCurrent
                  ? 'bg-slate-900 border-sky-500/50 shadow-lg shadow-sky-500/10'
                  : isDone
                  ? 'bg-slate-900/40 border-slate-800 opacity-80'
                  : 'bg-slate-950/40 border-slate-900 opacity-40'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className={`p-1.5 rounded-lg bg-slate-950 ${s.color}`}>
                    <IconComp className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-semibold text-slate-200">
                    {s.title}
                  </span>
                </div>
                {isDone ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                ) : isCurrent ? (
                  <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
                ) : null}
              </div>
              <p className="text-xs text-slate-400 mt-1 pl-8">
                {s.sub}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
