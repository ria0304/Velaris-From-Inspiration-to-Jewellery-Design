// src/components/JewelryBlueprint.tsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { DesignPackage, SVGGenerationRequest } from '../types';
import { ShieldCheck, RefreshCw, Sparkles, AlertCircle } from 'lucide-react';

interface BlueprintProps {
  design: DesignPackage;
}

type ViewKey = 'perspective' | 'front' | 'side';

// Gem colour for the badge dot — pure frontend display only
const GEM_BADGE_COLOR: Record<string, string> = {
  diamond: '#E8F4F8', moissanite: '#E0ECFA', emerald: '#10B981',
  ruby: '#EF4444', sapphire: '#3B82F6', garnet: '#DC2626',
  aquamarine: '#22D3EE', opal: '#C084FC', amethyst: '#8B5CF6',
  pearl: '#FEF3C7', morganite: '#FB923C',
};

function getGemColor(stone: string): string {
  const k = stone.toLowerCase();
  for (const [name, color] of Object.entries(GEM_BADGE_COLOR)) {
    if (k.includes(name)) return color;
  }
  return '#E8F4F8';
}

// ── Skeleton shown while waiting for the backend ──────────────────────────────
function BlueprintSkeleton({ progress }: { progress: number }) {
  return (
    <svg viewBox="0 0 200 200" className="w-full h-full">
      <rect width="200" height="200" fill="#050C08" />
      {[25, 50, 75, 100, 125, 150, 175].map(v => (
        <React.Fragment key={v}>
          <line x1={v} y1="0"   x2={v}   y2="200" stroke="#0D2018" strokeWidth="0.5" opacity="0.5" />
          <line x1="0" y1={v}   x2="200" y2={v}   stroke="#0D2018" strokeWidth="0.5" opacity="0.5" />
        </React.Fragment>
      ))}
      <circle cx="100" cy="100" r="70" stroke="#0D2018" strokeWidth="0.5" fill="none" strokeDasharray="3 8" />
      <circle cx="100" cy="100" r="40" stroke="#0D2018" strokeWidth="0.5" fill="none" strokeDasharray="2 5" />
      {/* Animated gold arc */}
      <circle
        cx="100" cy="100" r="52"
        stroke="#DFBE8B"
        strokeWidth="1.5"
        fill="none"
        strokeDasharray={`${(progress / 100) * 327} 327`}
        strokeLinecap="round"
        transform="rotate(-90 100 100)"
        style={{ transition: 'stroke-dasharray 0.35s ease' }}
      />
      <text x="100" y="97"  fill="#DFBE8B" fontSize="7" fontFamily="monospace" textAnchor="middle" opacity="0.7">GENERATING</text>
      <text x="100" y="108" fill="#DFBE8B" fontSize="5" fontFamily="monospace" textAnchor="middle" opacity="0.4">BESPOKE ILLUSTRATION</text>
      {/* Corner crosshairs */}
      {([[12,12],[188,12],[12,188],[188,188]] as [number,number][]).map(([x,y],i) => (
        <g key={i} stroke="#0D2018" strokeWidth="1.2" opacity="0.7">
          <line x1={x-6} y1={y} x2={x+6} y2={y} />
          <line x1={x} y1={y-6} x2={x} y2={y+6} />
        </g>
      ))}
    </svg>
  );
}

