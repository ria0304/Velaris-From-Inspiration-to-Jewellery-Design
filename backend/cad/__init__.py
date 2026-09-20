"""Velaris parametric CAD engine — deterministic, manufacturable SVG.

Single source of truth: one shared parameter set derived from the design
spec (stone size, shape, band width, setting) drives all three views, so
front/side/perspective stay geometrically consistent (unlike 3 independent
LLM calls). Also exposes DXF export for jeweller handoff.
"""
from __future__ import annotations
import math
import re

VIEWBOX = "0 0 200 200"
CX, CY = 100, 100

GEM_PALETTE = {
    "diamond": ("#E8F4F8", "#B0D8E8", "#FFFFFF", "#4A7890"),
    "moissanite": ("#E0ECFA", "#90C0E0", "#F8FCFF", "#3A6888"),
    "emerald": ("#10B981", "#059669", "#6EE7B7", "#064E3B"),
    "ruby": ("#EF4444", "#B91C1C", "#FCA5A5", "#450A0A"),
    "sapphire": ("#3B82F6", "#1D4ED8", "#93C5FD", "#172554"),
    "garnet": ("#DC2626", "#991B1B", "#FCA5A5", "#450A0A"),
    "aquamarine": ("#22D3EE", "#0891B2", "#A5F3FC", "#083344"),
    "opal": ("#C084FC", "#9333EA", "#F5D0FE", "#3B0764"),
    "amethyst": ("#8B5CF6", "#6D28D9", "#DDD6FE", "#2E1065"),
    "pearl": ("#FEF3C7", "#D97706", "#FFFBEB", "#451A03"),
    "morganite": ("#FB923C", "#EA580C", "#FFEDD5", "#431407"),
}
METAL_STROKE = {
    "platinum": "#C8D8D0", "white gold": "#B8CEC8",
    "yellow gold": "#DFBE8B", "14k yellow": "#C8A870",
    "rose gold": "#C4847A", "sterling silver": "#A8C0B8",
}


def gem_colors(stone: str):
    s = (stone or "").lower()
    for k, v in GEM_PALETTE.items():
        if k in s:
            return {"primary": v[0], "facet": v[1], "glow": v[2], "deep": v[3]}
    v = GEM_PALETTE["diamond"]
    return {"primary": v[0], "facet": v[1], "glow": v[2], "deep": v[3]}


def metal_stroke(metal: str) -> str:
    m = (metal or "").lower()
    for k, v in METAL_STROKE.items():
        if k in m:
            return v
    return METAL_STROKE["yellow gold"]


def parse_carat(stone_size: str) -> float:
    m = re.search(r"([\d.]+)", stone_size or "")
    try:
        return float(m.group(1)) if m else 1.0
    except ValueError:
        return 1.0


def parse_mm(band_width: str | None, default: float = 1.8) -> float:
    m = re.search(r"([\d.]+)", band_width or "")
    try:
        return float(m.group(1)) if m else default
    except ValueError:
        return default


def stone_radius_mm(carat: float) -> float:
    # round-brilliant approx diameter: d ≈ 6.5 * cbrt(carat) mm → radius
    return 6.5 * (max(carat, 0.1) ** (1 / 3)) / 2


