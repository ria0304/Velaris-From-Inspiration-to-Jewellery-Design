"""Coverage for the CAD / realistic / beauty / board / PDF pipeline (no API keys)."""
import base64
import io
import os
import re

os.environ["VELARIS_DB_PATH"] = "/tmp/velaris_test2.db"

from fastapi.testclient import TestClient

import main
from backend import storage

storage.init_db()

PHOENIX = {"type": "animal",
           "description": "phoenix with spread wings and ruby eye, standing on hind legs"}
TYPES = ["Ring", "Necklace", "Earrings", "Bracelet", "Brooch", "Tiara", "Pendant"]
VIEWS = ["front", "perspective", "side", "back"]


def _client():
    return TestClient(main.app)


# ── CAD engine ──────────────────────────────────────────────────────────────
def test_cad_all_types_all_views():
    from backend.cad import render_cad_svg
    for jt in TYPES:
        for v in VIEWS:
            svg, p = render_cad_svg(jt, "18K Yellow Gold", "Ruby", "Oval",
                                    "1.5 carat", "Halo", "2.0 mm", v, "t1")
            assert 'viewBox="0 0 200 200"' in svg, (jt, v)
            assert "<script" not in svg
            n = len(re.findall(r"<(path|rect|circle|ellipse|polygon|polyline|line)\b", svg))
            assert n >= 6, (jt, v, n)
    assert p.dims()["width_mm"] > 0


def test_cad_dims_scale_with_carat():
    from backend.cad import render_cad_svg
    _, small = render_cad_svg("Ring", "Platinum", "Diamond", "Round",
                              "0.5 carat", "Prong", "1.8 mm", "front", "d")
    _, big = render_cad_svg("Ring", "Platinum", "Diamond", "Round",
                            "3.0 carat", "Prong", "1.8 mm", "front", "d")
    assert big.dims()["stone_r_mm"] > small.dims()["stone_r_mm"]
    assert big.dims()["est_total_wt_g"] >= small.dims()["est_total_wt_g"]


def test_cad_phoenix_branch():
    from backend.cad import render_cad_svg
    svg, _ = render_cad_svg("Brooch", "18K Yellow Gold", "Ruby", "Oval",
                            "1.5 carat", "Prong", "N/A", "front", "px", PHOENIX)
    assert "phoenix" in svg  # dimension label marks the motif branch


def test_cad_dxf():
    from backend.cad import render_cad_svg, to_dxf_entities
    _, p = render_cad_svg("Ring", "Platinum", "Diamond", "Round",
                          "2.0 carat", "Prong", "1.8 mm", "front", "d")
    dxf = to_dxf_entities(p)
    assert "ENTITIES" in dxf and "STONE" in dxf and "EOF" in dxf


# ── SVG sanitize ────────────────────────────────────────────────────────────
def test_svg_sanitize_strips_xss():
    from backend.svg_generator import sanitize_svg
    dirty = '<svg><script>alert(1)</script><circle cx="1" onclick="x()"/>' + "<circle/>" * 7 + "</svg>"
    clean = sanitize_svg(dirty)
    assert clean is not None and "<script" not in clean and "onclick" not in clean
    assert 'viewBox="0 0 200 200"' in clean
    assert sanitize_svg('<svg><circle cx="1"/></svg>') is None  # too few elements


# ── Realistic renderer ──────────────────────────────────────────────────────
def test_realistic_all_types():
    from backend.render import render_realistic
    for jt in TYPES:
        img = render_realistic(jt, "Platinum", "Sapphire", "Round", 2.0, "front",
                               PHOENIX if jt == "Brooch" else None)
        assert img.size == (768, 768)
        assert img.mode == "RGB"


# ── Beauty layer ────────────────────────────────────────────────────────────
def test_beauty_prompt_mentions_spec():
    from backend.beauty import build_prompt
    p = build_prompt("Brooch", "18K Yellow Gold", "Ruby", "Oval", 1.5,
                     "Prong", "front", PHOENIX)
    for token in ("Ruby", "Oval", "1.5", "phoenix", "front"):
        assert token.lower() in p.lower()


def test_beauty_fallback_without_key():
    os.environ.pop("HUGGINGFACE_API_KEY", None)
    from backend.beauty import beauty_png
    raw, source = beauty_png("Ring", "18K Yellow Gold", "Diamond", "Round",
                             1.0, "Prong", "front", None)
    assert source == "procedural" and raw[:4] == b"\x89PNG"


def test_beauty_endpoints():
    c = _client()
    r = c.post("/api/render-beauty", json={"jewelry_type": "Ring", "view": "front"})
    assert r.status_code == 200 and r.headers["X-Render-Source"] == "procedural"
    r = c.post("/api/beauty-prompt", json={"jewelry_type": "Ring"})
    assert r.status_code == 200 and "prompt" in r.json()


