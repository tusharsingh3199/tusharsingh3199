#!/usr/bin/env python3

import base64
import html
import io
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "eureka.png"

# Banner / footer canvas sizes (SVG user units; the README scales them to 100% width).
BW, BH = 1280, 500
FW, FH = 1280, 280
TAB = 16  # footer dock: the visit counter sits right under this tab

NAME_1, NAME_2 = "TUSHAR", "SINGH"
ROLES = [
    "AI/ML ENGINEER",
    "WEB & DEVOPS ENGINEER",
    "GAME DEVELOPER",
]
ALT = "Tushar Singh - AI/ML Engineer, Web Dev & DevOps Engineer, Game Developer"
SECONDS_PER_ROLE = 3.6

HEADINGS = [("profile", "01 // PILOT PROFILE"), ("stack", "02 // COMPAC DRIVE")]

SANS = "font-family=\"'Helvetica Neue','Segoe UI',Arial,sans-serif\""
MONO = "font-family=\"'Courier New',monospace\""


def remove_title(img):
    """Paint out the 'Eureka Seven' lettering baked into the top-left sky."""
    box = (0, 0, 548, 215)
    region = img.crop(box)
    smooth = region.filter(ImageFilter.MedianFilter(15)).filter(ImageFilter.MedianFilter(15)).filter(ImageFilter.GaussianBlur(9))
    mask = Image.new("L", region.size, 0)
    ImageDraw.Draw(mask).rectangle((-30, -30, region.width - 14, region.height - 14), fill=255)
    out = img.copy()
    out.paste(smooth, box[:2], mask.filter(ImageFilter.GaussianBlur(8)))
    return out


def jpeg_uri(img, size, top, quality=80):
    """Crop the full-width band that starts at `top` (aspect of `size`) and embed it as JPEG."""
    ch = round(img.width * size[1] / size[0])
    top = max(0, min(top, img.height - ch))
    band = img.crop((0, top, img.width, top + ch)).resize(size, Image.LANCZOS).convert("RGB")
    buf = io.BytesIO()
    band.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


DEFS = """
    <filter id="soft" x="-30%" y="-150%" width="160%" height="400%"><feGaussianBlur stdDeviation="16"/></filter>
    <filter id="shadow" x="-10%" y="-30%" width="120%" height="170%">
      <feDropShadow dx="0" dy="2" stdDeviation="3.5" flood-color="#031030" flood-opacity="0.6"/>
    </filter>
    <filter id="glow" x="-10%" y="-60%" width="120%" height="220%">
      <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>"""


def clouds(specs):
    """specs: (cy, rx, ry, opacity, duration, begin) -> slowly drifting soft clouds."""
    parts = []
    for cy, rx, ry, op, dur, begin in specs:
        parts.append(
            f'<ellipse cx="0" cy="{cy}" rx="{rx}" ry="{ry}" opacity="{op}">'
            f'<animate attributeName="cx" values="-{rx + 60};{1280 + rx + 60}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></ellipse>'
        )
    return '<g filter="url(#soft)" fill="#fff">' + "".join(parts) + "</g>"


def particles(n, w, y_min, y_max, seed):
    """Tiny drifting lights, a nod to the trapar particles."""
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(y_min, y_max)
        r, dur = rnd.uniform(1.1, 2.7), rnd.uniform(13, 26)
        dx, dy = rnd.uniform(-20, 60), rnd.uniform(50, 130)
        b = f'dur="{dur:.1f}s" begin="-{rnd.uniform(0, dur):.1f}s" repeatCount="indefinite"'
        out.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" opacity="0">'
            f'<animate attributeName="cy" values="{y:.0f};{y - dy:.0f}" {b}/>'
            f'<animate attributeName="cx" values="{x:.0f};{x + dx:.0f}" {b}/>'
            f'<animate attributeName="opacity" values="0;0.85;0" {b}/></circle>'
        )
    return '<g fill="#eafaff">' + "".join(out) + "</g>"


def wave_path(y, amp, seg=160):
    return f"M-{2 * seg} {y} q{seg // 2} -{amp} {seg} 0" + f" t{seg} 0" * 11


