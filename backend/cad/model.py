"""Canonical jewellery geometry model — single source of truth (mm space).

All renderers (SVG views, DXF, dims table, PDF) derive from this model so
outputs stay consistent. Concept drawings only — not manufacturing-validated.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field

CUT_PROPORTIONS = {
    # scale factors applied to round-brilliant radius -> (rx_factor, ry_factor, depth_factor)
    "round": (1.0, 1.0, 0.62),
    "oval": (0.85, 1.20, 0.60),
    "pear": (0.85, 1.20, 0.60),
    "marquise": (0.70, 1.40, 0.55),
    "emerald": (1.0, 1.0, 0.65),
    "cushion": (1.0, 1.0, 0.62),
    "princess": (1.0, 1.0, 0.70),
}

SETTINGS = {"prong", "bezel", "halo", "pavé", "pave", "channel", "tension", "cathedral"}


def round_stone_radius_mm(carat: float) -> float:
    return 6.5 * (max(carat, 0.1) ** (1 / 3)) / 2


def normalize_cut(shape: str) -> str:
    s = (shape or "round").lower()
    for k in CUT_PROPORTIONS:
        if k in s:
            return k
    return "round"


@dataclass
class Prim:
    """2D geometric primitive in mm space, z=depth hint for side views."""
    kind: str  # circle | ellipse | rect | line | polyline | text
    layer: str = "BODY"
    data: dict = field(default_factory=dict)

    def bbox(self):
        d = self.data
        if self.kind == "circle":
            return (d["cx"] - d["r"], d["cy"] - d["r"], d["cx"] + d["r"], d["cy"] + d["r"])
        if self.kind == "ellipse":
            return (d["cx"] - d["rx"], d["cy"] - d["ry"], d["cx"] + d["rx"], d["cy"] + d["ry"])
        if self.kind == "rect":
            return (d["x"], d["y"], d["x"] + d["w"], d["y"] + d["h"])
        if self.kind == "line":
            return (min(d["x1"], d["x2"]), min(d["y1"], d["y2"]),
                    max(d["x1"], d["x2"]), max(d["y1"], d["y2"]))
        if self.kind == "polyline":
            xs = [p[0] for p in d["points"]]; ys = [p[1] for p in d["points"]]
            return (min(xs), min(ys), max(xs), max(ys))
        return (0, 0, 0, 0)


@dataclass
class JewelryModel:
    jewelry_type: str = "Ring"
    carat: float = 1.0
    cut: str = "round"
    band_w: float = 1.8
    band_thickness: float = 1.5
    ring_size_mm: float = 17.3  # inner diameter (~size 52)
    setting: str = "Prong"
    stone_l_mm: float | None = None
    stone_w_mm: float | None = None
    stone_depth_mm: float | None = None
    motif: dict | None = None

    def __post_init__(self):
        self.jewelry_type = (self.jewelry_type or "Ring").capitalize()
        self.cut = normalize_cut(self.cut)
        self.validate()

    def validate(self):
        if not math.isfinite(self.carat) or self.carat <= 0 or self.carat > 50:
            raise ValueError(f"invalid carat: {self.carat}")
        for name in ("band_w", "band_thickness", "ring_size_mm"):
            v = getattr(self, name)
            if not math.isfinite(v) or v <= 0 or v > 500:
                raise ValueError(f"invalid {name}: {v}")
        for name in ("stone_l_mm", "stone_w_mm", "stone_depth_mm"):
            v = getattr(self, name)
            if v is not None and (not math.isfinite(v) or v <= 0 or v > 200):
                raise ValueError(f"invalid {name}: {v}")
        if self.band_w < 0.8:
            raise ValueError("band too thin for manufacture (<0.8mm)")
        # stone vs setting clearance: halo/bezel need margin
        r = self.stone_r_mm
        if "bezel" in self.setting.lower() and self.band_w < 1.0:
            raise ValueError("bezel setting needs band_w >= 1.0mm")

    @property
    def stone_r_mm(self) -> float:
        return round_stone_radius_mm(self.carat)

    @property
    def stone_rx_mm(self) -> float:
        if self.stone_w_mm:
            return self.stone_w_mm / 2
        return self.stone_r_mm * CUT_PROPORTIONS[self.cut][0]

    @property
    def stone_ry_mm(self) -> float:
        if self.stone_l_mm:
            return self.stone_l_mm / 2
        return self.stone_r_mm * CUT_PROPORTIONS[self.cut][1]

    @property
    def setting_h_mm(self) -> float:
        depth = self.stone_depth_mm or (self.stone_r_mm * 2 * CUT_PROPORTIONS[self.cut][2])
        return round(depth + 1.2, 2)  # seat + gallery allowance

    def primitives(self, view: str = "front") -> list[Prim]:
        """Canonical per-type primitives in mm space (origin at piece centre)."""
        t = self.jewelry_type.lower()
        rx, ry = self.stone_rx_mm, self.stone_ry_mm
        R = self.ring_size_mm / 2
        prims: list[Prim] = []
        if t == "ring":
            prims += [Prim("circle", "BODY", {"cx": 0, "cy": 0, "r": R + self.band_w / 2}),
                      Prim("circle", "CONSTRUCTION", {"cx": 0, "cy": 0, "r": R}),
                      Prim("ellipse", "STONE", {"cx": 0, "cy": -(R + self.band_w / 2), "rx": rx, "ry": ry})]
            prims += self._setting_prims(0, -(R + self.band_w / 2), rx, ry)
            if view == "side":
                prims.append(Prim("rect", "BODY", {"x": -self.band_w / 2, "y": -R,
                                                  "w": self.band_w, "h": 2 * R}))
        elif t in ("necklace", "pendant"):
            prims += [Prim("polyline", "BODY", {"points": [(-40, -20), (0, -28), (40, -20)]}),
                      Prim("rect", "BODY", {"x": -2, "y": -20, "w": 4, "h": 6}),
                      Prim("ellipse", "STONE", {"cx": 0, "cy": 0, "rx": rx, "ry": ry})]
            prims += self._setting_prims(0, 0, rx, ry)
        elif t == "earrings":
            for cx in (-8, 8):
                prims += [Prim("line", "BODY", {"x1": cx, "y1": -18, "x2": cx, "y2": -8}),
                          Prim("ellipse", "STONE", {"cx": cx, "cy": 0, "rx": rx, "ry": ry})]
                prims += self._setting_prims(cx, 0, rx, ry)
                if view == "back":
                    prims.append(Prim("ellipse", "CONSTRUCTION",
                                      {"cx": cx, "cy": -10, "rx": 2.0, "ry": 2.0}))
        elif t == "bracelet":
            prims += [Prim("ellipse", "BODY", {"cx": 0, "cy": 0, "rx": 31, "ry": 25}),
                      Prim("ellipse", "CONSTRUCTION", {"cx": 0, "cy": 0,
                                                      "rx": 31 - self.band_w, "ry": 25 - self.band_w}),
                      Prim("ellipse", "STONE", {"cx": 0, "cy": -25, "rx": rx, "ry": ry})]
        elif t == "brooch":
            prims += [Prim("polyline", "BODY", {"points": [(-21, -24), (21, -24), (0, 24)]})]
            if ((self.motif or {}).get("description") or "").lower().find("phoenix") >= 0:
                prims.append(Prim("polyline", "BODY",
                                  {"points": [(-30, 0), (-10, -10), (0, 5), (10, -10), (30, 0)]}))
            prims += [Prim("ellipse", "STONE", {"cx": 0, "cy": 0, "rx": rx, "ry": ry})]
            if view == "back":
                # real pin assembly: hinge + stem + catch at distinct positions
                prims += [Prim("rect", "CONSTRUCTION", {"x": -24, "y": 6, "w": 5, "h": 4}),
                          Prim("line", "CONSTRUCTION", {"x1": -19, "y1": 8, "x2": 18, "y2": 8}),
                          Prim("rect", "CONSTRUCTION", {"x": 18, "y": 6, "w": 5, "h": 4})]
            else:
                prims.append(Prim("line", "CONSTRUCTION", {"x1": -22, "y1": 8, "x2": 22, "y2": 8}))
            prims += self._setting_prims(0, 0, rx, ry)
        elif t == "tiara":
            prims += [Prim("polyline", "BODY", {"points": [(-55, 20), (0, -5), (55, 20)]})]
            for mx in (-30, -15, 0, 15, 30):
                my = -5 - (1 - abs(mx) / 55) * 8
                prims.append(Prim("ellipse", "SETTING", {"cx": mx, "cy": my, "rx": 1.5, "ry": 1.5}))
            prims += [Prim("ellipse", "STONE", {"cx": 0, "cy": -8, "rx": rx, "ry": ry})]
            prims += self._setting_prims(0, -8, rx, ry)
        else:
            prims += [Prim("ellipse", "BODY", {"cx": 0, "cy": 0, "rx": 20, "ry": 14}),
                      Prim("ellipse", "STONE", {"cx": 0, "cy": 0, "rx": rx, "ry": ry})]
        return prims

    def _setting_prims(self, cx, cy, rx, ry) -> list[Prim]:
        s = self.setting.lower()
        out = []
        if "bezel" in s:
            out.append(Prim("ellipse", "SETTING", {"cx": cx, "cy": cy, "rx": rx + 0.6, "ry": ry + 0.6}))
        elif "halo" in s:
            out.append(Prim("ellipse", "SETTING", {"cx": cx, "cy": cy, "rx": rx + 1.5, "ry": ry + 1.5}))
        else:  # prong default: 4-6 prongs
            n = 6 if self.carat >= 1.5 else 4
            for i in range(n):
                a = 2 * math.pi * i / n
                out.append(Prim("line", "SETTING",
                                {"x1": cx + (rx + 0.3) * math.cos(a), "y1": cy + (ry + 0.3) * math.sin(a),
                                 "x2": cx + (rx + 0.9) * math.cos(a), "y2": cy + (ry + 0.9) * math.sin(a)}))
        if "cathedral" in s:
            out.append(Prim("line", "SETTING", {"x1": cx - 3, "y1": cy + ry, "x2": cx - 3, "y2": cy + ry + 4}))
            out.append(Prim("line", "SETTING", {"x1": cx + 3, "y1": cy + ry, "x2": cx + 3, "y2": cy + ry + 4}))
        return out

    def bbox_mm(self, view: str = "front") -> dict:
        prims = [p for p in self.primitives(view) if p.layer != "CONSTRUCTION"]
        xs0 = [p.bbox()[0] for p in prims]; ys0 = [p.bbox()[1] for p in prims]
        xs1 = [p.bbox()[2] for p in prims]; ys1 = [p.bbox()[3] for p in prims]
        w, h = round(max(xs1) - min(xs0), 2), round(max(ys1) - min(ys0), 2)
        return {"width_mm": w, "height_mm": h, "depth_mm": self.setting_h_mm,
                "stone_w_mm": round(self.stone_rx_mm * 2, 2),
                "stone_h_mm": round(self.stone_ry_mm * 2, 2)}
