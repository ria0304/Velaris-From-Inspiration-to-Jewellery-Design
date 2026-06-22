import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI, Type } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

// Parse incoming request JSON with generous payload bounds (for sketches and photos)
app.use(express.json({ limit: "15mb" }));

let aiInstance: GoogleGenAI | null = null;

function getAI() {
  if (!aiInstance) {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error("GEMINI_API_KEY environment variable is not configured. Please set your Gemini key in the Secrets panel.");
    }
    aiInstance = new GoogleGenAI({
      apiKey: apiKey,
      httpOptions: {
        headers: {
          'User-Agent': 'aistudio-build',
        }
      }
    });
  }
  return aiInstance;
}

// 1. API Endpoint: Generate Custom Jewelry Design from Text, Sketch, or Photo
app.post("/api/generate-design", async (req, res) => {
  try {
    const { prompt, inputType, style, budget, image } = req.body;

    const ai = getAI();
    let promptString = "";
    const systemIns = `You are Velaris AI, a master bespoke jewelry designer, gemologist, and designer.
Your task is to take customer inputs (ideas, sketch drawings, or photos of inspirational designs) and draft a masterfully designed, luxury piece of jewelry.

In corporate branding, remember we are 'Velaris — From Inspiration to Jewelry Design'. Keep descriptions beautiful, warm, romantic, and extremely easy for ordinary clients to understand (no complex engineering terms, no confusing technical acronyms). Focus on the beauty, shimmer, shape, and sentiment.

CRITICAL: Tailor pricing, materials, and stone size to the selected budget tier:
- 'Value': Select lovely, friendly materials like Sterling Silver or 14K Gold, moderate gemstone (0.5-1.0 ct), secure settings (Prong, Bezel). Total price should be lower ($300 to $1,000).
- 'Balanced': Select luxurious 18K Gold, sparkling diamonds, sapphire, or moissanite (1.0-2.0 ct), shimmering settings (Halo, Cathedral). Total price should be mid-range ($1,000 to $3,500).
- 'Premium': Select Platinum or 18K Gold, spectacular gem sizes (2.0-4.0+ ct), intricate settings, elegant galleries. Total price should be upper range ($4,000 to $15,000+).

Adhere strictly to standard enum options when outputting the following fields:
- Type: Ring, Earrings, Necklace, Bracelet, Brooch
- Metal: 18K Yellow Gold, 18K White Gold, 18K Rose Gold, Platinum, 14K Yellow Gold, Sterling Silver
- Gemstone: Diamond, Emerald, Sapphire, Ruby, Garnet, Moissanite, Aquamarine, Opal, Amethyst, Pearl, Morganite
- Gemstone Cut: Round, Oval, Emerald-Cut, Pear, Cushion, Princess, Marquise
- Setting Type: Prong, Bezel, Halo, Pavé, Channel, Tension, Cathedral
- Occasion: Engagement, Wedding, Anniversary, Birthday, Graduation, Self-Gift

Provide clear, friendly feedback for Casting, Setting, and Polishing, as well as distinct warm instructions for multi-perspective views (Front View, Side View, Perspective View).`;

    if (inputType === "text") {
      promptString = `Design an exquisite custom piece of jewelry with style orientation '${style}' and budget tier '${budget}' based on the user's inspiration concepts: "${prompt}".`;
    } else if (inputType === "sketch") {
      promptString = `The user has supplied a hand-drawn rough sketch or draft doodle. Inspect the layout of this sketch carefully and refine it into an exquisite physical product.
Adhere strictly to style orientation '${style}' and budget tier '${budget}'.
Customer additional description thoughts: "${prompt || "Refine my sketch into an artistic piece"}".`;
    } else if (inputType === "photo") {
      promptString = `The user has uploaded an inspiration photo. Extract the core metals, gemstone cuts, or general shape of this photo.
Then, adapt and transform them into a bespoke inspired original. Make sure it is not a direct copy, but rather a sophisticated reimagining following style orientation '${style}' and budget tier '${budget}'.
Customer custom requests: "${prompt || "Reimagine this beautiful layout"}".`;
    }

    const payloadParts: any[] = [];
    if (image && (inputType === "sketch" || inputType === "photo")) {
      // Clean up base64 prefix if present
      const base64Data = image.replace(/^data:image\/\w+;base64,/, "");
      payloadParts.push({
        inlineData: {
          mimeType: "image/png",
          data: base64Data
        }
      });
    }
    payloadParts.push({ text: promptString });

    const response = await ai.models.generateContent({
      model: "gemini-3.5-flash",
      contents: { parts: payloadParts },
      config: {
        systemInstruction: systemIns,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            name: { type: Type.STRING, description: "A beautiful, evocative name for this bespoke design" },
            type: { type: Type.STRING, description: "Type: Ring, Earrings, Necklace, Bracelet, or Brooch" },
            metal: { type: Type.STRING, description: "Metal choice matching standard enums" },
            stone: { type: Type.STRING, description: "Gemstone matching standard enums" },
            shape: { type: Type.STRING, description: "Gemstone Cut matching standard enums" },
            setting: { type: Type.STRING, description: "Setting Type matching standard enums" },
            occasion: { type: Type.STRING, description: "Occasion matching standard enums" },
            stoneSize: { type: Type.STRING, description: "Stone size/weight spec (e.g. '1.5 carats', '2.2ct')" },
            bandWidth: { type: Type.STRING, description: "Band width or frame thickness (e.g. '2.1mm')" },
            details: { type: Type.STRING, description: "An elegant, easy to understand summary of the design layout and gemstone settings" },
            notes: { type: Type.STRING, description: "The romantic design narrative, physical presence, and master jeweler thoughts, simple and gorgeous." },
            metalCost: { type: Type.INTEGER, description: "Raw metal material cost in USD" },
            stoneCost: { type: Type.INTEGER, description: "Gemstone/diamond cost in USD" },
            laborCost: { type: Type.INTEGER, description: "Craftsman setting and carving labor cost in USD" },
            castingComplexity: { type: Type.INTEGER, description: "Casting simplicity rating (0 to 100)" },
            settingComplexity: { type: Type.INTEGER, description: "Gemstone settings simplicity rating (0 to 100)" },
            polishingComplexity: { type: Type.INTEGER, description: "Finishing & polish rating (0 to 100)" },
            multiView: {
              type: Type.OBJECT,
              properties: {
                front: { type: Type.STRING, description: "Simple, easy descriptions of what a front-on view of the design shows" },
                side: { type: Type.STRING, description: "Simple description of the profile or side view details" },
                perspective: { type: Type.STRING, description: "Warm description of the design viewed from a 3/4 perspective angle" }
              },
              required: ["front", "side", "perspective"]
            }
          },
          required: [
            "name", "type", "metal", "stone", "shape", "setting", "occasion",
            "stoneSize", "bandWidth", "details", "notes",
            "metalCost", "stoneCost", "laborCost",
            "castingComplexity", "settingComplexity", "polishingComplexity", "multiView"
          ]
        }
      }
    });

    const outputText = response.text;
    if (!outputText) {
      throw new Error("No output content returned from Gemini model.");
    }

    const rawData = JSON.parse(outputText);

    // Compute derived specs to ensure full frontend compatibility
    const totalRaw = rawData.metalCost + rawData.stoneCost + rawData.laborCost;
    const markupPercent = 25; // standard jewelry retailer markup
    const totalCost = Math.round(totalRaw * (1 + markupPercent / 100));

    const avgComplexity = Math.round((rawData.castingComplexity + rawData.settingComplexity + rawData.polishingComplexity) / 3);
    let level: "Easy to Hand-craft" | "Moderate Craft" | "Intricate Masterpiece" = "Moderate Craft";
    if (avgComplexity < 40) level = "Easy to Hand-craft";
    else if (avgComplexity > 75) level = "Intricate Masterpiece";

    const designPackage = {
      id: "vel-" + Math.random().toString(36).substr(2, 9),
      name: rawData.name,
      timestamp: new Date().toLocaleDateString("en-US", { year: 'numeric', month: 'long', day: 'numeric' }),
      inputType,
      prompt: prompt || (inputType === "sketch" ? "Custom Sketch Conversion" : "Custom Photo Reimagining"),
      inputImage: image || null,
      spec: {
        type: rawData.type,
        metal: rawData.metal,
        stone: rawData.stone,
        shape: rawData.shape,
        setting: rawData.setting,
        occasion: rawData.occasion,
        stoneSize: rawData.stoneSize,
        bandWidth: rawData.bandWidth || "1.8 mm",
        details: rawData.details
      },
      cost: {
        metalCost: rawData.metalCost,
        stoneCost: rawData.stoneCost,
        laborCost: rawData.laborCost,
        markupPercent,
        totalCost
      },
      manufacturing: {
        score: avgComplexity,
        level,
        castingNotes: "This choice of metal is sturdy, easy to shape into standard curves, and holds a beautiful polish forever without tarnishing.",
        settingNotes: "The delicate mount relies on standard prong alignments. The prongs are hand-bent over the gem sides to keep your stone absolutely safe.",
        polishingNotes: "Expertly hand-polished to a high luster finish, making every facet shimmer beautifully in standard natural sunlight."
      },
      multiView: {
        front: rawData.multiView?.front || "A beautiful vertical balance highlighting the main stone.",
        side: rawData.multiView?.side || "The sparkling profile and basket stand elegant above the band.",
        perspective: rawData.multiView?.perspective || "A lovely angled view displaying the gorgeous integration of setting and supportive band."
      },
      notes: rawData.notes
    };

    res.json(designPackage);
  } catch (err: any) {
    console.error("Design Generation Error:", err);
    res.status(500).json({ error: err.message || "An error occurred during jewelry formulation." });
  }
});