# ── Presentation board ──────────────────────────────────────────────────────
def test_board_all_types():
    c = _client()
    for jt in TYPES:
        r = c.post("/api/presentation-board", json={
            "design_id": "t1", "design_name": jt, "jewelry_type": jt,
            "metal": "Platinum", "stone": "Sapphire", "stone_shape": "Round",
            "stone_size": "2.0 carat",
            "motif": PHOENIX if jt == "Brooch" else None})
        assert r.status_code == 200, (jt, r.text[:200])
        b = r.json()
        assert len(b["strip"]) == 4 and b["specs"]["width_mm"] > 0
        assert b["front"]["svg"].startswith("<svg")
        assert len(base64.b64decode(b["front"]["png_b64"])) > 5000


# ── ML modules 1, 2, 4 (live checkpoints) ────────────────────────────────────
def test_ml_health_flags():
    c = _client()
    h = c.get("/api/health").json()
    assert h["type_classifier"] is True
    assert h["style_classifier"] is True
    assert h["similarity_search"] is True
    # Module 3 hybrid: YOLO weights if trained, else OWL-ViT zero-shot —
    # live either way on this machine.
    assert h["gemstone_detector"] is True


def _sample_b64():
    import base64
    from backend.render import render_realistic
    img = render_realistic("Necklace", "18K Yellow Gold", "Ruby", "Oval", 1.5, "front", None)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def test_classify_type_live():
    c = _client()
    r = c.post("/api/classify-type", json={"image": _sample_b64()})
    assert r.status_code == 200 and r.json()["available"] is True


def test_classify_style_live():
    c = _client()
    r = c.post("/api/classify-style", json={"image": _sample_b64()})
    assert r.status_code == 200
    assert r.json()["style"] in ("Modern", "Traditional")


def test_find_similar_live():
    c = _client()
    r = c.post("/api/find-similar", json={"image": _sample_b64(), "top_k": 3})
    assert r.status_code == 200
    assert len(r.json()["matches"]) == 3


def test_detect_gemstones_live():
    """Module 3 hybrid backend: detects Diamond in a real ring photo fixture."""
    import glob
    c = _client()
    photo = sorted(glob.glob("ml_training/data/test/ring/*.jpg"))[0]
    with open(photo, "rb") as f:
        img = base64.b64encode(f.read()).decode()
    r = c.post("/api/detect-gemstones", json={"image": img})
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert len(body["detections"]) >= 1
    det = body["detections"][0]
    assert det["label"] in ("Diamond", "Emerald", "Ruby", "Sapphire")
    assert len(det["box"]) == 4 and det["backend"] in ("yolo", "owlvit")


def test_gemstone_hint_flows_to_design():
    from backend.design import resolve_gemstone_hint
    from backend.schemas import DesignRequest
    import glob
    photo = sorted(glob.glob("ml_training/data/test/ring/*.jpg"))[0]
    with open(photo, "rb") as f:
        img = base64.b64encode(f.read()).decode()
    hint = resolve_gemstone_hint(DesignRequest(prompt="ring", inputType="photo", image=img))
    assert hint is not None and "Diamond" in hint
def _phoenix_design():
    spec = {"type": "Brooch", "metal": "18K Yellow Gold", "stone": "Ruby",
            "shape": "Oval", "setting": "Prong", "occasion": "Anniversary",
            "stoneSize": "1.5 carat", "bandWidth": "N/A", "details": "Phoenix"}
    return {"id": "vel-phoenix1", "name": "Phoenix Brooch",
            "timestamp": "September 20, 2026", "motif": PHOENIX, "spec": spec,
            "cost": {"metalCost": 600, "stoneCost": 2500, "laborCost": 500,
                     "totalCost": 4500, "markupPercent": 25},
            "manufacturing": {"score": 68, "level": "Moderate Complexity",
                              "castingNotes": "c", "settingNotes": "s",
                              "polishingNotes": "p"},
            "multiView": {"front": "f", "side": "s", "perspective": "p", "back": "b"},
            "notes": "n", "modelUsed": "test"}


def test_pdf_full_sections_and_dxf():
    from backend.pdf_generator import generate_design_pdf
    from pypdf import PdfReader
    b64, fn = generate_design_pdf(_phoenix_design())
    raw = base64.b64decode(b64)
    assert len(raw) > 150000  # images embedded, not placeholders
    r = PdfReader(io.BytesIO(raw))
    text = "".join((p.extract_text() or "") for p in r.pages)
    for s in ("Front View", "Artistic View", "Profile View", "Back View",
              "REALISTIC PREVIEWS", "TECHNICAL SPECIFICATIONS",
              "Overall Height", "CAD DATA"):
        assert s in text, s
    assert any(n.endswith(".dxf") for n in (r.attachments or {}))
    assert fn == "Phoenix_Brooch.pdf"
