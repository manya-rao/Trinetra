import stringsData from '../../shared/strings.json';

export type Language = 'en' | 'hi';

export function getStrings() {
  return stringsData;
}

export function getVerdictStrings(verdictKey: string, lang: Language) {
  const verdicts = stringsData.verdicts as Record<
    string,
    {
      headline: { en: string; hi: string };
      detail: { en: string; hi: string };
      color: string;
      icon: string;
    }
  >;

  const defaultVerdict = verdicts.inconclusive;
  const target = verdicts[verdictKey] || defaultVerdict;

  // Key requirement: likely_real_looking must never be shown as a positive claim
  let headline = target.headline[lang] || target.headline.en;
  let detail = target.detail[lang] || target.detail.en;

  if (verdictKey === 'likely_real_looking') {
    headline = lang === 'en' ? 'No AI Signs Found (Not Proof)' : 'कोई एआई संकेत नहीं (प्रमाण नहीं)';
    detail =
      lang === 'en'
        ? 'Visual and sensor artifacts appear consistent with camera capture. Not definitive proof of authenticity.'
        : 'छवि के लक्षण प्राकृतिक कैमरे के समान हैं। यह पूर्ण प्रामाणिकता का अचूक प्रमाण नहीं है।';
  }

  return {
    headline,
    detail,
    color: target.color,
    icon: target.icon,
  };
}

export function getConfidenceBand(bandKey: string, lang: Language) {
  const bands = stringsData.confidence_bands as Record<string, { en: string; hi: string }>;
  const target = bands[bandKey] || bands.low;
  return target[lang] || target.en;
}

export function getReasonText(reasonKey: string, lang: Language): string {
  const reasons = stringsData.reasons as Record<string, { en: string; hi: string }>;
  if (reasons[reasonKey]) {
    return reasons[reasonKey][lang] || reasons[reasonKey].en;
  }
  // Quiet signals read "No AI signs found, not proof"
  if (reasonKey === 'no_ai_signs_found' || reasonKey === 'likely_real_looking') {
    return lang === 'en' ? 'No AI signs found, not proof.' : 'कोई एआई संकेत नहीं (प्रमाण नहीं)।';
  }
  return reasonKey.replace(/_/g, ' ');
}

export function getEyeStatus(eye: 'eye1' | 'eye2' | 'eye3', statusKey: string, lang: Language) {
  const eyes = stringsData.eyes as Record<
    string,
    {
      name: { en: string; hi: string };
      subtitle: { en: string; hi: string };
      status: Record<string, { en: string; hi: string }>;
    }
  >;

  const eyeObj = eyes[eye];
  const name = eyeObj.name[lang] || eyeObj.name.en;
  const subtitle = eyeObj.subtitle[lang] || eyeObj.subtitle.en;

  let statusText = statusKey;
  if (eyeObj.status[statusKey]) {
    statusText = eyeObj.status[statusKey][lang] || eyeObj.status[statusKey].en;
  }

  return {
    name,
    subtitle,
    statusText,
  };
}

export function getUIStrings(lang: Language) {
  const ui = stringsData.ui;
  return {
    appTitle: ui.app_title,
    appTagline: ui.app_tagline[lang] || ui.app_tagline.en,
    teamName: ui.team_name,
    eventTheme: ui.event_theme,
    demoBadge: ui.demo_badge,
    dropZoneTitle: ui.drop_zone_title[lang] || ui.drop_zone_title.en,
    dropZoneSub: ui.drop_zone_sub[lang] || ui.drop_zone_sub.en,
    pasteHint: ui.paste_hint[lang] || ui.paste_hint.en,
    shareWhatsappHint: ui.share_whatsapp_hint[lang] || ui.share_whatsapp_hint.en,
    privacyHashOnly: ui.privacy_hash_only[lang] || ui.privacy_hash_only.en,
    privacyDisclaimer: ui.privacy_disclaimer[lang] || ui.privacy_disclaimer.en,
    analyzingTitle: ui.analyzing_title[lang] || ui.analyzing_title.en,
    analyzingEye1: ui.analyzing_eye1[lang] || ui.analyzing_eye1.en,
    analyzingEye2: ui.analyzing_eye2[lang] || ui.analyzing_eye2.en,
    analyzingEye3: ui.analyzing_eye3[lang] || ui.analyzing_eye3.en,
    buttonAnalyze: ui.button_analyze[lang] || ui.button_analyze.en,
    buttonShareCard: ui.button_share_card[lang] || ui.button_share_card.en,
    buttonCopySummary: ui.button_copy_summary[lang] || ui.button_copy_summary.en,
    buttonCopied: ui.button_copied[lang] || ui.button_copied.en,
    buttonNewScan: ui.button_new_scan[lang] || ui.button_new_scan.en,
    tabComparison: ui.tab_comparison[lang] || ui.tab_comparison.en,
    toggleHeatmap: ui.toggle_heatmap[lang] || ui.toggle_heatmap.en,
    suspiciousRegionsLabel: ui.suspicious_regions_label[lang] || ui.suspicious_regions_label.en,
    scopeNoteHeading: ui.scope_note_heading[lang] || ui.scope_note_heading.en,
    scopeNote: ui.scope_note[lang] || ui.scope_note.en,
    externalSearchButton: ui.external_search_button[lang] || ui.external_search_button.en,
    consentModalTitle: ui.consent_modal_title[lang] || ui.consent_modal_title.en,
    consentModalBody: ui.consent_modal_body[lang] || ui.consent_modal_body.en,
    buttonProceed: ui.button_proceed[lang] || ui.button_proceed.en,
    buttonCancel: ui.button_cancel[lang] || ui.button_cancel.en,
  };
}

export function getErrorStrings(errorKey: 'network' | 'invalid_file' | 'image_too_small' | 'image_too_large', lang: Language): string {
  const errors = stringsData.ui.errors;
  const target = errors[errorKey];
  return target ? (target[lang] || target.en) : 'An error occurred during verification.';
}
