import React from 'react';
import VerdictBanner from './VerdictBanner';
import ThreeEyesRow from './ThreeEyesRow';
import ComparisonSlider from './ComparisonSlider';
import SuspiciousRegionView from './SuspiciousRegionView';
import EvidencePanel from './EvidencePanel';
import ScopeNoteAndExternalSearch from './ScopeNoteAndExternalSearch';
import ActionsBar from './ActionsBar';

export default function PassportScreen({
  passport,
  userImageUrl,
  lang,
  onReset,
  onOpenShareCard
}) {
  return (
    <div className="space-y-5 animate-fade-in pb-10">
      {/* 1. Verdict Banner */}
      <VerdictBanner passport={passport} lang={lang} />

      {/* 2. Three Eyes Row */}
      <ThreeEyesRow eyes={passport.eyes} lang={lang} />

      {/* 3. Comparison Slider (Eye 2 Change diff) */}
      {passport.diff && (
        <ComparisonSlider
          diff={passport.diff}
          userImageUrl={userImageUrl}
          lang={lang}
        />
      )}

      {/* 4. Suspicious Regions Artifact Map (Eye 3 Synthesis overlay) */}
      {passport.suspicious_regions_url && (
        <SuspiciousRegionView
          userImageUrl={userImageUrl}
          suspiciousRegionsUrl={passport.suspicious_regions_url}
          lang={lang}
        />
      )}

      {/* 5. Origin & Forensic Evidence */}
      <EvidencePanel passport={passport} lang={lang} />

      {/* 6. Scope Note & External Search Links */}
      <ScopeNoteAndExternalSearch passport={passport} lang={lang} />

      {/* 7. Action Bar */}
      <ActionsBar
        passport={passport}
        lang={lang}
        onReset={onReset}
        onOpenShareCard={onOpenShareCard}
      />
    </div>
  );
}