// 2. API Endpoint: AI Jewellery Advisor (Gemstone Recommender & Gifting advice)
app.post("/api/jewellery-advisor", async (req, res) => {
  try {
    const { age, budget, currency, occasion, stylePreferences } = req.body;
    const ai = getAI();

    const systemInstructions = `You are a high-end luxury Gifting and Gemstone Advisor for 'Velaris'.
Your purpose is to review a budget limit, the occasion, style thoughts, and age (of the recipient) to recommend 3 exquisite gemstones that match beautifully.
For each option, explain why it provides the ultimate sentimental value or fits the budget framework beautifully. Make sure to estimate approximate costs. Include suggested metal choices, an original design theme idea, and professional luxury pricing strategies.`;

    const promptText = `Generate customized jewellery advisor recommendations:
Recipient details: ${age ? age + " years old" : "N/A"}.
Occasion of gift: ${occasion}.
User budget amount: ${budget} [Currency: ${currency || 'USD'}].
Recipient's style taste: ${stylePreferences || 'Elegant classic'}.`;

    const response = await ai.models.generateContent({
      model: "gemini-3.5-flash",
      contents: promptText,
      config: {
        systemInstruction: systemInstructions,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            recommendations: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  gemstone: { type: Type.STRING, description: "Name of the gemstone (e.g. Blue Sapphire, Morganite, Moissanite)" },
                  suitability: { type: Type.STRING, description: "Brief rating of suitability (e.g. Excellent, Birthstone match, Durable for daily wear)" },
                  explanation: { type: Type.STRING, description: "Artisanal explanation of why this gem matches the criteria, age, and style preferences" },
                  approxCost: { type: Type.INTEGER, description: "Estimated typical cost segment (USD) for a beautiful stone specimen of this kind" }
                },
                required: ["gemstone", "suitability", "explanation", "approxCost"]
              }
            },
            suggestedMetal: { type: Type.STRING, description: "Elegant recommended metal (e.g. 18K Rose Gold for warmth, or Platinum for durability)" },
            designIdea: { type: Type.STRING, description: "A gorgeous, poetic jewelry concept combining the materials" },
            pricingStrategy: { type: Type.STRING, description: "Strategic buying tips to maximize sparkle and design footprint within their budget limit" }
          },
          required: ["recommendations", "suggestedMetal", "designIdea", "pricingStrategy"]
        }
      }
    });

    const outputText = response.text;
    if (!outputText) throw new Error("No advisory commentary returned from model.");
    res.json(JSON.parse(outputText));

  } catch (err: any) {
    console.error("Advisor Error:", err);
    res.status(500).json({ error: err.message || "An error occurred during advisor formulation." });
  }
});