class CadParams:
    """Shared millimetre-space parameters — one instance drives all 3 views."""
    def __init__(self, jewelry_type: str, metal: str, stone: str,
                 stone_shape: str, stone_size: str,
                 band_width: str | None = None, setting: str = "Prong"):
        self.jewelry_type = (jewelry_type or "Ring").lower()
        self.metal = metal or "18K Yellow Gold"
        self.stone = stone or "Diamond"
        self.stone_shape = (stone_shape or "Round").lower()
        self.setting = setting or "Prong"
        self.carat = parse_carat(stone_size)
        self.stone_r = stone_radius_mm(self.carat)          # mm
        self.band_w = parse_mm(band_width)                  # mm
        self.band_r = 9.0  # ring/bangle inner radius mm (size ~52)
        # px-per-mm scale into 200px canvas with padding
        self.scale = 4.2
        self.gem = gem_colors(self.stone)
        self.stroke = metal_stroke(self.metal)

    def px(self, mm_val: float) -> float:
        return mm_val * self.scale

    def dims(self) -> dict:
        """Full product dimensions in mm + estimates, shared by PDF + DXF."""
        rx, ry = self.gem_dims_px()
        stone_w = round(rx * 2 / self.scale, 2)
        stone_h = round(ry * 2 / self.scale, 2)
        spans = {"ring": (18.0, 20.0, 6.0), "earrings": (12.0, 18.0, 5.0),
                 "necklace": (420.0, 60.0, 4.0), "pendant": (20.0, 30.0, 4.0),
                 "bracelet": (62.0, 50.0, 6.0), "brooch": (42.0, 48.0, 8.0),
                 "tiara": (150.0, 55.0, 10.0)}
        w, h, d = spans.get(self.jewelry_type, (40.0, 40.0, 6.0))
        # scale span slightly with carat
        f = 1 + (max(self.carat - 1.0, 0) * 0.06)
        metal_wt = round({"platinum": 21.4, "sterling silver": 10.4}.get(
            self.metal.lower(), 15.5 if "gold" in self.metal.lower() else 14.0)
            * 0.35 * f, 1)
        return {"width_mm": round(w * f, 1), "height_mm": round(h * f, 1),
                "depth_mm": d, "stone_w_mm": stone_w, "stone_h_mm": stone_h,
                "stone_r_mm": round(self.stone_r, 3), "carat": self.carat,
                "band_w_mm": self.band_w, "band_r_mm": self.band_r,
                "est_metal_wt_g": metal_wt,
                "est_total_wt_g": round(metal_wt + self.carat * 0.2, 1)}

    def gem_dims_px(self) -> tuple[float, float]:
        r = self.px(self.stone_r)
        if "oval" in self.stone_shape or "pear" in self.stone_shape:
            return r * 0.85, r * 1.2
        if "marquise" in self.stone_shape:
            return r * 0.7, r * 1.4
        if "emerald" in self.stone_shape or "cushion" in self.stone_shape or "princess" in self.stone_shape:
            return r * 1.0, r * 1.0
        return r, r  # round


def gem_shape_elements(g: CadParams, cx: float, cy: float,
                       uid: str, setting: str = "") -> str:
    """Gem outline + facet lines honouring stone_shape; uid-scoped gradients."""
    rx, ry = g.gem_dims_px()
    c = g.gem
    s = g.stroke
    if "emerald" in g.stone_shape or "cushion" in g.stone_shape or "princess" in g.stone_shape:
        outline = f'<rect x="{cx-rx:.1f}" y="{cy-ry:.1f}" width="{2*rx:.1f}" height="{2*ry:.1f}" rx="3" fill="url(#{uid}-gem)" stroke="{c["deep"]}" stroke-width="1.2"/>'
        inner = f'<rect x="{cx-rx*0.6:.1f}" y="{cy-ry*0.6:.1f}" width="{1.2*rx:.1f}" height="{1.2*ry:.1f}" fill="none" stroke="{c["facet"]}" stroke-width="0.8"/>'
    elif "marquise" in g.stone_shape or "pear" in g.stone_shape:
        outline = f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="url(#{uid}-gem)" stroke="{c["deep"]}" stroke-width="1.2"/>'
        inner = f'<path d="M {cx-rx*0.6:.1f} {cy:.1f} L {cx:.1f} {cy-ry*0.6:.1f} L {cx+rx*0.6:.1f} {cy:.1f} L {cx:.1f} {cy+ry*0.6:.1f} Z" fill="none" stroke="{c["facet"]}" stroke-width="0.8"/>'
    else:  # round / oval
        outline = f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="url(#{uid}-gem)" stroke="{c["deep"]}" stroke-width="1.2"/>'
        inner = (f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx*0.55:.1f}" ry="{ry*0.55:.1f}" fill="none" stroke="{c["facet"]}" stroke-width="0.8"/>'
                 f'<line x1="{cx-rx:.1f}" y1="{cy:.1f}" x2="{cx+rx:.1f}" y2="{cy:.1f}" stroke="{c["facet"]}" stroke-width="0.6" opacity="0.8"/>'
                 f'<line x1="{cx:.1f}" y1="{cy-ry:.1f}" x2="{cx:.1f}" y2="{cy+ry:.1f}" stroke="{c["facet"]}" stroke-width="0.6" opacity="0.8"/>')
    halo = ""
    if "halo" in (setting or g.setting).lower():
        halo = f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx+5:.1f}" ry="{ry+5:.1f}" fill="none" stroke="{s}" stroke-width="0.8" stroke-dasharray="2,1.5" opacity="0.9"/>'
    bezel = ""
    if "bezel" in (setting or g.setting).lower():
        bezel = f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx+2.5:.1f}" ry="{ry+2.5:.1f}" fill="none" stroke="{s}" stroke-width="2"/>'
    return outline + inner + halo + bezel


