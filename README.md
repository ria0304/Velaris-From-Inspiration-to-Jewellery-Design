# Velaris — From Inspiration to Jewellery Design

> Type it. Sketch it. Upload it. Get a jewellery design you can actually build.

[![GitHub](https://img.shields.io/badge/GitHub-Velaris-black?style=flat-square&logo=github)](https://github.com/ria0304/Velaris-From-Inspiration-to-Jewellery-Design)

VELARIS AI is an AI-powered jewellery design tool that transforms natural language descriptions, sketches, or inspiration images into professional design concepts and manufacturer-ready briefs.

---

## The Problem

Custom jewellery design is slow, expensive, and built on miscommunication.

**Customers** struggle to describe what they want clearly, visualize the final piece, or understand costs before committing.

**Jewellers** spend hours interpreting vague briefs, creating multiple drafts, and handling revisions — before a single piece is made.

---

## The Solution

VELARIS AI bridges the gap between a customer's idea and a jeweller's workflow.

A user inputs their idea in one of three ways:

- **Text** — describe the piece in plain language
- **Sketch** — upload a rough hand-drawn drawing
- **Photo** — upload an inspiration image

The system outputs:

- A professional concept image
- A structured specification sheet (type, metal, stone, cut, style, setting, occasion)
- An exportable PDF the jeweller can use to quote and manufacture

---

## Core User Flow

```
User input (text / sketch / photo)
        ↓
AI generates concept image
        ↓
Structured specification sheet
        ↓
Exportable PDF → Jeweller
```

---

## Example

**Input:**
> "Vintage rose gold engagement ring with oval emerald and floral detailing"

**Output:**
- Concept render
- Spec sheet: Ring · Rose Gold · Emerald · Oval · Vintage · Engagement · Halo Setting
- PDF design brief ready for jeweller quotation

---

## Current Project Status

**Frontend:** Built. A React 19 + TypeScript + Vite app (`src/App.tsx`, `src/components/JewelryBlueprint.tsx`) covering the text/sketch/photo input flow, design results view, gifting advisor, trend intelligence panel, and a saved-designs collection.

**Backend:** Two implementations exist in this repo and are **not yet reconciled**:
- `server.ts` — an Express server (run via `npm run dev`) that calls Google Gemini directly via `@google/genai`. This is what currently serves the frontend and handles `/api/*` in dev.
- `main.py` + `backend/` — a FastAPI app that calls OpenRouter with a Claude → GPT-4o → Gemini fallback chain. This is the intended direction per `.env.example`, but **has not been wired up to the frontend or run end-to-end yet**.

Both implementations independently expose the same four endpoints (`/api/generate-design`, `/api/jewellery-advisor`, `/api/trends`, `/api/save-design` / `/api/saved-designs`) and both bind to port 3000.

**Not yet done:** no PDF export, no real image/concept generation, no persistent storage (saved designs live in an in-memory list and reset on restart), and no decision yet on which backend (`server.ts` vs. the Python/FastAPI one) the project will standardize on.

---

## Project Structure

```
Velaris-From-Inspiration-to-Jewellery-Design/
├── backend/                       # FastAPI implementation (not yet wired to frontend)
│   ├── __init__.py
│   ├── advisor.py                 # Gifting advisor endpoint logic
│   ├── config.py                  # Environment / settings loading
│   ├── design.py                  # Core design-generation logic
│   ├── json_schemas.py            # JSON schema defs for structured LLM outputs
│   ├── openrouter_client.py       # OpenRouter client (Claude → GPT-4o → Gemini fallback)
│   ├── schemas.py                 # Pydantic request/response models
│   ├── storage.py                 # In-memory saved-designs storage
│   └── trends.py                  # Trend intelligence endpoint logic
│
├── src/                            # React 19 + TypeScript + Vite frontend
│   ├── assets/
│   │   └── images/
│   │       └── luxury_agate_backdrop_1782161136573.jpg
│   ├── components/
│   │   └── JewelryBlueprint.tsx   # Blueprint/spec-sheet visualization component
│   ├── App.tsx                    # Main app: input flow, results view, advisor, trends, saved designs
│   ├── index.css
│   ├── main.tsx                   # Vite/React entry point
│   └── types.ts                   # Shared TypeScript types
│
├── index.html                      # Vite HTML entry point
├── main.py                         # FastAPI app entry point
├── server.ts                       # Express server — current active backend (calls Gemini directly)
├── package.json                    # Frontend deps + scripts (npm run dev, etc.)
├── requirements.txt                 # Python backend dependencies
├── tsconfig.json                    # TypeScript config
├── vite.config.ts                   # Vite build/dev config
├── .env.example                     # Required environment variables (both backends)
├── .gitignore
└── README.md
```

> **Note:** `server.ts` and `main.py` + `backend/` are two independent, unreconciled backend implementations — see [Current Project Status](#current-project-status) above. Only one will be kept going forward.

---

## Planned Features

**V1 — Core**
- Text-to-jewellery concept generation
- Structured specification sheet
- PDF export

**V2 — Advanced Design**
- Multi-view generation (front, side, perspective)
- Design variations (luxury, minimal, vintage, modern)
- Budget-aware design adjustment

**V3 — Business Intelligence**
- Manufacturing readiness score
- Cost estimation (metal, stone, labour)
- Jeweller quote request flow

---

## Target Users

- Engagement ring buyers
- Custom gift shoppers
- Independent jewellers
- Jewellery designers and manufacturers

---

*Velaris — from idea to manufacturable design in minutes.*
