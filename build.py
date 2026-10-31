#!/usr/bin/env python3
"""
Builds the animated sci-fi SVGs for the README from ONE image: eureka.png

It looks for eureka.png (any case; png / jpg / webp) in assets/ and then in the repo root.
No image found? You still get a clean animated sky banner.

    python tools/build.py                      # auto-detect everything
    python tools/build.py --mode cutout        # force a layout: wallpaper | cutout | panel
    python tools/build.py --focus 0.3          # vertical crop focus (0 = top, 1 = bottom)
    python tools/build.py --image path/to.png  # use a specific file

Layouts (auto-detected from the image):
  cutout     transparent PNG of the character -> floats on the right, inside rotating HUD rings
  wallpaper  wide opaque image (aspect >= 1.5)  -> full-bleed background, text on the left
  panel      opaque portrait / square image     -> framed panel on the right, faded into the sky

Images are embedded inside the SVG (GitHub does not let an SVG load other files), so
the banner works with no hosting. Requires:  pip install pillow
"""
import argparse
import base64
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTS = {".png", ".jpg", ".jpeg", ".webp"}
W, H = 1280, 440

LINE1, LINE2 = "TUSHAR", "KUMAR SINGH"
SUB1 = "AI / ML  ·  COMPUTER VISION  ·  GAME DEV"
SUB2 = "PHYSICS  ·  WEB  ·  DEVOPS"
TICKER = "AI/ML // COMPUTER VISION // GAME DEV // PHYSICS // WEB DEV // DEVOPS // " * 2

HEADINGS = [
    ("profile", "01 // PILOT PROFILE"),
    ("stack", "02 // COMPAC DRIVE"),
    ("projects", "03 // HANGAR"),
    ("log", "04 // MISSION LOG"),
    ("activity", "05 // TRAPAR WAVE"),
]


# ----------------------------------------------------------------------------- images
def find_image(explicit):
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    for folder in (ROOT / "assets", ROOT):
        if folder.is_dir():
            for f in sorted(folder.iterdir()):
                if f.is_file() and f.stem.lower() == "eureka" and f.suffix.lower() in EXTS:
                    return f
    return None


def to_uri(img, fmt):
    buf = io.BytesIO()
    if fmt == "JPEG":
        img.convert("RGB").save(buf, "JPEG", quality=82, optimize=True)
        mime = "image/jpeg"
    else:
        img.save(buf, "WEBP", quality=86, method=6)
        mime = "image/webp"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def cover(img, w, h, fy):
    from PIL import Image

    iw, ih = img.size
    target = w / h
    if iw / ih > target:
        nw = int(ih * target)
        left = (iw - nw) // 2
        img = img.crop((left, 0, left + nw, ih))
    else:
        nh = int(iw / target)
        top = int((ih - nh) * fy)
        img = img.crop((0, top, iw, top + nh))
    return img.resize((w, h), Image.LANCZOS)


def prepare(path, mode, focus):
    from PIL import Image

    img = Image.open(path)
    img.load()
    img = img.convert("RGBA")
    if mode == "auto":
        lo, _ = img.getchannel("A").getextrema()
        if lo < 200:
            mode = "cutout"
        else:
            mode = "wallpaper" if img.width / img.height >= 1.5 else "panel"

    if mode == "wallpaper":
        fy = 0.4 if focus is None else focus
        return dict(mode=mode, uri=to_uri(cover(img, W, H, fy), "JPEG"))

    if mode == "cutout":
        bbox = img.getchannel("A").getbbox()
        if bbox:
            img = img.crop(bbox)
        h = H - 68
        w = int(h * img.width / img.height)
        if w > 640:
            w = 640
            h = int(w * img.height / img.width)
        big = img.resize((int(w * 1.5), int(h * 1.5)), Image.LANCZOS)
        return dict(mode=mode, uri=to_uri(big, "WEBP"), w=w, h=h)

    fy = 0.2 if focus is None else focus
    w, h = 560, H
    return dict(mode="panel", uri=to_uri(cover(img, int(w * 1.5), int(h * 1.5), fy), "WEBP"), w=w, h=h)