def waves(y0):
    spec = [(0, 22, 0.20, 1.2, 0, 320, 26), (18, 18, 0.32, 1.2, 320, 0, 20), (36, 14, 0.50, 1.4, 0, 320, 15)]
    return '<g fill="none" stroke="#fff" stroke-linecap="round">' + "".join(
        f'<path d="{wave_path(y0 + dy, amp)}" stroke-opacity="{op}" stroke-width="{sw}">'
        f'<animateTransform attributeName="transform" type="translate" from="{a} 0" to="{b} 0" dur="{d}s" repeatCount="indefinite"/></path>'
        for dy, amp, op, sw, a, b, d in spec
    ) + "</g>"


def _keyframes(i, n, fade=0.02):
    """Shared opacity / slide keyframes for slide i of n (fraction of one full cycle)."""
    s, e = i / n, (i + 1) / n
    frames = [(0, 0, 12), (s, 0, 12), (s + fade, 1, 0), (e - fade, 1, 0), (e, 0, -12), (1, 0, -12)]
    clean = []
    for t, op, dy in frames:
        if not clean or t > clean[-1][0] + 1e-9:
            clean.append((min(t, 1), op, dy))
    clean[-1] = (1, clean[-1][1], clean[-1][2])
    return clean


def role_slideshow(x, y, dots_y):
    n = len(ROLES)
    dur = f"{n * SECONDS_PER_ROLE:.1f}s"
    out = []
    for i, role in enumerate(ROLES):
        k = _keyframes(i, n)
        kt = ";".join(f"{t:.4f}" for t, _, _ in k)
        ops = ";".join(str(o) for _, o, _ in k)
        dys = ";".join(f"0 {d}" for _, _, d in k)
        out.append(
            f'<g opacity="0" filter="url(#shadow)">'
            f'<animate attributeName="opacity" values="{ops}" keyTimes="{kt}" dur="{dur}" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="{dys}" keyTimes="{kt}" dur="{dur}" repeatCount="indefinite"/>'
            f'<text x="{x}" y="{y}" {SANS} font-size="29" letter-spacing="7" fill="#fff">{html.escape(role)}</text></g>'
        )
    for i in range(n):
        k = _keyframes(i, n)
        kt = ";".join(f"{t:.4f}" for t, _, _ in k)
        ops = ";".join(str(o) for _, o, _ in k)
        cx = x + 5 + i * 22
        out.append(
            f'<circle cx="{cx}" cy="{dots_y}" r="3.6" fill="#fff" opacity="0.35"/>'
            f'<circle cx="{cx}" cy="{dots_y}" r="3.6" fill="#8fe9ff" opacity="0" filter="url(#glow)">'
            f'<animate attributeName="opacity" values="{ops}" keyTimes="{kt}" dur="{dur}" repeatCount="indefinite"/></circle>'
        )
    return "".join(out)


def drift_image(uri, w, h, zoom=0.045, dur=46):
    """Slow breathing zoom so the artwork feels alive without any flashy effect."""
    dw, dh = w * zoom, h * zoom
    return (
        f'<image href="{uri}" x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="none">'
        f'<animate attributeName="x" values="0;-{dw / 2:.1f};0" dur="{dur}s" repeatCount="indefinite"/>'
        f'<animate attributeName="y" values="0;-{dh / 2:.1f};0" dur="{dur}s" repeatCount="indefinite"/>'
        f'<animate attributeName="width" values="{w};{w + dw:.1f};{w}" dur="{dur}s" repeatCount="indefinite"/>'
        f'<animate attributeName="height" values="{h};{h + dh:.1f};{h}" dur="{dur}s" repeatCount="indefinite"/></image>'
    )


