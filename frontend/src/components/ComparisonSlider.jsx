import React, { useState, useRef, useCallback } from 'react';
import { Layers, SplitSquareVertical } from 'lucide-react';
import { strings, getTranslation } from '../strings';

export default function ComparisonSlider({ diff, userImageUrl, lang }) {
  const [sliderPos, setSliderPos] = useState(50); // percentage 0-100
  const [showHeatmap, setShowHeatmap] = useState(false);
  const containerRef = useRef(null);
  const isDragging = useRef(false);

  const originalUrl = diff?.aligned_url || 'https://picsum.photos/seed/orig_base/600/400';
  const heatmapUrl = diff?.heatmap_url || null;
  const changedRegions = diff?.changed_regions || [];

  const handleMove = useCallback((clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPos(percentage);
  }, []);

  const onMouseDown = () => { isDragging.current = true; };
  const onMouseUp = () => { isDragging.current = false; };
  const onMouseMove = (e) => {
    if (isDragging.current) handleMove(e.clientX);
  };

  const onTouchMove = (e) => {
    if (e.touches[0]) handleMove(e.touches[0].clientX);
  };

  return (
    <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-4 sm:p-5 space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <SplitSquareVertical className="w-5 h-5 text-sky-400" />
          <h3 className="font-semibold text-slate-100 text-sm sm:text-base">
            {getTranslation(strings.ui.tab_comparison, lang)}
          </h3>
        </div>

        {heatmapUrl && (
          <button
            type="button"
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border ${
              showHeatmap
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-800'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{getTranslation(strings.ui.toggle_heatmap, lang)}</span>
          </button>
        )}
      </div>

      {/* Slider Container */}
      <div
        ref={containerRef}
        className="relative w-full aspect-[4/3] sm:aspect-[16/10] overflow-hidden rounded-xl bg-slate-950 select-none cursor-ew-resize border border-slate-800 shadow-inner"
        onMouseMove={onMouseMove}
        onMouseDown={onMouseDown}
        onMouseUp={onMouseUp}
        onTouchMove={onTouchMove}
      >
        {/* Under layer: Original Archive Image */}
        <img
          src={originalUrl}
          alt="Original Verified Archive"
          className="absolute inset-0 w-full h-full object-cover"
        />

        {/* Heatmap overlay (if active) */}
        {showHeatmap && heatmapUrl && (
          <img
            src={heatmapUrl}
            alt="Edit Heatmap Inconsistency Overlay"
            className="absolute inset-0 w-full h-full object-cover opacity-75 mix-blend-screen pointer-events-none"
          />
        )}

        {/* Top layer (clipped by slider): User Suspicious Image */}
        <div
          className="absolute inset-0 overflow-hidden"
          style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
        >
          <img
            src={userImageUrl || 'https://picsum.photos/seed/user_mod/600/400'}
            alt="User Suspicious Upload"
            className="absolute inset-0 w-full h-full object-cover"
          />

          {/* Spliced Region Highlight Boxes */}
          {changedRegions.map((region, idx) => (
            <div
              key={idx}
              className="absolute border-2 border-dashed border-amber-400 bg-amber-500/20 pointer-events-none rounded animate-pulse"
              style={{
                left: `${(region.x / 400) * 100}%`,
                top: `${(region.y / 300) * 100}%`,
                width: `${(region.w / 400) * 100}%`,
                height: `${(region.h / 300) * 100}%`
              }}
            />
          ))}
        </div>

        {/* Vertical Divider Line */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_10px_rgba(255,255,255,0.7)] pointer-events-none"
          style={{ left: `${sliderPos}%` }}
        >
          <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-slate-900/90 border-2 border-white shadow-xl flex items-center justify-center text-white">
            <SplitSquareVertical className="w-4 h-4 text-sky-400" />
          </div>
        </div>

        {/* Corner labels */}
        <div className="absolute top-2 left-2 px-2 py-1 rounded bg-black/70 backdrop-blur-sm text-[11px] font-bold text-slate-200 pointer-events-none">
          User Image
        </div>
        <div className="absolute top-2 right-2 px-2 py-1 rounded bg-black/70 backdrop-blur-sm text-[11px] font-bold text-slate-200 pointer-events-none">
          Original Source
        </div>
      </div>

      <p className="text-xs text-slate-400 text-center">
        Drag slider left or right to inspect spliced and modified pixel boundaries.
      </p>
    </div>
  );
}