# ----------------------------------------------------------------------------- svg bits
def wave(y, amp, seg=160):
    return f"M-{2 * seg} {y} q{seg // 2} -{amp} {seg} 0" + f" t{seg} 0" * 11


def waves(y0):
    return f"""<g fill="none" stroke-linecap="round">
      <path d="{wave(y0, 22)}" stroke="#fff" stroke-opacity="0.20" stroke-width="1.2"><animateTransform attributeName="transform" type="translate" from="0 0" to="320 0" dur="26s" repeatCount="indefinite"/></path>
      <path d="{wave(y0 + 18, 18)}" stroke="#fff" stroke-opacity="0.32" stroke-width="1.2"><animateTransform attributeName="transform" type="translate" from="320 0" to="0 0" dur="20s" repeatCount="indefinite"/></path>
      <path d="{wave(y0 + 36, 14)}" stroke="#fff" stroke-opacity="0.50" stroke-width="1.4"><animateTransform attributeName="transform" type="translate" from="0 0" to="320 0" dur="15s" repeatCount="indefinite"/></path>
    </g>"""


COMMON_DEFS = """
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#030918"/><stop offset="0.45" stop-color="#0a2c74"/>
      <stop offset="0.80" stop-color="#2b8ef0"/><stop offset="1" stop-color="#b4f1ff"/>
    </linearGradient>
    <radialGradient id="sun" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.85"/>
      <stop offset="0.4" stop-color="#8fe9ff" stop-opacity="0.35"/>
      <stop offset="1" stop-color="#2b8ef0" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="tint" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#030918" stop-opacity="0.55"/>
      <stop offset="0.55" stop-color="#0a2c74" stop-opacity="0.25"/>
      <stop offset="1" stop-color="#030918" stop-opacity="0.78"/>
    </linearGradient>
    <linearGradient id="trail" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#8fe9ff" stop-opacity="0"/><stop offset="1" stop-color="#ffffff"/>
    </linearGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#8fe9ff"/><stop offset="1" stop-color="#8fe9ff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#8fe9ff" stop-opacity="0"/><stop offset="0.5" stop-color="#8fe9ff" stop-opacity="0.15"/>
      <stop offset="1" stop-color="#8fe9ff" stop-opacity="0"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-100%" width="140%" height="300%"><feGaussianBlur stdDeviation="14"/></filter>
    <filter id="glow" x="-10%" y="-60%" width="120%" height="220%">
      <feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
"""

CLOUDS = """<g filter="url(#soft)" fill="#fff">
      <ellipse cx="0" cy="120" rx="170" ry="26" opacity="0.28"><animate attributeName="cx" values="-250;1530" dur="90s" repeatCount="indefinite"/></ellipse>
      <ellipse cx="0" cy="250" rx="230" ry="34" opacity="0.36"><animate attributeName="cx" values="-300;1580" dur="70s" begin="-30s" repeatCount="indefinite"/></ellipse>
      <ellipse cx="0" cy="340" rx="300" ry="30" opacity="0.45"><animate attributeName="cx" values="-350;1630" dur="55s" begin="-15s" repeatCount="indefinite"/></ellipse>
    </g>"""


