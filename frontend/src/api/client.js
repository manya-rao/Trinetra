import originalMock from '../mocks/original.json';
import modifiedMock from '../mocks/modified.json';
import outOfContextMock from '../mocks/out_of_context.json';
import aiConfirmedMock from '../mocks/ai_confirmed.json';
import likelyAiMock from '../mocks/likely_ai.json';
import likelyRealLookingMock from '../mocks/likely_real_looking.json';
import inconclusiveMock from '../mocks/inconclusive.json';

const MOCK_FIXTURES = {
  original: originalMock,
  modified: modifiedMock,
  out_of_context: outOfContextMock,
  ai_confirmed: aiConfirmedMock,
  likely_ai: likelyAiMock,
  likely_real_looking: likelyRealLookingMock,
  inconclusive: inconclusiveMock
};

// Check if Mock Mode is forced via query param or default env
const urlParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
const isMockForced = urlParams ? urlParams.get('mock') !== '0' : true;

export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  useMock: isMockForced
};

export function setMockMode(enabled) {
  config.useMock = enabled;
}

export function getAvailableMocks() {
  return Object.keys(MOCK_FIXTURES);
}

export function getMockFixture(verdictKey) {
  return MOCK_FIXTURES[verdictKey] || MOCK_FIXTURES.inconclusive;
}

/**
 * Normalizes passport payload to guarantee null safety & schema adherence
 */
export function normalizePassport(raw) {
  if (!raw) return MOCK_FIXTURES.inconclusive;
  
  const validVerdicts = [
    'original', 'modified', 'out_of_context',
    'ai_confirmed', 'likely_ai', 'likely_real_looking', 'inconclusive'
  ];
  
  const verdict = validVerdicts.includes(raw.verdict) ? raw.verdict : 'inconclusive';
  
  return {
    id: raw.id || `pass_${Date.now()}`,
    verdict: verdict,
    confidence_band: raw.confidence_band || 'medium',
    reasons: Array.isArray(raw.reasons) ? raw.reasons : [],
    eyes: {
      origin: raw.eyes?.origin || 'inconclusive',
      change: raw.eyes?.change || 'n/a',
      synthesis: raw.eyes?.synthesis || 'inconclusive'
    },
    origin: raw.origin || null,
    diff: raw.diff || null,
    c2pa: raw.c2pa || { status: 'none', issuer: null, ai_generated: false, history: [] },
    suspicious_regions_url: raw.suspicious_regions_url || null,
    scope_note: raw.scope_note || {
      en: "Matched against the Trinetra fact-check index. For a wider web search, tap below.",
      hi: "त्रिनेत्र तथ्य-जांच सूचकांक से मिलान किया गया। व्यापक वेब खोज के लिए नीचे टैप करें।"
    },
    external_search: raw.external_search || { lens: '#', tineye: '#' },
    lang: raw.lang || { en: '', hi: '' },
    demo_data: Boolean(raw.demo_data)
  };
}

/**
 * Analyzes an image (POST /analyze) or loads corresponding mock based on filename or active mock selection
 */
export async function analyzeImage(fileOrBlob, options = {}) {
  const { lang = 'en', hashOnly = false, preferredMock = null } = options;

  if (config.useMock) {
    // Artificial latency for analyzing animation fidelity
    await new Promise((resolve) => setTimeout(resolve, 1400));
    
    // Check if filename suggests fixture
    let fixtureKey = preferredMock;
    if (!fixtureKey && fileOrBlob && fileOrBlob.name) {
      const lower = fileOrBlob.name.toLowerCase();
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
  formData.append('hash_only', hashOnly ? '1' : '0');

  try {
    const res = await fetch(`${config.apiUrl}/analyze`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }
    const data = await res.json();
    return normalizePassport(data);
  } catch (err) {
    console.warn('Backend call failed, falling back to mock fixture:', err);
    return normalizePassport(getMockFixture('inconclusive'));
  }
}

/**
 * Fetches passport by ID (GET /passport/{id})
 */
export async function fetchPassport(passportId) {
  if (config.useMock) {
    return normalizePassport(getMockFixture('likely_ai'));
  }
  const res = await fetch(`${config.apiUrl}/passport/${passportId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return normalizePassport(data);
}
