"""Pydantic models shared across the design, advisor, and trends endpoints.

Kept identical in shape to the original single-file version so that
src/types.ts on the frontend needs no changes.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Design generation
# ---------------------------------------------------------------------------

class DesignRequest(BaseModel):
    prompt: Optional[str] = ""
    inputType: str = "text"   # "text", "sketch", "photo"
    style: str = "Contemporary Minimalist"
    budget: str = "Balanced"
    image: Optional[str] = None  # base64 image data


class MultiView(BaseModel):
    front: str = Field(description="A beautiful, simple description of what a front-on view of the design shows")
    side: str = Field(description="A simple, clear description of the profile or side view details")
    perspective: str = Field(description="A warm, romantic description of the overall design from an artistic 3D angle")


class RawDesignResponse(BaseModel):
    """The shape we ask the model to return. Validated before we trust it."""
    name: str = Field(description="A beautiful, evocative name for this bespoke design")
    type: str = Field(description="Type: Ring, Earrings, Necklace, Bracelet, or Brooch")
    metal: str = Field(description="Metal choice: 18K Yellow Gold, 18K White Gold, 18K Rose Gold, Platinum, 14K Yellow Gold, Sterling Silver")
    stone: str = Field(description="Gemstone: Diamond, Emerald, Sapphire, Ruby, Garnet, Moissanite, Aquamarine, Opal, Amethyst, Pearl, Morganite")
    shape: str = Field(description="Gemstone Cut: Round, Oval, Emerald-Cut, Pear, Cushion, Princess, Marquise")
    setting: str = Field(description="Setting Type: Prong, Bezel, Halo, Pavé, Channel, Tension, Cathedral")
    occasion: str = Field(description="Occasion: Engagement, Wedding, Anniversary, Birthday, Graduation, Self-Gift")
    stoneSize: str = Field(description="Stone size/weight spec (e.g. '1.5 carats', '2.2ct')")
    bandWidth: str = Field(description="Band width or frame thickness (e.g. '2.1mm')")
    details: str = Field(description="An elegant, easy to understand summary of the design layout and gemstone settings")
    notes: str = Field(description="The romantic design narrative, physical presence, and master jeweler thoughts, simple and gorgeous")
    metalCost: int = Field(description="Estimated raw metal material cost in USD")
    stoneCost: int = Field(description="Estimated gemstone/diamond cost in USD")
    laborCost: int = Field(description="Estimated craftsman setting and carving labor cost in USD")
    castingComplexity: int = Field(description="Casting simplicity rating (0 to 100)")
    settingComplexity: int = Field(description="Gemstone settings simplicity rating (0 to 100)")
    polishingComplexity: int = Field(description="Finishing & polish rating (0 to 100)")
    multiView: MultiView


class DesignSpec(BaseModel):
    type: str
    metal: str
    stone: str
    shape: str
    setting: str
    occasion: str
    stoneSize: str
    bandWidth: str
    details: str


class CostStructure(BaseModel):
    metalCost: int
    stoneCost: int
    laborCost: int
    markupPercent: int
    totalCost: int


class ManufacturingSpecs(BaseModel):
    score: int
    level: str
    castingNotes: str
    settingNotes: str
    polishingNotes: str


class FinalDesignPackage(BaseModel):
    id: str
    name: str
    timestamp: str
    inputType: str
    prompt: str
    inputImage: Optional[str] = None
    spec: DesignSpec
    cost: CostStructure
    manufacturing: ManufacturingSpecs
    multiView: MultiView
    notes: str
    modelUsed: Optional[str] = None  # which fallback-chain model produced this


# ---------------------------------------------------------------------------
# Advisor
# ---------------------------------------------------------------------------

class AdvisorOption(BaseModel):
    gemstone: str
    suitability: str
    explanation: str
    approxCost: int


class AdvisorResponse(BaseModel):
    recommendations: List[AdvisorOption]
    suggestedMetal: str
    designIdea: str
    pricingStrategy: str


class AdvisorRequest(BaseModel):
    age: Optional[int] = None
    budget: int = 3000
    currency: str = "USD"
    occasion: str = "Engagement"
    stylePreferences: str = "Elegant classic"


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------

class GrowthStyle(BaseModel):
    style: str
    growth: str
    popularity: int
    season: str


class SeasonalGem(BaseModel):
    season: str
    stone: str
    reason: str
    hotFactor: int


class StyleComparison(BaseModel):
    dimension: str
    optionA: str
    optionB: str
    weightA: int
    weightB: int


class TrendsResponse(BaseModel):
    trendingStyles: List[GrowthStyle]
    seasonalGemstones: List[SeasonalGem]
    styleComparisons: List[StyleComparison]


# ---------------------------------------------------------------------------
# PDF Export
# ---------------------------------------------------------------------------

class PDFExportRequest(BaseModel):
    design_id: str = Field(description="The ID of the design to export as PDF")


class PDFExportResponse(BaseModel):
    success: bool
    pdf_base64: str
    message: str
    design_name: Optional[str] = None
    filename: Optional[str] = Field(
        default=None, 
        description="Suggested filename for the PDF (e.g., 'Aurum_Bloom.pdf')"
    )
