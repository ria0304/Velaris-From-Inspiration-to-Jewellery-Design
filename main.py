# Velaris — From Inspiration to Jewelry Design
# Python backend entrypoint. Run with: python main.py
# or: uvicorn main:app --reload --port 3000

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import advisor, design, storage, trends

app = FastAPI(
    title="Velaris Jewelry Design Engine",
    description="FastAPI backend powered by an OpenRouter multi-model fallback chain",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(design.router)
app.include_router(advisor.router)
app.include_router(trends.router)
app.include_router(storage.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
