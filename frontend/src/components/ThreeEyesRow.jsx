import React from 'react';
import { Compass, GitCompare, Cpu, CheckCircle2, AlertCircle, HelpCircle, MinusCircle } from 'lucide-react';
import { strings, getTranslation } from '../strings';

function getEyeBadge(status, eyeKey, lang) {
  const eyeConfig = strings.eyes?.[eyeKey];
  const label = getTranslation(eyeConfig?.status?.[status], lang) || status;

  if (status === 'confirmed') {
    return {
      label,
      classes: 'bg-red-500/20 text-red-300 border-red-500/40',
      icon: AlertCircle
    };
  }
  if (status === 'likely' || (eyeKey === 'eye2' && status === 'found')) {
    return {
      label,
      classes: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      icon: AlertCircle
    };
  }
  if (status === 'found' || (eyeKey === 'eye2' && status === 'none') || (eyeKey === 'eye3' && status === 'none')) {
    return {
      label,
      classes: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      icon: CheckCircle2
    };
  }
  if (status === 'inconclusive') {
    return {
      label,
      classes: 'bg-slate-700/50 text-slate-300 border-slate-600',
      icon: HelpCircle
    };
  }
  return {
    label,
    classes: 'bg-slate-800/60 text-slate-400 border-slate-700',
    icon: MinusCircle
  };
}

export default function ThreeEyesRow({ eyes, lang }) {
  const eye1Badge = getEyeBadge(eyes.origin, 'eye1', lang);
  const eye2Badge = getEyeBadge(eyes.change, 'eye2', lang);
  const eye3Badge = getEyeBadge(eyes.synthesis, 'eye3', lang);

  const Eye1Icon = eye1Badge.icon;
  const Eye2Icon = eye2Badge.icon;
  const Eye3Icon = eye3Badge.icon;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {/* Eye 1: Origin */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-3.5 flex flex-col justify-between space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-sky-950/60 border border-sky-800/40 text-sky-400">
              <Compass className="w-4 h-4" />
            </div>
            <span className="font-semibold text-sm text-slate-100">
              {getTranslation(strings.eyes?.eye1?.name, lang)}
            </span>
          </div>
        </div>
        <p className="text-xs text-slate-400">
          {getTranslation(strings.eyes?.eye1?.subtitle, lang)}
        </p>
        <div className="pt-1">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${eye1Badge.classes}`}>
            <Eye1Icon className="w-3.5 h-3.5 shrink-0" />
            <span>{eye1Badge.label}</span>
          </span>
        </div>
      </div>

      {/* Eye 2: Change */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-3.5 flex flex-col justify-between space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-amber-950/60 border border-amber-800/40 text-amber-400">
              <GitCompare className="w-4 h-4" />
            </div>
            <span className="font-semibold text-sm text-slate-100">
              {getTranslation(strings.eyes?.eye2?.name, lang)}
            </span>
          </div>
        </div>
        <p className="text-xs text-slate-400">
          {getTranslation(strings.eyes?.eye2?.subtitle, lang)}
        </p>
        <div className="pt-1">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${eye2Badge.classes}`}>
            <Eye2Icon className="w-3.5 h-3.5 shrink-0" />
            <span>{eye2Badge.label}</span>
          </span>
        </div>
      </div>

      {/* Eye 3: Synthesis */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-3.5 flex flex-col justify-between space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-purple-950/60 border border-purple-800/40 text-purple-400">
              <Cpu className="w-4 h-4" />
            </div>
            <span className="font-semibold text-sm text-slate-100">
              {getTranslation(strings.eyes?.eye3?.name, lang)}
            </span>
          </div>
        </div>
        <p className="text-xs text-slate-400">
          {getTranslation(strings.eyes?.eye3?.subtitle, lang)}
        </p>
        <div className="pt-1">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${eye3Badge.classes}`}>
            <Eye3Icon className="w-3.5 h-3.5 shrink-0" />
            <span>{eye3Badge.label}</span>
          </span>
        </div>
      </div>
    </div>
  );
}