def rings(cx, cy):
    return f"""<g transform="translate({cx:.0f} {cy})" fill="none" stroke="#8fe9ff">
      <circle r="208" stroke-opacity="0.55" stroke-width="6" stroke-dasharray="1.5 12.6"><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="90s" repeatCount="indefinite"/></circle>
      <circle r="186" stroke-opacity="0.40" stroke-width="1.4" stroke-dasharray="70 18 8 18"><animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="34s" repeatCount="indefinite"/></circle>
      <circle r="150" stroke-opacity="0.30" stroke-width="1.2"/>
      <circle r="150" stroke-opacity="0.85" stroke-width="2.4" stroke-dasharray="40 900" stroke-linecap="round"><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="6s" repeatCount="indefinite"/></circle>
      <circle r="112" stroke-opacity="0.22" stroke-width="1.2" stroke-dasharray="4 8"><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="50s" repeatCount="indefinite"/></circle>
      <path d="M-228 0 H-196 M196 0 H228 M0 -228 V-196 M0 196 V228" stroke-opacity="0.7" stroke-width="2"/>
    </g>"""


def banner(art):
    mode = art["mode"] if art else "none"
    ax = ay = 0
    if mode == "cutout":
        ax, ay = W - art["w"] - 30, H - 40 + 14 - art["h"]
    elif mode == "panel":
        ax, ay = W - art["w"], 0
    cx = 1010 if mode in ("none", "wallpaper") else ax + art["w"] / 2
    cx = max(cx, 880)
    cy = 205

    defs_extra = f"""
    <linearGradient id="leftshade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#030918" stop-opacity="0.88"/><stop offset="0.5" stop-color="#030918" stop-opacity="0.55"/>
      <stop offset="0.85" stop-color="#030918" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="maskfade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#000"/><stop offset="0.38" stop-color="#fff"/><stop offset="1" stop-color="#fff"/>
    </linearGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0 H0 V40" fill="none" stroke="#8fe9ff" stroke-opacity="0.07" stroke-width="1"/>
      <animateTransform attributeName="patternTransform" type="translate" from="0 0" to="40 0" dur="10s" repeatCount="indefinite"/>
    </pattern>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="#8fe9ff" fill-opacity="0.06"/>
    </pattern>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>"""

    if mode == "wallpaper":
        scene = (f'<image href="{art["uri"]}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>'
                 f'<rect width="{W}" height="{H}" fill="url(#tint)"/>'
                 f'<rect width="{W}" height="{H}" fill="url(#leftshade)"/>'
                 + rings(cx, cy))
    else:
        scene = f'<rect width="{W}" height="{H}" fill="url(#sky)"/><circle cx="{cx:.0f}" cy="400" r="430" fill="url(#sun)"/>{CLOUDS}'
        scene += f'<rect width="{W}" height="{H}" fill="url(#leftshade)" opacity="0.7"/>'
        scene += rings(cx, cy)
        if mode in ("cutout", "panel"):
            fill = "url(#maskfade)" if mode == "panel" else "#fff"
            defs_extra += (f'\n    <mask id="artmask" maskUnits="userSpaceOnUse" x="{ax}" y="{ay}" width="{art["w"]}" height="{art["h"]}">'
                           f'<rect x="{ax}" y="{ay}" width="{art["w"]}" height="{art["h"]}" fill="{fill}"/></mask>')
            float_anim = ('<animateTransform attributeName="transform" type="translate" values="0 0;0 -7;0 0" dur="6s" repeatCount="indefinite"/>'
                          if mode == "cutout" else "")
            scene += (f'<ellipse cx="{cx:.0f}" cy="{cy + 20}" rx="{art["w"] * 0.62:.0f}" ry="{art["h"] * 0.52:.0f}" fill="url(#sun)" opacity="0.75"/>'
                      f'<g>{float_anim}<g mask="url(#artmask)"><image href="{art["uri"]}" x="{ax}" y="{ay}" width="{art["w"]}" height="{art["h"]}" preserveAspectRatio="none"/></g></g>')

    mono = "font-family=\"'Courier New', monospace\""
    sans = "font-family=\"'Helvetica Neue','Segoe UI',Arial,sans-serif\""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Tushar Kumar Singh - AI/ML, Computer Vision, Game Dev, Physics, Web, DevOps">
  <defs>{COMMON_DEFS}{defs_extra}
  </defs>
  <g clip-path="url(#frame)">
    {scene}
    <rect width="{W}" height="{H}" fill="url(#grid)"/>
    <rect width="{W}" height="{H}" fill="url(#scan)"/>
    <rect y="0" width="240" height="{H}" fill="url(#sweep)"><animate attributeName="x" values="-300;1300" dur="8s" repeatCount="indefinite"/></rect>
    <g transform="rotate(-9)" filter="url(#glow)">
      <rect width="260" height="2.6" rx="1.3" fill="url(#trail)">
        <animate attributeName="x" values="-400;1500" dur="9s" repeatCount="indefinite"/>
        <animate attributeName="y" values="420;280" dur="9s" repeatCount="indefinite"/>
      </rect>
    </g>
    {waves(350)}

    <!-- HUD frame -->
    <g stroke="#8fe9ff" stroke-width="2.5" fill="none" stroke-opacity="0.9" filter="url(#glow)">
      <path d="M30 64 V30 H64"/><path d="M{W - 64} 30 H{W - 30} V64"/>
    </g>

    <!-- title block -->
    <text x="64" y="72" {mono} font-size="12" letter-spacing="5" fill="#8fe9ff">// GEKKOSTATE PILOT TERMINAL</text>
    <text x="64" y="148" {sans} font-size="68" font-weight="300" letter-spacing="14" fill="#fff" filter="url(#glow)">{LINE1}</text>
    <text x="64" y="214" {sans} font-size="68" font-weight="300" letter-spacing="14" fill="#fff" filter="url(#glow)">{LINE2}</text>
    <rect x="64" y="234" width="560" height="1.6" fill="url(#rule)"/>
    <rect x="64" y="231" width="46" height="7" fill="#8fe9ff"><animate attributeName="opacity" values="1;0.25;1" dur="2.2s" repeatCount="indefinite"/></rect>
    <text x="64" y="266" {sans} font-size="14" letter-spacing="6" fill="#dff6ff">{SUB1}</text>
    <text x="64" y="290" {sans} font-size="14" letter-spacing="6" fill="#dff6ff">{SUB2}</text>
    <circle cx="68" cy="322" r="4" fill="#8fe9ff"><animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/></circle>
    <text x="84" y="326" {mono} font-size="11" letter-spacing="3" fill="#8fe9ff">ONLINE  ·  TRAPAR SYNC 100%  ·  DELHI 28.6°N 77.2°E</text>

    <!-- data ticker -->
    <rect y="{H - 40}" width="{W}" height="40" fill="#030918" fill-opacity="0.74"/>
    <rect y="{H - 40}" width="{W}" height="1.2" fill="#8fe9ff" fill-opacity="0.5"/>
    <g {mono} font-size="12" fill="#8fe9ff" fill-opacity="0.9">
      <text x="0" y="{H - 15}" textLength="{W}" lengthAdjust="spacing">{TICKER}</text>
      <text x="{W}" y="{H - 15}" textLength="{W}" lengthAdjust="spacing">{TICKER}</text>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-{W} 0" dur="32s" repeatCount="indefinite"/>
    </g>
  </g>
  <rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="14" fill="none" stroke="#8fe9ff" stroke-opacity="0.45"/>