// ── Helper to check if motif is animal type ──────────────────────────────────
function isAnimalMotif(motif: any): boolean {
  return motif?.type === 'animal';
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function JewelryBlueprint({ design }: BlueprintProps) {
  const [activeView, setActiveView] = useState<ViewKey>('perspective');
  // Cache: designId → { view → svg }
  const svgCache = useRef<Record<string, Partial<Record<ViewKey, string>>>>({});
  const [currentSVG, setCurrentSVG]       = useState<string | null>(null);
  const [isLoading, setIsLoading]         = useState(false);
  const [error, setError]                 = useState<string | null>(null);
  const [modelUsed, setModelUsed]         = useState<string | null>(null);
  const [streamProgress, setStreamProgress] = useState(0);
  const abortRef  = useRef<AbortController | null>(null);
  const cacheKey  = design.id;
  const spec      = design.spec;

  // ── Cache helpers ────────────────────────────────────────────────────────────
  const getCached = useCallback((view: ViewKey): string | null =>
    svgCache.current[cacheKey]?.[view] ?? null,
  [cacheKey]);

  const setCached = useCallback((view: ViewKey, svg: string) => {
    if (!svgCache.current[cacheKey]) svgCache.current[cacheKey] = {};
    svgCache.current[cacheKey][view] = svg;
  }, [cacheKey]);

  // ── Fetch from /api/generate-svg (backend → OpenRouter free model) ───────────
  const loadView = useCallback(async (view: ViewKey) => {
    const cached = getCached(view);
    if (cached) {
      setCurrentSVG(cached);
      setIsLoading(false);
      setError(null);
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);
    setCurrentSVG(null);
    setModelUsed(null);
    setStreamProgress(0);

    // Fake progress tick so the user sees movement during the backend call
    const ticker = setInterval(() => {
      setStreamProgress(p => Math.min(p + 2, 88));
    }, 300);

    try {
      const viewDescription = design.multiView[view];

      // ─── BUILD REQUEST WITH MOTIF DATA ──────────────────────────────────────
      const requestBody: SVGGenerationRequest = {
        design_id: design.id,
        design_name: design.name,
        prompt: design.prompt,
        notes: design.notes,
        view,
        view_description: viewDescription,
        jewelry_type: spec.type,
        metal: spec.metal,
        stone: spec.stone,
        stone_shape: spec.shape,
        stone_size: spec.stoneSize,
        setting: spec.setting,
        details: spec.details,
        motif: design.motif || null, // ← PASS MOTIF DATA TO BACKEND
      };

      const res = await fetch('/api/generate-svg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify(requestBody),
      });

      clearInterval(ticker);

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || `Server error ${res.status}`);
      }

      const data = await res.json();
      setStreamProgress(100);
      setModelUsed(data.model_used ?? null);
      setCached(view, data.svg);
      setCurrentSVG(data.svg);

    } catch (err: any) {
      clearInterval(ticker);
      if (err.name !== 'AbortError') {
        setError(err.message ?? 'SVG generation failed');
      }
    } finally {
      setIsLoading(false);
    }
  }, [design, spec, getCached, setCached]);

  // Reset + load on design change
  useEffect(() => {
    svgCache.current[cacheKey] = {};
    setActiveView('perspective');
    setModelUsed(null);
    loadView('perspective');
    return () => { abortRef.current?.abort(); };
  }, [design.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load on view switch
  useEffect(() => {
    loadView(activeView);
  }, [activeView]); // eslint-disable-line react-hooks/exhaustive-deps

  const views: { key: ViewKey; label: string }[] = [
    { key: 'perspective', label: 'Artistic Angle' },
    { key: 'front',       label: 'Front Face'     },
    { key: 'side',        label: 'Profile View'   },
  ];

  const gemColor      = getGemColor(spec.stone);
  const viewDesc      = design.multiView[activeView];
  const activeLabel   = views.find(v => v.key === activeView)?.label ?? '';
  
  // ─── Check if motif is present ──────────────────────────────────────────────
  const hasMotif = design.motif && design.motif.type !== 'abstract';
  const motifType = design.motif?.type || '';

  return (
    <div className="bg-[#0b120f] border border-[#1e3a2b] rounded-lg overflow-hidden shadow-2xl" id="jewelry-blueprint-wrapper">

      {/* ── Header ── */}
      <div className="px-6 py-4 border-b border-[#1e3a2b] bg-[#070c0a] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="w-2 h-2 rounded-full bg-[#DFBE8B] animate-pulse" />
            <h3 className="text-xs uppercase tracking-widest text-[#DFBE8B] font-semibold">
              Interactive Jewelry Visualizer
            </h3>
            {isLoading && (
              <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                <Sparkles className="w-3 h-3 animate-pulse" />
                Illustrating…
              </span>
            )}
            {modelUsed && !isLoading && (
              <span className="text-[9px] text-gray-500 font-mono bg-[#0a1411] border border-[#1e3a2b] px-1.5 py-0.5 rounded">
                {modelUsed.split('/').pop()?.replace(':free', '')}
              </span>
            )}
            {/* ─── Motif Badge ────────────────────────────────────────────────── */}
            {hasMotif && !isLoading && (
              <span className="text-[9px] text-[#DFBE8B] font-mono bg-[#1a3828] border border-[#DFBE8B]/30 px-2 py-0.5 rounded-full uppercase tracking-wider">
                {motifType} motif
              </span>
            )}
          </div>
          <p className="text-xl font-serif text-white tracking-wide mt-1">{design.name}</p>
        </div>

        {/* View tabs */}
        <div className="flex bg-[#0f1b14] border border-[#1e3a2b] p-1 rounded-md self-start md:self-auto">
          {views.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveView(key)}
              id={`view-${key}-btn`}
              className={`relative px-3 py-1.5 rounded text-xs font-medium uppercase tracking-wider transition ${
                activeView === key
                  ? 'bg-[#1a3828] text-[#DFBE8B] border border-[#DFBE8B]/30'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {label}
              {/* Green dot = cached */}
              {getCached(key) && (
                <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-emerald-400" />
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12">

        {/* ── SVG Canvas ── */}
        <div className="lg:col-span-7 bg-[#050807] p-6 flex flex-col items-center justify-center relative min-h-[360px] border-b lg:border-b-0 lg:border-r border-[#1e3a2b]">
          <div className="absolute top-4 left-4 text-[10px] text-emerald-500/50 font-mono flex flex-col gap-0.5 pointer-events-none select-none">
            <span>VELARIS STUDIO DESIGNER</span>
            <span>BESPOKE AI ILLUSTRATION</span>
            <span>PRECISION HAND-CRAFTED RATIOS</span>
          </div>
          <div className="absolute bottom-4 left-4 text-[10px] text-[#DFBE8B]/60 font-mono pointer-events-none select-none">
            STABILITY RATING: PERFECT HARMONY
          </div>

          {/* Canvas */}
          <div className="w-full max-w-sm aspect-square relative z-10">
            {error ? (
              <div className="w-full h-full flex flex-col items-center justify-center gap-3 text-center p-6">
                <AlertCircle className="w-8 h-8 text-red-400" />
                <p className="text-xs text-red-300 font-mono leading-relaxed break-all">{error}</p>
                <button
                  onClick={() => {
                    if (svgCache.current[cacheKey]) delete svgCache.current[cacheKey][activeView];
                    loadView(activeView);
                  }}
                  className="flex items-center gap-1.5 text-xs text-[#DFBE8B] border border-[#DFBE8B]/40 px-3 py-1.5 rounded hover:bg-[#DFBE8B]/10 transition"
                >
                  <RefreshCw className="w-3 h-3" /> Retry
                </button>
              </div>
            ) : currentSVG ? (
              <div
                className="w-full h-full drop-shadow-[0_0_18px_rgba(223,190,139,0.15)]"
                dangerouslySetInnerHTML={{ __html: currentSVG }}
              />
            ) : (
              <BlueprintSkeleton progress={streamProgress} />
            )}
          </div>

          {/* Gem badge */}
          <div className="absolute bottom-4 right-4 flex items-center gap-1.5 bg-[#0a1411]/80 border border-[#1e3a2b]/60 px-2.5 py-1.5 rounded text-[11px] text-gray-300">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: gemColor, border: '1px solid #1e3a2b' }} />
            <span className="font-medium tracking-wide text-xs">{spec.stone} ({spec.metal})</span>
          </div>
        </div>

        {/* ── Properties Panel ── */}
        <div className="lg:col-span-5 p-6 flex flex-col justify-between h-full bg-[#080d0b]">
          <div className="space-y-4">
            <span className="text-[10px] uppercase font-mono tracking-widest text-[#DFBE8B]/80 block border-b border-[#1e3a2b] pb-2">
              DESIGN DIMENSIONS
            </span>

            {/* Spec grid */}
            <div>
              <p className="text-xs text-gray-400 font-mono mb-1.5">GEM &amp; METAL OVERVIEW</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {([
                  ['Jewelry Style', spec.type],
                  ['Occasion',      spec.occasion],
                  ['Gem Size',      spec.stoneSize],
                  ['Setting Style', spec.setting],
                ] as [string,string][]).map(([label, value]) => (
                  <div key={label} className="bg-[#0f1b14] border border-[#1e3a2b]/30 p-2 rounded">
                    <span className="text-gray-400 font-serif block text-[10px]">{label}</span>
                    <span className="text-white font-medium">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* ─── Motif Details (NEW) ────────────────────────────────────────── */}
            {hasMotif && (
              <div>
                <p className="text-xs text-gray-400 font-mono mb-1.5">DESIGN MOTIF</p>
                <div className="bg-[#1a2820] border border-[#DFBE8B]/20 p-3 rounded">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] uppercase tracking-wider text-[#DFBE8B] font-mono">
                      {design.motif?.type}
                    </span>
                    <span className="w-1 h-1 rounded-full bg-[#DFBE8B]/30" />
                    <span className="text-[10px] text-gray-400 font-mono">
                      {design.motif?.elements?.length || 0} elements
                    </span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {design.motif?.description || 'Custom design motif'}
                  </p>
                  {design.motif?.visualKeywords && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {design.motif.visualKeywords.slice(0, 4).map((kw, i) => (
                        <span key={i} className="text-[8px] bg-[#0f1b14] text-gray-400 px-1.5 py-0.5 rounded border border-[#1e3a2b]/30">
                          {kw}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* View description */}
            <div>
              <p className="text-xs text-gray-400 font-mono mb-1.5">ARTISAN VIEW DETAILS</p>
              <div className="text-xs text-gray-300 leading-relaxed bg-[#0a1411] border border-[#1e3a2b]/80 p-3.5 rounded">
                <strong className="text-[#DFBE8B] font-sans font-semibold uppercase text-[10px] block tracking-wider mb-1">
                  {activeLabel} View
                </strong>
                <p className="italic leading-relaxed">{viewDesc}</p>
              </div>
            </div>

            {/* Progress bar */}
            {isLoading && (
              <div className="bg-[#0a1411] border border-[#1e3a2b]/50 rounded p-3 flex items-center gap-2">
                <RefreshCw className="w-3.5 h-3.5 text-[#DFBE8B] animate-spin shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] text-[#DFBE8B] font-mono mb-1.5">
                    Rendering bespoke illustration…
                  </div>
                  <div className="w-full bg-[#050c08] rounded-full h-1 border border-[#1e3a2b]/30">
                    <div
                      className="bg-[#DFBE8B] h-full rounded-full transition-all duration-300"
                      style={{ width: `${streamProgress}%` }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Cache dots */}
            <div className="flex items-center gap-3 pt-1">
              {views.map(({ key, label }) => (
                <div key={key} className="flex items-center gap-1 text-[10px] font-mono text-gray-500">
                  <span className={`w-1.5 h-1.5 rounded-full ${getCached(key) ? 'bg-emerald-400' : 'bg-gray-700'}`} />
                  {label.split(' ')[0]}
                </div>
              ))}
              <span className="text-[10px] text-gray-600 font-mono ml-auto">cached views</span>
            </div>
          </div>

          {/* Footer badge */}
          <div className="mt-6 pt-4 border-t border-[#1e3a2b]/50 flex items-center gap-3">
            <div className="p-2 bg-[#DFBE8B]/10 border border-[#DFBE8B]/20 rounded-md">
              <ShieldCheck className="w-5 h-5 text-[#DFBE8B]" />
            </div>
            <div className="text-xs">
              <span className="text-gray-400 font-serif block">Design Status</span>
              <span className="text-emerald-400 font-semibold font-mono tracking-wide">
                100% Craftsmanship Approved
              </span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