def _defs(g: CadParams, uid: str) -> str:
    c = g.gem
    return (f'<defs><radialGradient id="{uid}-gem"><stop offset="0%" stop-color="{c["glow"]}" stop-opacity="0.9"/>'
            f'<stop offset="60%" stop-color="{c["primary"]}" stop-opacity="0.7"/>'
            f'<stop offset="100%" stop-color="{c["deep"]}" stop-opacity="0.3"/></radialGradient>'
            f'<linearGradient id="{uid}-metal" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'<stop offset="0%" stop-color="{g.stroke}" stop-opacity="0.35"/>'
            f'<stop offset="50%" stop-color="{g.stroke}" stop-opacity="0.85"/>'
            f'<stop offset="100%" stop-color="{g.stroke}" stop-opacity="0.3"/></linearGradient>'
            f'<filter id="{uid}-soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.2"/></filter></defs>'
            f'<rect width="200" height="200" fill="#050C08"/>'
            + "".join(f'<line x1="{v}" y1="0" x2="{v}" y2="200" stroke="#0D2018" stroke-width="0.5" opacity="0.4"/>'
                      f'<line x1="0" y1="{v}" x2="200" y2="{v}" stroke="#0D2018" stroke-width="0.5" opacity="0.4"/>'
                      for v in (25, 50, 75, 100, 125, 150, 175)))


def _dim(text: str) -> str:
    return (f'<line x1="45" y1="183" x2="155" y2="183" stroke="#10B981" stroke-width="0.6" stroke-dasharray="3,2"/>'
            f'<line x1="45" y1="180" x2="45" y2="186" stroke="#10B981" stroke-width="0.8"/>'
            f'<line x1="155" y1="180" x2="155" y2="186" stroke="#10B981" stroke-width="0.8"/>'
            f'<text x="100" y="180" text-anchor="middle" fill="#10B981" font-size="8" font-family="monospace">{text}</text>')


