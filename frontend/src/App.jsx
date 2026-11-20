import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import HomeScreen from './components/HomeScreen';
import AnalyzingScreen from './components/AnalyzingScreen';
import PassportScreen from './components/PassportScreen';
import ShareCardScreen from './components/ShareCardScreen';
import { analyzeImage, getMockFixture, normalizePassport } from './api/client';

export default function App() {
  const [screen, setScreen] = useState('home'); // 'home' | 'analyzing' | 'passport' | 'shareCard'
  const [lang, setLang] = useState('en'); // 'en' | 'hi'
  const [hashOnly, setHashOnly] = useState(false);
  const [activeMock, setActiveMock] = useState('likely_ai');
  const [passport, setPassport] = useState(null);
  const [userImageUrl, setUserImageUrl] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Register service worker and handle Web Share Target incoming files
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch((err) => {
        console.debug('ServiceWorker registration ignored/unsupported in sandbox:', err);
      });
    }

    // Check if redirected from PWA share-target
    const params = new URLSearchParams(window.location.search);
    if (params.get('shared') === '1' && 'caches' in window) {
      caches.open('trinetra-shared').then(async (cache) => {
        const response = await cache.match('/shared-image');
        if (response) {
          const blob = await response.blob();
          handleSelectImage(blob);
          cache.delete('/shared-image');
        }
      });
    }
  }, []);

  const handleSelectImage = useCallback(async (fileOrBlob) => {
    setErrorMsg(null);
    if (!fileOrBlob) return;

    // Minimum sanity check
    if (fileOrBlob.size && fileOrBlob.size > 25 * 1024 * 1024) {
      setErrorMsg('Image file size exceeds maximum limit of 25MB.');
      return;
    }

    // Revoke any previous object URL to prevent memory leaks
    if (userImageUrl) {
      URL.revokeObjectURL(userImageUrl);
    }

    const objectUrl = URL.createObjectURL(fileOrBlob);
    setUserImageUrl(objectUrl);
    setScreen('analyzing');

    try {
      const result = await analyzeImage(fileOrBlob, {
        lang,
        hashOnly,
        preferredMock: activeMock
      });
      setPassport(result);
      setScreen('passport');
    } catch (err) {
      console.error('Scan error:', err);
      setErrorMsg('Analysis failed. Falling back to safe inconclusive state.');
      setPassport(normalizePassport(getMockFixture('inconclusive')));
      setScreen('passport');
    }
  }, [lang, hashOnly, activeMock, userImageUrl]);

  const handleReset = useCallback(() => {
    if (userImageUrl) {
      URL.revokeObjectURL(userImageUrl);
      setUserImageUrl(null);
    }
    setPassport(null);
    setErrorMsg(null);
    setScreen('home');
  }, [userImageUrl]);

  const handleSelectMockDirectly = (mockKey) => {
    setActiveMock(mockKey);
    const mockData = getMockFixture(mockKey);
    setPassport(normalizePassport(mockData));
    if (!userImageUrl) {
      setUserImageUrl('https://picsum.photos/seed/trinetra_sample/600/400');
    }
    setScreen('passport');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0c1017] text-slate-100">
      <Header
        lang={lang}
        setLang={setLang}
        activeMock={activeMock}
        setActiveMock={handleSelectMockDirectly}
        onReset={handleReset}
      />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-6">
        {screen === 'home' && (
          <HomeScreen
            onSelectImage={handleSelectImage}
            lang={lang}
            hashOnly={hashOnly}
            setHashOnly={setHashOnly}
            errorMsg={errorMsg}
          />
        )}

        {screen === 'analyzing' && (
          <AnalyzingScreen lang={lang} />
        )}

        {screen === 'passport' && passport && (
          <PassportScreen
            passport={passport}
            userImageUrl={userImageUrl}
            lang={lang}
            onReset={handleReset}
            onOpenShareCard={() => setScreen('shareCard')}
          />
        )}

        {screen === 'shareCard' && passport && (
          <ShareCardScreen
            passport={passport}
            lang={lang}
            onBack={() => setScreen('passport')}
          />
        )}
      </main>

      <footer className="border-t border-slate-900 py-4 text-center text-xs text-slate-400">
        <p>Trinetra &bull; Team Kinetix &bull; Code for Innovex '26 (Navyug &mdash; A New Era)</p>
      </footer>
    </div>
  );
}
