import React, { useState } from 'react';
import { DesignPackage } from '../types';
import { Ruler, Sparkles, Layers, ShieldCheck, Hammer } from 'lucide-react';

interface BlueprintProps {
  design: DesignPackage;
}

export default function JewelryBlueprint({ design }: BlueprintProps) {
  const [activeTab, setActiveTab] = useState<'front' | 'side' | 'perspective'>('perspective');
  const spec = design.spec;

  // Helper to determine gemstone color specifications dynamically
  const getGemstoneColors = () => {
    const stone = (spec.stone || 'Diamond').toLowerCase();
    if (stone.includes('emerald')) {
      return { fill: '#053123', stroke: '#10b981', accent: '#6ee7b7' }; // Royal Emerald Green
    } else if (stone.includes('ruby')) {
      return { fill: '#4c0519', stroke: '#ef4444', accent: '#fca5a5' }; // Vivid Ruby Crimson Red
    } else if (stone.includes('sapphire')) {
      return { fill: '#172554', stroke: '#3b82f6', accent: '#93c5fd' }; // Royal Velvet Sapphire Blue
    } else if (stone.includes('garnet')) {
      return { fill: '#450a0a', stroke: '#991b1b', accent: '#fca5a5' }; // Rich Wine Garnet
    } else if (stone.includes('moissanite') || stone.includes('diamond')) {
      return { fill: '#0f172a', stroke: '#cbd5e1', accent: '#f8fafc' }; // Brilliant Sparkle White
    } else if (stone.includes('aquamarine')) {
      return { fill: '#082f49', stroke: '#0284c7', accent: '#bae6fd' }; // Ice-cool Aquamarine Blue
    } else if (stone.includes('opal')) {
      return { fill: '#2e1065', stroke: '#c084fc', accent: '#f5d0fe' }; // Pearlescent Pastel Pink/Lavender Opal
    } else if (stone.includes('amethyst')) {
      return { fill: '#3b0764', stroke: '#8b5cf6', accent: '#ddd6fe' }; // Deep Amethyst Violet
    } else if (stone.includes('pearl')) {
      return { fill: '#451a03', stroke: '#d97706', accent: '#fef3c7' }; // Smooth Golden Cream Pearl
    } else if (stone.includes('morganite')) {
      return { fill: '#431407', stroke: '#ea580c', accent: '#ffedd5' }; // Soft Warm Peach Morganite
    }
    // Default Sparkling crystal
    return { fill: '#0f172a', stroke: '#a8a29e', accent: '#f5f5f4' };
  };

  // Helper to determine metal color specifications dynamically
  const getMetalColors = () => {
    const metal = (spec.metal || 'Platinum').toLowerCase();
    if (metal.includes('yellow gold') || metal.includes('yellow')) {
      return { stroke: '#DFBE8B', bandFill: '#53432a', innerFill: '#050807', high: '#F1DAB4' }; // 18K / 14K Shimmering Yellow Gold
    } else if (metal.includes('rose gold') || metal.includes('rose')) {
      return { stroke: '#8F5C64', bandFill: '#412d31', innerFill: '#050807', high: '#BA8D94' }; // 18K Warm Rose Gold
    } else if (metal.includes('white gold') || metal.includes('platinum') || metal.includes('silver')) {
      return { stroke: '#9ABCAB', bandFill: '#2E3D35', innerFill: '#050807', high: '#C6DDD1' }; // Sage-tinted Platinum or Silver Luxury Lustre
    }
    return { stroke: '#DFBE8B', bandFill: '#53432a', innerFill: '#050807', high: '#F1DAB4' };
  };

  const gemColor = getGemstoneColors();
  const metalColor = getMetalColors();

  // Helper to determine gemstone shape path
  const renderGemstoneSVG = (x: number, y: number, r: number) => {
    const shape = (spec.shape || 'Round').toLowerCase();
    
    if (shape.includes('round')) {
      return (
        <g stroke={gemColor.stroke} strokeWidth="1.5" fill={gemColor.fill} fillOpacity="0.85">
          <circle cx={x} cy={y} r={r} />
          {/* Facets */}
          <circle cx={x} cy={y} r={r * 0.52} strokeDasharray="2 1" stroke={gemColor.accent} />
          <path d={`M ${x - r} ${y} L ${x + r} ${y}`} strokeWidth="0.8" stroke={gemColor.accent} />
          <path d={`M ${x} ${y - r} L ${x} ${y + r}`} strokeWidth="0.8" stroke={gemColor.accent} />
          <path d={`M ${x - r * 0.7} ${y - r * 0.7} L ${x + r * 0.7} ${y + r * 0.7}`} strokeWidth="0.8" stroke={gemColor.accent} />
          <path d={`M ${x - r * 0.7} ${y + r * 0.7} L ${x + r * 0.7} ${y - r * 0.7}`} strokeWidth="0.8" stroke={gemColor.accent} />
        </g>
      );
    } else if (shape.includes('emerald') || shape.includes('princess')) {
      return (
        <g stroke={gemColor.stroke} strokeWidth="1.5" fill={gemColor.fill} fillOpacity="0.85">
          <rect x={x - r} y={y - r} width={r * 2} height={r * 2} rx={shape.includes('emerald') ? 3 : 0} />
          {/* Facets */}
          <rect x={x - r * 0.6} y={y - r * 0.6} width={r * 1.2} height={r * 1.2} strokeDasharray="2 1" stroke={gemColor.accent} />
          <path d={`M ${x - r} ${y - r} L ${x - r * 0.6} ${y - r * 0.6}`} strokeWidth="0.8" stroke={gemColor.accent} />
          <path d={`M ${x + r} ${y - r} L ${x + r * 0.6} ${y - r * 0.6}`} strokeWidth="0.8" stroke={gemColor.accent} />
          <path d={`M ${x - r} ${y + r} L ${x - r * 0.6} ${y + r * 0.6}`} strokeWidth="0.8" stroke={gemColor.accent} />
          <path d={`M ${x + r} ${y + r} L ${x + r * 0.6} ${y + r * 0.6}`} strokeWidth="0.8" stroke={gemColor.accent} />
        </g>
      );
    } else if (shape.includes('oval') || shape.includes('marquise')) {
      const rx = r * 1.35;
      const ry = r * 0.82;
      return (
        <g stroke={gemColor.stroke} strokeWidth="1.5" fill={gemColor.fill} fillOpacity="0.85">
          <ellipse cx={x} cy={y} rx={rx} ry={ry} />
          {/* Facets */}
          <ellipse cx={x} cy={y} rx={rx * 0.6} ry={ry * 0.6} strokeDasharray="2 1" stroke={gemColor.accent} />
          <path d={`M ${x - rx} ${y} L ${x + rx} ${y}`} strokeWidth="0.8" stroke={gemColor.accent} />
          <path d={`M ${x} ${y - ry} L ${x} ${y + ry}`} strokeWidth="0.8" stroke={gemColor.accent} />
        </g>
      );
    } else if (shape.includes('cushion') || shape.includes('pear')) {
      // Elegant Drop or rounded cushion shape
      return (
        <g stroke={gemColor.stroke} strokeWidth="1.5" fill={gemColor.fill} fillOpacity="0.85">
          <path d={`M ${x} ${y - r} C ${x + r * 1.2} ${y - r * 0.25} ${x + r * 0.85} ${y + r} ${x} ${y + r} C ${x - r * 0.85} ${y + r} ${x - r * 1.2} ${y - r * 0.25} z`} />
          <line x1={x} y1={y - r} x2={x} y2={y + r} strokeWidth="0.8" stroke={gemColor.accent} />
          <path d={`M ${x - r * 0.5} ${y} Q ${x} ${y - r * 0.3} ${x + r * 0.5} ${y}`} fill="none" stroke={gemColor.accent} strokeWidth="0.8" strokeDasharray="1 1" />
        </g>
      );
    } else {
      // Default sparkling geometric teardrop
      return (
        <g stroke={gemColor.stroke} strokeWidth="1.5" fill={gemColor.fill} fillOpacity="0.85">
          <polygon points={`${x},${y - r} ${x + r},${y} ${x},${y + r} ${x - r},${y}`} />
          <line x1={x - r} y1={y} x2={x + r} y2={y} strokeWidth="0.8" stroke={gemColor.accent} />
          <line x1={x} y1={y - r} x2={x} y2={y + r} strokeWidth="0.8" stroke={gemColor.accent} />
        </g>
      );
    }
  };

  // Extract a numeric representation for the band width
  const parsedBandWidth = parseFloat(spec.bandWidth || '2.0') || 2.0;

  return (
    <div className="bg-[#0b120f] border border-[#1e3a2b] rounded-lg overflow-hidden shadow-2xl" id="jewelry-blueprint-wrapper">
      {/* Header section with elegant consumer style */}
      <div className="px-6 py-4 border-b border-[#1e3a2b] bg-[#070c0a] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#DFBE8B] animate-pulse"></span>
            <h3 className="text-xs uppercase tracking-widest text-[#DFBE8B] font-semibold">Interactive Jewelry Visualizer</h3>
          </div>
          <p className="text-xl font-serif text-white tracking-wide mt-1">{design.name}</p>
        </div>
        
        {/* View Switches */}
        <div className="flex bg-[#0f1b14] border border-[#1e3a2b] p-1 rounded-md self-start md:self-auto">
          <button
            onClick={() => setActiveTab('perspective')}
            className={`px-3 py-1.5 rounded text-xs font-medium uppercase tracking-wider transition ${
              activeTab === 'perspective' ? 'bg-[#1a3828] text-[#DFBE8B] border border-[#DFBE8B]/30' : 'text-gray-400 hover:text-white'
            }`}
            id="view-perspective-btn"
          >
            Artistic Angle
          </button>
          <button
            onClick={() => setActiveTab('front')}
            className={`px-3 py-1.5 rounded text-xs font-medium uppercase tracking-wider transition ${
              activeTab === 'front' ? 'bg-[#1a3828] text-[#DFBE8B] border border-[#DFBE8B]/30' : 'text-gray-400 hover:text-white'
            }`}
            id="view-front-btn"
          >
            Front Face
          </button>
          <button
            onClick={() => setActiveTab('side')}
            className={`px-3 py-1.5 rounded text-xs font-medium uppercase tracking-wider transition ${
              activeTab === 'side' ? 'bg-[#1a3828] text-[#DFBE8B] border border-[#DFBE8B]/30' : 'text-gray-400 hover:text-white'
            }`}
            id="view-side-btn"
          >
            Profile View
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12">
        {/* Dynamic Interactive SVG Canvas */}
        <div className="lg:col-span-7 bg-[#050807] p-6 flex flex-col items-center justify-center relative min-h-[360px] border-b lg:border-b-0 lg:border-r border-[#1e3a2b]">
          {/* Blueprint Matrix Grid overlay */}
          <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#1e3a2b_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none"></div>
          
          <div className="absolute top-4 left-4 text-[10px] text-emerald-500/60 font-mono flex flex-col gap-0.5 pointer-events-none">
            <span>VELARIS STUDIO DESIGNER</span>
            <span>CUSTOM DESIGN COMPASS</span>
            <span>PRECISION HAND-CRAFTED RATIOS</span>
          </div>

          <div className="absolute bottom-4 left-4 text-[10px] text-[#DFBE8B]/70 font-mono pointer-events-none">
            <span>STABILITY RATING: PERFECT HARMONY</span>
          </div>

          <div className="w-full max-w-sm aspect-square relative z-10">
            <svg viewBox="0 0 200 200" className="w-full h-full drop-shadow-[0_0_15px_rgba(223,190,139,0.18)]">
              {/* Outer grid boundary lines */}
              <line x1="10" y1="100" x2="190" y2="100" stroke="#102e1c" strokeWidth="0.5" strokeDasharray="4 4" />
              <line x1="100" y1="10" x2="100" y2="190" stroke="#102e1c" strokeWidth="0.5" strokeDasharray="4 4" />
              
              <circle cx="100" cy="100" r="85" stroke="#102e1c" strokeWidth="0.5" strokeDasharray="1 9" fill="none" />
              <circle cx="100" cy="100" r="50" stroke="#102e1c" strokeWidth="0.5" strokeDasharray="1 9" fill="none" />

              {/* DRAW FRONT VIEW */}
              {activeTab === 'front' && (
                <g>
                  {/* Outer Ring Metal Band with Dynamic Metal Fill */}
                  <circle cx="100" cy="115" r="50" stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 2.4} fill="none" />
                  
                  {/* Inner finger hole */}
                  <circle cx="100" cy="115" r={50 - parsedBandWidth} stroke={metalColor.stroke} strokeWidth="0.8" fill="#050807" />
                  
                  {/* Gemstone Setting Basket/Crown on Top (y=65) */}
                  <path d="M 82 65 L 85 53 L 115 53 L 118 65 Z" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.2" />
                  
                  {/* Setting Prongs */}
                  <line x1="82" y1="65" x2="79" y2="45" stroke={metalColor.stroke} strokeWidth="2" strokeLinecap="round" />
                  <line x1="118" y1="65" x2="121" y2="45" stroke={metalColor.stroke} strokeWidth="2" strokeLinecap="round" />
                  
                  {/* Accent stones in shoulders */}
                  {spec.setting.toLowerCase().includes('halo') || spec.setting.toLowerCase().includes('pavé') ? (
                    <g fill={gemColor.stroke}>
                      <circle cx="75" cy="74" r="2.2" />
                      <circle cx="125" cy="74" r="2.2" />
                      <circle cx="68" cy="84" r="1.8" />
                      <circle cx="132" cy="84" r="1.8" />
                    </g>
                  ) : null}

                  {/* Gemstone */}
                  {renderGemstoneSVG(100, 50, 18)}

                  {/* Horizontal Dimension line for Band Width */}
                  <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                    <line x1="100" y1="115" x2="100" y2="160" strokeDasharray="2 2" />
                    <line x1="150" y1="115" x2="150" y2="160" strokeDasharray="2 2" />
                    <line x1="100" y1="153" x2="150" y2="153" />
                    {/* Tick bounds */}
                    <line x1="100" y1="150" x2="100" y2="156" />
                    <line x1="150" y1="150" x2="150" y2="156" />
                  </g>
                  <text x="125" y="147" fill="#10b981" fontSize="8" fontFamily="monospace" textAnchor="middle">
                    {spec.bandWidth || '1.8mm'} Band Width
                  </text>

                  {/* Vert Dimension line for Gemstone */}
                  <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                    <line x1="100" y1="32" x2="148" y2="32" strokeDasharray="2 2" />
                    <line x1="100" y1="68" x2="148" y2="68" strokeDasharray="2 2" />
                    <line x1="144" y1="32" x2="144" y2="68" />
                    <line x1="141" y1="32" x2="147" y2="32" />
                    <line x1="141" y1="68" x2="147" y2="68" />
                  </g>
                  <text x="156" y="54" fill="#10b981" fontSize="8" fontFamily="monospace" transform="rotate(90 156 54)" textAnchor="middle">
                    Setting Height: ~8.2 mm
                  </text>
                </g>
              )}

              {/* DRAW PROFILE / SIDE VIEW */}
              {activeTab === 'side' && (
                <g>
                  {/* Side view of band (perfectly vertical slice) */}
                  <rect x="94" y="65" width="12" height="100" rx="3" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="0.5" />
                  <rect x="96" y="70" width="8" height="90" rx="2" fill="#070c0a" />

                  {/* Profile of the gemstone setting crown */}
                  <ellipse cx="100" cy="55" rx="14" ry="10" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="1" />
                  <line x1="100" y1="65" x2="100" y2="55" stroke={metalColor.stroke} strokeWidth="1.2" />

                  {/* Prongs (Side showing 2 visible) */}
                  <line x1="88" y1="65" x2="91" y2="44" stroke={metalColor.stroke} strokeWidth="1.8" />
                  <line x1="112" y1="65" x2="109" y2="44" stroke={metalColor.stroke} strokeWidth="1.8" />

                  {/* Side Gemstone Profile outline */}
                  <polygon points="86,47 114,47 100,60" fill={gemColor.fill} stroke={gemColor.stroke} strokeWidth="1.2" />
                  <polygon points="86,47 114,47 100,53" fill="none" stroke={gemColor.stroke} strokeWidth="0.8" strokeDasharray="2 2" />

                  <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                    {/* Dimension marker */}
                    <line x1="80" y1="47" x2="80" y2="60" />
                    <line x1="77" y1="47" x2="83" y2="47" />
                    <line x1="77" y1="60" x2="83" y2="60" />
                  </g>
                  <text x="70" y="56" fill="#10b981" fontSize="8" fontFamily="monospace" textAnchor="middle">
                    Gem Depth: 5.5mm
                  </text>
                </g>
              )}

              {/* DRAW 3D PERSPECTIVE (Default) */}
              {activeTab === 'perspective' && (
                <g>
                  {/* Perspective Ellipse Band (Outer) */}
                  <ellipse cx="100" cy="115" rx="55" ry="32" stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 2.3} fill="none" />
                  {/* Perspective Ellipse Band (Inner) */}
                  <ellipse cx="100" cy="115" rx="51" ry="28" stroke={metalColor.stroke} strokeWidth="1" fill="#050807" />
                  
                  {/* Dynamic back portion of the hoop behind finger gap */}
                  <path d="M 45 115 C 45 140 155 140 155 115" stroke={metalColor.bandFill} strokeWidth={parsedBandWidth * 1.5} fill="none" />

                  {/* Elegant Filigree work undercarriage (if premium style) */}
                  {(design.cost.totalCost > 3000) && (
                    <g stroke={metalColor.stroke} strokeWidth="0.7" fill="none" opacity="0.85">
                      <path d="M 75 75 C 80 82 90 85 100 85 C 110 85 120 82 125 75" />
                      <circle cx="88" cy="81" r="3" />
                      <circle cx="112" cy="81" r="3" />
                    </g>
                  )}

                  {/* Support columns of cathedral structure rising to centerpiece */}
                  <path d="M 60 98 Q 78 95 82 78 L 86 78 Q 82 92 64 102 Z" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="0.7" />
                  <path d="M 140 98 Q 122 95 118 78 L 114 78 Q 118 92 136 102 Z" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="0.7" />

                  {/* Central crown rim */}
                  <ellipse cx="100" cy="74" rx="20" ry="12" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="1.2" />

                  {/* Prongs */}
                  <line x1="81" y1="74" x2="78" y2="52" stroke={metalColor.stroke} strokeWidth="2.2" strokeLinecap="round" />
                  <line x1="119" y1="74" x2="122" y2="52" stroke={metalColor.stroke} strokeWidth="2.2" strokeLinecap="round" />
                  <line x1="94" y1="83" x2="92" y2="60" stroke={metalColor.stroke} strokeWidth="1.8" strokeLinecap="round" opacity="0.9" />
                  <line x1="106" y1="83" x2="108" y2="60" stroke={metalColor.stroke} strokeWidth="1.8" strokeLinecap="round" opacity="0.9" />

                  {/* Master Gemstone rendered in 3D-angled perspective projection with beautiful customized color */}
                  {renderGemstoneSVG(100, 58, 17)}
                </g>
              )}
            </svg>
          </div>

          {/* Color theme indicators */}
          <div className="absolute bottom-4 right-4 flex items-center gap-1.5 bg-[#0a1411]/80 border border-[#1e3a2b]/60 px-2.5 py-1.5 rounded text-[11px] text-gray-300">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: gemColor.stroke, border: '1px solid #1e3a2b' }}></span>
            <span className="font-medium tracking-wide text-xs">{spec.stone} ({spec.metal})</span>
          </div>
        </div>

        {/* CAD Properties & Descriptions */}
        <div className="lg:col-span-5 p-6 flex flex-col justify-between h-full bg-[#080d0b]">
          <div>
            <span className="text-[10px] uppercase font-mono tracking-widest text-[#DFBE8B]/80 block border-b border-[#1e3a2b] pb-2 mb-4">
              DESIGN DIMENSIONS
            </span>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs text-gray-400 font-mono">GEM & METAL OVERVIEW</p>
                <div className="mt-1.5 grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-[#0f1b14] border border-[#1e3a2b]/30 p-2 rounded">
                    <span className="text-gray-400 font-serif block text-[10px]">Jewelry Style</span>
                    <span className="text-white font-medium">{spec.type}</span>
                  </div>
                  <div className="bg-[#0f1b14] border border-[#1e3a2b]/30 p-2 rounded">
                    <span className="text-gray-400 font-serif block text-[10px]">Occasion</span>
                    <span className="text-white font-medium">{spec.occasion}</span>
                  </div>
                  <div className="bg-[#0f1b14] border border-[#1e3a2b]/30 p-2 rounded">
                    <span className="text-gray-400 font-serif block text-[10px]">Gem Size</span>
                    <span className="text-white font-medium">{spec.stoneSize}</span>
                  </div>
                  <div className="bg-[#0f1b14] border border-[#1e3a2b]/30 p-2 rounded">
                    <span className="text-gray-400 font-serif block text-[10px]">Setting Style</span>
                    <span className="text-white font-medium">{spec.setting}</span>
                  </div>
                </div>
              </div>

              <div>
                <p className="text-xs text-gray-400 font-mono">ARTISAN VIEW DETAILS</p>
                <div className="mt-1.5 text-xs text-gray-300 leading-relaxed bg-[#0a1411] border border-[#1e3a2b]/80 p-3.5 rounded space-y-2">
                  {activeTab === 'perspective' && (
                    <div>
                      <strong className="text-[#DFBE8B] font-sans font-semibold uppercase text-[10px] block tracking-wider mb-1">Artistic Angle View</strong>
                      <p className="italic leading-relaxed">{design.multiView.perspective}</p>
                    </div>
                  )}
                  {activeTab === 'front' && (
                    <div>
                      <strong className="text-[#DFBE8B] font-sans font-semibold uppercase text-[10px] block tracking-wider mb-1">Front Face View</strong>
                      <p className="italic leading-relaxed">{design.multiView.front}</p>
                    </div>
                  )}
                  {activeTab === 'side' && (
                    <div>
                      <strong className="text-[#DFBE8B] font-sans font-semibold uppercase text-[10px] block tracking-wider mb-1">Profile Side View</strong>
                      <p className="italic leading-relaxed">{design.multiView.side}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[#1e3a2b]/50">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#DFBE8B]/10 border border-[#DFBE8B]/20 rounded-md">
                <ShieldCheck className="w-5 h-5 text-[#DFBE8B]" />
              </div>
              <div className="text-xs">
                <span className="text-gray-400 font-serif block">Design Status</span>
                <span className="text-emerald-400 font-semibold font-mono tracking-wide">100% Craftsmanship Approved</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
