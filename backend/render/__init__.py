"""Velaris realistic renderer — photorealistic-style raster previews (PIL).

Companion to backend/cad (manufacturing vectors). This module produces
studio-lit PNG previews: PBR-ish metal gradients, faceted gems with
sparkle, soft shadows, for every jewellery type x view, incl. phoenix.
"""
from __future__ import annotations
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 768
BG = (8, 14, 11)

METALS = {
    "yellow gold": [(62, 42, 14), (223, 190, 139), (255, 236, 190), (120, 85, 35)],
    "rose gold": [(66, 28, 26), (196, 132, 122), (255, 200, 185), (110, 60, 55)],
    "white gold": [(30, 42, 40), (184, 206, 200), (240, 250, 248), (90, 110, 105)],
    "platinum": [(35, 52, 46), (200, 216, 208), (245, 252, 250), (95, 115, 108)],
    "sterling silver": [(28, 40, 36), (168, 192, 184), (235, 245, 242), (85, 105, 100)],
    "14k yellow": [(55, 38, 12), (200, 168, 112), (240, 215, 160), (105, 75, 30)],
}
GEMS = {
    "ruby": ((239, 68, 68), (185, 28, 28), (252, 165, 165), (69, 10, 10)),
    "emerald": ((16, 185, 129), (5, 150, 105), (110, 231, 183), (6, 78, 59)),
    "sapphire": ((59, 130, 246), (29, 78, 216), (147, 197, 253), (23, 37, 84)),
    "diamond": ((232, 244, 248), (176, 216, 232), (255, 255, 255), (74, 120, 144)),
    "garnet": ((220, 38, 38), (153, 27, 27), (252, 165, 165), (60, 8, 8)),
    "amethyst": ((139, 92, 246), (109, 40, 217), (221, 214, 254), (46, 16, 101)),
    "aquamarine": ((34, 211, 238), (8, 145, 178), (165, 243, 252), (8, 51, 68)),
    "opal": ((192, 132, 252), (147, 51, 234), (245, 208, 254), (59, 7, 100)),
    "pearl": ((254, 243, 199), (217, 119, 6), (255, 251, 235), (69, 26, 3)),
    "moissanite": ((224, 236, 250), (144, 192, 224), (248, 252, 255), (58, 104, 136)),
    "morganite": ((251, 146, 60), (234, 88, 12), (255, 237, 213), (67, 20, 7)),
}


def metal(st: str):
    s = (st or "").lower()
    for k, v in METALS.items():
        if k in s:
            return v
    return METALS["yellow gold"]


def gem(st: str):
    s = (st or "").lower()
    for k, v in GEMS.items():
        if k in s:
            return v
    return GEMS["diamond"]


def studio_bg() -> Image.Image:
    img = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(img, "RGBA")
    for r in range(380, 0, -4):  # soft spotlight
        a = int(26 * (1 - r / 380))
        d.ellipse([SIZE//2-r, SIZE//2-r-30, SIZE//2+r, SIZE//2+r-30], fill=(30, 48, 40, a))
    return img.filter(ImageFilter.GaussianBlur(2))


def shadow(base: Image.Image, box, blur=18, alpha=110):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse(box, fill=(0, 0, 0, alpha))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))


