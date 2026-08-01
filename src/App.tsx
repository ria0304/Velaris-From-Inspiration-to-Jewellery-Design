import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  PenTool, 
  Upload, 
  Ruler, 
  Briefcase, 
  Coins, 
  FileText, 
  Heart, 
  RefreshCw, 
  Share2, 
  Check, 
  ChevronRight, 
  AlertCircle, 
  TrendingUp, 
  Scale, 
  HelpCircle, 
  Star,
  Info,
  Layers,
  Trash2,
  Bookmark,
  Printer
} from 'lucide-react';
import { DesignPackage, JewelrySpec, CostBreakdown, ManufacturingScore, AdvisorResponse, TrendReport } from './types';
import JewelryBlueprint from './components/JewelryBlueprint';
// @ts-ignore
import agateBgImage from './assets/images/luxury_agate_backdrop_1782161136573.jpg';

export default function App() {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<'design' | 'advisor' | 'trends' | 'saved'>('design');
  
  // Design tab inputs
  const [inputType, setInputType] = useState<'text' | 'sketch' | 'photo'>('text');
  const [textPrompt, setTextPrompt] = useState('');
  const [styleOrientation, setStyleOrientation] = useState('Contemporary Minimalist');
  const [budgetTier, setBudgetTier] = useState<'Value' | 'Balanced' | 'Premium'>('Balanced');
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  
  // Canvas drawing state
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  
  // App state
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [currentDesign, setCurrentDesign] = useState<DesignPackage | null>(null);
  const [savedDesigns, setSavedDesigns] = useState<DesignPackage[]>([]);
  
  // Advisor state
  const [advisorAge, setAdvisorAge] = useState('28');
  const [advisorBudget, setAdvisorBudget] = useState('3200');
  const [advisorOccasion, setAdvisorOccasion] = useState('Engagement');
  const [advisorStyle, setAdvisorStyle] = useState('Sleek Solitaire');
  const [advisorResult, setAdvisorResult] = useState<AdvisorResponse | null>(null);
  const [isAdvisorLoading, setIsAdvisorLoading] = useState(false);

  // Trend Intel state
  const [trendReport, setTrendReport] = useState<TrendReport | null>(null);
  const [isTrendLoading, setIsTrendLoading] = useState(false);

  // Load initial templates & trends on mount
  useEffect(() => {
    fetchTrends();
    fetchSavedDesigns();
    
    // Set a magnificent default design package as the introduction
    const welcomeDesign: DesignPackage = {
      id: "vel-welcome",
      name: "The Emerald Sovereign Ring",
      timestamp: "June 22, 2026",
      inputType: "text",
      prompt: "Emerald-cut deep green emerald ring with standard 18K white gold shoulder halo and whisper band",
      spec: {
        type: "Ring",
        metal: "18K White Gold",
        stone: "Emerald",
        shape: "Emerald-Cut",
        setting: "Halo",
        occasion: "Engagement",
        stoneSize: "2.3 carat",
        bandWidth: "1.9 mm",
        details: "Featuring beautiful, ultra-compressed pavé halo shoulders holding micro-diamonds with hand-scalloped under-galleries."
      },
      cost: {
        metalCost: 850,
        stoneCost: 1900,
        laborCost: 650,
        markupPercent: 25,
        totalCost: 4250
      },
      manufacturing: {
        score: 65,
        level: "Moderate Complexity",
        castingNotes: "Casting Complexity: 65%. Perfect vacuum centrifuge with sprue thickeners to guide molten gold.",
        settingNotes: "Setting Complexity: 72%. Tight micro-prong halo settings require a high-magnification microscope mount.",
        polishingNotes: "Finishing Level: 58%. Delicate scalloped side walls need rogue composite polishing before stone insertion."
      },
      multiView: {
        front: "The front view displays the dominant emerald octagon emerald centered atop an exquisite step-cut micro halo background that sparkles on the visual margins.",
        side: "From the profile, the Cathedral arch rises cleanly to meet the secure setting basket, with intricate crown cutouts to let sunlight ignite the green gem depth.",
        perspective: "The 3D angle emphasizes the slim, high-polished 1.9mm white gold comfort-fit band as it tapers elegantly towards the sparkling crown array."
      },
      notes: "The Emerald Sovereign is a masterpiece of symmetry and natural brilliance. The green emerald's depth is coupled with modern geometric lines to recall vintage royal prestige reimagined for the contemporary woman."
    };
    setCurrentDesign(welcomeDesign);
  }, []);

  // Initialize Canvas
  useEffect(() => {
    if (inputType === 'sketch' && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.strokeStyle = '#d4af37';
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.fillStyle = '#050c08';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }
    }
  }, [inputType]);

  // Sketch Drawing Handlers
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    setIsDrawing(true);
    const pos = getEventCoords(e, canvas);
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const pos = getEventCoords(e, canvas);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
    // Convert canvas to base64 image
    if (canvasRef.current) {
      const dataUrl = canvasRef.current.toDataURL('image/png');
      setUploadedImage(dataUrl);
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#050c08';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      setUploadedImage(null);
    }
  };

  const getEventCoords = (e: any, canvas: HTMLCanvasElement) => {
    const rect = canvas.getBoundingClientRect();
    // Support touch and mouse coordinates
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return {
      x: clientX - rect.left,
      y: clientY - rect.top
    };
  };

  // Upload Photo as Inspiration
  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setUploadedImage(event.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  // Drag and Drop files
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setUploadedImage(event.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  // Call express server backend to generate custom design
  const generateJewelryDesign = async () => {
    setIsGenerating(true);
    setErrorMsg(null);
    
    // Fallback prompt validation
    if (inputType === 'text' && !textPrompt.trim()) {
      setErrorMsg("Please describe your jewelry design concepts first.");
      setIsGenerating(false);
      return;
    }

    if ((inputType === 'sketch' || inputType === 'photo') && !uploadedImage) {
      setErrorMsg(inputType === 'sketch' ? "Please draw something on the canvas above first." : "Please upload or drop an inspiration image.");
      setIsGenerating(false);
      return;
    }

    try {
      const res = await fetch("/api/generate-design", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: inputType === 'text' ? textPrompt : `Style focus: ${styleOrientation}. Details: ${textPrompt}`,
          inputType,
          style: styleOrientation,
          budget: budgetTier,
          image: uploadedImage // sketch base64 or photo base64
        })
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || "Bespoke compilation failed. Please check your API configuration.");
      }

      const data: DesignPackage = await res.json();
      setCurrentDesign(data);
      
      // Auto-save generated packages directly in the local collection session
      await saveDesignToCollection(data);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "An unexpected error occurred during jewelry formulation.");
    } finally {
      setIsGenerating(false);
    }
  };

  // Helper: Save Design to express state
  const saveDesignToCollection = async (design: DesignPackage) => {
    try {
      const response = await fetch("/api/save-design", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(design)
      });
      if (response.ok) {
        fetchSavedDesigns();
      }
    } catch (err) {
      console.error("Failed to save to express state, carrying on in client state:", err);
    }
  };

  // Helper: Fetch saved designs
  const fetchSavedDesigns = async () => {
    try {
      const res = await fetch("/api/saved-designs");
      if (res.ok) {
        const list: DesignPackage[] = await res.json();
        setSavedDesigns(list);
      }
    } catch (err) {
      console.error("Failed to fetch saved designs:", err);
    }
  };

  // Helper: Fetch Trend intelligence from server
  const fetchTrends = async () => {
    setIsTrendLoading(true);
    try {
      const res = await fetch("/api/trends");
      if (res.ok) {
        const data: TrendReport = await res.json();
        setTrendReport(data);
      }
    } catch (err) {
      console.error("Failed to fetch trends catalog:", err);
    } finally {
      setIsTrendLoading(false);
    }
  };

  // Gifting Advisor formulation submit
  const getGiftAdvice = async () => {
    setIsAdvisorLoading(true);
    try {
      const res = await fetch("/api/jewellery-advisor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          age: advisorAge,
          budget: parseFloat(advisorBudget) || 2500,
          currency: 'USD',
          occasion: advisorOccasion,
          stylePreferences: advisorStyle
        })
      });

      if (!res.ok) {
        throw new Error("Could not formulate advice. Please verify API configurations.");
      }
      
      const data: AdvisorResponse = await res.json();
      setAdvisorResult(data);
    } catch (err: any) {
      console.error("Advisor Error:", err);
      setErrorMsg(err.message || "Advisor recommendation model encountered an issue.");
    } finally {
      setIsAdvisorLoading(false);
    }
  };

  // Pre-configured Quick Prompts to spark instant gorgeous ideas
  const samplePrompts = [
    { title: "Art Deco Emerald Ring", prompt: "An Art Deco vintage engagement ring containing an emerald-cut deep green emerald center, flanked by sapphire baguettes on a platinum scroll band" },
    { title: "Celestial Rose Gold Necklace", prompt: "A delicate fine crescent celestial pendant, embedded with micro-diamonds and central marquise aquamarine representing starlight" },
    { title: "Toi et Moi Romance Ring", prompt: "A classic Toi et Moi cluster duo holding an oval ruby beside a pear diamond on a polished warm rose gold crossover band" }
  ];

  // Printable professional PDF design brief trigger
  const printBrief = () => {
    window.print();
  };

  // Quick select gemstone to advisor format
  const copyAdvisorConcept = (rec: any) => {
    setInputType('text');
    setTextPrompt(`A modern ${rec.gemstone} piece suited for an elegant ${advisorOccasion}. Style guideline: ${rec.explanation.substring(0, 100)}...`);
    setActiveTab('design');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#072D33] text-[#dae2de] selection:bg-[#DFBE8B] selection:text-[#33091B] antialiased font-sans pb-16 relative overflow-hidden">
      
      {/* Exact Luxury Agate Master Image Background */}
      <div className="absolute inset-0 w-full h-full pointer-events-none -z-10 no-print">
        <img 
          src={agateBgImage} 
          alt="Luxury Agate Background" 
          className="w-full h-full object-cover select-none"
          referrerPolicy="no-referrer"
        />
        {/* Soft elegant overlays to maintain contrast for the text while showing the luxurious veins and waves */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#072D33]/40 via-[#101a1c]/75 to-[#33091B]/85 mix-blend-multiply" />
        <div className="absolute inset-0 bg-black/5" />
      </div>

      {/* Sophisticated Jewelry Blueprint Tech Grid with Agate Sage tinted lines */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#3a7564_1px,transparent_1px),linear-gradient(to_bottom,#3a7564_1px,transparent_1px)] bg-[size:4.5rem_4.5rem] [mask-image:radial-gradient(ellipse_80%_60%_at_50%_40%,#000_30%,transparent_100%)] opacity-[0.12] pointer-events-none -z-10 no-print" />
      
      {/* Plus signs / coordinate markers styled with Champagne Gold */}
      <div className="absolute inset-0 bg-[radial-gradient(#DFBE8B_1px,transparent_1px)] bg-[size:9rem_9rem] [mask-image:radial-gradient(ellipse_90%_70%_at_50%_50%,#000_25%,transparent_75%)] opacity-[0.08] pointer-events-none -z-10 no-print" />

      {/* Elegant Ring Vectors in background for the extra luxury feel */}
      <div className="absolute top-[12%] right-[8%] w-56 h-56 border border-[#DFBE8B]/[0.08] rounded-full pointer-events-none -z-10 no-print hidden xl:flex items-center justify-center">
        <div className="w-40 h-40 border border-[#DFBE8B]/[0.1] rounded-full border-dashed animate-[spin_100s_linear_infinite]" />
        <div className="absolute w-2 h-2 rounded-full bg-[#DFBE8B]/30 top-[15%] left-[15%]" />
      </div>
      <div className="absolute bottom-[18%] left-[6%] w-72 h-72 border border-[#DFBE8B]/[0.06] rounded-full pointer-events-none -z-10 no-print hidden xl:flex items-center justify-center">
        <div className="w-56 h-56 border border-[#DFBE8B]/[0.08] rounded-full border-dashed animate-[spin_160s_linear_infinite]" />
        <div className="w-28 h-28 border border-[#3A7564]/[0.1] rounded-full" />
      </div>
      
      {/* Dynamic Printing Styles exclusively for Clean Jewelry PDF briefing */}
      <style>{`
        @media print {
          body {
            background: white !important;
            color: black !important;
          }
          header, footer, nav, button, .no-print {
            display: none !important;
          }
          .print-full {
            width: 100% !important;
            grid-template-cols: 1fr !important;
            background: white !important;
            color: black !important;
            box-shadow: none !important;
            border: none !important;
          }
          .print-dark-text {
            color: #0c0f0e !important;
          }
        }
      `}</style>
      
      {/* Brand Header & Hero Area */}
      <header className="border-b border-[#12221a] bg-[#030806]/95 backdrop-blur-md sticky top-0 z-40 no-print">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            {/* Elegant Serif Branding */}
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-[#d4af37] text-2xl font-serif tracking-widest font-semibold uppercase">Velaris</span>
                <span className="text-[10px] bg-[#d4af37]/10 text-[#d4af37] border border-[#d4af37]/30 px-2 py-0.5 rounded font-mono font-medium">Bespoke Creator</span>
              </div>
              <span className="text-[10.5px] uppercase tracking-[0.25em] text-[#d4af37]/75 font-mono">From Inspiration to Jewellery Design</span>
            </div>

            {/* Premium Navigation Tabs */}
            <nav className="hidden md:flex space-x-1 bg-[#09110d] p-1 rounded-md border border-[#12221a]">
              <button
                onClick={() => { setActiveTab('design'); setErrorMsg(null); }}
                className={`flex items-center gap-2 px-4 py-2 rounded text-xs uppercase tracking-wider font-semibold transition ${
                  activeTab === 'design' ? 'bg-[#122f1f] text-[#d4af37] border-b border-[#d4af37]' : 'text-gray-400 hover:text-white'
                }`}
                id="tab-design-lab"
              >
                <Sparkles className="w-3.5 h-3.5 text-[#d4af37]" />
                Design Lab
              </button>
              
              <button
                onClick={() => { setActiveTab('advisor'); setErrorMsg(null); }}
                className={`flex items-center gap-2 px-4 py-2 rounded text-xs uppercase tracking-wider font-semibold transition ${
                  activeTab === 'advisor' ? 'bg-[#122f1f] text-[#d4af37] border-b border-[#d4af37]' : 'text-gray-400 hover:text-white'
                }`}
                id="tab-advisor"
              >
                <Heart className="w-3.5 h-3.5 text-[#d4af37]" />
                Gemstone Advisor
              </button>

              <button
                onClick={() => { setActiveTab('trends'); setErrorMsg(null); }}
                className={`flex items-center gap-2 px-4 py-2 rounded text-xs uppercase tracking-wider font-semibold transition ${
                  activeTab === 'trends' ? 'bg-[#122f1f] text-[#d4af37] border-b border-[#d4af37]' : 'text-gray-400 hover:text-white'
                }`}
                id="tab-trends"
              >
                <TrendingUp className="w-3.5 h-3.5 text-[#d4af37]" />
                Trend Intel
              </button>

              <button
                onClick={() => { setActiveTab('saved'); setErrorMsg(null); }}
                className={`flex items-center gap-2 px-4 py-2 rounded text-xs uppercase tracking-wider font-semibold transition relative ${
                  activeTab === 'saved' ? 'bg-[#122f1f] text-[#d4af37] border-b border-[#d4af37]' : 'text-gray-400 hover:text-white'
                }`}
                id="tab-saved-collections"
              >
                <Bookmark className="w-3.5 h-3.5 text-[#d4af37]" />
                My Collection
                {savedDesigns.length > 0 && (
                  <span className="absolute -top-1 -right-1 bg-[#d4af37] text-[#020504] text-[9px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
                    {savedDesigns.length}
                  </span>
                )}
              </button>
            </nav>

            {/* CTA action for jeweller feedback */}
            <div className="flex items-center gap-3">
              <button 
                onClick={printBrief}
                className="hidden lg:flex items-center gap-1.5 px-3.5 py-1.5 bg-[#0e1612] border border-[#1a3a29] text-xs uppercase tracking-wider text-gray-300 hover:text-[#d4af37] hover:border-[#d4af37]/60 rounded transition"
              >
                <Printer className="w-3.5 h-3.5" />
                Print PDF
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Sticky Navigation Banner */}
      <div className="block md:hidden bg-[#050b08] border-b border-[#12221a] py-2 px-4 overflow-x-auto whitespace-nowrap sticky top-20 z-40 no-print flex gap-2">
        <button
          onClick={() => { setActiveTab('design'); }}
          className={`px-3 py-2 rounded text-xs uppercase tracking-wider font-medium ${activeTab === 'design' ? 'bg-[#112d1c] text-[#d4af37]' : 'text-gray-400'}`}
        >
          Design Lab
        </button>
        <button
          onClick={() => { setActiveTab('advisor'); }}
          className={`px-3 py-2 rounded text-xs uppercase tracking-wider font-medium ${activeTab === 'advisor' ? 'bg-[#112d1c] text-[#d4af37]' : 'text-gray-400'}`}
        >
          Gemstone Advisor
        </button>
        <button
          onClick={() => { setActiveTab('trends'); }}
          className={`px-3 py-2 rounded text-xs uppercase tracking-wider font-medium ${activeTab === 'trends' ? 'bg-[#112d1c] text-[#d4af37]' : 'text-gray-400'}`}
        >
          Trend Intel
        </button>
        <button
          onClick={() => { setActiveTab('saved'); }}
          className={`px-3 py-2 rounded text-xs uppercase tracking-wider font-medium relative ${activeTab === 'saved' ? 'bg-[#112d1c] text-[#d4af37]' : 'text-gray-400'}`}
        >
          My Collection
          {savedDesigns.length > 0 && (
            <span className="ml-1 bg-[#d4af37] text-black text-[9px] px-1 rounded-full font-bold">{savedDesigns.length}</span>
          )}
        </button>
      </div>

      {/* Main Body Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-10">
        
        {/* Error Boundary banner alerting missing parameters gracefully */}
        {errorMsg && (
          <div className="mb-8 p-4 bg-[#2c1313] border border-[#f87171]/40 rounded-lg flex items-start gap-3 no-print" id="alert-banner">
            <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-red-200">Bespoke Creator Warning</h4>
              <p className="text-xs text-red-300/90 leading-relaxed mt-1">{errorMsg}</p>
              <div className="mt-2 text-[10px] text-gray-400">
                To bypass, ensure your Velaris API is configured correctly in your environment.
              </div>
            </div>
          </div>
        )}

        {/* 1. BESPOKE LAB TAB */}
        {activeTab === 'design' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            {/* LEFT INPUT SECTION - 5 units width */}
            <section className="lg:col-span-5 space-y-6 no-print">
              <div className="bg-[#050c08] border border-[#122e1e] rounded-xl p-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-[#d4af37]/5 rounded-full blur-2xl pointer-events-none"></div>
                
                <h2 className="text-xs font-mono uppercase tracking-widest text-[#d4af37] flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5" /> Concept Formulation Lab
                </h2>
                <p className="text-xs text-gray-400 font-serif mt-1">Scribble ideas, doodle models, or upload inspiration snapshots recursively.</p>

                {/* Horizontal Category Switcher */}
                <div className="grid grid-cols-3 bg-[#020503] border border-[#12221a]/60 p-1 rounded-md mt-5">
                  <button
                    onClick={() => { setInputType('text'); setUploadedImage(null); }}
                    className={`flex flex-col items-center py-2.5 rounded text-xs gap-1 transition ${
                      inputType === 'text' ? 'bg-[#112d1c] text-[#d4af37] border border-[#2b5e3d]/30' : 'text-gray-400 hover:text-white'
                    }`}
                    id="input-text-tab"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Type It</span>
                  </button>
                  <button
                    onClick={() => { setInputType('sketch'); setUploadedImage(null); }}
                    className={`flex flex-col items-center py-2.5 rounded text-xs gap-1 transition ${
                      inputType === 'sketch' ? 'bg-[#112d1c] text-[#d4af37] border border-[#2b5e3d]/30' : 'text-gray-400 hover:text-white'
                    }`}
                    id="input-sketch-tab"
                  >
                    <PenTool className="w-4 h-4" />
                    <span>Sketch It</span>
                  </button>
                  <button
                    onClick={() => { setInputType('photo'); setUploadedImage(null); }}
                    className={`flex flex-col items-center py-2.5 rounded text-xs gap-1 transition ${
                      inputType === 'photo' ? 'bg-[#112d1c] text-[#d4af37] border border-[#2b5e3d]/30' : 'text-gray-400 hover:text-white'
                    }`}
                    id="input-photo-tab"
                  >
                    <Upload className="w-4 h-4" />
                    <span>Upload It</span>
                  </button>
                </div>

                {/* DYNAMIC FORM VIEWS */}
                <div className="mt-6 space-y-4">
                  {/* TEXT INPUT FIELD */}
                  {inputType === 'text' && (
                    <div className="space-y-2">
                      <label className="text-xs font-serif tracking-wider text-gray-300">Detailed Design Concept Description</label>
                      <textarea
                        value={textPrompt}
                        onChange={(e) => setTextPrompt(e.target.value)}
                        placeholder="e.g. vintage 18k yellow gold solitaire ring with cushion-cut moissanite centerpiece and split pave shank design..."
                        className="w-full text-xs font-sans h-36 p-4 bg-[#020604] border border-[#122e1e] rounded-lg text-white focus:outline-none focus:border-[#d4af37] placeholder-gray-500 transition resize-none"
                        id="text-prompt-textarea"
                      />
                      
                      {/* Suggestion tags */}
                      <p className="text-[10px] text-gray-400 font-mono italic">Need master concepts? Select one below:</p>
                      <div className="flex flex-wrap gap-2 pt-1">
                        {samplePrompts.map((p, idx) => (
                          <button
                            key={idx}
                            onClick={() => setTextPrompt(p.prompt)}
                            className="text-[10.5px] bg-[#0c1410] border border-[#182d21]/60 px-2.5 py-1.5 rounded text-emerald-400 hover:text-[#d4af37] hover:border-[#d4af37]/40 transition text-left block"
                            id={`quick-sample-${idx}`}
                          >
                            + {p.title}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* DRAWING SKETCH CANVAS SUB-VIEW */}
                  {inputType === 'sketch' && (
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <label className="text-xs font-serif tracking-wider text-gray-300">Doodle/Sketch Your Custom Shape</label>
                        <button
                          onClick={clearCanvas}
                          className="text-[10px] uppercase font-mono tracking-wider text-red-400 hover:text-red-300 transition"
                          id="clear-canvas-btn"
                        >
                          Clear Board
                        </button>
                      </div>

                      <div className="border border-[#122e1e] rounded-lg overflow-hidden bg-[#050c08] relative aspect-square">
                        <canvas
                          ref={canvasRef}
                          width={320}
                          height={320}
                          onMouseDown={startDrawing}
                          onMouseMove={draw}
                          onMouseUp={stopDrawing}
                          onMouseLeave={stopDrawing}
                          onTouchStart={startDrawing}
                          onTouchMove={draw}
                          onTouchEnd={stopDrawing}
                          className="w-full h-full cursor-crosshair touch-none"
                        />
                        <div className="absolute bottom-2 right-2 text-[9px] text-[#d4af37]/75 font-mono px-2 py-0.5 bg-[#020503]/80 border border-[#1a3a29] rounded pointer-events-none">
                          Gold Brush Tool
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-xs font-serif tracking-widest text-gray-300 block">Additional Sketch Specifications (Optional)</label>
                        <input
                          type="text"
                          value={textPrompt}
                          onChange={(e) => setTextPrompt(e.target.value)}
                          placeholder="e.g. adjust width back to 2.2mm"
                          className="w-full text-xs p-3 bg-[#020604] border border-[#122e1e] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#d4af37]"
                          id="sketch-notes-input"
                        />
                      </div>
                    </div>
                  )}

                  {/* DRAG AND DROP FILE UPLOAD */}
                  {inputType === 'photo' && (
                    <div className="space-y-4">
                      <label className="text-xs font-serif tracking-wider text-gray-300 block">Upload Jewelry Inspiration Snapshots</label>
                      
                      <div
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                        className="border-2 border-dashed border-[#183626] hover:border-[#d4af37]/60 rounded-lg p-6 bg-[#040906] flex flex-col items-center justify-center text-center transition min-h-[180px] cursor-pointer"
                        onClick={() => document.getElementById('photo-file-picker')?.click()}
                        id="drag-drop-zone"
                      >
                        <input
                          id="photo-file-picker"
                          type="file"
                          accept="image/*"
                          onChange={handlePhotoUpload}
                          className="hidden"
                        />
                        
                        {uploadedImage ? (
                          <div className="space-y-3">
                            <img
                              src={uploadedImage}
                              alt="Inspiration Preview"
                              className="max-h-32 object-contain rounded border border-[#1e3a2b] mx-auto"
                            />
                            <p className="text-[10px] text-emerald-400 font-mono">Image loaded successfully</p>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <Upload className="w-8 h-8 text-[#d4af37]/60 mx-auto" strokeWidth={1.5} />
                            <p className="text-xs text-gray-300">Drag & drop your reference photo, or <span className="text-[#d4af37] underline font-medium">browse</span></p>
                            <p className="text-[10px] text-gray-500">Supports PNG, JPG references</p>
                          </div>
                        )}
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-xs font-serif tracking-widest text-gray-300 block">Reimagining Guidance (Optional)</label>
                        <input
                          type="text"
                          value={textPrompt}
                          onChange={(e) => setTextPrompt(e.target.value)}
                          placeholder="e.g. change gold color to 18K Yellow and use high prong halo details"
                          className="w-full text-xs p-3 bg-[#020604] border border-[#122e1e] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#d4af37]"
                          id="photo-notes-input"
                        />
                      </div>
                    </div>
                  )}

                  {/* STYLE MATRIX SELECTIONS */}
                  <div className="grid grid-cols-2 gap-4 pt-3 border-t border-[#122e1e]/60">
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-mono text-gray-400 uppercase tracking-wider block">Style Orientation</label>
                      <select
                        value={styleOrientation}
                        onChange={(e) => setStyleOrientation(e.target.value)}
                        className="w-full text-xs p-2.5 bg-[#020503] border border-[#122e1e] rounded text-gray-200 focus:outline-none focus:border-[#d4af37]"
                        id="select-style-orientation"
                      >
                        <option value="Contemporary Minimalist">Contemporary Minimalist</option>
                        <option value="Art Deco & Vintage">Art Deco Vintage</option>
                        <option value="Royal Sovereign Classic">Sovereign Royal Classic</option>
                        <option value="Avant-Garde Architectural">Avant-Garde Sculpted</option>
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[11px] font-mono text-gray-400 uppercase tracking-wider block">Budget & Material Tier</label>
                      <select
                        value={budgetTier}
                        onChange={(e) => setBudgetTier(e.target.value as any)}
                        className="w-full text-xs p-2.5 bg-[#020503] border border-[#122e1e] rounded text-gray-200 focus:outline-none focus:border-[#d4af37]"
                        id="select-budget-tier"
                      >
                        <option value="Value">Value Tier (14K / Silver, Gem &lt; 1.0ct)</option>
                        <option value="Balanced">Balanced Tier (18K, Gem 1.0-2.0ct)</option>
                        <option value="Premium">Premium Elite (Platinum, Gem &gt; 2.2ct)</option>
                      </select>
                    </div>
                  </div>

                  {/* SUBMIT BUTTON */}
                  <button
                    onClick={generateJewelryDesign}
                    disabled={isGenerating}
                    className="w-full mt-4 flex items-center justify-center gap-2 bg-[#d4af37] text-[#020503] py-3.5 px-4 rounded-lg font-semibold uppercase tracking-widest text-xs hover:bg-[#ffe180] active:scale-[0.98] transition shadow-lg disabled:opacity-40 disabled:cursor-not-allowed"
                    id="submit-generate-be-btn"
                  >
                    {isGenerating ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Formulating CAD Specs...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 fill-current" />
                        <span>Assemble Jewellery Design</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Informative Tips block */}
              <div className="bg-[#030907] border border-[#1a3a29]/30 rounded-lg p-5 text-xs text-gray-400 space-y-2">
                <div className="flex gap-2 text-[#d4af37] font-semibold items-center font-serif text-[11px] uppercase tracking-wider">
                  <Info className="w-3.5 h-3.5" />
                  <span>The Velaris Core Integrity Promise</span>
                </div>
                <p className="leading-relaxed font-serif">
                  Our system evaluates molecular fluid models, material weights, stone alignments, and mechanical prongs to generate flawless blueprint schemas ready for physical casting instantly.
                </p>
              </div>
            </section>

            {/* RIGHT SIDE OUTPUT CONTAINER - 7 units width */}
            <section className="lg:col-span-7 space-y-8">
              {currentDesign ? (
                <div className="space-y-6 print-full" id="active-design-package-content">
                  
                  {/* DESIGN CAD SCHEMATIC BLUEPRINT */}
                  <JewelryBlueprint design={currentDesign} />

                  {/* SPECIFICATION CARD AND WORK ORDER BRIEF */}
                  <div className="bg-[#050c08] border border-[#122e1e] rounded-xl p-6 shadow-xl relative">
                    <div className="flex justify-between items-start border-b border-[#122e1e] pb-4 mb-6">
                      <div>
                        <span className="text-[10px] text-[#d4af37]/80 font-mono uppercase tracking-widest block">Bespoke Design Brief Spec Sheet</span>
                        <h2 className="text-2xl font-serif text-white tracking-wide mt-1">{currentDesign.name}</h2>
                        <span className="text-xs text-gray-400 font-mono block mt-1">Formulated {currentDesign.timestamp} • ID: {currentDesign.id}</span>
                      </div>
                      
                      <div className="flex gap-2 shrink-0 no-print">
                        <button
                          onClick={printBrief}
                          className="p-2.5 bg-[#0f1b14] border border-[#1e3a2b] text-white hover:text-[#d4af37] hover:border-[#d4af37] rounded-md transition"
                          title="Print Jeweller Work Order Design Brief"
                          id="btn-print-brief"
                        >
                          <Printer className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* ROMANTIC PROMPT NARRATIVE */}
                    <div className="space-y-2 mb-6">
                      <p className="text-xs text-gray-400 font-serif uppercase tracking-wider font-semibold">Artisanal Design Narrative</p>
                      <p className="text-xs text-stone-300 leading-relaxed italic bg-[#020504] border-l-2 border-[#d4af37] p-3.5 rounded-r">
                        "{currentDesign.notes}"
                      </p>
                    </div>

                    {/* TWO COLUMN SUMMARY DETAILS AND COSTS BREAKDOWN */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-2">
                      
                      {/* Left: Material Attributes */}
                      <div className="space-y-4">
                        <div className="border-b border-[#122e1e]/60 pb-1">
                          <span className="text-xs text-[#d4af37] font-mono uppercase tracking-widest">Aesthetic Chemistry</span>
                        </div>
                        
                        <div className="space-y-2.5 font-mono text-xs">
                          <div className="flex justify-between py-1 border-b border-[#0f1d14]">
                            <span className="text-gray-400">Gemstone Center</span>
                            <span className="text-white text-right">{currentDesign.spec.stone}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-[#0f1d14]">
                            <span className="text-gray-400">Gem Shape Cut</span>
                            <span className="text-white text-right">{currentDesign.spec.shape}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-[#0f1d14]">
                            <span className="text-gray-400">Primary Alloy Metal</span>
                            <span className="text-white text-right">{currentDesign.spec.metal}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-[#0f1d14]">
                            <span className="text-gray-400">Mount Setting Type</span>
                            <span className="text-white text-right">{currentDesign.spec.setting}</span>
                          </div>
                          {currentDesign.spec.bandWidth && (
                            <div className="flex justify-between py-1 border-b border-[#0f1d14]">
                              <span className="text-gray-400">Band Shank Width</span>
                              <span className="text-white text-right">{currentDesign.spec.bandWidth}</span>
                            </div>
                          )}
                          <div className="flex justify-between py-1 border-b border-[#0f1d14]">
                            <span className="text-gray-400 font-semibold text-emerald-400">Production Feasibility</span>
                            <span className="text-emerald-400 font-semibold uppercase text-right">Pass (Excellent)</span>
                          </div>
                        </div>

                        {/* Detailed Description */}
                        <div className="bg-[#020603] p-3 rounded border border-[#153421]/40">
                          <p className="text-[10px] text-[#d4af37] font-mono uppercase tracking-widest mb-1 font-semibold">Gemologist Notes</p>
                          <p className="text-xs text-slate-300 leading-relaxed font-serif">
                            {currentDesign.spec.details}
                          </p>
                        </div>
                      </div>

                      {/* Right: Cost Estimation Engine & Gauges */}
                      <div className="space-y-4">
                        <div className="border-b border-[#122e1e]/60 pb-1">
                          <span className="text-xs text-[#d4af37] font-mono uppercase tracking-widest">Bespoke Pricing Engine</span>
                        </div>

                        <div className="space-y-3">
                          {/* Cost Breakdowns with mini bars */}
                          <div>
                            <div className="flex justify-between text-xs font-mono mb-1 text-gray-300">
                              <span>Raw Metal Alloy Feedstock</span>
                              <span>${currentDesign.cost.metalCost}</span>
                            </div>
                            <div className="w-full bg-[#030906] h-1.5 roundedOverflow-hidden rounded-full border border-[#1a3a29]/30">
                              <div className="bg-amber-400 h-full rounded-full" style={{ width: `${Math.min(100, (currentDesign.cost.metalCost / currentDesign.cost.totalCost) * 100 * 2.5)}%` }}></div>
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between text-xs font-mono mb-1 text-gray-300">
                              <span>Sourced Diamond/Gem Specimen</span>
                              <span>${currentDesign.cost.stoneCost}</span>
                            </div>
                            <div className="w-full bg-[#030906] h-1.5 roundedOverflow-hidden rounded-full border border-[#1a3a29]/30">
                              <div className="bg-teal-400 h-full rounded-full" style={{ width: `${Math.min(100, (currentDesign.cost.stoneCost / currentDesign.cost.totalCost) * 100 * 1.5)}%` }}></div>
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between text-xs font-mono mb-1 text-gray-300">
                              <span>Master Artisan Bench Setup & Labor</span>
                              <span>${currentDesign.cost.laborCost}</span>
                            </div>
                            <div className="w-full bg-[#030906] h-1.5 roundedOverflow-hidden rounded-full border border-[#1a3a29]/30">
                              <div className="bg-[#d4af37] h-full rounded-full" style={{ width: `${Math.min(100, (currentDesign.cost.laborCost / currentDesign.cost.totalCost) * 100 * 2)}%` }}></div>
                            </div>
                          </div>

                          <div className="bg-[#020504] border border-[#d4af37]/20 p-4 rounded-lg mt-3 flex justify-between items-center relative overflow-hidden">
                            <div className="absolute right-[-10px] bottom-[-10px] w-14 h-14 bg-[#d4af37]/5 rounded-full pointer-events-none"></div>
                            
                            <div>
                              <span className="text-[10px] text-[#d4af37] font-mono tracking-widest uppercase block">ESTIMATED PRODUCTION COST</span>
                              <span className="text-[9px] text-gray-400 italic font-serif">Includes 25% bench markup</span>
                            </div>
                            <div className="text-right">
                              <span className="text-xl md:text-2xl font-serif text-[#d4af37] font-bold tracking-wide">${currentDesign.cost.totalCost.toLocaleString()}</span>
                              <span className="text-[10px] text-emerald-400 font-mono block">Work Order Quote</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* MANUFACTURING READY SCORES */}
                    <div className="mt-8 pt-6 border-t border-[#122e1e]">
                      <div className="flex items-center gap-2 mb-4">
                        <Scale className="w-4 h-4 text-emerald-400" />
                        <h3 className="text-xs uppercase font-mono text-[#dae2de] tracking-widest">Bench Manufacturing Readiness Analysis</h3>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-[#020503] border border-[#1e3a2b]/30 p-4 rounded-lg">
                          <span className="text-[10.5px] uppercase font-mono text-gray-400 block tracking-wider">Casting Feasibility</span>
                          <span className="text-sm font-semibold text-white mt-1 block">Alloy Casting</span>
                          <p className="text-[11px] text-gray-400 font-serif leading-relaxed mt-1.5">{currentDesign.manufacturing.castingNotes}</p>
                        </div>

                        <div className="bg-[#020503] border border-[#1e3a2b]/30 p-4 rounded-lg">
                          <span className="text-[10.5px] uppercase font-mono text-gray-400 block tracking-wider">Setting Feasibility</span>
                          <span className="text-sm font-semibold text-white mt-1 block">Mount Prongs Fit</span>
                          <p className="text-[11px] text-gray-400 font-serif leading-relaxed mt-1.5">{currentDesign.manufacturing.settingNotes}</p>
                        </div>

                        <div className="bg-[#020503] border border-[#1e3a2b]/30 p-4 rounded-lg">
                          <span className="text-[10.5px] uppercase font-mono text-gray-400 block tracking-wider">Luster Polishing</span>
                          <span className="text-sm font-semibold text-white mt-1 block">Polishing Grade</span>
                          <p className="text-[11px] text-gray-400 font-serif leading-relaxed mt-1.5">{currentDesign.manufacturing.polishingNotes}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-[#050c08] border border-[#122e1e] rounded-xl p-16 text-center shadow-xl flex flex-col items-center justify-center">
                  <Star className="w-12 h-12 text-[#d4af37] animate-pulse mb-4" />
                  <h3 className="text-lg font-serif text-white tracking-wide">Ready to design your masterwork?</h3>
                  <p className="text-xs text-gray-400 max-w-md mx-auto leading-relaxed mt-2">
                    Fill the form metrics on the left column using plain english, sketching interactive rings on the digital drawing canvas, or uploading an inspiration snapshot.
                  </p>
                </div>
              )}
            </section>
          </div>
        )}

        {/* 2. ADVISOR TAB */}
        {activeTab === 'advisor' && (
          <div className="space-y-8">
            <div className="bg-[#050c08] border border-[#122e1e] rounded-xl p-8 relative overflow-hidden max-w-4xl mx-auto shadow-2xl">
              <div className="absolute top-0 right-0 w-36 h-36 bg-[#d4af37]/5 rounded-full blur-2.5xl pointer-events-none"></div>
              
              <div className="border-b border-[#122e1e] pb-4 mb-6">
                <span className="text-[10px] font-mono text-[#d4af37] uppercase tracking-widest block">AI-Powered Strategic Sourcing</span>
                <h2 className="text-3xl font-serif text-white tracking-wide mt-1">Gifting & Gemstone Advisor</h2>
                <p className="text-xs text-gray-400 font-serif mt-1">Our computational pricing module optimizes stone size, alloy formulations, and structural settings around your exact gifting metrics.</p>
              </div>

              {/* INPUT FIELDS MATRIX */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-[#020503] border border-[#122e1e] p-4 rounded-lg">
                <div className="space-y-1.5">
                  <label className="text-[10px] text-gray-400 font-mono uppercase tracking-widest block">Target Age Group</label>
                  <input
                    type="number"
                    value={advisorAge}
                    onChange={(e) => setAdvisorAge(e.target.value)}
                    placeholder="e.g. 25"
                    className="w-full text-xs p-2.5 bg-[#050c08] border border-[#122e1e] rounded text-white focus:outline-none focus:border-[#d4af37]"
                    id="advisor-input-age"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] text-gray-400 font-mono uppercase tracking-widest block">Budget Limit (USD)</label>
                  <input
                    type="number"
                    value={advisorBudget}
                    onChange={(e) => setAdvisorBudget(e.target.value)}
                    placeholder="e.g. 3000"
                    className="w-full text-xs p-2.5 bg-[#050c08] border border-[#122e1e] rounded text-white focus:outline-none focus:border-[#d4af37]"
                    id="advisor-input-budget"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] text-gray-400 font-mono uppercase tracking-widest block">Gift Occasion</label>
                  <select
                    value={advisorOccasion}
                    onChange={(e) => setAdvisorOccasion(e.target.value)}
                    className="w-full text-xs p-2.5 bg-[#050c08] border border-[#122e1e] rounded text-white focus:outline-none focus:border-[#d4af37]"
                    id="advisor-input-occasion"
                  >
                    <option value="Engagement">Engagement</option>
                    <option value="Wedding">Wedding</option>
                    <option value="Anniversary">Anniversary</option>
                    <option value="Birthday Gift">Birthday Gift</option>
                    <option value="Graduation Award">Graduation</option>
                    <option value="Self-Reward">Self-Reward</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] text-gray-400 font-mono uppercase tracking-widest block">Recipient Style preferences</label>
                  <input
                    type="text"
                    value={advisorStyle}
                    onChange={(e) => setAdvisorStyle(e.target.value)}
                    placeholder="e.g. minimalist floral organic"
                    className="w-full text-xs p-2.5 bg-[#050c08] border border-[#122e1e] rounded text-white focus:outline-none focus:border-[#d4af37]"
                    id="advisor-input-style"
                  />
                </div>
              </div>

              {/* ACTION BTN */}
              <button
                onClick={getGiftAdvice}
                disabled={isAdvisorLoading}
                className="mt-6 flex items-center justify-center gap-2 bg-[#d4af37] text-black py-3 px-6 h-12 uppercase tracking-widest text-xs font-semibold hover:bg-[#ebd582] transition rounded-lg w-full md:w-auto"
                id="advisor-submit-btn"
              >
                {isAdvisorLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Analyzing Sourcing Models...</span>
                  </>
                ) : (
                  <>
                    <Heart className="w-4 h-4 fill-current" />
                    <span>Sift Sourcing Options</span>
                  </>
                )}
              </button>

              {/* RESPONSE VIEW */}
              {advisorResult && (
                <div className="mt-8 pt-8 border-t border-[#122e1e] space-y-6" id="advisor-advice-recommendations">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {advisorResult.recommendations.map((rec, idx) => (
                      <div key={idx} className="bg-[#020503] border border-[#1e3a2b]/40 rounded-lg p-5 flex flex-col justify-between relative hover:border-[#d4af37]/50 transition">
                        <div>
                          <div className="flex justify-between items-start">
                            <span className="text-[10px] bg-[#d4af37]/10 text-[#d4af37] border border-[#d4af37]/30 px-2 py-0.5 rounded font-mono">Option 0{idx+1}</span>
                            <span className="text-xs text-[#10b981] font-semibold tracking-wider font-mono">{rec.suitability}</span>
                          </div>
                          
                          <h4 className="text-lg font-serif text-white tracking-wide mt-3">{rec.gemstone}</h4>
                          <p className="text-xs text-gray-300 font-serif leading-relaxed mt-2">{rec.explanation}</p>
                        </div>

                        <div className="mt-6 pt-3 border-t border-[#122e1e]/60 flex justify-between items-center">
                          <div>
                            <span className="text-[10px] text-gray-400 block font-mono">Stone Spec Cost</span>
                            <span className="text-sm font-semibold text-white font-mono">${rec.approxCost} USD</span>
                          </div>
                          
                          <button
                            onClick={() => copyAdvisorConcept(rec)}
                            className="text-[10.5px] text-[#d4af37] hover:text-white uppercase font-semibold font-mono tracking-wider flex items-center gap-1 transition"
                            id={`copy-advisor-concept-rec-${idx}`}
                          >
                            Use This <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* HIGH CLASS PAIRING NOTE */}
                  <div className="bg-[#03130c] border border-emerald-500/20 rounded-lg p-5 grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                    <div className="md:col-span-8 space-y-1.5">
                      <span className="text-[10px] text-[#d4af37] uppercase font-mono tracking-widest font-semibold block">RECOMMENDED metal & original concept design</span>
                      <p className="text-xs text-white font-serif font-medium leading-relaxed italic">
                        "{advisorResult.designIdea}"
                      </p>
                      <p className="text-[11px] text-gray-400 font-serif mt-1">Matched flawlessly on: <strong className="text-emerald-300 font-sans">{advisorResult.suggestedMetal}</strong></p>
                    </div>
                    
                    <div className="md:col-span-4 bg-[#020503] p-3.5 rounded border border-[#1e3a2b] space-y-1">
                      <span className="text-[9px] text-[#d4af37] font-mono uppercase tracking-widest block font-medium">Pricing Optimization strategy</span>
                      <p className="text-[11px] text-gray-300 font-serif leading-relaxed">
                        {advisorResult.pricingStrategy}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 3. TREND INTELLIGENCE TAB */}
        {activeTab === 'trends' && (
          <div className="space-y-8 max-w-5xl mx-auto">
            <div className="bg-[#050c08] border border-[#122e1e] rounded-xl p-8">
              
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#122e1e] pb-5 mb-6">
                <div>
                  <span className="text-[10px] font-mono text-[#d4af37] uppercase tracking-widest block">Velaris Haute Joaillerie Index</span>
                  <h2 className="text-2xl font-serif text-white tracking-wide mt-1">Trend Intelligence Matrix</h2>
                  <p className="text-xs text-gray-400 font-serif mt-1">Track market interest parameters, gemstone popularity variations, and seasonal design shifts globally.</p>
                </div>
                
                <button
                  onClick={fetchTrends}
                  disabled={isTrendLoading}
                  className="flex items-center gap-1.5 text-xs text-gray-300 hover:text-white border border-[#1e3a2b] p-2 rounded bg-[#020503] transition font-mono self-start md:self-auto"
                  id="trends-refresh-btn"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Refresh Matrix
                </button>
              </div>

              {trendReport ? (
                <div className="space-y-8" id="live-trend-report-container">
                  
                  {/* TWO COLUMN GRID FOR STYLE COMPARISONS AND GEMSTONES */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    
                    {/* Style Growth indexes */}
                    <div className="space-y-4">
                      <h3 className="text-xs uppercase tracking-widest font-mono text-[#d4af37] border-b border-[#122e1e] pb-1.5">Trending Ring & Setting Formations</h3>
                      <div className="space-y-3.5">
                        {trendReport.trendingStyles.map((style, idx) => (
                          <div key={idx} className="bg-[#020503] border border-[#1a3a29]/30 p-4 rounded-lg flex justify-between items-center">
                            <div>
                              <span className="text-xs font-semibold text-white tracking-wide font-serif">{style.style}</span>
                              <div className="flex gap-2 items-center mt-1">
                                <span className="text-[10px] text-emerald-400 font-semibold font-mono">{style.growth}</span>
                                <span className="text-[9px] text-gray-500 font-mono">• {style.season}</span>
                              </div>
                            </div>
                            
                            <div className="text-right">
                              <span className="text-sm font-semibold font-mono text-[#d4af37]">{style.popularity}%</span>
                              <span className="text-[9px] text-gray-400 block font-mono">Market Index</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Seasonal Gemstones Focus */}
                    <div className="space-y-4">
                      <h3 className="text-xs uppercase tracking-widest font-mono text-[#d4af37] border-b border-[#122e1e] pb-1.5">Seasonal Sourced Gemstones focus</h3>
                      <div className="space-y-3.5">
                        {trendReport.seasonalGemstones.map((gem, idx) => (
                          <div key={idx} className="bg-[#020503] border border-[#1a3a29]/30 p-4 rounded-lg">
                            <div className="flex justify-between items-start">
                              <div>
                                <span className="text-[10px] text-[#d4af37] font-mono uppercase tracking-widest">{gem.season}</span>
                                <h4 className="text-sm font-semibold text-white tracking-wide mt-1 font-serif">{gem.stone}</h4>
                              </div>
                              <span className="text-xs font-semibold text-amber-500 font-mono">Ratio: {gem.hotFactor}/10</span>
                            </div>
                            <p className="text-xs text-gray-400 leading-relaxed font-serif mt-2 italic">
                              "{gem.reason}"
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                  </div>

                  {/* DESIGN AXIS CONTRASTS */}
                  <div className="space-y-4 pt-6 border-t border-[#122e1e]">
                    <h3 className="text-xs uppercase tracking-widest font-mono text-[#d4af37]">Contemporary Preference Dimensions</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {trendReport.styleComparisons.map((c, idx) => (
                        <div key={idx} className="bg-[#020503] border border-[#1e3a2b]/30 p-4 rounded-lg space-y-3">
                          <span className="text-[10px] text-gray-400 font-mono uppercase tracking-widest block">{c.dimension}</span>
                          
                          <div className="flex justify-between text-xs font-medium font-serif text-white">
                            <span>{c.optionA}</span>
                            <span>{c.optionB}</span>
                          </div>

                          <div className="w-full bg-[#050c08] h-3 rounded overflow-hidden rounded-full flex border border-[#1e3a2b]/50 font-mono text-[9px] text-center text-[#020504] font-bold">
                            <div className="bg-[#d4af37] h-full flex items-center justify-center" style={{ width: `${c.weightA}%` }}>
                              {c.weightA}%
                            </div>
                            <div className="bg-[#10b981] h-full flex items-center justify-center ml-auto" style={{ width: `${c.weightB}%` }}>
                              {c.weightB}%
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              ) : (
                <div className="text-center py-12">
                  <RefreshCw className="w-8 h-8 animate-spin text-[#d4af37] mx-auto mb-4" />
                  <p className="text-xs text-gray-400 font-serif">Querying index parameters from server...</p>
                </div>
              )}

            </div>
          </div>
        )}

        {/* 4. MY SAVED COLLECTION TAB */}
        {activeTab === 'saved' && (
          <div className="space-y-6">
            <div className="text-center lg:text-left max-w-5xl mx-auto border-b border-[#122e1e] pb-4 mb-6">
              <span className="text-[10px] font-mono text-[#d4af37] uppercase tracking-widest block">Bespoke Library collection</span>
              <h2 className="text-3xl font-serif text-white tracking-wide mt-1">My Sourced Collection</h2>
              <p className="text-xs text-gray-400 font-serif mt-1">Retrieve, review, or print technical specifications for physical workshop quotes anytime.</p>
            </div>

            {savedDesigns.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto" id="saved-designs-collection-grid">
                {savedDesigns.map((design, index) => (
                  <div
                    key={index}
                    className="bg-[#050c08] border border-[#122e1e] rounded-xl overflow-hidden hover:border-[#d4af37]/50 active:scale-[0.99] cursor-pointer transition flex flex-col justify-between"
                    onClick={() => {
                      setCurrentDesign(design);
                      setActiveTab('design');
                    }}
                    id={`saved-design-item-card-${index}`}
                  >
                    {/* Micro CAD Preview preview header */}
                    <div className="p-5 border-b border-[#122e1e]/60 bg-[#020503]">
                      <div className="flex justify-between items-start">
                        <span className="text-[10px] bg-[#d4af37]/10 text-[#d4af37] border border-[#d4af37]/30 px-2 py-0.5 rounded font-mono">
                          {design.spec.type}
                        </span>
                        <span className="text-xs font-mono font-bold text-[#d4af37]">${design.cost.totalCost.toLocaleString()}</span>
                      </div>
                      
                      <h3 className="text-lg font-serif text-white tracking-wide mt-3">{design.name}</h3>
                      <p className="text-[10px] text-gray-500 font-mono mt-1">Saved {design.timestamp}</p>
                    </div>

                    <div className="p-5 space-y-3 flex-grow">
                      {/* Specs badges */}
                      <div className="grid grid-cols-2 gap-1.5 text-[10.5px] font-mono text-slate-300">
                        <div>Metal: <strong className="text-white font-sans font-medium block">{design.spec.metal}</strong></div>
                        <div>Stones: <strong className="text-white font-sans font-medium block">{design.spec.stone}</strong></div>
                        <div>Setting: <strong className="text-white font-sans font-medium block">{design.spec.setting}</strong></div>
                        <div>Occasion: <strong className="text-white font-sans font-medium block">{design.spec.occasion}</strong></div>
                      </div>

                      <p className="text-[11.5px] text-stone-400 leading-relaxed font-serif pt-2 border-t border-[#122e1e]/40 line-clamp-3">
                        "{design.notes}"
                      </p>
                    </div>

                    {/* View specifications call to action */}
                    <div className="p-4 bg-[#0a1410] border-t border-[#122e1e]/60 text-xs text-[#d4af37] font-semibold font-mono tracking-widest text-center uppercase hover:bg-[#12251b] transition">
                      Load Into CAD Lab
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="max-w-md mx-auto text-center border border-[#122e1e] rounded-xl p-12 bg-[#050c08] space-y-4 shadow-xl">
                <Bookmark className="w-12 h-12 text-[#d4af37]/60 mx-auto" />
                <h3 className="text-lg font-serif text-white tracking-wide">No saved jewellery packages</h3>
                <p className="text-xs text-gray-400 leading-relaxed">
                  Your custom formulated masterpieces will show up here directly. Use the Design Lab tab to compile a layout today.
                </p>
                <button
                  onClick={() => setActiveTab('design')}
                  className="bg-[#d4af37] text-black text-xs font-semibold uppercase tracking-wider py-2.5 px-5 rounded hover:bg-[#ebd582] transition"
                  id="go-to-design-blank-btn"
                >
                  Start First Formula
                </button>
              </div>
            )}
          </div>
        )}

      </main>

      {/* FOOTER */}
      <footer className="mt-20 border-t border-[#12221a]/80 py-10 bg-[#010302] no-print">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row md:items-center justify-between gap-6 text-xs text-gray-500">
          <div className="flex flex-col gap-0.5">
            <span className="text-[#d4af37] font-serif uppercase tracking-widest font-semibold text-[13px]">Velaris</span>
            <span className="font-mono text-[9px] tracking-wider text-gray-600 block mt-0.5">PRECISION FORMULATED TO DAY ONE PRODUCTION</span>
          </div>

          <div className="flex gap-6 font-mono text-[10px]">
            <span>© 2026 Velaris Inc.</span>
            <span>All schematic blueprint rights reserved.</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