</svg>
"""


def footer(FW=1280, FH=170):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FW} {FH}" width="{FW}" height="{FH}" role="img" aria-label="Ride the wave. Build the sky.">
  <defs>{COMMON_DEFS}
    <radialGradient id="vig" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#020718" stop-opacity="0.55"/><stop offset="1" stop-color="#020718" stop-opacity="0"/></radialGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0 H0 V40" fill="none" stroke="#8fe9ff" stroke-opacity="0.08"/><animateTransform attributeName="patternTransform" type="translate" from="0 0" to="40 0" dur="10s" repeatCount="indefinite"/></pattern>
    <clipPath id="f"><rect width="{FW}" height="{FH}" rx="14"/></clipPath>
  </defs>
  <g clip-path="url(#f)">
    <rect width="{FW}" height="{FH}" fill="url(#sky)"/>
    <rect width="{FW}" height="{FH}" fill="url(#grid)"/>
    {waves(108)}
    <ellipse cx="{FW // 2}" cy="64" rx="470" ry="52" fill="url(#vig)"/>
    <text x="{FW // 2}" y="72" text-anchor="middle" font-family="'Helvetica Neue','Segoe UI',Arial,sans-serif" font-size="22" font-weight="300" letter-spacing="12" fill="#fff" filter="url(#glow)">RIDE THE WAVE · BUILD THE SKY</text>
    <text x="{FW // 2}" y="98" text-anchor="middle" font-family="'Courier New', monospace" font-size="11" letter-spacing="6" fill="#8fe9ff">// END OF TRANSMISSION</text>
  </g>
  <rect x="0.75" y="0.75" width="{FW - 1.5}" height="{FH - 1.5}" rx="14" fill="none" stroke="#8fe9ff" stroke-opacity="0.45"/>
</svg>
"""


