// src/components/PresentationBoard.tsx — pilot editorial board (software only).
// Hero shows BOTH realistic + CAD (toggle + side-by-side), then Front/Back
// columns like the reference, transformation strip, details rail.
import React, { useEffect, useState } from 'react';
import DOMPurify from 'dompurify';
import type { DesignPackage } from '../types';

interface BoardView { svg: string; png_b64: string; note: string; source?: string }
interface BoardData {
  design_name: string; tagline: string;
  hero: BoardView; front: BoardView; back: BoardView; strip: BoardView[];
  features: string[]; gems: { name: string; shape: string; weight: string; dims: string }[];
  specs: Record<string, string | number>;
}

type HeroMode = 'both' | 'realistic' | 'cad';

export default function PresentationBoard({ design }: { design: DesignPackage }) {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [heroMode, setHeroMode] = useState<HeroMode>('both');
  const [showBoard, setShowBoard] = useState(true);
  const [shareMsg, setShareMsg] = useState<string | null>(null);

  async function shareBoard() {
    const url = window.location.href;
    const text = `${board?.design_name ?? design.name} — Velaris presentation board`;
    try {
      if (navigator.share) {
        await navigator.share({ title: text, url });
        return;
      }
      await navigator.clipboard.writeText(`${text}\n${url}`);
      setShareMsg('Link copied to clipboard');
    } catch {
      setShareMsg('Sharing not available in this browser');
    }
    setTimeout(() => setShareMsg(null), 2500);
  }

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true); setError(null);
      try {
        const res = await fetch('/api/presentation-board', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            design_id: design.id, design_name: design.name,
            jewelry_type: design.spec.type, metal: design.spec.metal,
            stone: design.spec.stone, stone_shape: design.spec.shape,
            stone_size: design.spec.stoneSize, setting: design.spec.setting,
            band_width: design.spec.bandWidth, motif: design.motif || null,
            view_notes: design.multiView,
          }),
        });
        if (!res.ok) throw new Error(await res.text() || `Server error ${res.status}`);
        const data = await res.json();
        if (!cancelled) setBoard(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Board failed to load');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [design.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!showBoard) {
    return (
      <div className="mt-6 text-center">
        <button onClick={() => setShowBoard(true)} id="board-show-btn"
          className="text-xs uppercase tracking-widest text-[#DFBE8B] border border-[#DFBE8B]/40 px-4 py-2 rounded hover:bg-[#DFBE8B]/10 transition">
          Show Presentation Board (Pilot)
        </button>
      </div>
    );
  }

  return (
    <div className="mt-6 overflow-hidden rounded-lg border border-[#1e3a2b]" id="presentation-board">
      {/* Board header */}
      <div className="flex items-center justify-between bg-[#070c0a] px-6 py-3 border-b border-[#1e3a2b]">
        <span className="text-xs uppercase tracking-widest text-[#DFBE8B] font-semibold">
          Presentation Board · Pilot
        </span>
        <div className="flex items-center gap-2">
          {(['both', 'realistic', 'cad'] as HeroMode[]).map(m => (
            <button key={m} onClick={() => setHeroMode(m)} id={`board-hero-${m}-btn`}
              className={`px-3 py-1 rounded text-[11px] uppercase tracking-wider transition ${
                heroMode === m ? 'bg-[#1a3828] text-[#DFBE8B] border border-[#DFBE8B]/30'
                               : 'text-gray-400 hover:text-white'}`}>
              {m === 'both' ? 'Both' : m === 'realistic' ? 'Realistic' : 'CAD'}
            </button>
          ))}
          <button onClick={() => setShowBoard(false)} id="board-hide-btn"
            className="ml-2 text-[11px] text-gray-500 hover:text-white uppercase tracking-wider">Hide</button>
          <button onClick={shareBoard} id="board-share-btn"
            className="ml-2 text-[11px] uppercase tracking-wider text-[#DFBE8B] border border-[#DFBE8B]/40 px-3 py-1 rounded hover:bg-[#DFBE8B]/10 transition">Share</button>
          {shareMsg && <span className="ml-2 text-[11px] font-mono text-emerald-400">{shareMsg}</span>}
        </div>
      </div>

      {loading && (
        <div className="bg-[#0b120f] px-6 py-10 text-center text-xs font-mono text-[#DFBE8B]/70">
          Composing presentation board…
        </div>
      )}
      {error && (
        <div className="bg-[#0b120f] px-6 py-8 text-center">
          <p className="text-xs font-mono text-red-300 break-all">{error}</p>
          <button onClick={() => window.location.reload()} className="mt-3 text-xs text-[#DFBE8B] border border-[#DFBE8B]/40 px-3 py-1.5 rounded">Retry</button>
        </div>
      )}

      {board && (
        <>
          {/* ── Row 1: Hero (BOTH) + Front + Back + Details ── */}
          <div className="grid grid-cols-1 xl:grid-cols-12">
            {/* Hero */}
            <div className="xl:col-span-4 bg-[#F5F0EB] p-6 text-[#1A1A1A]">
              <h2 className="font-serif text-2xl leading-tight">{board.design_name}</h2>
              <p className="text-sm italic text-[#555] mt-0.5">{board.tagline}</p>
              {(heroMode === 'both' || heroMode === 'realistic') && (
                <>
                  <img src={`data:image/png;base64,${board.hero.png_b64}`} alt={`${board.design_name} realistic hero`}
                    className={`w-full mt-4 rounded shadow ${heroMode === 'both' ? 'aspect-square object-cover' : ''}`} id="board-hero-realistic" />
                  <p className="mt-1 text-[10px] font-mono text-[#888]">
                    {board.hero.source === 'diffusion' || board.hero.source === 'diffusion-cached'
                      ? '✨ AI diffusion render — illustrative, see CAD for exact dimensions'
                      : 'Procedural preview — add HUGGINGFACE_API_KEY for AI diffusion renders'}
                  </p>
                </>
              )}
              {(heroMode === 'both' || heroMode === 'cad') && (
                <div className="w-full mt-4 rounded bg-[#050C08] p-2" id="board-hero-cad"
                  dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(board.hero.svg, { USE_PROFILES: { svg: true } }) }} />
              )}
              <p className="mt-3 text-[11px] text-[#666] font-mono">
                {design.spec.type} · {design.spec.stone} {design.spec.stoneSize}
              </p>
            </div>
            {/* Front column */}
            <div className="xl:col-span-3 bg-[#0a0a0a] p-6 border-t xl:border-t-0 xl:border-l border-[#1e3a2b]">
              <p className="text-[10px] font-mono uppercase tracking-widest text-gray-500">1 · Front</p>
              <img src={`data:image/png;base64,${board.front.png_b64}`} alt="Front view"
                className="w-full mt-2 rounded" id="board-front-realistic" />
              <div className="mt-2 bg-[#050C08] rounded p-1" id="board-front-cad"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(board.front.svg, { USE_PROFILES: { svg: true } }) }} />
              <p className="mt-2 text-center text-xs text-gray-300">Front<br /><span className="text-gray-500 font-mono text-[11px]">{design.spec.stone}</span></p>
            </div>
            {/* Back column */}
            <div className="xl:col-span-3 bg-[#0a0a0a] p-6 border-t xl:border-t-0 xl:border-l border-[#2a2a2a] relative">
              <span className="hidden xl:flex absolute top-1/2 -left-3 -translate-y-1/2 w-6 h-6 items-center justify-center rounded-full bg-[#1a3828] text-[#DFBE8B] text-sm">→</span>
              <p className="text-[10px] font-mono uppercase tracking-widest text-gray-500">2 · Back</p>
              <img src={`data:image/png;base64,${board.back.png_b64}`} alt="Back view"
                className="w-full mt-2 rounded" id="board-back-realistic" />
              <div className="mt-2 bg-[#050C08] rounded p-1" id="board-back-cad"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(board.back.svg, { USE_PROFILES: { svg: true } }) }} />
              <p className="mt-2 text-center text-xs text-gray-300">Back<br /><span className="text-gray-500 font-mono text-[11px]">pin · hinge · catch</span></p>
            </div>
            {/* Details rail */}
            <div className="xl:col-span-2 bg-[#F5F0EB] p-6 text-[#1A1A1A] border-t xl:border-t-0 xl:border-l border-[#d8cfc2]">
              <p className="text-xs font-bold uppercase tracking-wider">Key Features</p>
              <ul className="mt-2 space-y-1.5 text-xs leading-relaxed list-disc list-inside">
                {board.features.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
              <p className="mt-4 text-xs font-bold uppercase tracking-wider">Gemstones Used</p>
              {board.gems.map((g, i) => (
                <div key={i} className="mt-2 text-xs">
                  <p className="font-semibold">{g.name} ({g.shape})</p>
                  <p className="text-[#666] font-mono text-[11px]">{g.weight} · {g.dims}</p>
                </div>
              ))}
              <p className="mt-4 text-xs font-bold uppercase tracking-wider">Dimensions</p>
              <div className="mt-1 text-[11px] font-mono text-[#444] space-y-0.5">
                <p>{board.specs.width_mm} × {board.specs.height_mm} × {board.specs.depth_mm} mm</p>
                <p>≈ {board.specs.est_total_wt_g} g total</p>
              </div>
            </div>
          </div>

          {/* ── Row 2: transformation strip ── */}
          <div className="bg-[#EFEBE3] px-6 py-4 border-t border-[#d8cfc2]">
            <div className="flex items-center gap-3 overflow-x-auto">
              {board.strip.map((s, i) => (
                <React.Fragment key={i}>
                  <div className="shrink-0 w-24">
                    <img src={`data:image/png;base64,${s.png_b64}`} alt={`View ${i + 1}`}
                      className="w-full rounded border border-[#d8cfc2]" id={`board-strip-${i}`} />
                  </div>
                  {i < board.strip.length - 1 && <span className="text-[#888] shrink-0">→</span>}
                </React.Fragment>
              ))}
              <span className="ml-2 text-[11px] font-mono text-[#666] shrink-0">Continuous view cycle</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