// 3. API Endpoint: Trend Intelligence & Style Comparison
app.get("/api/trends", async (req, res) => {
  try {
    const ai = getAI();
    const systemInstructions = `You are the chief Haute Joaillerie trend analyst at Velaris.
Formulate a highly reliable, up-to-the-minute trend intel summary report, identifying trending styles, seasonal gemstone focus, and custom style matrices. Provide insightful descriptions.`;

    const response = await ai.models.generateContent({
      model: "gemini-3.5-flash",
      contents: "Compile a live jewellery trend intelligence report with trending styles, seasonal preferences, and contrasting design dimensions.",
      config: {
        systemInstruction: systemInstructions,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            trendingStyles: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  style: { type: Type.STRING, description: "Trending Ring / Setting Style name" },
                  growth: { type: Type.STRING, description: "Stat indicating popularity growth (e.g., '+42% YoY')" },
                  popularity: { type: Type.INTEGER, description: "Current market share index (1-100)" },
                  season: { type: Type.STRING, description: "Primary alignment season" }
                },
                required: ["style", "growth", "popularity", "season"]
              }
            },
            seasonalGemstones: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  season: { type: Type.STRING, description: "Season (e.g., Autumn, Spring Solstice)" },
                  stone: { type: Type.STRING, description: "Stone name" },
                  reason: { type: Type.STRING, description: "Consumer preference explanation" },
                  hotFactor: { type: Type.INTEGER, description: "Interest index (1 to 10)" }
                },
                required: ["season", "stone", "reason", "hotFactor"]
              }
            },
            styleComparisons: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  dimension: { type: Type.STRING, description: "Comparison category axis (e.g., Proportions, Design Approach, Era)" },
                  optionA: { type: Type.STRING, description: "Left attribute name" },
                  optionB: { type: Type.STRING, description: "Right attribute name" },
                  weightA: { type: Type.INTEGER, description: "Current preference ratio for Left (percentage)" },
                  weightB: { type: Type.INTEGER, description: "Current preference ratio for Right (percentage)" }
                },
                required: ["dimension", "optionA", "optionB", "weightA", "weightB"]
              }
            }
          },
          required: ["trendingStyles", "seasonalGemstones", "styleComparisons"]
        }
      }
    });

    const outputText = response.text;
    if (!outputText) throw new Error("No trend intel compiled.");
    res.json(JSON.parse(outputText));

  } catch (err: any) {
    // Fallback static high-fidelity response if Gemini API key isn't provided or fails, to keep app interactive
    console.warn("Trend intel API using offline backup data due to connection constraint:", err.message);
    res.json({
      trendingStyles: [
        { style: "Toi et Moi Duet Rings", growth: "+68% Quarter-over-Quarter", popularity: 89, season: "Summer Weddings" },
        { style: "Bespoke Scalloped Halos", growth: "+45% YoY", popularity: 78, season: "Spring Engagement" },
        { style: "Whisper Band Micro-settings", growth: "+34% YoY", popularity: 82, season: "Year Round" },
        { style: "Brushed Celestial Signets", growth: "+51% YoY", popularity: 70, season: "Autumn Releases" }
      ],
      seasonalGemstones: [
        { season: "Summer / Autumn Transition", stone: "Peachy-Pink Morganite", reason: "Warm pastel shades are replacing typical pure diamonds as couples seek tender, organic tones.", hotFactor: 9 },
        { season: "Winter Holiday season", stone: "Deep Teal Montana Sapphires", reason: "Colder months see a massive spike in green-blue sapphires matching well on platinum frames.", hotFactor: 8 },
        { season: "Spring Renewal", stone: "Chatham Lab Emeralds", reason: "Verdant hues are widely favored for anniversaries, conveying fidelity and regrowth.", hotFactor: 7 }
      ],
      styleComparisons: [
        { dimension: "Design Approach", optionA: "Luxury Maximalism", optionB: "Modern Minimalism", weightA: 55, weightB: 45 },
        { dimension: "Aesthetic Era", optionA: "Art Deco Vintage", optionB: "Ultra Sleek Contemporary", weightA: 62, weightB: 38 },
        { dimension: "Band Profiles", optionA: "Organic Sculpted", optionB: "Perfect Symmetric Edge", weightA: 40, weightB: 60 }
      ]
    });
  }
});

// Mock/Fake DB for Saved Designs - stored in-memory during container session
const localSavedPackages: any[] = [];

app.post("/api/save-design", (req, res) => {
  const design = req.body;
  if (!design.id) {
    design.id = "vel-" + Math.random().toString(36).substr(2, 9);
  }
  const existsIndex = localSavedPackages.findIndex(d => d.id === design.id);
  if (existsIndex >= 0) {
    localSavedPackages[existsIndex] = design;
  } else {
    localSavedPackages.push(design);
  }
  res.json({ success: true, id: design.id, totalCount: localSavedPackages.length });
});

app.get("/api/saved-designs", (req, res) => {
  res.json(localSavedPackages);
});

// Serve frontend assets
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Velaris Server running on http://localhost:${PORT}`);
  });
}

startServer();