def heading(text):
    cx, w = 450, len(text) * (15 * 0.66 + 7)
    le, rs = cx - w / 2 - 22, cx + w / 2 + 22
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 48" width="900" height="48" role="img" aria-label="{text}">
  <defs>
    <linearGradient id="a" x1="0" x2="1"><stop offset="0" stop-color="#2a8cf0" stop-opacity="0"/><stop offset="1" stop-color="#2a8cf0"/></linearGradient>
    <linearGradient id="b" x1="0" x2="1"><stop offset="0" stop-color="#2a8cf0"/><stop offset="1" stop-color="#2a8cf0" stop-opacity="0"/></linearGradient>
  </defs>
  <rect x="20" y="23.25" width="{le - 20:.0f}" height="1.5" fill="url(#a)"/>
  <rect x="{rs:.0f}" y="23.25" width="{880 - rs:.0f}" height="1.5" fill="url(#b)"/>
  <circle r="2.5" cy="24" fill="#8fe9ff"><animate attributeName="cx" values="20;{le:.0f};20" dur="4.5s" repeatCount="indefinite"/></circle>
  <circle r="2.5" cy="24" fill="#8fe9ff"><animate attributeName="cx" values="880;{rs:.0f};880" dur="4.5s" repeatCount="indefinite"/></circle>
  <rect x="{le - 3:.0f}" y="21" width="6" height="6" fill="#2a8cf0" transform="rotate(45 {le:.0f} 24)"><animate attributeName="opacity" values="1;0.25;1" dur="3s" repeatCount="indefinite"/></rect>
  <rect x="{rs - 3:.0f}" y="21" width="6" height="6" fill="#2a8cf0" transform="rotate(45 {rs:.0f} 24)"><animate attributeName="opacity" values="0.25;1;0.25" dur="3s" repeatCount="indefinite"/></rect>
  <text x="{cx}" y="29" text-anchor="middle" font-family="'Courier New', monospace" font-size="15" font-weight="700" letter-spacing="7" fill="#2a8cf0">{text}</text>
</svg>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default=None)
    ap.add_argument("--mode", default="auto", choices=["auto", "wallpaper", "cutout", "panel"])
    ap.add_argument("--focus", type=float, default=None)
    ap.add_argument("--out", default=str(ROOT / "assets"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    def write(name, svg):
        (out / name).write_text(svg, encoding="utf-8")
        print(f"  {name:<14}{len(svg) / 1024:6.0f} KB")

    path = find_image(a.image)
    art = prepare(path, a.mode, a.focus) if path else None
    print("image :", path or "eureka.png not found -> default sky banner")
    if art:
        print("layout:", art["mode"])
    write("banner.svg", banner(art))
    write("footer.svg", footer())
    for stem, text in HEADINGS:
        write(f"h-{stem}.svg", heading(text))
    print("done.")


if __name__ == "__main__":
    main()