def metal_band(d: ImageDraw.ImageDraw, pts, w: int, pal, closed=True):
    dark, mid, hi, deep = pal
    for ww, col in ((w+10, deep), (w+4, dark), (w, mid)):
        d.line(pts, fill=col, width=ww, joint="curve")
    # travelling highlight
    hl = [(x, y - w//3) for x, y in pts]
    d.line(hl, fill=hi, width=max(2, w//5), joint="curve")


def gemstone(img: Image.Image, cx: float, cy: float, r: float, pal,
             shape: str = "round", sparkle: bool = True) -> None:
    base = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    light, mid, glow, deep = pal
    sq = "emerald" in shape or "cushion" in shape or "princess" in shape
    elong = 1.25 if ("oval" in shape or "pear" in shape) else (1.5 if "marquise" in shape else 1.0)
    rx, ry = r, r * elong
    # glow halo (tight, subtle) — use pale glow tone so no dark disc shows
    d.ellipse([cx-rx*1.22, cy-ry*1.22, cx+rx*1.22, cy+ry*1.22], fill=glow+(26,))
    if sq:
        d.rounded_rectangle([cx-rx, cy-ry, cx+rx, cy+ry], radius=int(r*0.25), fill=deep+(255,))
        d.rounded_rectangle([cx-rx, cy-ry, cx+rx, cy+ry], radius=int(r*0.25), outline=mid, width=4)
    else:
        d.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=deep+(255,), outline=mid, width=4)
    # facet shell: concentric shaded rings
    for i, f in ((0.85, mid), (0.65, light), (0.45, mid), (0.28, glow)):
        c = tuple(min(255, int(c*1.05)) for c in f) + (235,)
        if sq:
            d.rounded_rectangle([cx-rx*i, cy-ry*i, cx+rx*i, cy+ry*i], radius=int(r*0.2*i), fill=c)
        else:
            d.ellipse([cx-rx*i, cy-ry*i, cx+rx*i, cy+ry*i], fill=c)
    # facet cross lines
    for ang in range(0, 180, 30):
        a = math.radians(ang)
        d.line([cx-rx*0.8*math.cos(a), cy-ry*0.8*math.sin(a),
                cx+rx*0.8*math.cos(a), cy+ry*0.8*math.sin(a)], fill=deep+(160,), width=2)
    # table highlight + sparkles
    d.ellipse([cx-r*0.28, cy-r*0.38, cx-r*0.02, cy-r*0.12], fill=(255, 255, 255, 220))
    if sparkle:
        for sx, sy, L in ((cx+rx*0.55, cy-ry*0.6, r*0.5), (cx-rx*0.5, cy+ry*0.45, r*0.35)):
            d.line([sx-L, sy, sx+L, sy], fill=(255, 255, 255, 230), width=3)
            d.line([sx, sy-L, sx, sy+L], fill=(255, 255, 255, 230), width=3)
    img.alpha_composite(base.filter(ImageFilter.GaussianBlur(0.4)))


def _chain(d, pal, w=7):
    dark, mid, hi, deep = pal
    pts = [(150, 200)] + [(150+i*9, 200+int(120*math.sin(math.pi*i/48))) for i in range(49)] + [(618, 200)]
    for ww, col in ((w+5, deep), (w, mid)):
        d.line(pts, fill=col, width=ww, joint="curve")
    for i in range(0, 49, 2):  # chain links glint
        x, y = pts[i+1]
        d.ellipse([x-5, y-5, x+5, y+5], outline=hi, width=2)


def _phoenix_filled(d, pal, gem_pal, cx=384, cy=360, s=1.0, spread=1.0):
    dark, mid, hi, deep = pal
    # tail plumes behind (smooth, tapered)
    for dx, sway in ((-70, -40), (-35, -12), (35, 12), (70, 40)):
        d.line([(cx+dx*0.4*s, cy+70*s), (cx+dx*s, cy+150*s), (cx+dx*s+sway*0.4, cy+185*s)],
               fill=dark, width=int(10*s), joint="curve")
        d.line([(cx+dx*0.4*s, cy+70*s), (cx+dx*s, cy+150*s)],
               fill=mid, width=int(4*s), joint="curve")
    # wings: fanned feather rows — tapered vanes radiating from the shoulder,
    # light outer coverts over darker flight feathers, with clear gaps
    for side in (-1, 1):
        sx = cx + side*18*s
        for row, (dy, ln, wd, tone, ol) in enumerate(
                ((6, 215, 34, hi, mid), (34, 180, 30, mid, hi), (60, 140, 26, dark, mid))):
            for f in range(6):  # 6 primaries per row, spread along the arc
                t = f / 5
                fx = sx + side*ln*spread*(0.35+0.65*t)*s
                fy = cy-58*s + dy*s + (t-0.5)*36*s
                # tapered vane: quad from quill to rounded tip
                tipx, tipy = fx + side*26*s, fy - 20*s + t*30*s
                d.polygon([(fx-5*s, fy+14*s), (fx-9*s, fy-14*s), (tipx-9*s, tipy),
                           (tipx+9*s, tipy+8*s), (fx+9*s, fy+12*s)],
                          fill=tone, outline=ol, width=2)
                d.line([(fx, fy-10*s), (tipx, tipy+2*s)], fill=ol, width=2)
    # torso + breast shading
    d.ellipse([cx-42*s, cy-70*s, cx+42*s, cy+80*s], fill=dark, outline=mid, width=4)
    d.ellipse([cx-26*s, cy-52*s, cx+26*s, cy+60*s], fill=mid)
    d.ellipse([cx-14*s, cy-38*s, cx+14*s, cy+30*s], fill=hi)
    # neck + head + hooked beak
    d.line([(cx, cy-66*s), (cx+6*s, cy-120*s)], fill=mid, width=int(20*s), joint="curve")
    d.ellipse([cx-14*s, cy-152*s, cx+26*s, cy-112*s], fill=mid, outline=hi, width=3)
    d.polygon([(cx+22*s, cy-140*s), (cx+44*s, cy-130*s), (cx+22*s, cy-122*s)], fill=hi)
    for dx in (-8, 0, 8):  # crest
        d.line([(cx+dx*s, cy-150*s), (cx+dx*1.6*s, cy-172*s)], fill=hi, width=4)
    # ruby eyes
    for ex in (-6, 12):
        d.ellipse([cx+ex*s-7, cy-140*s-7, cx+ex*s+7, cy-140*s+7], fill=(69, 10, 10))
        d.ellipse([cx+ex*s-5, cy-140*s-5, cx+ex*s+5, cy-140*s+5], fill=gem_pal[0])
        d.ellipse([cx+ex*s-2, cy-140*s-4, cx+ex*s+2, cy-140*s], fill=(255, 255, 255, 230))
    # legs: exactly 2, taloned
    for side in (-1, 1):
        d.line([(cx+side*22*s, cy+70*s), (cx+side*34*s, cy+140*s)], fill=dark, width=int(13*s))
        d.line([(cx+side*22*s, cy+70*s), (cx+side*34*s, cy+140*s)], fill=mid, width=int(6*s))
        for tx in (-12, 0, 12):
            d.line([(cx+side*34*s, cy+140*s), (cx+side*34*s+tx*s, cy+158*s)], fill=hi, width=4)


def render_realistic(jewelry_type: str, metal_name: str, stone: str, shape: str,
                     carat: float, view: str = "front",
                     motif: dict | None = None) -> Image.Image:
    jt = (jewelry_type or "Ring").lower()
    pal, gpal = metal(metal_name), gem(stone)
    img = studio_bg().convert("RGBA")
    C = SIZE // 2
    r = 34 + 26 * (max(carat, 0.2) ** (1/3))  # gem radius px from carat
    back = view == "back"
    tiny = 0.82 if view == "perspective" else 1.0
    if view == "side":
        shadow(img, [C-160, 500, C+160, 540])
    else:
        shadow(img, [C-220, 560, C+220, 600])

    d = ImageDraw.Draw(img)
    if jt == "ring":
        if view == "side":
            metal_band(d, [(C-30, 180), (C-30, 560)], 34, pal)
            gemstone(img, C, 180, r*0.7, gpal, shape); d = ImageDraw.Draw(img)
        else:
            # smooth band: true ellipses, not polyline
            dark, mid, hi, deep = pal
            for ww, col in ((40, deep), (34, dark), (28, mid)):
                d.ellipse([C-150, 250, C+150, 590], outline=col, width=ww)
            d.arc([C-150, 262, C+150, 602], start=200, end=340, fill=hi, width=6)
            for i in range(7):  # pavé accents ride the smooth band
                a = math.pi*(0.2+0.6*i/6)
                gemstone(img, C+150*math.cos(a), 420-170*math.sin(a), 10, gem("diamond"), "round", False)
            d = ImageDraw.Draw(img)
            gemstone(img, C, 232, r, gpal, shape)
            for px in (-22, 22):  # prongs
                d.line([(C+px, 275), (C+px*1.2, 232+r*0.8)], fill=pal[1], width=8)
    elif jt in ("necklace", "pendant"):
        _chain(d, pal)
        d.line([(C, 320), (C, 380)], fill=pal[1], width=10)
        gemstone(img, C, 430, r*1.3, gpal, shape); d = ImageDraw.Draw(img)
        d.ellipse([C-r*1.3-10, 430-r*1.5, C+r*1.3+10, 430+r*1.5], outline=pal[1], width=6)
    elif jt == "earrings":
        for ex in (C-110, C+110):
            d.line([(ex, 180), (ex, 300)], fill=pal[1], width=9)
            d.ellipse([ex-14, 300, ex+14, 330], fill=pal[1])
            gemstone(img, ex, 380, r, gpal, shape)
        d = ImageDraw.Draw(img)
    elif jt == "bracelet":
        pts = [(C+190*math.cos(a), 400+130*math.sin(a)) for a in [math.pi*2*i/40 for i in range(41)]]
        metal_band(d, pts, 26, pal)
        for i in range(0, 40, 5):
            gemstone(img, *pts[i], 13, gpal, "round", False)
        d = ImageDraw.Draw(img)
        gemstone(img, C, 268, r, gpal, shape)
    elif jt == "tiara":
        band = [(C-220, 520), (C-200, 380), (C-140, 280), (C-60, 220), (C, 200),
                (C+60, 220), (C+140, 280), (C+200, 380), (C+220, 520),
                (C+200, 520), (C+180, 400), (C, 260), (C-180, 400), (C-200, 520)]
        d.polygon(band, fill=pal[0], outline=pal[1])
        # metallic face: mid inner band + travelling highlight
        inner = [(C-205, 515), (C-188, 385), (C-135, 295), (C-60, 232), (C, 214),
                 (C+60, 232), (C+135, 295), (C+188, 385), (C+205, 515)]
        d.line(inner, fill=pal[1], width=14, joint="curve")
        d.line([(x, y-8) for x, y in inner], fill=pal[2], width=4, joint="curve")
        for i, (sx, sy, gr) in enumerate(((-140, 285, 16), (-60, 228, 20), (0, 208, r), (60, 228, 20), (140, 285, 16))):
            d.ellipse([C+sx-gr-7, sy-gr*1.2-7, C+sx+gr+7, sy+gr*1.2+7], outline=pal[1], width=4)
            gemstone(img, C+sx, sy, gr, gpal, shape)
        d = ImageDraw.Draw(img)
    else:  # brooch (+motif)
        m = ((motif or {}).get("description") or "").lower()
        if "phoenix" in m:
            _phoenix_filled(d, pal, gpal, spread=0.55 if view == "side" else 1.0)
            gemstone(img, C, 375, r*0.95, gpal, shape); d = ImageDraw.Draw(img)
            d.ellipse([C-r*0.95-9, 375-r*1.15, C+r*0.95+9, 375+r*1.15], outline=pal[1], width=6)
            if back:
                d.line([(C-150, 330), (C+150, 330)], fill=pal[2], width=8)
                d.ellipse([C-170, 312, C-140, 342], outline=pal[2], width=5)
                d.rectangle([C+140, 318, C+172, 342], outline=pal[2], width=5)
        else:
            for k in range(8):  # starburst
                a = math.pi*2*k/8
                d.line([(C, 360), (C+190*math.cos(a), 360+190*math.sin(a))], fill=pal[0], width=26, joint="curve")
                gemstone(img, C+150*math.cos(a), 360+150*math.sin(a), 12, gem("diamond"), "round", False)
            d = ImageDraw.Draw(img)
            gemstone(img, C, 360, r*1.2, gpal, shape)
    if back and jt != "brooch":
        d.text((C-90, 90), "BACK · findings", fill=pal[2])
    # caption + vignette
    img = img.convert("RGB")
    dd = ImageDraw.Draw(img)
    dd.text((24, SIZE-40), f"{jewelry_type} · {stone} {carat}ct · {metal_name} · {view}",
            fill=(223, 190, 139))
    return img
