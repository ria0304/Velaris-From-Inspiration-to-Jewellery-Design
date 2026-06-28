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

  // ---------------------------------------------------------------------------
  // Type-aware silhouette dispatcher
  // Each branch renders front / side / perspective views for its jewelry type.
  // Gem color, metal color, and gemstone shape are all applied on top.
  // ---------------------------------------------------------------------------
  const renderJewelryType = () => {
    const type = (spec.type || 'Ring').toLowerCase();
    const hasAccentStones = spec.setting.toLowerCase().includes('halo') || spec.setting.toLowerCase().includes('pavé');

    // ── RING (original layout, kept intact) ──────────────────────────────────
    if (type === 'ring') {
      return (
        <>
          {activeTab === 'front' && (
            <g>
              <circle cx="100" cy="115" r="50" stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 2.4} fill="none" />
              <circle cx="100" cy="115" r={50 - parsedBandWidth} stroke={metalColor.stroke} strokeWidth="0.8" fill="#050807" />
              <path d="M 82 65 L 85 53 L 115 53 L 118 65 Z" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.2" />
              <line x1="82" y1="65" x2="79" y2="45" stroke={metalColor.stroke} strokeWidth="2" strokeLinecap="round" />
              <line x1="118" y1="65" x2="121" y2="45" stroke={metalColor.stroke} strokeWidth="2" strokeLinecap="round" />
              {hasAccentStones && (
                <g fill={gemColor.stroke}>
                  <circle cx="75" cy="74" r="2.2" /><circle cx="125" cy="74" r="2.2" />
                  <circle cx="68" cy="84" r="1.8" /><circle cx="132" cy="84" r="1.8" />
                </g>
              )}
              {renderGemstoneSVG(100, 50, 18)}
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="100" y1="115" x2="100" y2="160" strokeDasharray="2 2" />
                <line x1="150" y1="115" x2="150" y2="160" strokeDasharray="2 2" />
                <line x1="100" y1="153" x2="150" y2="153" />
                <line x1="100" y1="150" x2="100" y2="156" />
                <line x1="150" y1="150" x2="150" y2="156" />
              </g>
              <text x="125" y="147" fill="#10b981" fontSize="8" fontFamily="monospace" textAnchor="middle">{spec.bandWidth || '1.8mm'} Band Width</text>
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="100" y1="32" x2="148" y2="32" strokeDasharray="2 2" />
                <line x1="100" y1="68" x2="148" y2="68" strokeDasharray="2 2" />
                <line x1="144" y1="32" x2="144" y2="68" />
                <line x1="141" y1="32" x2="147" y2="32" />
                <line x1="141" y1="68" x2="147" y2="68" />
              </g>
              <text x="156" y="54" fill="#10b981" fontSize="8" fontFamily="monospace" transform="rotate(90 156 54)" textAnchor="middle">Setting Height: ~8.2 mm</text>
            </g>
          )}
          {activeTab === 'side' && (
            <g>
              <rect x="94" y="65" width="12" height="100" rx="3" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="0.5" />
              <rect x="96" y="70" width="8" height="90" rx="2" fill="#070c0a" />
              <ellipse cx="100" cy="55" rx="14" ry="10" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="1" />
              <line x1="100" y1="65" x2="100" y2="55" stroke={metalColor.stroke} strokeWidth="1.2" />
              <line x1="88" y1="65" x2="91" y2="44" stroke={metalColor.stroke} strokeWidth="1.8" />
              <line x1="112" y1="65" x2="109" y2="44" stroke={metalColor.stroke} strokeWidth="1.8" />
              <polygon points="86,47 114,47 100,60" fill={gemColor.fill} stroke={gemColor.stroke} strokeWidth="1.2" />
              <polygon points="86,47 114,47 100,53" fill="none" stroke={gemColor.stroke} strokeWidth="0.8" strokeDasharray="2 2" />
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="80" y1="47" x2="80" y2="60" />
                <line x1="77" y1="47" x2="83" y2="47" />
                <line x1="77" y1="60" x2="83" y2="60" />
              </g>
              <text x="70" y="56" fill="#10b981" fontSize="8" fontFamily="monospace" textAnchor="middle">Gem Depth: 5.5mm</text>
            </g>
          )}
          {activeTab === 'perspective' && (
            <g>
              <ellipse cx="100" cy="115" rx="55" ry="32" stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 2.3} fill="none" />
              <ellipse cx="100" cy="115" rx="51" ry="28" stroke={metalColor.stroke} strokeWidth="1" fill="#050807" />
              <path d="M 45 115 C 45 140 155 140 155 115" stroke={metalColor.bandFill} strokeWidth={parsedBandWidth * 1.5} fill="none" />
              {(design.cost.totalCost > 3000) && (
                <g stroke={metalColor.stroke} strokeWidth="0.7" fill="none" opacity="0.85">
                  <path d="M 75 75 C 80 82 90 85 100 85 C 110 85 120 82 125 75" />
                  <circle cx="88" cy="81" r="3" /><circle cx="112" cy="81" r="3" />
                </g>
              )}
              <path d="M 60 98 Q 78 95 82 78 L 86 78 Q 82 92 64 102 Z" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="0.7" />
              <path d="M 140 98 Q 122 95 118 78 L 114 78 Q 118 92 136 102 Z" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="0.7" />
              <ellipse cx="100" cy="74" rx="20" ry="12" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="1.2" />
              <line x1="81" y1="74" x2="78" y2="52" stroke={metalColor.stroke} strokeWidth="2.2" strokeLinecap="round" />
              <line x1="119" y1="74" x2="122" y2="52" stroke={metalColor.stroke} strokeWidth="2.2" strokeLinecap="round" />
              <line x1="94" y1="83" x2="92" y2="60" stroke={metalColor.stroke} strokeWidth="1.8" strokeLinecap="round" opacity="0.9" />
              <line x1="106" y1="83" x2="108" y2="60" stroke={metalColor.stroke} strokeWidth="1.8" strokeLinecap="round" opacity="0.9" />
              {renderGemstoneSVG(100, 58, 17)}
            </g>
          )}
        </>
      );
    }

    // ── NECKLACE / PENDANT ────────────────────────────────────────────────────
    if (type === 'necklace' || type === 'pendant') {
      return (
        <>
          {activeTab === 'front' && (
            <g>
              {/* Chain arc */}
              <path d="M 30 40 Q 100 20 170 40" fill="none" stroke={metalColor.stroke} strokeWidth="2" strokeLinecap="round" />
              {/* Chain links suggestion */}
              {[40,55,70,85,100,115,130,145,160].map((x, i) => (
                <ellipse key={i} cx={x} cy={30 + Math.abs(x - 100) * 0.08} rx="3.5" ry="2" fill="none" stroke={metalColor.stroke} strokeWidth="1" />
              ))}
              {/* Drop chain */}
              <line x1="100" y1="38" x2="100" y2="68" stroke={metalColor.stroke} strokeWidth="1.5" />
              {/* Bail */}
              <rect x="94" y="62" width="12" height="10" rx="3" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1" />
              {/* Pendant frame */}
              <ellipse cx="100" cy="108" rx="26" ry="30" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="2.5" />
              <ellipse cx="100" cy="108" rx="20" ry="24" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="0.8" />
              {hasAccentStones && (
                <g fill={gemColor.stroke}>
                  {[0,60,120,180,240,300].map((deg, i) => (
                    <circle key={i} cx={100 + 23 * Math.cos(deg * Math.PI / 180)} cy={108 + 27 * Math.sin(deg * Math.PI / 180)} r="2" />
                  ))}
                </g>
              )}
              {renderGemstoneSVG(100, 108, 16)}
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="126" y1="78" x2="148" y2="78" strokeDasharray="2 2" />
                <line x1="126" y1="138" x2="148" y2="138" strokeDasharray="2 2" />
                <line x1="144" y1="78" x2="144" y2="138" />
                <line x1="141" y1="78" x2="147" y2="78" /><line x1="141" y1="138" x2="147" y2="138" />
              </g>
              <text x="156" y="112" fill="#10b981" fontSize="7" fontFamily="monospace" transform="rotate(90 156 112)" textAnchor="middle">Pendant: ~30mm</text>
            </g>
          )}
          {activeTab === 'side' && (
            <g>
              {/* Side profile — thin chain, pendant edge */}
              <line x1="100" y1="20" x2="100" y2="65" stroke={metalColor.stroke} strokeWidth="1.5" />
              <rect x="96" y="65" width="8" height="8" rx="2" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1" />
              <ellipse cx="100" cy="105" rx="8" ry="28" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="2" />
              <ellipse cx="100" cy="105" rx="4" ry="22" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="0.7" />
              <polygon points="92,93 108,93 100,118" fill={gemColor.fill} stroke={gemColor.stroke} strokeWidth="1.2" />
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="80" y1="77" x2="80" y2="133" />
                <line x1="77" y1="77" x2="83" y2="77" /><line x1="77" y1="133" x2="83" y2="133" />
              </g>
              <text x="68" y="108" fill="#10b981" fontSize="7" fontFamily="monospace" transform="rotate(90 68 108)" textAnchor="middle">Depth: ~6mm</text>
            </g>
          )}
          {activeTab === 'perspective' && (
            <g>
              <path d="M 25 45 Q 100 15 175 45" fill="none" stroke={metalColor.stroke} strokeWidth="2.5" strokeLinecap="round" />
              <line x1="100" y1="38" x2="100" y2="65" stroke={metalColor.stroke} strokeWidth="1.5" />
              <rect x="93" y="60" width="14" height="10" rx="3" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.2" />
              <ellipse cx="100" cy="112" rx="28" ry="34" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 1.8} />
              <ellipse cx="100" cy="112" rx="22" ry="28" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="0.8" />
              {(design.cost.totalCost > 3000) && (
                <g stroke={metalColor.stroke} strokeWidth="0.6" fill="none" opacity="0.7">
                  <path d="M 78 88 Q 89 82 100 80 Q 111 82 122 88" />
                  <path d="M 74 112 Q 87 108 100 107 Q 113 108 126 112" />
                </g>
              )}
              {hasAccentStones && (
                <g fill={gemColor.stroke}>
                  {[0,51,103,154,206,257,309].map((deg, i) => (
                    <circle key={i} cx={100 + 25 * Math.cos(deg * Math.PI / 180)} cy={112 + 31 * Math.sin(deg * Math.PI / 180)} r="2.2" />
                  ))}
                </g>
              )}
              {renderGemstoneSVG(100, 112, 17)}
            </g>
          )}
        </>
      );
    }

    // ── EARRINGS ──────────────────────────────────────────────────────────────
    if (type === 'earrings') {
      const renderEarring = (cx: number) => (
        <g>
          {/* Ear post */}
          <circle cx={cx} cy="32" r="4" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.2" />
          <line x1={cx} y1="36" x2={cx} y2="55" stroke={metalColor.stroke} strokeWidth="1.2" />
          {/* Drop frame */}
          <ellipse cx={cx} cy="90" rx="18" ry="22" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="2" />
          <ellipse cx={cx} cy="90" rx="13" ry="17" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="0.7" />
          {hasAccentStones && (
            <g fill={gemColor.stroke}>
              <circle cx={cx - 16} cy="90" r="2" /><circle cx={cx + 16} cy="90" r="2" />
              <circle cx={cx} cy="68" r="2" /><circle cx={cx} cy="112" r="2" />
            </g>
          )}
          {renderGemstoneSVG(cx, 90, 11)}
          {/* Backing connector */}
          <line x1={cx} y1="55" x2={cx} y2="68" stroke={metalColor.stroke} strokeWidth="1" strokeDasharray="2 2" />
        </g>
      );
      return (
        <>
          {activeTab === 'front' && (
            <g>
              {renderEarring(65)}
              {renderEarring(135)}
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="65" y1="155" x2="135" y2="155" />
                <line x1="65" y1="152" x2="65" y2="158" /><line x1="135" y1="152" x2="135" y2="158" />
              </g>
              <text x="100" y="168" fill="#10b981" fontSize="7" fontFamily="monospace" textAnchor="middle">Pair spread: ~35mm</text>
            </g>
          )}
          {activeTab === 'side' && (
            <g>
              {/* Side: single earring edge-on */}
              <circle cx="100" cy="32" r="4" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.2" />
              <line x1="100" y1="36" x2="100" y2="55" stroke={metalColor.stroke} strokeWidth="1.2" />
              <rect x="95" y="68" width="10" height="44" rx="3" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.5" />
              <rect x="97" y="72" width="6" height="36" rx="2" fill={metalColor.innerFill} />
              <polygon points="94,74 106,74 100,112" fill={gemColor.fill} stroke={gemColor.stroke} strokeWidth="1" />
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="80" y1="68" x2="80" y2="112" />
                <line x1="77" y1="68" x2="83" y2="68" /><line x1="77" y1="112" x2="83" y2="112" />
              </g>
              <text x="68" y="93" fill="#10b981" fontSize="7" fontFamily="monospace" transform="rotate(90 68 93)" textAnchor="middle">Drop: ~22mm</text>
            </g>
          )}
          {activeTab === 'perspective' && (
            <g>
              {/* Perspective: both earrings slight 3/4 angle */}
              {[60, 140].map((cx, i) => (
                <g key={i}>
                  <circle cx={cx} cy="30" r="5" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.2" />
                  <line x1={cx} y1="35" x2={cx} y2="55" stroke={metalColor.stroke} strokeWidth="1.3" />
                  <ellipse cx={cx} cy="93" rx="20" ry="26" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 1.6} />
                  <ellipse cx={cx} cy="93" rx="15" ry="20" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="0.7" />
                  {hasAccentStones && (
                    <g fill={gemColor.stroke}>
                      <circle cx={cx - 18} cy="93" r="1.8" /><circle cx={cx + 18} cy="93" r="1.8" />
                      <circle cx={cx} cy="73" r="1.8" /><circle cx={cx} cy="113" r="1.8" />
                    </g>
                  )}
                  {renderGemstoneSVG(cx, 93, 12)}
                </g>
              ))}
            </g>
          )}
        </>
      );
    }

    // ── BRACELET ──────────────────────────────────────────────────────────────
    if (type === 'bracelet') {
      return (
        <>
          {activeTab === 'front' && (
            <g>
              {/* Bangle oval top face */}
              <ellipse cx="100" cy="100" rx="75" ry="40" fill="none" stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 2.5} />
              <ellipse cx="100" cy="100" rx="67" ry="33" fill="#050807" stroke={metalColor.stroke} strokeWidth="0.8" />
              {/* Link suggestion marks */}
              {[-60,-30,0,30,60].map((deg, i) => (
                <line key={i}
                  x1={100 + 71 * Math.cos(deg * Math.PI / 180)}
                  y1={100 + 37 * Math.sin(deg * Math.PI / 180)}
                  x2={100 + 63 * Math.cos(deg * Math.PI / 180)}
                  y2={100 + 31 * Math.sin(deg * Math.PI / 180)}
                  stroke={metalColor.stroke} strokeWidth="1" opacity="0.6"
                />
              ))}
              {/* Centre stone on top */}
              <ellipse cx="100" cy="62" rx="16" ry="10" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.5" />
              {hasAccentStones && (
                <g fill={gemColor.stroke}>
                  <circle cx="74" cy="70" r="2" /><circle cx="126" cy="70" r="2" />
                  <circle cx="64" cy="82" r="1.8" /><circle cx="136" cy="82" r="1.8" />
                </g>
              )}
              {renderGemstoneSVG(100, 58, 14)}
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="25" y1="100" x2="25" y2="130" strokeDasharray="2 2" />
                <line x1="175" y1="100" x2="175" y2="130" strokeDasharray="2 2" />
                <line x1="25" y1="124" x2="175" y2="124" />
                <line x1="25" y1="121" x2="25" y2="127" /><line x1="175" y1="121" x2="175" y2="127" />
              </g>
              <text x="100" y="138" fill="#10b981" fontSize="7" fontFamily="monospace" textAnchor="middle">Inner Dia: ~58mm</text>
            </g>
          )}
          {activeTab === 'side' && (
            <g>
              {/* Side cross-section of bangle */}
              <rect x="80" y="50" width="40" height="100" rx="20" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="2" />
              <rect x="86" y="58" width="28" height="84" rx="14" fill="#050807" />
              {/* Stone on crown */}
              <ellipse cx="100" cy="45" rx="14" ry="8" fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="1" />
              {renderGemstoneSVG(100, 42, 10)}
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="60" y1="50" x2="60" y2="150" />
                <line x1="57" y1="50" x2="63" y2="50" /><line x1="57" y1="150" x2="63" y2="150" />
              </g>
              <text x="48" y="103" fill="#10b981" fontSize="7" fontFamily="monospace" transform="rotate(90 48 103)" textAnchor="middle">Bangle Height: 40mm</text>
            </g>
          )}
          {activeTab === 'perspective' && (
            <g>
              {/* 3/4 perspective elliptical bangle */}
              <ellipse cx="100" cy="118" rx="70" ry="35" stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 2.2} fill="none" />
              <ellipse cx="100" cy="118" rx="62" ry="28" stroke={metalColor.stroke} strokeWidth="1" fill="#050807" />
              <path d="M 30 118 C 30 145 170 145 170 118" stroke={metalColor.bandFill} strokeWidth={parsedBandWidth * 1.4} fill="none" />
              {(design.cost.totalCost > 3000) && (
                <g stroke={metalColor.stroke} strokeWidth="0.6" fill="none" opacity="0.7">
                  <path d="M 55 95 Q 78 88 100 86 Q 122 88 145 95" />
                </g>
              )}
              {/* Crown + stone */}
              <path d="M 84 82 L 87 70 L 113 70 L 116 82 Z" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.2" />
              {hasAccentStones && (
                <g fill={gemColor.stroke}>
                  <circle cx="78" cy="90" r="2" /><circle cx="122" cy="90" r="2" />
                </g>
              )}
              {renderGemstoneSVG(100, 66, 16)}
            </g>
          )}
        </>
      );
    }

    // ── BROOCH ────────────────────────────────────────────────────────────────
    if (type === 'brooch') {
      return (
        <>
          {activeTab === 'front' && (
            <g>
              {/* Ornate brooch body — starburst/shield shape */}
              <polygon points="100,18 115,50 150,50 123,70 133,102 100,82 67,102 77,70 50,50 85,50"
                fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="2" />
              <polygon points="100,30 111,55 138,55 117,70 125,95 100,80 75,95 83,70 62,55 89,55"
                fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="0.8" />
              {/* Pin back indicator */}
              <line x1="70" y1="148" x2="130" y2="148" stroke={metalColor.stroke} strokeWidth="3" strokeLinecap="round" />
              <circle cx="128" cy="148" r="4" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.2" />
              <text x="100" y="162" fill="#10b981" fontSize="7" fontFamily="monospace" textAnchor="middle">Pin Back</text>
              {hasAccentStones && (
                <g fill={gemColor.stroke}>
                  {[18,54,90,126,162,198,234,270,306,342].map((deg, i) => (
                    <circle key={i} cx={100 + 28 * Math.cos(deg * Math.PI / 180)} cy={60 + 22 * Math.sin(deg * Math.PI / 180)} r="2" />
                  ))}
                </g>
              )}
              {renderGemstoneSVG(100, 60, 16)}
            </g>
          )}
          {activeTab === 'side' && (
            <g>
              {/* Brooch side: flat profile with pin */}
              <rect x="60" y="55" width="80" height="60" rx="8" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="2" />
              <rect x="65" y="60" width="70" height="50" rx="6" fill={metalColor.innerFill} />
              {/* Pin bar extending left */}
              <line x1="25" y1="138" x2="140" y2="138" stroke={metalColor.stroke} strokeWidth="3" strokeLinecap="round" />
              <circle cx="140" cy="138" r="5" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1.2" />
              {/* Gem profile */}
              <polygon points="88,62 112,62 100,82" fill={gemColor.fill} stroke={gemColor.stroke} strokeWidth="1.2" />
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="45" y1="55" x2="45" y2="115" />
                <line x1="42" y1="55" x2="48" y2="55" /><line x1="42" y1="115" x2="48" y2="115" />
              </g>
              <text x="33" y="88" fill="#10b981" fontSize="7" fontFamily="monospace" transform="rotate(90 33 88)" textAnchor="middle">Body: ~35mm</text>
            </g>
          )}
          {activeTab === 'perspective' && (
            <g>
              {/* Perspective starburst brooch */}
              <polygon points="100,15 117,52 158,52 126,74 138,112 100,90 62,112 74,74 42,52 83,52"
                fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="2.2" />
              <polygon points="100,28 113,57 146,57 120,74 130,105 100,86 70,105 80,74 54,57 87,57"
                fill={metalColor.innerFill} stroke={metalColor.stroke} strokeWidth="0.8" />
              {(design.cost.totalCost > 3000) && (
                <g stroke={metalColor.stroke} strokeWidth="0.7" fill="none" opacity="0.8">
                  {[30,90,150,210,270,330].map((deg, i) => (
                    <path key={i} d={`M 100 60 L ${100 + 18 * Math.cos(deg * Math.PI / 180)} ${60 + 14 * Math.sin(deg * Math.PI / 180)}`} />
                  ))}
                </g>
              )}
              {hasAccentStones && (
                <g fill={gemColor.stroke}>
                  {[0,40,80,120,160,200,240,280,320].map((deg, i) => (
                    <circle key={i} cx={100 + 32 * Math.cos(deg * Math.PI / 180)} cy={60 + 24 * Math.sin(deg * Math.PI / 180)} r="2.2" />
                  ))}
                </g>
              )}
              {renderGemstoneSVG(100, 60, 18)}
              {/* Pin back hint */}
              <line x1="68" y1="155" x2="132" y2="155" stroke={metalColor.stroke} strokeWidth="2.5" strokeLinecap="round" opacity="0.6" />
            </g>
          )}
        </>
      );
    }

    // ── TIARA ─────────────────────────────────────────────────────────────────
    if (type === 'tiara') {
      return (
        <>
          {activeTab === 'front' && (
            <g>
              {/* Base arc band */}
              <path d="M 20 140 Q 100 125 180 140" fill="none" stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 2.5} strokeLinecap="round" />
              {/* Rising spires */}
              <line x1="100" y1="128" x2="100" y2="30" stroke={metalColor.stroke} strokeWidth="3" strokeLinecap="round" />
              <line x1="72" y1="131" x2="60" y2="60" stroke={metalColor.stroke} strokeWidth="2.2" strokeLinecap="round" />
              <line x1="128" y1="131" x2="140" y2="60" stroke={metalColor.stroke} strokeWidth="2.2" strokeLinecap="round" />
              <line x1="50" y1="136" x2="38" y2="90" stroke={metalColor.stroke} strokeWidth="1.5" strokeLinecap="round" />
              <line x1="150" y1="136" x2="162" y2="90" stroke={metalColor.stroke} strokeWidth="1.5" strokeLinecap="round" />
              {/* Spire tips */}
              <polygon points="100,28 106,48 94,48" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1" />
              <polygon points="60,58 65,74 55,74" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1" />
              <polygon points="140,58 145,74 135,74" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1" />
              {/* Centre gem — crown jewel */}
              {renderGemstoneSVG(100, 55, 18)}
              {/* Flanking gems */}
              {renderGemstoneSVG(60, 80, 11)}
              {renderGemstoneSVG(140, 80, 11)}
              {hasAccentStones && (
                <g fill={gemColor.stroke}>
                  {[38,50,150,162].map((x, i) => <circle key={i} cx={x} cy={98} r="2.5" />)}
                  {[30,170].map((x, i) => <circle key={i} cx={x} cy={112} r="2" />)}
                </g>
              )}
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="20" y1="158" x2="180" y2="158" />
                <line x1="20" y1="155" x2="20" y2="161" /><line x1="180" y1="155" x2="180" y2="161" />
              </g>
              <text x="100" y="170" fill="#10b981" fontSize="7" fontFamily="monospace" textAnchor="middle">Tiara span: ~160mm</text>
            </g>
          )}
          {activeTab === 'side' && (
            <g>
              {/* Side arc */}
              <path d="M 60 155 Q 100 140 140 155" fill="none" stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 2} />
              <line x1="100" y1="142" x2="100" y2="30" stroke={metalColor.stroke} strokeWidth="2.5" />
              <polygon points="100,28 105,46 95,46" fill={metalColor.bandFill} stroke={metalColor.stroke} strokeWidth="1" />
              {renderGemstoneSVG(100, 52, 13)}
              <g stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                <line x1="75" y1="28" x2="75" y2="155" />
                <line x1="72" y1="28" x2="78" y2="28" /><line x1="72" y1="155" x2="78" y2="155" />
              </g>
              <text x="60" y="95" fill="#10b981" fontSize="7" fontFamily="monospace" transform="rotate(90 60 95)" textAnchor="middle">Height: ~127mm</text>
            </g>
          )}
          {activeTab === 'perspective' && (
            <g>
              {/* Curved base in perspective */}
              <path d="M 15 150 Q 100 128 185 150" fill="none" stroke={metalColor.stroke} strokeWidth={parsedBandWidth * 2.5} strokeLinecap="round" />
              {/* Spires in perspective */}
              <line x1="100" y1="132" x2="100" y2="25" stroke={metalColor.stroke} strokeWidth="3.5" strokeLinecap="round" />
              <line x1="70" y1="136" x2="55" y2="58" stroke={metalColor.stroke} strokeWidth="2.5" strokeLinecap="round" />
              <line x1="130" y1="136" x2="145" y2="58" stroke={metalColor.stroke} strokeWidth="2.5" strokeLinecap="round" />
              <line x1="45" y1="143" x2="32" y2="88" stroke={metalColor.stroke} strokeWidth="1.8" strokeLinecap="round" />
              <line x1="155" y1="143" x2="168" y2="88" stroke={metalColor.stroke} strokeWidth="1.8" strokeLinecap="round" />
              {(design.cost.totalCost > 3000) && (
                <g stroke={metalColor.stroke} strokeWidth="0.7" fill="none" opacity="0.7">
                  <path d="M 55 120 Q 78 112 100 110 Q 122 112 145 120" />
                  <path d="M 65 105 Q 83 100 100 98 Q 117 100 135 105" />
                </g>
              )}
              {renderGemstoneSVG(100, 48, 20)}
              {renderGemstoneSVG(55, 74, 12)}
              {renderGemstoneSVG(145, 74, 12)}
              {hasAccentStones && (
                <g fill={gemColor.stroke}>
                  {[32,170].map((x, i) => <circle key={i} cx={x} cy={100} r="2.5" />)}
                  {[20,180].map((x, i) => <circle key={i} cx={x} cy={118} r="2" />)}
                </g>
              )}
            </g>
          )}
        </>
      );
    }

    // ── FALLBACK (unknown type → ring) ────────────────────────────────────────
    return renderJewelryType();
  };

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
              {/* Blueprint grid overlay */}
              <line x1="10" y1="100" x2="190" y2="100" stroke="#102e1c" strokeWidth="0.5" strokeDasharray="4 4" />
              <line x1="100" y1="10" x2="100" y2="190" stroke="#102e1c" strokeWidth="0.5" strokeDasharray="4 4" />
              <circle cx="100" cy="100" r="85" stroke="#102e1c" strokeWidth="0.5" strokeDasharray="1 9" fill="none" />
              <circle cx="100" cy="100" r="50" stroke="#102e1c" strokeWidth="0.5" strokeDasharray="1 9" fill="none" />

              {/* Type-aware jewelry renderer */}
              {renderJewelryType()}
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
