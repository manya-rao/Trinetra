import React from 'react';
import {
  ShieldCheck,
  Scissors,
  History,
  AlertTriangle,
  Sparkles,
  Camera,
  HelpCircle
} from 'lucide-react';
import { strings, getVerdictConfig, getTranslation } from '../strings';

const ICONS = {
  'shield-check': ShieldCheck,
  'scissors': Scissors,
  'clock-rewind': History,
  'cpu-alert': AlertTriangle,
  'sparkles': Sparkles,
  'camera': Camera,
  'help-circle': HelpCircle
};

const STYLES = {
  green: {
    border: 'border-emerald-500/40',
    bg: 'bg-emerald-950/20',
    badgeBg: 'bg-emerald-500/15',
    badgeText: 'text-emerald-300',
    iconColor: 'text-emerald-400',
    glow: 'shadow-emerald-500/10'
  },
  amber: {
    border: 'border-amber-500/40',
    bg: 'bg-amber-950/20',
    badgeBg: 'bg-amber-500/15',
    badgeText: 'text-amber-300',
    iconColor: 'text-amber-400',
    glow: 'shadow-amber-500/10'
  },
  orange: {
    border: 'border-orange-500/40',
    bg: 'bg-orange-950/20',
    badgeBg: 'bg-orange-500/15',
    badgeText: 'text-orange-300',
    iconColor: 'text-orange-400',
    glow: 'shadow-orange-500/10'
  },
  red: {
    border: 'border-red-500/50',
    bg: 'bg-red-950/30',
    badgeBg: 'bg-red-500/20',
    badgeText: 'text-red-300',
    iconColor: 'text-red-400',
    glow: 'shadow-red-500/15'
  },
  teal: {
    border: 'border-teal-500/40',
    bg: 'bg-teal-950/20',
    badgeBg: 'bg-teal-500/15',
    badgeText: 'text-teal-300',
    iconColor: 'text-teal-400',
    glow: 'shadow-teal-500/10'
  },
  'grey-blue': {
    border: 'border-slate-600/50',
    bg: 'bg-slate-900/40',
    badgeBg: 'bg-slate-700/30',
    badgeText: 'text-slate-300',
    iconColor: 'text-slate-400',
    glow: 'shadow-slate-500/5'
  }
};

export default function VerdictBanner({ passport, lang }) {
  const verdictConfig = getVerdictConfig(passport.verdict);
  const colorKey = verdictConfig.color || 'grey-blue';
  const style = STYLES[colorKey] || STYLES['grey-blue'];
  const IconComponent = ICONS[verdictConfig.icon] || HelpCircle;

  const headline = getTranslation(verdictConfig.headline, lang);
  const detail = getTranslation(verdictConfig.detail, lang);
  const bandKey = passport.confidence_band || 'medium';
  const bandLabel = getTranslation(strings.confidence_bands?.[bandKey], lang) || bandKey;

  return (
    <div
      className={`rounded-2xl border ${style.border} ${style.bg} p-4 sm:p-5 shadow-xl ${style.glow} transition-all`}
      role="region"
      aria-label="Verdict Passport Banner"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          {/* Status pill badge with icon + text */}
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${style.badgeBg} ${style.badgeText} border border-current/20`}
          >
            <IconComponent className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{bandLabel}</span>
          </span>
        </div>

        {/* DEMO DATA Badge if demo_data is true */}
        {passport.demo_data && (
          <span
            className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40"
            title="Demonstration seed data with neutral placeholder claims"
          >
            {strings.ui.demo_badge}
          </span>
        )}
      </div>

      <div className="flex items-start gap-3.5 mt-3">
        <div className={`p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 ${style.iconColor} shrink-0`}>
          <IconComponent className="w-7 h-7" aria-hidden="true" />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white leading-snug">
            {headline}
          </h2>
          <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
            {detail}
          </p>
          {passport.lang && (passport.lang[lang] || passport.lang.en) && (
            <p className="text-xs sm:text-sm text-slate-400 italic pt-1">
              "{passport.lang[lang] || passport.lang.en}"
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