def _ring(g: CadParams, view: str, uid: str) -> str:
    bw = max(g.px(g.band_w) / 2, 2.0)
    R = g.px(g.band_r)
    s = g.stroke
    rx, ry = g.gem_dims_px()
    if view == "side":
        w = bw * 2
        return (f'<rect x="{CX-8:.1f}" y="{CY-R:.1f}" width="16" height="{2*R:.1f}" rx="4" fill="none" stroke="url(#{uid}-metal)" stroke-width="{w:.1f}"/>'
                f'<ellipse cx="{CX:.1f}" cy="{CY-R:.1f}" rx="{rx:.1f}" ry="{ry*0.6:.1f}" fill="url(#{uid}-gem)" stroke="{g.gem["deep"]}" stroke-width="1"/>'
                + _dim(f'{g.band_w:.1f}mm band · {g.carat}ct'))
    if view == "front":
        els = (f'<circle cx="{CX}" cy="{CY}" r="{R:.1f}" fill="none" stroke="url(#{uid}-metal)" stroke-width="{bw*2:.1f}"/>'
               f'<circle cx="{CX}" cy="{CY}" r="{R-bw:.1f}" fill="none" stroke="{s}" stroke-width="0.6" opacity="0.6"/>'
               + gem_shape_elements(g, CX, CY - R, uid))
        n = max(int(g.carat * 4), 4)
        for i in range(n):
            a = math.pi * (0.25 + 0.5 * i / max(n - 1, 1))
            x = CX + (R * math.cos(a)); y = CY - (R * math.sin(a)) * 0.9
            els += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.4" fill="{g.gem["primary"]}" opacity="0.85"/>'
        return els + _dim(f'Ø{(g.band_r*2):.0f}mm · {g.carat}ct {g.stone_shape}')
    # perspective: ellipse band + raised head
    els = (f'<ellipse cx="{CX}" cy="{CY+10:.1f}" rx="{R:.1f}" ry="{R*0.72:.1f}" fill="none" stroke="url(#{uid}-metal)" stroke-width="{bw*2:.1f}" filter="url(#{uid}-soft)"/>'
           f'<line x1="{CX-4:.1f}" y1="{CY+10-R*0.72:.1f}" x2="{CX-4:.1f}" y2="{CY-R-ry:.1f}" stroke="{s}" stroke-width="1.4"/>'
           f'<line x1="{CX+4:.1f}" y1="{CY+10-R*0.72:.1f}" x2="{CX+4:.1f}" y2="{CY-R-ry:.1f}" stroke="{s}" stroke-width="1.4"/>'
           + gem_shape_elements(g, CX, CY - R, uid))
    return els + _dim(f'{g.carat}ct · {g.setting}')


def _generic_body(g: CadParams, view: str, uid: str, span: float, label: str) -> str:
    s = g.stroke
    rx, ry = g.gem_dims_px()
    gem = gem_shape_elements(g, CX, CY, uid)
    if view == "side":
        return (f'<line x1="{CX-span:.1f}" y1="{CY:.1f}" x2="{CX+span:.1f}" y2="{CY:.1f}" stroke="url(#{uid}-metal)" stroke-width="4"/>'
                f'<ellipse cx="{CX:.1f}" cy="{CY:.1f}" rx="{rx*0.5:.1f}" ry="{ry:.1f}" fill="url(#{uid}-gem)" stroke="{g.gem["deep"]}" stroke-width="1"/>' + _dim(label))
    if view == "front":
        return (f'<ellipse cx="{CX}" cy="{CY}" rx="{span:.1f}" ry="{span*0.7:.1f}" fill="none" stroke="url(#{uid}-metal)" stroke-width="3"/>' + gem + _dim(label))
    return (f'<ellipse cx="{CX}" cy="{CY}" rx="{span:.1f}" ry="{span*0.55:.1f}" fill="none" stroke="url(#{uid}-metal)" stroke-width="3" filter="url(#{uid}-soft)"/>' + gem + _dim(label))


def _wing(side: int, s: str, uid: str, folded: bool = False) -> str:
    """Layered feather wing. side=-1 left, +1 right. Folded for side/back views."""
    if folded:
        x0 = CX + side * 8
        return (
            f'<path d="M {x0} 96 C {x0 + side*22} 84 {x0 + side*30} 88 {x0 + side*26} 100 C {x0 + side*18} 108 {x0 + side*8} 106 {x0} 102 Z" fill="none" stroke="{s}" stroke-width="2"/>'
            f'<path d="M {x0} 98 C {x0 + side*14} 92 {x0 + side*20} 94 {x0 + side*17} 101" fill="none" stroke="{s}" stroke-width="0.9" opacity="0.8"/>'
            f'<path d="M {x0} 100 C {x0 + side*10} 96 {x0 + side*14} 98 {x0 + side*12} 103" fill="none" stroke="{s}" stroke-width="0.8" opacity="0.7"/>'
        )
    x0 = CX + side * 4
    tip = CX + side * 78
    return (
        # wing outline: leading edge up-out, scalloped feather trailing edge
        f'<path d="M {x0} 98 C {CX + side*30} 76 {CX + side*58} 66 {tip} 76'
        f' L {CX + side*68} 82 L {CX + side*72} 90 L {CX + side*62} 93 L {CX + side*64} 101'
        f' L {CX + side*52} 101 L {CX + side*50} 108 C {CX + side*32} 112 {x0 + side*6} 108 {x0} 102 Z"'
        f' fill="none" stroke="{s}" stroke-width="2"/>'
        # primary feather separations
        f'<path d="M {CX + side*40} 84 L {CX + side*46} 102 M {CX + side*52} 79 L {CX + side*58} 100 M {CX + side*62} 77 L {CX + side*64} 96"'
        f' fill="none" stroke="{s}" stroke-width="0.9" opacity="0.85"/>'
        # covert rows
        f'<path d="M {x0 + side*8} 94 C {CX + side*28} 86 {CX + side*44} 84 {CX + side*56} 88" fill="none" stroke="{s}" stroke-width="0.8" opacity="0.7"/>'
        f'<path d="M {x0 + side*8} 98 C {CX + side*26} 92 {CX + side*40} 91 {CX + side*50} 94" fill="none" stroke="{s}" stroke-width="0.7" opacity="0.6"/>'
    )


