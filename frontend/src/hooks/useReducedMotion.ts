import { useState, useEffect } from 'react';

export function useReducedMotion(): boolean {
  const [prefersReduced, setPrefersReduced] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setPrefersReduced(mediaQuery.matches);
    mediaQuery.addEventListener('change', onChange);
    return () => mediaQuery.removeEventListener('change', onChange);
  }, []);

  return prefersReduced;
}
