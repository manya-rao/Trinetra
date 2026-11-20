import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, Camera, Image as ImageIcon, Shield, Smartphone, Lock, AlertCircle } from 'lucide-react';
import { strings, getTranslation } from '../strings';

export default function HomeScreen({ onSelectImage, lang, hashOnly, setHashOnly, errorMsg }) {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  // Global paste handler (Ctrl+V)
  useEffect(() => {
    const handlePaste = (e) => {
      if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
        const file = e.clipboardData.files[0];
        if (file.type.startsWith('image/')) {
          onSelectImage(file);
        }
      }
    };
    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [onSelectImage]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/')) {
        onSelectImage(file);
      }
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onSelectImage(e.target.files[0]);
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-6 py-4 animate-fade-in">
      {/* Hero Headline */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white leading-tight">
          Verify Image Origin, Edits & AI Synthesis
        </h1>
        <p className="text-sm sm:text-base text-slate-300 max-w-md mx-auto leading-relaxed">
          {getTranslation(strings.ui.app_tagline, lang)}
        </p>
      </div>

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-500/50 flex items-center gap-2.5 text-red-300 text-xs sm:text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Upload Dropzone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative group rounded-3xl border-2 border-dashed p-6 sm:p-10 text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-sky-400 bg-sky-950/30 scale-[1.01]'
            : 'border-slate-700/80 hover:border-slate-500 bg-slate-900/40 hover:bg-slate-900/60'
        }`}
        role="button"
        tabIndex={0}
        aria-label="Upload suspicious image"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={handleChange}
        />
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={handleChange}
        />

        <div className="flex flex-col items-center gap-3">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-sky-600/20 to-indigo-600/20 border border-sky-500/30 flex items-center justify-center text-sky-400 group-hover:scale-110 transition-transform">
            <UploadCloud className="w-8 h-8" />
          </div>

          <div className="space-y-1">
            <p className="font-bold text-base sm:text-lg text-white">
              {getTranslation(strings.ui.drop_zone_title, lang)}
            </p>
            <p className="text-xs sm:text-sm text-slate-400">
              {getTranslation(strings.ui.drop_zone_sub, lang)}
            </p>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <span className="text-[11px] font-medium text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded-md">
              JPEG, PNG, WebP
            </span>
            <span className="text-[11px] font-medium text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded-md">
              Min 256x256 px
            </span>
          </div>

          <p className="text-xs text-sky-400/80 font-medium pt-1">
            {getTranslation(strings.ui.paste_hint, lang)}
          </p>
        </div>
      </div>

      {/* Secondary Mobile Actions: Camera Button */}
      <div className="sm:hidden flex justify-center">
        <button
          type="button"
          onClick={() => cameraInputRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-2xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-semibold active:scale-95 transition-transform"
        >
          <Camera className="w-4 h-4 text-sky-400" />
          <span>Take Photo with Camera</span>
        </button>
      </div>

      {/* WhatsApp Share Hint */}
      <div className="p-3.5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 flex items-center gap-3 text-emerald-300">
        <Smartphone className="w-5 h-5 shrink-0 text-emerald-400" />
        <p className="text-xs sm:text-sm leading-snug">
          {getTranslation(strings.ui.share_whatsapp_hint, lang)}
        </p>
      </div>

      {/* Hash-Only Privacy Toggle */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <Lock className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <label htmlFor="hash-toggle" className="text-xs sm:text-sm font-semibold text-slate-200 cursor-pointer">
              {getTranslation(strings.ui.privacy_hash_only, lang)}
            </label>
            <p className="text-[11px] text-slate-400">
              Only perceptual hash is sent first. If previously verified, original pixels never leave device.
            </p>
          </div>
        </div>

        <input
          id="hash-toggle"
          type="checkbox"
          checked={hashOnly}
          onChange={(e) => setHashOnly(e.target.checked)}
          className="w-4 h-4 text-sky-600 bg-slate-800 border-slate-700 rounded focus:ring-sky-500 cursor-pointer"
        />
      </div>

      {/* Privacy Guarantee Note */}
      <p className="text-center text-xs text-slate-400 flex items-center justify-center gap-1.5 pt-1">
        <Shield className="w-3.5 h-3.5 text-slate-400" />
        <span>{getTranslation(strings.ui.privacy_disclaimer, lang)}</span>
      </p>
    </div>
  );
}
