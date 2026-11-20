import stringsData from '../../shared/strings.json';

export const strings = stringsData;

export function getTranslation(dict, lang = 'en') {
  if (!dict) return '';
  if (typeof dict === 'string') return dict;
  return dict[lang] || dict['en'] || '';
}

export function getVerdictConfig(verdictKey) {
  const verdict = strings.verdicts[verdictKey] || strings.verdicts.inconclusive;
  return verdict;
}

export function getReasonText(reasonKey, lang = 'en') {
  const reason = strings.reasons[reasonKey];
  if (!reason) return reasonKey;
  return reason[lang] || reason.en;
}