def banner(uri):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BW} {BH}" width="{BW}" height="{BH}" role="img" aria-label="{html.escape(ALT)}">
  <defs>{DEFS}
    <linearGradient id="leftshade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#04163f" stop-opacity="0.55"/><stop offset="0.38" stop-color="#06205a" stop-opacity="0.28"/>
      <stop offset="0.62" stop-color="#0a2c74" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0.72" stop-color="#04163f" stop-opacity="0"/><stop offset="1" stop-color="#04163f" stop-opacity="0.5"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{BW}" height="{BH}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    {drift_image(uri, BW, BH)}
    {clouds([(70, 190, 24, 0.20, 95, 0), (150, 250, 30, 0.22, 120, -50), (250, 210, 26, 0.16, 80, -25)])}
    <rect width="{BW}" height="{BH}" fill="url(#leftshade)"/>
    <rect width="{BW}" height="{BH}" fill="url(#floor)"/>
    {particles(34, BW, 120, BH - 30, 7)}

    <text x="66" y="86" {MONO} font-size="12.5" letter-spacing="5.5" fill="#dff6ff" filter="url(#shadow)">DELHI, INDIA</text>
    <g filter="url(#shadow)" {SANS} font-size="64" font-weight="300" letter-spacing="11" fill="#fff">
      <text x="62" y="160">{NAME_1}</text>
      <text x="62" y="228">{NAME_2}</text>
    </g>
    <rect x="66" y="252" width="330" height="1.6" rx="0.8" fill="#fff" fill-opacity="0.75"/>
    <rect x="66" y="249" width="48" height="7.4" rx="3.7" fill="#8fe9ff"/>
    {role_slideshow(66, 302, 336)}
  </g>
  <rect x="0.75" y="0.75" width="{BW - 1.5}" height="{BH - 1.5}" rx="15.5" fill="none" stroke="#fff" stroke-opacity="0.4"/>
</svg>
"""


def footer(uri):
    H = FH + TAB
    cx = FW // 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FW} {H}" width="{FW}" height="{H}" role="img" aria-label="Ride the wave. Build the sky.">
  <defs>{DEFS}
    <linearGradient id="band" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#04163f" stop-opacity="0"/><stop offset="0.2" stop-color="#04163f" stop-opacity="0.8"/>
      <stop offset="0.8" stop-color="#04163f" stop-opacity="0.8"/><stop offset="1" stop-color="#04163f" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0.55" stop-color="#04163f" stop-opacity="0"/><stop offset="1" stop-color="#04163f" stop-opacity="0.55"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{FW}" height="{FH}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    {drift_image(uri, FW, FH, zoom=0.04, dur=52)}
    {clouds([(60, 210, 24, 0.20, 100, -20), (130, 260, 28, 0.18, 130, -70)])}
    <rect width="{FW}" height="{FH}" fill="url(#floor)"/>
    {waves(204)}
    {particles(26, FW, 90, FH - 20, 21)}
    <rect y="88" width="{FW}" height="76" fill="url(#band)" filter="url(#soft)"/>
    <text x="{cx}" y="128" text-anchor="middle" {SANS} font-size="30" font-weight="300" letter-spacing="13" fill="#fff" filter="url(#shadow)">RIDE THE WAVE · BUILD THE SKY</text>
    <text x="{cx}" y="162" text-anchor="middle" {MONO} font-size="14" letter-spacing="5" fill="#fff" filter="url(#shadow)">good night, good bye, and... good luck.</text>
  </g>
  <rect x="0.75" y="0.75" width="{FW - 1.5}" height="{FH - 1.5}" rx="15.5" fill="none" stroke="#fff" stroke-opacity="0.4"/>
  <!-- dock tab: the profile-visit counter sits directly beneath it -->
  <path d="M{cx - 150} {FH - 1} H{cx + 150} L{cx + 128} {H - 1} H{cx - 128} Z" fill="#0a2c74" stroke="#8fe9ff" stroke-opacity="0.45"/>
  <circle cx="{cx}" cy="{FH + TAB / 2 - 0.5}" r="2.4" fill="#8fe9ff"><animate attributeName="opacity" values="1;0.25;1" dur="2.4s" repeatCount="indefinite"/></circle>
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
    if not SOURCE.exists():
        raise SystemExit(f"missing {SOURCE}")
    art = Image.open(SOURCE).convert("RGB")
    art = remove_title(art)

    def write(name, svg):
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"  {name:<14}{len(svg) / 1024:6.0f} KB")

    write("banner.svg", banner(jpeg_uri(art, (1600, round(1600 * BH / BW)), top=30)))
    write("footer.svg", footer(jpeg_uri(art, (1600, round(1600 * FH / FW)), top=380)))
    for stem, text in HEADINGS:
        write(f"h-{stem}.svg", heading(text))
    print("done.")


if __name__ == "__main__":
    main()