def _phoenix(g: CadParams, uid: str, eye_color: str = "#EF4444", view: str = "front") -> str:
    """V2 rampant phoenix: feather-layered wings, torso behind gem, hooked beak,
    exactly 2 taloned hind legs, tail plumes routed behind the gem.
    Side/back views fold the far wing and turn the head to profile."""
    s = g.stroke
    ruby = eye_color
    profile = view in ("side", "back")
    folded = view in ("side", "back")
    persp = view == "perspective"
    # tail plumes FIRST (behind gem)
    tail = (
        f'<path d="M 84 128 C 74 142 64 150 52 156 M 92 130 C 88 146 82 156 74 164'
        f' M 108 130 C 112 146 118 156 126 164 M 116 128 C 126 142 136 150 148 156"'
        f' fill="none" stroke="{s}" stroke-width="1.5"/>'
        f'<path d="M 52 156 q -4 3 -2 7 q 4 1 6 -2 Z" fill="{s}" opacity="0.85"/>'
        f'<path d="M 148 156 q 4 3 2 7 q -4 1 -6 -2 Z" fill="{s}" opacity="0.85"/>'
        f'<circle cx="74" cy="164" r="2.2" fill="{g.gem["primary"]}" stroke="{g.gem["deep"]}" stroke-width="0.6"/>'
        f'<circle cx="126" cy="164" r="2.2" fill="{g.gem["primary"]}" stroke="{g.gem["deep"]}" stroke-width="0.6"/>'
    )
    # torso ellipse (gem sits ON breast, body visible around it)
    torso = (f'<ellipse cx="{CX}" cy="112" rx="14" ry="22" fill="#0A1512" stroke="url(#{uid}-metal)" stroke-width="2.5"/>'
             f'<path d="M 90 100 q 4 4 8 0 M 90 108 q 4 4 8 0 M 110 100 q -4 4 -8 0 M 110 108 q -4 4 -8 0"'
             f' fill="none" stroke="{s}" stroke-width="0.7" opacity="0.7"/>')
    wings = _wing(-1, s, uid, folded) + _wing(1, s, uid, folded and view == "side")
    if persp:  # near wing slightly larger/lower for 3/4 depth
        wings += f'<path d="M 104 100 C 130 88 150 86 162 92" fill="none" stroke="{s}" stroke-width="0.7" opacity="0.5"/>'
    # neck + head: frontal in front view, profile in side/back
    if profile:
        neck_head = (
            f'<path d="M 100 92 C 102 82 108 76 116 74" fill="none" stroke="{s}" stroke-width="2.6"/>'
            f'<ellipse cx="118" cy="72" rx="7" ry="6" fill="#0A1512" stroke="{s}" stroke-width="2"/>'
            f'<path d="M 124 69 L 133 72 L 124 76 Z" fill="{s}"/>'
            f'<path d="M 124 69 L 130 72" stroke="{g.gem["deep"]}" stroke-width="0.8"/>'
            f'<circle cx="119" cy="71" r="2.4" fill="{ruby}" stroke="#450A0A" stroke-width="0.9"/>'
            f'<circle cx="119.8" cy="70.2" r="0.8" fill="#FCA5A5"/>'
            f'<path d="M 112 66 C 108 59 103 56 98 55 M 114 65 C 112 58 110 54 107 52 M 116 65 C 116 58 115 54 113 51"'
            f' fill="none" stroke="{s}" stroke-width="1.1"/>'
        )
    else:
        neck_head = (
            f'<path d="M 94 92 C 94 82 96 76 100 72 M 106 92 C 106 82 104 76 100 72" fill="none" stroke="{s}" stroke-width="2.2"/>'
            f'<circle cx="100" cy="66" r="8" fill="#0A1512" stroke="{s}" stroke-width="2"/>'
            f'<path d="M 100 58 L 97 51 L 100 56 L 103 50 L 102 57 L 107 53 L 103 59"'
            f' fill="none" stroke="{s}" stroke-width="1.2" stroke-linecap="round"/>'
            f'<path d="M 100 68 L 96 71 L 100 74 L 104 71 Z" fill="{s}"/>'
            f'<path d="M 100 74 q 0 2 -2 2" fill="none" stroke="{s}" stroke-width="0.9"/>'
            f'<circle cx="96.8" cy="64.5" r="1.7" fill="{ruby}" stroke="#450A0A" stroke-width="0.8"/>'
            f'<circle cx="103.2" cy="64.5" r="1.7" fill="{ruby}" stroke="#450A0A" stroke-width="0.8"/>'
            f'<path d="M 93.5 61.5 L 96.5 62.5 M 106.5 61.5 L 103.5 62.5" stroke="{s}" stroke-width="0.9"/>'
        )
    # exactly TWO hind legs, planted stance with 3 talons each
    legs = (
        f'<path d="M 93 132 C 92 140 91 146 89 152 M 107 132 C 108 140 109 146 111 152"'
        f' fill="none" stroke="{s}" stroke-width="2.6" stroke-linecap="round"/>'
        f'<path d="M 89 152 l -7 2 M 89 152 l -2 6 M 89 152 l 6 3 M 111 152 l 7 2 M 111 152 l 2 6 M 111 152 l -6 3"'
        f' fill="none" stroke="{s}" stroke-width="1.4" stroke-linecap="round"/>'
        f'<circle cx="89" cy="152" r="1.6" fill="{s}"/>'
        f'<circle cx="111" cy="152" r="1.6" fill="{s}"/>'
    )
    # thigh feather tufts
    tufts = (f'<path d="M 93 130 q -5 2 -6 7 q 4 1 7 -2 Z M 107 130 q 5 2 6 7 q -4 1 -7 -2 Z"'
             f' fill="{s}" opacity="0.8"/>')
    return tail + torso + wings + neck_head + legs + tufts


