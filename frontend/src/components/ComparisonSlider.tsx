import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ChangedRegion } from '../api/client';

interface ComparisonSliderProps {
  userImageUrl: string | null;
  originalThumbUrl: string | null;
  changedRegions?: ChangedRegion[] | null;
  hasSuspiciousOverlay?: boolean;
  lang: 'en' | 'hi';
}

export const ComparisonSlider: React.FC<ComparisonSliderProps> = ({
  userImageUrl,
  originalThumbUrl,
  changedRegions = [],
  hasSuspiciousOverlay = false,
  lang,
}) => {
  const [sliderPos, setSliderPos] = useState<number>(50);
  const [showChanges, setShowChanges] = useState<boolean>(true);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const handlePointerDown = () => {
    setIsDragging(true);
  };

  const handlePointerMove = useCallback(
    (e: PointerEvent) => {
      if (!isDragging || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const pct = Math.round((x / rect.width) * 100);
      setSliderPos(pct);
    },
    [isDragging]
  );

  const handlePointerUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('pointermove', handlePointerMove);
      window.addEventListener('pointerup', handlePointerUp);
    }
    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };
  }, [isDragging, handlePointerMove, handlePointerUp]);

  // Keyboard navigation for role="slider"
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      setSliderPos((prev) => Math.max(0, prev - 5));
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      setSliderPos((prev) => Math.min(100, prev + 5));
    } else if (e.key === 'Home') {
      e.preventDefault();
      setSliderPos(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      setSliderPos(100);
    }
  };

  return (
    <div className="w-full space-y-3">
      {/* Controls Bar: Toggle & Slider labels */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-4 text-muted">
          <span>{lang === 'en' ? 'YOUR IMAGE (LEFT)' : 'आपकी छवि (बाएं)'}</span>
          <span>&bull;</span>
          <span>{lang === 'en' ? 'ORIGINAL (RIGHT)' : 'मूल स्रोत (दाएं)'}</span>
        </div>

        {changedRegions && changedRegions.length > 0 && (
          <button
            type="button"
            onClick={() => setShowChanges(!showChanges)}
            className={`flex items-center gap-2 px-3 py-1 rounded border text-xs font-mono transition-colors focus:outline-none focus:ring-1 focus:ring-accent ${
              showChanges
                ? 'border-amber-400 bg-amber-400/15 text-amber-300'
                : 'border-surface bg-void-2 text-muted hover:text-text'
            }`}
            aria-pressed={showChanges}
          >
            <span
              className={`w-2 h-2 rounded-full ${showChanges ? 'bg-amber-400 animate-pulse' : 'bg-muted'}`}
            />
            {lang === 'en' ? 'Highlight Edit Heatmap' : 'एडिट हीटमैप दिखाएं'}
          </button>
        )}
      </div>

      {/* Comparison Viewport */}
      <div
        ref={containerRef}
        role="slider"
        tabIndex={0}
        aria-label="Image comparison split"
        aria-valuenow={sliderPos}
        aria-valuemin={0}
        aria-valuemax={100}
        onKeyDown={handleKeyDown}
        onPointerDown={handlePointerDown}
        className="relative w-full h-64 sm:h-80 md:h-96 rounded-xl border border-surface overflow-hidden bg-void select-none cursor-ew-resize focus:outline-none focus:ring-2 focus:ring-accent shadow-xl"
      >
        {/* Layer 1 (Right): Verified Original Reference */}
        <div className="absolute inset-0 flex items-center justify-center bg-void-2">
          {originalThumbUrl ? (
            <img
              src={originalThumbUrl}
              alt="Verified Origin Reference"
              className="w-full h-full object-contain pointer-events-none"
              onError={(e) => {
                // If local image fails to load, fallback to styled SVG placeholder
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          ) : (
            <div className="flex flex-col items-center justify-center p-6 text-center text-muted font-mono text-xs">
              <svg viewBox="0 0 48 48" className="w-12 h-12 stroke-muted/60 mb-2" fill="none">
                <rect x="6" y="8" width="36" height="32" rx="4" strokeWidth="1.5" />
                <circle cx="16" cy="18" r="4" strokeWidth="1.5" />
                <path d="M 6 34 L 18 22 L 28 32 L 34 26 L 42 34" strokeWidth="1.5" />
              </svg>
              <span>{lang === 'en' ? 'Verified Origin Reference' : 'सत्यापित मूल संदर्भ'}</span>
              <span className="text-[10px] text-accent mt-1">DEMO ARCHIVE 2021</span>
            </div>
          )}
          <span className="absolute bottom-3 right-3 font-mono text-[10px] bg-void/80 text-muted px-2 py-0.5 rounded border border-surface pointer-events-none">
            {lang === 'en' ? 'ORIGINAL' : 'मूल छवि'}
          </span>
        </div>

        {/* Layer 2 (Left): Your Submitted Image (clipped to sliderPos) */}
        <div
          className="absolute inset-0 overflow-hidden"
          style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
        >
          <div className="relative w-full h-full flex items-center justify-center bg-void">
            {userImageUrl ? (
              <img
                src={userImageUrl}
                alt="Submitted Image"
                className="w-full h-full object-contain pointer-events-none"
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-6 text-center text-accent font-mono text-xs">
                <svg viewBox="0 0 48 48" className="w-12 h-12 stroke-accent mb-2" fill="none">
                  <rect x="8" y="8" width="32" height="32" rx="4" strokeWidth="1.5" strokeDasharray="3 3" />
                  <path d="M 16 24 L 32 24 M 24 16 L 24 32" strokeWidth="1.5" />
                </svg>
                <span>{lang === 'en' ? 'Submitted Query Image' : 'प्रस्तुत की गई छवि'}</span>
              </div>
            )}

            {/* Changed Regions Bounding Boxes Overlay */}
            {showChanges &&
              changedRegions &&
              changedRegions.map((region, i) => (
                <div
                  key={i}
                  className="absolute border-2 border-amber-400 bg-amber-400/25 pointer-events-none animate-pulse rounded"
                  style={{
                    left: `${region.x % 70}%`,
                    top: `${region.y % 60}%`,
                    width: `${Math.max(20, region.w % 40)}%`,
                    height: `${Math.max(20, region.h % 40)}%`,
                  }}
                >
                  <span className="absolute -top-5 left-0 font-mono text-[9px] bg-amber-400 text-void font-bold px-1.5 py-0.2 rounded">
                    DIFF Δ
                  </span>
                </div>
              ))}

            {/* Suspicious regions label */}
            {hasSuspiciousOverlay && (
              <div className="absolute top-3 left-3 bg-orange-500/90 text-void font-mono text-[10px] font-bold px-2 py-0.5 rounded shadow pointer-events-none">
                {lang === 'en' ? 'Suspicious regions, not proof' : 'संभावित संदेहास्पद क्षेत्र (प्रमाण नहीं)'}
              </div>
            )}

            <span className="absolute bottom-3 left-3 font-mono text-[10px] bg-void/80 text-accent px-2 py-0.5 rounded border border-surface pointer-events-none">
              {lang === 'en' ? 'SUBMITTED' : 'प्रस्तुत छवि'}
            </span>
          </div>
        </div>

        {/* Split Divider Line & Handle */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-accent pointer-events-none"
          style={{ left: `${sliderPos}%` }}
        >
          <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full border-2 border-accent bg-void-2 flex items-center justify-center shadow-lg">
            <svg viewBox="0 0 16 16" className="w-4 h-4 fill-accent" xmlns="http://www.w3.org/2000/svg">
              <path d="M 4 8 L 8 4 L 8 12 Z M 12 8 L 8 4 L 8 12 Z" />
            </svg>
          </div>
        </div>
      </div>

      <div className="text-center font-mono text-[11px] text-muted/60">
        {lang === 'en'
          ? 'Drag slider or use Left / Right arrow keys to compare'
          : 'तुलना करने हेतु स्लाइडर खींचें या तीर (Left / Right) कुंजियों का उपयोग करें'}
      </div>
    </div>
  );
};
