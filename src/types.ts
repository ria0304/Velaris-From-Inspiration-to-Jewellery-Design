// src/types.ts

export interface JewelrySpec {
  type: 'Ring' | 'Earrings' | 'Necklace' | 'Bracelet' | 'Brooch';
  metal: '18K Yellow Gold' | '18K White Gold' | '18K Rose Gold' | 'Platinum' | '14K Yellow Gold' | 'Sterling Silver';
  stone: 'Diamond' | 'Emerald' | 'Sapphire' | 'Ruby' | 'Garnet' | 'Moissanite' | 'Aquamarine' | 'Opal' | 'Amethyst' | 'Pearl' | 'Morganite';
  shape: 'Round' | 'Oval' | 'Emerald-Cut' | 'Pear' | 'Cushion' | 'Princess' | 'Marquise';
  setting: 'Prong' | 'Bezel' | 'Halo' | 'Pavé' | 'Channel' | 'Tension' | 'Cathedral';
  occasion: 'Engagement' | 'Wedding' | 'Anniversary' | 'Birthday' | 'Graduation' | 'Self-Gift';
  stoneSize: string; // e.g., "1.8 carat"
  bandWidth?: string; // e.g., "2.0 mm"
  details: string; // design notes
}

export interface CostBreakdown {
  metalCost: number;
  stoneCost: number;
  laborCost: number;
  markupPercent: number;
  totalCost: number;
}

export interface ManufacturingScore {
  score: number; // 0 to 100
  level: 'Easy to Manufacture' | 'Moderate Complexity' | 'Complex Design';
  castingNotes: string;
  settingNotes: string;
  polishingNotes: string;
}

export interface MultiView {
  front: string;       // Front perspective narrative description
  side: string;        // Side perspective narrative description
  perspective: string; // 3D perspective narrative description
}

// ─── NEW: Motif Data Structure ────────────────────────────────────────────────
export interface MotifData {
  type: 'animal' | 'floral' | 'geometric' | 'celestial' | 'abstract' | 'other';
  description: string;           // e.g., "phoenix with spread wings and ruby eye"
  elements: string[];            // e.g., ['wings', 'tail feathers', 'ruby eye']
  specificDetails?: {
    [key: string]: string | number | boolean;
    // e.g., { wings: 'spread', eyeColor: 'ruby', tailLength: 'long' }
  };
  visualKeywords: string[];      // For SVG generation prompt
  shapeHint?: string;            // e.g., "bird silhouette", "flower petals", "geometric pattern"
}

// ─── UPDATED: DesignPackage with motif ────────────────────────────────────────
export interface DesignPackage {
  id: string;
  name: string;
  timestamp: string;
  inputType: 'text' | 'sketch' | 'photo';
  prompt: string;
  spec: JewelrySpec;
  cost: CostBreakdown;
  manufacturing: ManufacturingScore;
  multiView: MultiView;
  notes: string;
  inputImage?: string; // base64 if sketch/photo
  motif?: MotifData;   // NEW: Motif information from AI spec
}

// ─── API Request for SVG Generation ───────────────────────────────────────────
export interface SVGGenerationRequest {
  design_id: string;
  design_name: string;
  prompt: string;
  notes: string;
  view: 'perspective' | 'front' | 'side';
  view_description: string;
  jewelry_type: string;
  metal: string;
  stone: string;
  stone_shape: string;
  stone_size: string;
  setting: string;
  details: string;
  motif?: MotifData | null;  // NEW: Pass motif to backend
}

// ─── Existing types (unchanged) ──────────────────────────────────────────────
export interface AdvisorRequest {
  age?: string;
  budget: number;
  currency: string;
  occasion: string;
  stylePreferences: string;
}

export interface GemOption {
  gemstone: string;
  suitability: string;
  explanation: string;
  approxCost: number;
}

export interface AdvisorResponse {
  recommendations: GemOption[];
  suggestedMetal: string;
  designIdea: string;
  pricingStrategy: string;
}

export interface TrendReport {
  trendingStyles: { style: string; growth: string; popularity: number; season: string }[];
  seasonalGemstones: { season: string; stone: string; reason: string; hotFactor: number }[];
  styleComparisons: { dimension: string; optionA: string; optionB: string; weightA: number; weightB: number }[];
}