def _back_view(g: CadParams, uid: str, front_body: str) -> str:
    """Back view: same silhouette (mirrored) + findings (pin stem, hinge, catch)."""
    s = g.stroke
    findings = (
        f'<line x1="55" y1="95" x2="145" y2="95" stroke="{s}" stroke-width="2"/>'
        f'<circle cx="55" cy="95" r="3.5" fill="none" stroke="{s}" stroke-width="1.5"/>'
        f'<rect x="138" y="91" width="10" height="8" rx="1.5" fill="none" stroke="{s}" stroke-width="1.5"/>'
        f'<circle cx="100" cy="150" r="2" fill="none" stroke="{s}" stroke-width="1" stroke-dasharray="1.5,1.5"/>'
        f'<text x="100" y="42" text-anchor="middle" fill="{s}" font-size="7" font-family="monospace" opacity="0.8">BACK · pin + catch</text>'
    )
    return (f'<g opacity="0.92" transform="translate(200,0) scale(-1,1)">'
            f'{front_body.split("<text")[0]}'  # silhouette without dim text duplication
            f'</g>' + findings + _dim(f'{g.dims()["width_mm"]}mm wide · back'))


def render_cad_svg(jewelry_type: str, metal: str, stone: str, stone_shape: str,
                   stone_size: str, setting: str, band_width: str | None,
                   view: str, design_id: str = "cad", motif: dict | None = None) -> tuple[str, CadParams]:
    """Primary deterministic renderer. Returns (svg, params)."""
    view = view if view in ("front", "side", "perspective", "back") else "perspective"
    g = CadParams(jewelry_type, metal, stone, stone_shape, stone_size, band_width, setting)
    uid = f"{re.sub(r'[^a-zA-Z0-9]', '', design_id)[:12]}-{view}"
    t = g.jewelry_type
    if t == "ring":
        body = _ring(g, view, uid)
        label = f'{g.carat}ct'
    elif t in ("necklace", "pendant"):
        chain = (f'<path d="M 40 55 Q 100 25 160 55" fill="none" stroke="url(#{uid}-metal)" stroke-width="2.5"/>'
                 f'<line x1="100" y1="55" x2="100" y2="{CY-20:.1f}" stroke="{g.stroke}" stroke-width="1.4"/>')
        body = chain + gem_shape_elements(g, CX, CY, uid)
        body += _dim(f'{g.carat}ct pendant')
    elif t == "earrings":
        one = gem_shape_elements(g, 70, 95, uid)
        two = gem_shape_elements(g, 130, 95, uid)
        body = (f'<line x1="70" y1="45" x2="70" y2="70" stroke="{g.stroke}" stroke-width="2"/>'
                f'<line x1="130" y1="45" x2="130" y2="70" stroke="{g.stroke}" stroke-width="2"/>' + one + two
                + _dim(f'pair · {g.carat}ct ea'))
    elif t == "bracelet":
        body = _generic_body(g, view, uid, 58, f'{g.carat}ct · Ø{(g.band_r*2+8):.0f}mm')
    elif t == "brooch":
        mtype = ((motif or {}).get("type") or "").lower()
        desc = ((motif or {}).get("description") or "").lower()
        if mtype == "animal" and "phoenix" in desc:
            eye = "#EF4444"  # ruby eyes per request
            pv = "front" if view == "back" else view
            body = (_phoenix(g, uid, eye, pv)
                    + gem_shape_elements(g, CX, 115, uid)
                    + _dim(f'phoenix · {g.carat}ct'))
        else:
            body = (f'<polygon points="100,45 118,78 155,80 126,102 136,138 100,118 64,138 74,102 45,80 82,78" fill="none" stroke="url(#{uid}-metal)" stroke-width="2.5"/>'
                    + gem_shape_elements(g, CX, 95, uid) + _dim(f'{g.carat}ct brooch'))
    elif t == "tiara":
        body = (f'<path d="M 45 155 Q 100 120 155 155 L 150 120 L 128 70 L 100 45 L 72 70 L 50 120 Z" fill="none" stroke="url(#{uid}-metal)" stroke-width="2.5"/>'
                + gem_shape_elements(g, CX, 78, uid) + _dim(f'{g.carat}ct tiara'))
    else:
        body = _generic_body(g, "perspective" if view == "back" else view, uid, 55, f'{g.carat}ct')
    if view == "back":
        # render matching front silhouette, then mirror + add findings
        body = _back_view(g, uid, body)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEWBOX}" width="200" height="200" role="img">'
           f'{_defs(g, uid)}<g filter="url(#{uid}-soft)">{body}</g></svg>')
    return svg, g


def to_dxf_entities(g: CadParams) -> str:
    """Minimal DXF (R12) with true mm dimensions for jeweller handoff."""
    r = g.band_r; sw = g.stone_r
    return (f"0\nSECTION\n2\nENTITIES\n"
            f"0\nCIRCLE\n8\nBAND\n10\n0.0\n20\n0.0\n40\n{r:.3f}\n"
            f"0\nCIRCLE\n8\nSTONE\n10\n0.0\n20\n{r:.3f}\n40\n{sw:.3f}\n"
            f"0\nTEXT\n8\nLABEL\n10\n0.0\n20\n{-r-4:.3f}\n40\n1.5\n1\n{g.stone} {g.carat}ct {g.metal}\n"
            f"0\nENDSEC\n0\nEOF\n")
