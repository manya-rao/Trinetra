import originalMock from '../mocks/original.json';
import modifiedMock from '../mocks/modified.json';
import outOfContextMock from '../mocks/out_of_context.json';
import aiConfirmedMock from '../mocks/ai_confirmed.json';
import likelyAiMock from '../mocks/likely_ai.json';
import likelyRealLookingMock from '../mocks/likely_real_looking.json';
import inconclusiveMock from '../mocks/inconclusive.json';

export type Verdict =
  | 'original'
  | 'modified'
  | 'out_of_context'
  | 'ai_confirmed'
  | 'likely_ai'
  | 'likely_real_looking'
  | 'inconclusive';

export type ConfidenceBand = 'high' | 'medium' | 'low' | 'n/a';

export interface ReasonItem {
  key: string;
  en: string;
  hi: string;
}

export interface EyesStatus {
  origin: 'found' | 'none' | 'inconclusive';
  change: 'found' | 'none' | 'n/a' | 'inconclusive';
  synthesis: 'confirmed' | 'likely' | 'none' | 'inconclusive';
}

export interface OriginDetail {
  source: string;
  date: string;
  factcheck_url: string;
  claim_en: string;
  claim_hi: string;
  thumb_url: string;
}

export interface ChangedRegion {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface DiffDetail {
  heatmap_url: string;
  aligned_url: string;
  changed_regions: ChangedRegion[];
}

export interface C2PADetail {
  status: string;
  issuer: string | null;
  ai_generated: boolean;
  history: Array<Record<string, unknown>>;
}

export interface LocalizedString {
  en: string;
  hi: string;
}

export interface ExternalSearch {
  lens: string;
  tineye: string;
}

export interface Passport {
  id: string;
  verdict: Verdict;
  confidence_band: ConfidenceBand;
  reasons: ReasonItem[];
  eyes: EyesStatus;
  origin: OriginDetail | null;
  diff: DiffDetail | null;
  c2pa: C2PADetail;
  suspicious_regions_url: string | null;
  scope_note: LocalizedString;
  external_search: ExternalSearch;
  lang: LocalizedString;
  demo_data: boolean;
}

export const MOCK_FIXTURES: Record<string, Passport> = {
  original: originalMock as unknown as Passport,
  modified: modifiedMock as unknown as Passport,
  out_of_context: outOfContextMock as unknown as Passport,
  ai_confirmed: aiConfirmedMock as unknown as Passport,
  likely_ai: likelyAiMock as unknown as Passport,
  likely_real_looking: likelyRealLookingMock as unknown as Passport,
  inconclusive: inconclusiveMock as unknown as Passport,
};

// Check if Mock Mode is forced via query param or env var
const urlParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
const isMockForced = urlParams ? urlParams.get('mock') !== '0' : (import.meta.env.VITE_MOCK !== '0');

export const config = {
  apiUrl: import.meta.env.VITE_API_URL || '',
  useMock: isMockForced,
};

export function setMockMode(enabled: boolean) {
  config.useMock = enabled;
}

export function getAvailableMocks(): string[] {
  return Object.keys(MOCK_FIXTURES);
}

export function getMockFixture(verdictKey: string): Passport {
  return MOCK_FIXTURES[verdictKey] || MOCK_FIXTURES.inconclusive;
}

/**
 * Normalizes any raw passport payload to guarantee null safety & schema adherence
 */
export function normalizePassport(raw: any): Passport {
  if (!raw || typeof raw !== 'object') {
    return MOCK_FIXTURES.inconclusive;
  }

  const validVerdicts: Verdict[] = [
    'original',
    'modified',
    'out_of_context',
    'ai_confirmed',
    'likely_ai',
    'likely_real_looking',
    'inconclusive',
  ];

  const verdict: Verdict = validVerdicts.includes(raw.verdict) ? raw.verdict : 'inconclusive';

  return {
    id: raw.id || `pass_${Date.now()}`,
    verdict,
    confidence_band: raw.confidence_band || 'low',
    reasons: Array.isArray(raw.reasons) ? raw.reasons : [],
    eyes: {
      origin: raw.eyes?.origin || 'inconclusive',
      change: raw.eyes?.change || 'n/a',
      synthesis: raw.eyes?.synthesis || 'inconclusive',
    },
    origin: raw.origin || null,
    diff: raw.diff || null,
    c2pa: raw.c2pa || { status: 'none', issuer: null, ai_generated: false, history: [] },
    suspicious_regions_url: raw.suspicious_regions_url || null,
    scope_note: raw.scope_note || {
      en: 'Matched against the Trinetra fact-check index. For a wider web search, tap below.',
      hi: 'त्रिनेत्र तथ्य-जांच सूचकांक से मिलान किया गया। व्यापक वेब खोज के लिए नीचे टैप करें।',
    },
    external_search: raw.external_search || { lens: 'https://lens.google.com/', tineye: 'https://tineye.com/' },
    lang: raw.lang || { en: '', hi: '' },
    demo_data: Boolean(raw.demo_data),
  };
}

export interface AnalyzeOptions {
  lang?: string;
  hashOnly?: boolean;
  preferredMock?: string | null;
  claimText?: string | null;
  consentExternal?: boolean;
}

export async function analyzeImage(fileOrBlob: File | Blob, options: AnalyzeOptions = {}): Promise<Passport> {
  const { lang = 'en', hashOnly = false, preferredMock = null, claimText = null, consentExternal = false } = options;

  if (config.useMock) {
    await new Promise((resolve) => setTimeout(resolve, 1200));

    let fixtureKey = preferredMock;
    if (!fixtureKey && 'name' in fileOrBlob && typeof (fileOrBlob as File).name === 'string') {
      const lower = (fileOrBlob as File).name.toLowerCase();
      for (const k of Object.keys(MOCK_FIXTURES)) {
        if (lower.includes(k)) {
          fixtureKey = k;
          break;
        }
      }
    }

    const mock = getMockFixture(fixtureKey || 'likely_ai');
    return normalizePassport(mock);
  }

  // Real backend call
  const formData = new FormData();
  formData.append('image', fileOrBlob);
  formData.append('lang', lang);
  formData.append('hash_only', hashOnly ? 'true' : 'false');
  formData.append('consent_external', consentExternal ? 'true' : 'false');
  if (claimText) {
    formData.append('claim_text', claimText);
  }

  try {
    const res = await fetch(`${config.apiUrl}/analyze`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }
    const data = await res.json();
    return normalizePassport(data);
  } catch (err) {
    console.warn('Backend call failed, falling back to normalized inconclusive mock:', err);
    throw err;
  }
}

export async function fetchPassport(passportId: string): Promise<Passport> {
  if (config.useMock) {
    return normalizePassport(getMockFixture('likely_ai'));
  }
  const res = await fetch(`${config.apiUrl}/passport/${passportId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return normalizePassport(data);
}
