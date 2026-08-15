# -*- coding: utf-8 -*-
"""Zero-to-Ship (Z2S) documentation shell. © Zerø Effort.

Holds the things every generated document shares:
  TOKENS  — the Zero Style design-system tokens, inlined verbatim
  STRUCT  — structural CSS for the document chrome (never per-document)
  RUNTIME — the JSON-driven renderer + interactivity
  LOGO_*  — the Zerø Effort hand-painted Ø brand mark, built deterministically

Each document is one self-contained HTML file: a skeleton, its spec embedded as
JSON, and this runtime. The human view is BUILT FROM the embedded JSON at load
time, so the readable document and the machine-readable one cannot drift.
"""
import math as _math
import urllib.parse as _urlq

FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wght@0,400..700;1,400..700'
    '&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" />'
)

# ---------------------------------------------------------------------------
# Brand mark — the Zerø Effort hand-painted Ø. Geometry is computed with a
# seeded pseudo-noise function (no random module) so regeneration stays
# byte-identical. Black ink on transparency, pure vector.
#   LOGO_STATIC — the finished mark (app bar, favicon)
#   LOGO_ANIM   — the same art revealed in two brush strokes: circle, then slash
# ---------------------------------------------------------------------------
def _wob(i, salt):
    """Deterministic noise in [-1, 1] — the brush's hand tremor."""
    x = _math.sin(i * 12.9898 + salt * 78.233) * 43758.5453
    return (x - _math.floor(x)) * 2.0 - 1.0


def _smooth(pts):
    """Closed Catmull-Rom loop -> cubic beziers through every sampled point."""
    d = "M%.2f %.2f" % pts[0]
    n = len(pts)
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        d += "C%.2f %.2f %.2f %.2f %.2f %.2f" % (
            p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0,
            p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0,
            p2[0], p2[1])
    return d + "Z"


def _ring_d():
    """The O: a ring whose thickness swells where the brush presses (lower left)
    and thins where it lifts, with ragged painted edges on both contours."""
    cx = cy = 120.0
    outer, inner = [], []
    n = 44
    for i in range(n):
        th = 2 * _math.pi * i / n
        half = 9.5 + 4.5 * _math.cos(th - 3.3)
        r = 78.0 + 1.0 * _wob(i, 1) + 0.8 * _math.sin(2 * th + 1.7)
        ro = r + half + 0.45 * _wob(i, 2)
        ri = r - half + 0.45 * _wob(i, 3)
        outer.append((cx + ro * _math.cos(th), cy + ro * _math.sin(th)))
        inner.append((cx + ri * _math.cos(th), cy + ri * _math.sin(th)))
    return _smooth(outer) + " " + _smooth(inner)


def _slash_d():
    """The slash: lands heavy at lower left, bows slightly, lifts to a point."""
    ax, ay, bx, by = 36.0, 206.0, 208.0, 34.0
    dx, dy = bx - ax, by - ay
    ln = _math.hypot(dx, dy)
    px, py = -dy / ln, dx / ln
    top, bot = [], []
    n = 16
    for i in range(n):
        u = i / (n - 1.0)
        x = ax + dx * u + px * 5.0 * _math.sin(_math.pi * u)
        y = ay + dy * u + py * 5.0 * _math.sin(_math.pi * u)
        w = (8.5 * (1.0 - u) ** 0.6 + 2.0) * (1.0 + 0.05 * _wob(i, 5))
        top.append((x + px * w, y + py * w))
        bot.append((x - px * w, y - py * w))
    return _smooth(top + bot[::-1])


_RING = _ring_d()
_SLASH = _slash_d()
_SVG_OPEN = 'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"'

LOGO_STATIC = (
    '<svg %s role="img" aria-label="Zerø Effort">'
    '<path d="%s" fill="#000" fill-rule="evenodd"/>'
    '<path d="%s" fill="#000"/></svg>' % (_SVG_OPEN, _RING, _SLASH)
)

LOGO_ANIM = (
    '<svg %s role="img" aria-label="Zerø Effort">'
    '<defs>'
    '<mask id="z2sMr"><path d="M120 42 A78 78 0 1 1 120 198 A78 78 0 1 1 120 42"'
    ' pathLength="100" fill="none" stroke="#fff" stroke-width="36"'
    ' stroke-linecap="round" class="z2sS1"/></mask>'
    '<mask id="z2sMs"><path d="M32 211 L212 29" pathLength="100" fill="none"'
    ' stroke="#fff" stroke-width="28" stroke-linecap="round" class="z2sS2"/></mask>'
    '</defs>'
    '<g mask="url(#z2sMr)"><path d="%s" fill="#000" fill-rule="evenodd"/></g>'
    '<g mask="url(#z2sMs)"><path d="%s" fill="#000"/></g>'
    '<style>.z2sS1,.z2sS2{stroke-dasharray:104 104;stroke-dashoffset:104}'
    '.z2sS1{animation:z2s-paint .95s cubic-bezier(.45,.05,.35,1) .25s forwards}'
    '.z2sS2{animation:z2s-paint .38s cubic-bezier(.5,.05,.4,1) 1.35s forwards}'
    '@keyframes z2s-paint{to{stroke-dashoffset:0}}'
    '@media (prefers-reduced-motion:reduce){.z2sS1,.z2sS2{animation:none;stroke-dashoffset:0}}'
    '</style></svg>' % (_SVG_OPEN, _RING, _SLASH)
)

FAVICON = "data:image/svg+xml," + _urlq.quote(LOGO_STATIC)

# ---------------------------------------------------------------------------
# Zero Style design-system tokens — copied verbatim from the design system's
# tokens/ directory (colors, typography, spacing, elevation, motion).
# Light theme only: the system defines no dark palette.
# ---------------------------------------------------------------------------
TOKENS = r"""
:root{
  /* Blue (primary) — slate ramp */
  --blue-50:#F0F3F7;--blue-100:#DFE5EE;--blue-200:#C0CCDD;--blue-300:#98AAC5;--blue-400:#7089AC;
  --blue-500:#536E95;--blue-600:#3E587E;--blue-700:#324763;--blue-800:#263549;--blue-900:#1A2433;
  /* Info blue (semantic only) */
  --info-50:#EAF1FC;--info-200:#ADC9F3;--info-600:#0B5FD9;
  /* Warm neutrals (paper) */
  --gray-0:#FFFFFF;--gray-25:#FAFAF7;--gray-50:#F0F0EA;--gray-100:#E6E6E0;--gray-200:#D9D9D3;
  --gray-300:#C2C2BC;--gray-400:#9A9A96;--gray-500:#71716E;--gray-600:#545452;--gray-700:#3A3A38;
  --gray-800:#232322;--gray-900:#0D0D0C;
  /* Brand */
  --vermillion-100:#F8E4DC;--vermillion-400:#E07A55;--vermillion-500:#D0603C;--vermillion-600:#B84E2E;
  --ink-900:#121110;
  /* Semantic status */
  --green-600:#1E7F4F;--green-100:#E3F2E8;--green-200:#BFE3CD;
  --amber-600:#B97D10;--amber-100:#FBF2DD;--amber-200:#F3DFAE;
  --red-600:#C03530;--red-100:#F9E5E3;--red-200:#F0C6C2;
  /* Semantic aliases */
  --color-primary:var(--blue-600);--color-primary-hover:var(--blue-500);--color-primary-active:var(--blue-700);
  --color-accent:var(--vermillion-500);
  --surface-page:var(--gray-50);--surface-card:var(--gray-0);--surface-raised:var(--gray-25);
  --surface-sunken:var(--gray-100);--surface-inverse:var(--gray-900);
  --text-body:var(--gray-900);--text-secondary:var(--gray-600);--text-muted:var(--gray-400);
  --text-inverse:#FFFFFF;--text-link:var(--blue-600);--text-link-hover:var(--blue-500);
  --border-default:var(--gray-200);--border-strong:var(--gray-300);--border-focus:var(--blue-600);
  --status-success:var(--green-600);--status-success-bg:var(--green-100);
  --status-info:var(--info-600);--status-info-bg:var(--info-50);
  --status-warning:var(--amber-600);--status-warning-bg:var(--amber-100);
  --status-error:var(--red-600);--status-error-bg:var(--red-100);
  --focus-ring:0 0 0 3px rgba(62,88,126,0.32);
  /* Typography */
  --font-sans:"Instrument Sans",-apple-system,"Segoe UI",sans-serif;
  --font-mono:"JetBrains Mono",ui-monospace,"SF Mono",monospace;
  --text-h1-size:32px;--text-h1-weight:700;--text-h1-line:1.15;--text-h1-tracking:-0.02em;
  --text-h2-size:24px;--text-h2-weight:600;--text-h2-line:1.2;--text-h2-tracking:-0.01em;
  --text-subtitle-size:18px;--text-subtitle-weight:500;--text-subtitle-line:1.35;
  --text-body1-size:15px;--text-body1-weight:400;--text-body1-line:1.5;
  --text-body2-size:13px;--text-body2-weight:400;--text-body2-line:1.5;
  --text-caption-size:12px;--text-caption-weight:400;--text-caption-line:1.4;
  --text-button-size:14px;--text-button-weight:600;--text-button-line:1;
  --text-mono-size:13px;
  /* Spacing & radius */
  --space-1:4px;--space-2:8px;--space-3:16px;--space-4:24px;--space-5:32px;--space-6:48px;
  --radius-none:0px;--radius-sm:4px;--radius-md:8px;--radius-lg:16px;--radius-full:999px;
  --control-height-sm:28px;--control-height-md:36px;--control-height-lg:44px;
  /* Elevation */
  --shadow-0:none;
  --shadow-1:0 1px 2px rgba(13,13,12,0.06),0 1px 3px rgba(13,13,12,0.08);
  --shadow-2:0 2px 4px rgba(13,13,12,0.05),0 6px 16px rgba(13,13,12,0.10);
  --shadow-3:0 4px 12px rgba(13,13,12,0.08),0 18px 44px rgba(13,13,12,0.14);
  --shadow-glow:0 0 0 1px var(--blue-600),0 0 0 4px rgba(62,88,126,0.22),0 8px 24px rgba(62,88,126,0.25);
  --shadow-inset:inset 0 1px 2px rgba(13,13,12,0.06);
  /* Motion */
  --ease-out:cubic-bezier(0.22,1,0.36,1);--ease-out-expo:cubic-bezier(0.16,1,0.3,1);
  --ease-spring:cubic-bezier(0.34,1.56,0.64,1);--ease-in-out:cubic-bezier(0.65,0,0.35,1);
  --duration-fast:120ms;--duration-base:200ms;--duration-slow:360ms;--duration-hero:700ms;
}
@keyframes zs-fade-up{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@keyframes zs-fade-in{from{opacity:0}to{opacity:1}}
@keyframes zs-scale-in{from{opacity:0;transform:scale(.94)}to{opacity:1;transform:scale(1)}}
@keyframes zs-flash{0%{box-shadow:var(--shadow-glow)}100%{box-shadow:var(--shadow-1)}}
@keyframes zs-draw{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}
"""

# ---------------------------------------------------------------------------
# Structural CSS — document chrome. Tokens only; no hard-coded colour or font.
# ---------------------------------------------------------------------------
STRUCT = r"""
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:88px}
body{margin:0;background:var(--surface-page);color:var(--text-body);font-family:var(--font-sans);
  font-size:var(--text-body1-size);line-height:var(--text-body1-line);-webkit-font-smoothing:antialiased}
a{color:var(--text-link);text-decoration:none}
a:hover{color:var(--text-link-hover);text-decoration:underline}
:focus-visible{outline:none;box-shadow:var(--focus-ring);border-radius:var(--radius-sm)}
h1,h2,h3,h4{margin:0;font-weight:var(--text-h2-weight);letter-spacing:var(--text-h2-tracking)}
p{margin:0 0 var(--space-3)}
p:last-child{margin-bottom:0}
code,kbd,samp,pre{font-family:var(--font-mono);font-size:var(--text-mono-size)}
::selection{background:var(--blue-100)}

/* ---- app bar ---- */
.bar{position:sticky;top:0;z-index:40;background:rgba(240,240,234,.86);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--border-default)}
.bar-in{max-width:1240px;margin:0 auto;padding:var(--space-2) var(--space-4);display:flex;align-items:center;
  gap:var(--space-3)}
.brand{display:flex;align-items:center;gap:var(--space-2);font-weight:700;letter-spacing:-.01em;
  color:var(--text-body);white-space:nowrap}
.brand:hover{text-decoration:none}
.mark{width:26px;height:26px;display:grid;place-items:center;flex:none}
.mark svg{width:100%;height:100%;display:block}
.brand .kind{font-family:var(--font-mono);font-size:var(--text-caption-size);font-weight:500;
  color:var(--text-secondary);padding:2px var(--space-2);border:1px solid var(--border-default);
  border-radius:var(--radius-full);background:var(--surface-card)}
.bar-tools{margin-left:auto;display:flex;align-items:center;gap:var(--space-2);flex-wrap:wrap;min-width:0}
/* 230px when there is room, and free to shrink when there is not: the filter box
   used to hold a fixed width and push the whole sticky bar past a narrow screen,
   which scrolled every page sideways by a few pixels. */
.search{position:relative;flex:0 1 230px;min-width:0}
.search input{height:var(--control-height-md);width:100%;min-width:0;border:1px solid var(--border-default);
  background:var(--surface-card);border-radius:var(--radius-md);padding:0 var(--space-3);font:inherit;
  font-size:var(--text-body2-size);color:var(--text-body);transition:border-color var(--duration-fast) var(--ease-out),
  box-shadow var(--duration-fast) var(--ease-out)}
.search input::placeholder{color:var(--text-muted)}
.search input:hover{border-color:var(--border-strong)}
.search input:focus{outline:none;border-color:var(--border-focus);box-shadow:var(--focus-ring)}
.btn{height:var(--control-height-md);display:inline-flex;align-items:center;gap:var(--space-1);
  padding:0 var(--space-3);border-radius:var(--radius-md);border:1px solid var(--border-default);
  background:var(--surface-card);color:var(--text-body);font-family:inherit;font-size:var(--text-button-size);
  font-weight:var(--text-button-weight);cursor:pointer;white-space:nowrap;
  transition:background var(--duration-fast) var(--ease-out),border-color var(--duration-fast) var(--ease-out),
  transform var(--duration-fast) var(--ease-spring),box-shadow var(--duration-fast) var(--ease-out)}
.btn:hover{background:var(--blue-50);border-color:var(--blue-200)}
.btn:active{transform:scale(.97)}
.btn.primary{background:var(--color-primary);border-color:var(--color-primary);color:var(--text-inverse)}
.btn.primary:hover{background:var(--color-primary-hover);border-color:var(--color-primary-hover)}
.btn.sm{height:var(--control-height-sm);font-size:var(--text-caption-size);padding:0 var(--space-2)}

/* ---- layout ---- */
.wrap{max-width:1240px;margin:0 auto;padding:var(--space-5) var(--space-4) var(--space-6);
  display:grid;grid-template-columns:236px minmax(0,1fr);gap:var(--space-5);align-items:start}
.toc{position:sticky;top:76px;max-height:calc(100vh - 100px);overflow:auto;padding-right:var(--space-2)}
.toc h4{font-size:var(--text-caption-size);text-transform:uppercase;letter-spacing:.12em;
  color:var(--text-muted);margin:0 0 var(--space-2);font-weight:600}
.toc a{display:flex;gap:var(--space-2);align-items:baseline;padding:6px var(--space-2);border-radius:var(--radius-sm);
  color:var(--text-secondary);font-size:var(--text-body2-size);line-height:1.35;
  transition:background var(--duration-fast) var(--ease-out),color var(--duration-fast) var(--ease-out)}
.toc a:hover{background:var(--surface-card);color:var(--text-body);text-decoration:none}
.toc a.on{background:var(--surface-card);color:var(--color-primary);font-weight:600;box-shadow:var(--shadow-1)}
.toc a .n{font-family:var(--font-mono);font-size:11px;color:var(--text-muted);flex:none}
.toc a.on .n{color:var(--color-primary)}
.toc .prog{margin-top:var(--space-3);padding:var(--space-3);background:var(--surface-card);
  border:1px solid var(--border-default);border-radius:var(--radius-md);box-shadow:var(--shadow-1)}
.toc .prog .lab{font-size:var(--text-caption-size);color:var(--text-secondary);display:flex;justify-content:space-between;
  margin-bottom:var(--space-2);gap:var(--space-2)}
.toc .prog .lab b{font-family:var(--font-mono);color:var(--text-body)}
.meter{height:6px;background:var(--surface-sunken);border-radius:var(--radius-full);overflow:hidden}
.meter i{display:block;height:100%;width:0;background:var(--color-primary);border-radius:var(--radius-full);
  transition:width var(--duration-slow) var(--ease-out-expo)}
.main{min-width:0;display:flex;flex-direction:column;gap:var(--space-4)}

/* ---- cards / sections ---- */
.block{background:var(--surface-card);border:1px solid var(--border-default);border-radius:var(--radius-md);
  box-shadow:var(--shadow-1);padding:var(--space-4);scroll-margin-top:88px;animation:zs-fade-up var(--duration-slow) var(--ease-out) both}
.block.flush{background:none;border:0;box-shadow:none;padding:0}
.block.flash{animation:zs-flash var(--duration-hero) var(--ease-out)}
.sec-head{display:flex;align-items:baseline;gap:var(--space-3);margin-bottom:var(--space-3)}
.sec-head .num{font-family:var(--font-mono);font-size:var(--text-caption-size);font-weight:700;
  color:var(--color-primary);background:var(--blue-50);border:1px solid var(--blue-100);
  border-radius:var(--radius-sm);padding:2px 6px;flex:none}
.sec-head h2{font-size:var(--text-h2-size);font-weight:var(--text-h2-weight);letter-spacing:var(--text-h2-tracking)}
.sec-head .sub{margin-left:auto;font-size:var(--text-caption-size);color:var(--text-muted);
  font-family:var(--font-mono);white-space:nowrap}
.lede{color:var(--text-secondary);margin-bottom:var(--space-3)}
.block.flush > .sec-head{padding:0 var(--space-1)}

/* ---- hero ---- */
.hero{background:var(--surface-card);border:1px solid var(--border-default);border-radius:var(--radius-lg);
  box-shadow:var(--shadow-2);padding:var(--space-6) var(--space-5);position:relative;overflow:hidden;
  display:flex;align-items:center;gap:var(--space-5)}
.hero-body{flex:1;min-width:0;position:relative;z-index:1}
.heroArt{flex:none;width:188px;max-width:26vw;position:relative;z-index:1;align-self:center}
.heroArt svg{width:100%;height:auto;display:block}
@media (max-width:720px){.heroArt{display:none}}
.hero::after{content:"";position:absolute;inset:auto -80px -120px auto;width:320px;height:320px;
  border-radius:50%;background:radial-gradient(circle,var(--blue-50),transparent 68%);pointer-events:none}
.hero .kicker{font-family:var(--font-mono);font-size:var(--text-caption-size);letter-spacing:.12em;
  text-transform:uppercase;color:var(--color-primary);margin-bottom:var(--space-2)}
.hero h1{font-size:var(--text-h1-size);font-weight:var(--text-h1-weight);line-height:var(--text-h1-line);
  letter-spacing:var(--text-h1-tracking);max-width:22ch}
.hero .lead{margin-top:var(--space-3);font-size:var(--text-subtitle-size);line-height:var(--text-subtitle-line);
  color:var(--text-secondary);max-width:70ch}
.metaGrid{margin-top:var(--space-5);display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:var(--space-3);position:relative}
.metaGrid div{border-left:2px solid var(--border-default);padding-left:var(--space-3)}
.metaGrid dt{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--text-muted);font-weight:600}
.metaGrid dd{margin:2px 0 0;font-size:var(--text-body2-size);font-weight:500}

/* ---- generic bits ---- */
.chip{display:inline-flex;align-items:center;gap:4px;font-family:var(--font-mono);font-size:11px;font-weight:500;
  padding:2px 7px;border-radius:var(--radius-full);border:1px solid var(--border-default);
  background:var(--surface-raised);color:var(--text-secondary);white-space:nowrap}
a.chip:hover{border-color:var(--blue-200);background:var(--blue-50);color:var(--color-primary);text-decoration:none}
.chip.must{background:var(--blue-50);border-color:var(--blue-200);color:var(--blue-700)}
.chip.should{background:var(--info-50);border-color:var(--info-200);color:var(--info-600)}
.chip.could{background:var(--surface-sunken);border-color:var(--border-strong);color:var(--text-secondary)}
.chip.wont{background:var(--red-100);border-color:var(--red-200);color:var(--red-600)}
.chip.ok{background:var(--status-success-bg);border-color:var(--green-200);color:var(--status-success)}
.chip.warn{background:var(--status-warning-bg);border-color:var(--amber-200);color:var(--status-warning)}
.chip.err{background:var(--status-error-bg);border-color:var(--red-200);color:var(--status-error)}
.chip.info{background:var(--status-info-bg);border-color:var(--info-200);color:var(--status-info)}
.chip.accent{background:var(--vermillion-100);border-color:var(--vermillion-400);color:var(--vermillion-600)}
.chips{display:flex;flex-wrap:wrap;gap:var(--space-1)}
.mono{font-family:var(--font-mono);font-size:var(--text-mono-size)}
.id{font-family:var(--font-mono);font-size:var(--text-body2-size);font-weight:500;color:var(--color-primary)}
.muted{color:var(--text-secondary)}
.tiny{font-size:var(--text-caption-size)}
hr{border:0;border-top:1px solid var(--border-default);margin:var(--space-4) 0}

.grid{display:grid;gap:var(--space-3)}
.g2{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(210px,1fr))}
.tile{background:var(--surface-raised);border:1px solid var(--border-default);border-radius:var(--radius-md);
  padding:var(--space-3);transition:transform var(--duration-base) var(--ease-out),box-shadow var(--duration-base) var(--ease-out),
  border-color var(--duration-base) var(--ease-out)}
.tile:hover{transform:translateY(-2px);box-shadow:var(--shadow-2);border-color:var(--blue-200)}
a.tile{display:block;color:inherit;text-decoration:none}
a.tile h4{color:var(--color-primary)}
a.tile:hover h4{text-decoration:underline}
a.tile:focus-visible{outline:2px solid var(--color-primary);outline-offset:2px}
.tile .k{font-family:var(--font-mono);font-size:11px;text-transform:uppercase;letter-spacing:.1em;
  color:var(--color-primary);font-weight:600}
.tile h4{margin:var(--space-1) 0 var(--space-2);font-size:var(--text-subtitle-size);font-weight:600}
.tile p{font-size:var(--text-body2-size);color:var(--text-secondary)}
.stat{text-align:left}
.stat .v{font-family:var(--font-mono);font-size:28px;font-weight:700;color:var(--color-primary);line-height:1}
.stat .l{font-size:var(--text-body2-size);font-weight:600;margin-top:var(--space-2)}
.stat .n{font-size:var(--text-caption-size);color:var(--text-secondary);margin-top:2px}

ul.plain,ol.plain{margin:0;padding-left:var(--space-4)}
ul.plain li,ol.plain li{margin-bottom:var(--space-2);font-size:var(--text-body1-size)}
ul.plain li:last-child,ol.plain li:last-child{margin-bottom:0}
ul.ticks{list-style:none;margin:0;padding:0}
ul.ticks li{position:relative;padding-left:var(--space-4);margin-bottom:var(--space-2);font-size:var(--text-body2-size)}
ul.ticks li::before{content:"";position:absolute;left:0;top:.45em;width:8px;height:8px;border-radius:var(--radius-sm);
  background:var(--blue-200);border:1px solid var(--blue-300)}
ul.ticks.ok li::before{background:var(--green-200);border-color:var(--green-600)}
ul.ticks.err li::before{background:var(--red-200);border-color:var(--red-600)}
dl.defs{margin:0;display:grid;gap:var(--space-2)}
dl.defs > div{border-left:2px solid var(--blue-200);padding-left:var(--space-3)}
dl.defs dt{font-weight:600;font-size:var(--text-body2-size)}
dl.defs dd{margin:2px 0 0;font-size:var(--text-body2-size);color:var(--text-secondary)}

.tblwrap{overflow-x:auto;border:1px solid var(--border-default);border-radius:var(--radius-md);background:var(--surface-card)}
table{border-collapse:collapse;width:100%;font-size:var(--text-body2-size)}
th,td{text-align:left;padding:var(--space-2) var(--space-3);border-bottom:1px solid var(--border-default);
  vertical-align:top}
th{background:var(--surface-raised);font-weight:600;font-size:var(--text-caption-size);text-transform:uppercase;
  letter-spacing:.06em;color:var(--text-secondary);white-space:nowrap;position:sticky;top:0;z-index:1}
tbody tr:last-child td{border-bottom:0}
tbody tr{transition:background var(--duration-fast) var(--ease-out)}
tbody tr:hover{background:var(--blue-50)}
td.m,th.m{font-family:var(--font-mono);font-size:var(--text-caption-size);white-space:nowrap}

pre.code{margin:0;background:var(--gray-900);color:#EDEDE8;border-radius:var(--radius-md);padding:var(--space-3);
  overflow-x:auto;font-size:var(--text-caption-size);line-height:1.6;border:1px solid var(--gray-800)}
pre.code .c{color:var(--gray-400)}
pre.code .k{color:var(--blue-300)}
pre.code .s{color:var(--vermillion-400)}
.codeblock{margin-bottom:var(--space-3)}
.codeblock:last-child{margin-bottom:0}
.codeblock .cap{display:flex;align-items:center;gap:var(--space-2);margin-bottom:var(--space-2);
  font-size:var(--text-caption-size);color:var(--text-secondary)}
.codeblock .cap b{font-family:var(--font-mono);font-size:var(--text-caption-size);color:var(--text-body);font-weight:600}
.note{border-left:3px solid var(--color-accent);background:var(--vermillion-100);padding:var(--space-3);
  border-radius:0 var(--radius-md) var(--radius-md) 0;font-size:var(--text-body2-size)}
.note b{color:var(--vermillion-600)}
.note.info{border-left-color:var(--status-info);background:var(--status-info-bg)}
.note.info b{color:var(--status-info)}
.note.ok{border-left-color:var(--status-success);background:var(--status-success-bg)}
.note.ok b{color:var(--status-success)}

/* ---- collapsible group ---- */
.group{border:1px solid var(--border-default);border-radius:var(--radius-md);background:var(--surface-card);
  margin-bottom:var(--space-3);overflow:hidden}
.group:last-child{margin-bottom:0}
.group > .gh{width:100%;display:flex;align-items:center;gap:var(--space-3);padding:var(--space-3);
  background:var(--surface-raised);border:0;border-bottom:1px solid transparent;cursor:pointer;text-align:left;
  font-family:inherit;transition:background var(--duration-fast) var(--ease-out)}
.group > .gh:hover{background:var(--blue-50)}
.group.open > .gh{border-bottom-color:var(--border-default)}
.group > .gh .key{font-family:var(--font-mono);font-size:var(--text-caption-size);font-weight:700;
  color:var(--color-primary);flex:none}
.group > .gh .t{font-weight:600;font-size:var(--text-body1-size)}
.group > .gh .d{color:var(--text-secondary);font-size:var(--text-body2-size);flex:1;min-width:0}
.group > .gh .cnt{margin-left:auto;font-family:var(--font-mono);font-size:11px;color:var(--text-muted);flex:none}
.group > .gh .car{flex:none;transition:transform var(--duration-base) var(--ease-spring);color:var(--text-muted)}
.group.open > .gh .car{transform:rotate(90deg)}
.group > .gb{display:none;padding:var(--space-3)}
.group.open > .gb{display:block;animation:zs-fade-in var(--duration-base) var(--ease-out)}

/* ---- requirement rows ---- */
.req{display:grid;grid-template-columns:auto 1fr auto;gap:var(--space-3);align-items:start;
  padding:var(--space-3);border:1px solid var(--border-default);border-radius:var(--radius-md);
  background:var(--surface-card);margin-bottom:var(--space-2);scroll-margin-top:96px;
  transition:box-shadow var(--duration-base) var(--ease-out),border-color var(--duration-base) var(--ease-out),
  transform var(--duration-base) var(--ease-out)}
.req:last-child{margin-bottom:0}
.req:hover{border-color:var(--blue-200);box-shadow:var(--shadow-2);transform:translateY(-1px)}
.req.flash{box-shadow:var(--shadow-glow)}
.req.done{background:var(--surface-raised)}
.rev{appearance:none;width:18px;height:18px;border:1px solid var(--border-strong);border-radius:var(--radius-sm);
  background:var(--surface-card);cursor:pointer;flex:none;margin-top:2px;position:relative;
  transition:background var(--duration-fast) var(--ease-out),border-color var(--duration-fast) var(--ease-out)}
.rev:hover{border-color:var(--color-primary)}
.rev:checked{background:var(--color-primary);border-color:var(--color-primary)}
.rev:checked::after{content:"";position:absolute;left:5px;top:1px;width:5px;height:10px;
  border:solid var(--text-inverse);border-width:0 2px 2px 0;transform:rotate(42deg)}
.rev:focus-visible{box-shadow:var(--focus-ring)}
.req .hd{display:flex;align-items:center;gap:var(--space-2);flex-wrap:wrap;margin-bottom:var(--space-1)}
.req .hd .ttl{font-weight:600}
.req .tx{font-size:var(--text-body2-size);color:var(--text-body)}
.req .nt{margin-top:var(--space-2);font-size:var(--text-caption-size);color:var(--text-secondary);
  border-left:2px solid var(--border-default);padding-left:var(--space-2)}
.req .side{display:flex;flex-direction:column;align-items:flex-end;gap:var(--space-1)}
.anchor{opacity:0;font-family:var(--font-mono);font-size:11px;color:var(--text-muted);transition:opacity var(--duration-fast)}
.req:hover .anchor,.story:hover .anchor{opacity:1}

/* ---- story / use-case / ADR cards ---- */
.story{border:1px solid var(--border-default);border-radius:var(--radius-md);background:var(--surface-card);
  padding:var(--space-3);margin-bottom:var(--space-3);scroll-margin-top:96px;
  transition:box-shadow var(--duration-base) var(--ease-out),border-color var(--duration-base) var(--ease-out)}
.story:last-child{margin-bottom:0}
.story:hover{border-color:var(--blue-200);box-shadow:var(--shadow-2)}
.story.flash{box-shadow:var(--shadow-glow)}
.story > .sh{display:flex;align-items:center;gap:var(--space-2);flex-wrap:wrap;margin-bottom:var(--space-2)}
.story > .sh .ttl{font-weight:600;font-size:var(--text-subtitle-size)}
.story .narr{background:var(--blue-50);border:1px solid var(--blue-100);border-radius:var(--radius-md);
  padding:var(--space-3);font-size:var(--text-body2-size);margin-bottom:var(--space-3)}
.story .narr b{color:var(--blue-700)}
.scn{border-top:1px solid var(--border-default);padding-top:var(--space-2);margin-top:var(--space-2)}
.scn .sid{font-family:var(--font-mono);font-size:11px;color:var(--color-primary);font-weight:600}
.scn .st{font-weight:600;font-size:var(--text-body2-size);margin-bottom:var(--space-2)}
.gwt{display:grid;grid-template-columns:auto 1fr;gap:var(--space-1) var(--space-3);font-size:var(--text-body2-size)}
.gwt b{font-family:var(--font-mono);font-size:11px;color:var(--text-secondary);text-transform:uppercase;
  letter-spacing:.06em;padding-top:2px}
.uc{display:grid;gap:var(--space-2);font-size:var(--text-body2-size)}
.uc .row{display:grid;grid-template-columns:120px 1fr;gap:var(--space-3)}
.uc .row > b{font-size:var(--text-caption-size);text-transform:uppercase;letter-spacing:.06em;
  color:var(--text-secondary);font-weight:600}
.uc ol{margin:0;padding-left:var(--space-4)}
.uc ol li{margin-bottom:var(--space-1)}
.adr{display:grid;gap:var(--space-2);font-size:var(--text-body2-size)}
.adr .row{display:grid;grid-template-columns:110px 1fr;gap:var(--space-3);align-items:start}
.adr .row > b{font-size:var(--text-caption-size);text-transform:uppercase;letter-spacing:.06em;
  color:var(--text-secondary);font-weight:600}
.adr .dec{background:var(--blue-50);border:1px solid var(--blue-100);border-radius:var(--radius-md);
  padding:var(--space-2) var(--space-3);font-weight:500}

/* ---- tactile editorial art ----
   Diagrams are drawn as photographed model-shop objects: one soft daylight from
   the upper left, matte materials, real contact shadows, hairline blueprint-blue
   line work. Motion runs only while the figure is on screen, and never under
   prefers-reduced-motion — the finished state is the default state, so the art
   is complete even if the script never runs. */
.artfig{margin:0 0 var(--space-4)}
.artfig:last-child{margin-bottom:0}
.artwrap{overflow-x:auto;border:1px solid var(--border-default);border-radius:var(--radius-md);
  background:var(--surface-card);box-shadow:var(--shadow-1)}
.zsart{display:block;width:100%;min-width:672px;height:auto;font-family:var(--font-sans);
  shape-rendering:geometricPrecision;isolation:isolate}
.zsart text{-webkit-font-smoothing:antialiased}
.artkey{display:grid;grid-template-columns:repeat(auto-fit,minmax(212px,1fr));
  gap:var(--space-2) var(--space-4);margin-top:var(--space-3)}
.artkey .ki{display:flex;gap:var(--space-2)}
.artkey .kn{font-family:var(--font-mono);font-size:11px;font-weight:500;color:var(--color-primary);
  flex:none;min-width:1.5em;padding-top:2px}
.artkey b{display:block;font-size:var(--text-body2-size);font-weight:600}
.artkey p{margin:1px 0 0;font-size:var(--text-caption-size);line-height:1.45;color:var(--text-secondary)}
.artnote{margin-top:var(--space-2);font-size:var(--text-caption-size);color:var(--text-muted)}
@keyframes zsart-set{from{opacity:0;transform:translateY(-34px)}to{opacity:1;transform:none}}
@keyframes zsart-land{from{opacity:0;transform:scale(1.7)}to{opacity:1;transform:none}}
@keyframes zsart-ink{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}
@keyframes zsart-rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
/* The sheen is 34% as wide as the face it crosses, so it must travel 100/34 =
   294% of its own width to leave the far edge. It used to stop at 260% and park
   a visible sliver on the right arris for the rest of the cycle, then snap back. */
@keyframes zsart-sheen{0%,6%{transform:translateX(-140%)}52%,100%{transform:translateX(310%)}}
.zsart .sh,.zsart .gloss{transform-box:fill-box;transform-origin:center}
.zsart.in .hd{animation:zsart-rise .62s var(--ease-out) both}
.zsart.in .rod{animation:zsart-ink 1.15s var(--ease-out-expo) both;animation-delay:.12s}
.zsart.in .sh{animation:zsart-land .58s var(--ease-out) both;animation-delay:calc(var(--i)*.105s + .34s)}
.zsart.in .obj{animation:zsart-set .8s var(--ease-spring) both;animation-delay:calc(var(--i)*.105s + .26s)}
.zsart.in .lab{animation:zsart-rise .52s var(--ease-out) both;animation-delay:calc(var(--i)*.105s + .52s)}
.zsart.in .cue{animation:zsart-ink .72s var(--ease-out) both;animation-delay:calc(var(--i)*.105s + .72s)}
.zsart.in .gloss{animation:zsart-sheen 7.5s var(--ease-in-out) 2.1s infinite}
@media (prefers-reduced-motion:reduce){.zsart *{animation:none!important}}

/* ---- playbook steps ---- */
.step{border:1px solid var(--border-default);border-radius:var(--radius-md);background:var(--surface-card);
  margin-bottom:var(--space-3);overflow:hidden;scroll-margin-top:96px}
.step:last-child{margin-bottom:0}
.step.flash{box-shadow:var(--shadow-glow)}
.step > .sh{display:flex;align-items:center;gap:var(--space-3);padding:var(--space-3);background:var(--surface-raised);
  border-bottom:1px solid var(--border-default)}
.step > .sh .n{width:30px;height:30px;border-radius:var(--radius-full);background:var(--color-primary);
  color:var(--text-inverse);display:grid;place-items:center;font-family:var(--font-mono);font-size:var(--text-caption-size);
  font-weight:700;flex:none}
.step > .sh .t{font-weight:600;font-size:var(--text-subtitle-size)}
.step > .sb{padding:var(--space-3);display:grid;gap:var(--space-3)}
.lane{border-left:3px solid var(--border-default);padding-left:var(--space-3)}
.lane > .lh{font-family:var(--font-mono);font-size:11px;text-transform:uppercase;letter-spacing:.1em;
  font-weight:700;margin-bottom:var(--space-2)}
.lane.do{border-left-color:var(--color-primary)}
.lane.do > .lh{color:var(--color-primary)}
.lane.gate{border-left-color:var(--status-success)}
.lane.gate > .lh{color:var(--status-success)}
.lane.stop{border-left-color:var(--status-error)}
.lane.stop > .lh{color:var(--status-error)}
/* The execution-instructions control.
   It used to be a folded lane whose summary was small caption text with a
   pseudo-element triangle. The owner reviewed it and could not tell that it
   opened, or that a prompt was what it held. So it is a control now: a boxed
   row that names what it holds, carries a caret, lights on hover, and keeps its
   copy button visible while shut — because copying without reading is what a
   reader actually wants from a block they are never going to read on screen
   (FR-EXE-15, amended). */
.pf{border:1px solid var(--blue-100);border-radius:var(--radius-md);background:var(--blue-50);
  margin:var(--space-2) 0}
.pf > summary{display:flex;align-items:center;gap:var(--space-2);padding:var(--space-2) var(--space-3);
  cursor:pointer;list-style:none}
.pf > summary::-webkit-details-marker{display:none}
.pf > summary:hover{background:var(--blue-100);border-radius:var(--radius-md)}
.pf[open] > summary{border-bottom:1px solid var(--blue-100);border-radius:var(--radius-md) var(--radius-md) 0 0}
.pf .car{flex:none;color:var(--color-primary);transition:transform var(--duration-base) var(--ease-spring)}
.pf[open] .car{transform:rotate(90deg)}
.pf .pft{flex:1 1 auto;min-width:0;font-family:var(--font-mono);font-size:11px;text-transform:uppercase;
  letter-spacing:.1em;font-weight:700;color:var(--color-primary)}
.pf > summary .copy{flex:none}
.pf > pre.code{margin:var(--space-3)}
.lane.why{border-left-color:var(--color-accent)}
.lane.why > .lh{color:var(--vermillion-600)}

/* ---- milestone tree ---- */
.ms{border:1px solid var(--border-default);border-radius:var(--radius-md);background:var(--surface-card);
  margin-bottom:var(--space-3);overflow:hidden;scroll-margin-top:96px}
.ms > .mh{display:flex;align-items:center;gap:var(--space-3);padding:var(--space-3);cursor:pointer;
  background:var(--surface-raised);border:0;width:100%;text-align:left;font-family:inherit}
.ms > .mh:hover{background:var(--blue-50)}
.ms > .mh .t{font-weight:600;font-size:var(--text-subtitle-size)}
.ms > .mb{display:none;padding:var(--space-3);border-top:1px solid var(--border-default)}
.ms.open > .mb{display:block}
/* Phases and tasks fold the same way milestones always did. A plan is
   navigated, not read end to end: with every level expanded, one milestone
   opened three phases, twelve tasks, thirty-six red/green/refactor lines and a
   hundred criteria at once, and finding anything in it meant scrolling past all
   of them (FR-SPC-10, amended). */
.ph{border:1px solid var(--border-default);border-radius:var(--radius-md);margin-bottom:var(--space-3);
  background:var(--surface-raised);scroll-margin-top:96px}
.ph:last-child{margin-bottom:0}
.ph > .phh{padding:var(--space-2) var(--space-3);
  display:flex;gap:var(--space-2);align-items:center;flex-wrap:wrap;cursor:pointer;
  background:none;border:0;width:100%;text-align:left;font:inherit;color:inherit}
.ph > .phh:hover{background:var(--blue-50)}
.ph.open > .phh{border-bottom:1px solid var(--border-default)}
.ph > .phb{display:none;padding:var(--space-3);background:var(--surface-card);
  border-radius:0 0 var(--radius-md) var(--radius-md)}
.ph.open > .phb{display:block}
.task{border:1px solid var(--border-default);border-radius:var(--radius-md);padding:var(--space-3);
  margin-bottom:var(--space-2);background:var(--surface-card);scroll-margin-top:96px;
  transition:border-color var(--duration-base) var(--ease-out),box-shadow var(--duration-base) var(--ease-out)}
.task:last-child{margin-bottom:0}
.task:hover{border-color:var(--blue-200);box-shadow:var(--shadow-1)}
.task:hover .anchor{opacity:1}
.task.flash{box-shadow:var(--shadow-glow)}
.task > .thd{display:flex;align-items:center;gap:var(--space-2)}
.task > .thd > .hd{flex:1 1 auto;min-width:0;display:flex;gap:var(--space-2);align-items:center;
  flex-wrap:wrap;cursor:pointer;background:none;border:0;padding:0;font:inherit;color:inherit;
  text-align:left}
.task > .tb{display:none;margin-top:var(--space-2)}
.task.open > .tb{display:block}
.ms > .mh .car,.ph > .phh .car,.task > .thd > .hd .car{flex:none;color:var(--text-muted);
  transition:transform var(--duration-base) var(--ease-spring)}
.ms.open > .mh .car,.ph.open > .phh .car,.task.open > .thd > .hd .car{transform:rotate(90deg)}
.tdd{display:grid;gap:var(--space-1);margin-top:var(--space-2);font-size:var(--text-caption-size)}
.tdd > div{display:grid;grid-template-columns:64px 1fr;gap:var(--space-2)}
.tdd b{font-family:var(--font-mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em}
.tdd .r b{color:var(--status-error)}
.tdd .g b{color:var(--status-success)}
.tdd .f b{color:var(--color-primary)}
.crit{list-style:none;margin:var(--space-2) 0 0;padding:0;display:grid;gap:var(--space-1)}
.crit li{display:grid;grid-template-columns:auto auto 1fr;gap:var(--space-2);align-items:start;
  font-size:var(--text-caption-size)}
.crit .box{width:14px;height:14px;border:1px solid var(--border-strong);border-radius:3px;margin-top:2px;flex:none}
.crit .box.on{background:var(--color-primary);border-color:var(--color-primary)}
.wave{display:flex;gap:var(--space-2);align-items:center;padding:var(--space-2) var(--space-3);
  border:1px solid var(--border-default);border-radius:var(--radius-md);background:var(--surface-card);
  margin-bottom:var(--space-2)}
.wave .wn{font-family:var(--font-mono);font-size:var(--text-caption-size);font-weight:700;color:var(--color-primary);
  background:var(--blue-50);border:1px solid var(--blue-100);border-radius:var(--radius-sm);padding:2px 6px;flex:none}

/* ---- amendments ---- */
/* Set apart by a rule and a heading rather than woven into the text: a reader
   has to be able to see which words were frozen and which arrived later. */
.amended{margin-top:var(--space-3);padding-top:var(--space-2);
  border-top:1px solid var(--border-default)}
.amended > b{display:block;font-family:var(--font-mono);font-size:11px;
  text-transform:uppercase;letter-spacing:.1em;color:var(--text-muted)}
.amended .when{color:var(--color-primary)}

/* ---- filter state ---- */
.hidden{display:none !important}
.noRes{padding:var(--space-4);text-align:center;color:var(--text-secondary);font-size:var(--text-body2-size)}

/* ---- machine section ---- */
pre.spec{max-height:460px;overflow:auto}
footer.foot{max-width:1240px;margin:0 auto;padding:var(--space-4);color:var(--text-muted);
  font-size:var(--text-caption-size);border-top:1px solid var(--border-default)}
.docnav{display:flex;flex-wrap:wrap;gap:var(--space-2);margin-top:var(--space-3)}
.docnav a{font-size:var(--text-caption-size)}

@media (max-width:980px){
  .wrap{grid-template-columns:1fr;padding-top:var(--space-4)}
  .toc{position:static;max-height:none;order:-1}
  .toc .list{display:flex;flex-wrap:wrap;gap:var(--space-1)}
  .toc a{background:var(--surface-card);border:1px solid var(--border-default)}
  .req{grid-template-columns:auto 1fr}
  .req .side{flex-direction:row;grid-column:1/-1}
  .uc .row,.adr .row{grid-template-columns:1fr}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms !important;animation-iteration-count:1 !important;
    transition-duration:.01ms !important;scroll-behavior:auto !important}
}
@media print{
  .bar,.toc,.btn,.search{display:none !important}
  .wrap{display:block;max-width:none;padding:0}
  .block,.hero{break-inside:avoid;box-shadow:none;border-color:var(--gray-300)}
  .group > .gb{display:block !important}
  /* Everything the accordion folds is expanded on paper: a printed page has no
     controls, so content it hides is content it loses (FR-SPC-11). */
  .ms > .mb,.ph > .phb,.task > .tb{display:block !important}
  /* Instructions are the one exception, dropped rather than expanded. Paper
     cannot be copied from, and 173 sets of them would be the whole document. */
  .pf{display:none !important}
}
"""

# ---------------------------------------------------------------------------
# Runtime — renders the document from its embedded JSON, then wires interactivity.
# ---------------------------------------------------------------------------
RUNTIME = r"""
(function(){
"use strict";
var SPEC = JSON.parse(document.getElementById("__SPEC_ID__").textContent);
var DOC  = SPEC.document || {};
var NS   = "z2s:" + (DOC.slug || "doc");
var $    = function(s,r){return (r||document).querySelector(s);};
var $$   = function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s));};

function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
/* Inline markup for authored prose: **bold**, `code`, [text](href) */
function rich(s){
  return esc(s)
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,'<a href="$2">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")
    .replace(/`([^`]+)`/g,'<code class="mono">$1</code>');
}
function el(html){var t=document.createElement("template");t.innerHTML=html.trim();return t.content.firstElementChild;}
function cls(p){return String(p||"").toLowerCase().replace(/[^a-z]/g,"");}
function pill(text,kind){return '<span class="chip '+(kind||"")+'">'+esc(text)+"</span>";}
/* A closed-set value is stored as its id and read as the word a reader knows.
   The maps ride in the spec, built from the one legend the plan document also
   renders as a table, so a chip cannot drift from the table that defines it —
   which is exactly how the stories document came to spell e2e "end-to-end".

   One map per set, never merged: "auto" is an autonomy class AND a criterion
   kind, and it means a different word in each. */
function labelled(set,id,kind){
  var m=(SPEC.labels||{})[set]||{};
  return pill(m[id]||id,kind);
}
function idChip(id){
  /* Route a trace to the document that defines it: try the two-segment prefix
     (FR-DOC), then the one-segment prefix (ADR). An identifier defined in THIS
     document always wins, so same-document traces stay local. */
  var L = SPEC.links||{}, parts = String(id).split("-");
  var href = L[parts.slice(0,2).join("-")] || L[parts[0]] || null;
  var target = "#"+id;
  if(!document.getElementById(id) && href) target = href+"#"+id;
  return '<a class="chip" href="'+target+'">'+esc(id)+"</a>";
}
function traceChips(tr){
  if(!tr) return "";
  var out=[],order=["fr","nfr","adr","us","uc","cap","goal","bc","ul"];
  order.forEach(function(k){(tr[k]||[]).forEach(function(id){out.push(idChip(id));});});
  return out.length?'<div class="chips">'+out.join("")+"</div>":"";
}
function searchText(){return Array.prototype.slice.call(arguments).filter(Boolean).join(" ").toLowerCase();}

/* ================= tactile editorial art =================
   Every diagram in this set is drawn as a photographed model-shop object rather
   than an illustration: axonometric solids under one soft daylight from the
   upper left, matte materials, real contact shadows offset down-right, hairline
   blueprint-blue line work, generous margins on an ivory sweep.

   Material carries the meaning, and carries it identically across all ten
   documents — translucent acrylic for what is abstract and cheap to redo, dense
   basalt for what is human and irreversible, warm oak for structure that spans,
   terracotta for the one decisive piece, brushed steel for the armature the
   sequence is threaded onto. The accent never exceeds one object in a frame.

   The art is drawn from the same section data the key beneath it renders from,
   so the picture and the words cannot disagree. */
var ART_SEQ = 0;
var ART_BLUE = "#3E587E";
var ART_MAT = {
  oak:     {t:"#E8D5B6", f:"#D5BC96", s:"#BCA177", e:"#A3885F", fib:1},
  plaster: {t:"#F4F1E9", f:"#E6E2D7", s:"#D1CCC0", e:"#B6B1A5"},
  basalt:  {t:"#46453F", f:"#34332F", s:"#232220", e:"#131312", dark:1},
  acrylic: {t:"#E9EFF7", f:"#DBE4F0", s:"#C5D1E2", e:"#A6B7CE", glass:1},
  clay:    {t:"#E48D65", f:"#D0603C", s:"#AD492B", e:"#8C3B22", dark:1}
};
function artMat(k){
  return ART_MAT[k==="input"?"acrylic":k==="gate"?"basalt":k==="accent"?"clay":"oak"];
}
var ART_CUE = {gate:"A gate — nothing passes it unproven", accent:"The decisive piece"};
function n1(v){return Math.round(v*10)/10;}

function artDefs(u){
  return '<defs>'
  + '<linearGradient id="gd'+u+'" x1="0" y1="0" x2=".34" y2="1">'
    + '<stop offset="0" stop-color="#FCFAF6"/><stop offset=".54" stop-color="#F3EFE6"/>'
    + '<stop offset="1" stop-color="#E6E0D4"/></linearGradient>'
  + '<radialGradient id="gl'+u+'" cx=".18" cy=".06" r=".92">'
    + '<stop offset="0" stop-color="#FFFFFF" stop-opacity=".7"/>'
    + '<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient>'
  + '<linearGradient id="lt'+u+'" x1="0" y1="0" x2="1" y2="1">'
    + '<stop offset="0" stop-color="#FFFFFF" stop-opacity=".42"/>'
    + '<stop offset=".6" stop-color="#FFFFFF" stop-opacity="0"/>'
    + '<stop offset="1" stop-color="#000000" stop-opacity=".05"/></linearGradient>'
  + '<linearGradient id="dn'+u+'" x1="0" y1="0" x2=".22" y2="1">'
    + '<stop offset="0" stop-color="#FFFFFF" stop-opacity=".18"/>'
    + '<stop offset=".5" stop-color="#000000" stop-opacity="0"/>'
    + '<stop offset="1" stop-color="#000000" stop-opacity=".26"/></linearGradient>'
  + '<radialGradient id="sh'+u+'" cx=".5" cy=".5" r=".5">'
    + '<stop offset="0" stop-color="#3B3529" stop-opacity=".62"/>'
    + '<stop offset=".42" stop-color="#3B3529" stop-opacity=".3"/>'
    + '<stop offset="1" stop-color="#3B3529" stop-opacity="0"/></radialGradient>'
  + '<pattern id="fb'+u+'" width="6" height="3.4" patternUnits="userSpaceOnUse" patternTransform="rotate(-5)">'
    + '<path d="M0 .8H6M0 2.4H6" stroke="#8A7047" stroke-opacity=".3" stroke-width=".45"/></pattern>'
  + '<filter id="gn'+u+'" x="0" y="0" width="100%" height="100%">'
    + '<feTurbulence type="fractalNoise" baseFrequency=".92" numOctaves="4" seed="11" stitchTiles="stitch"/>'
    + '<feColorMatrix type="saturate" values="0"/></filter>'
  + '</defs>';
}

/* One axonometric solid, lit from the upper left: top face brightest, the front
   face turned toward the window, the right face in shade. Hairline joinery on
   every edge and a catch light along the top front arris. */
function artSolid(x, base, w, h, d, m, u, gid){
  var dx=d*0.62, dy=d*0.34, top=base-h;
  var P=function(a){return "M "+a.map(function(p){return n1(p[0])+" "+n1(p[1]);}).join(" L ")+" Z";};
  var fT=P([[x,top],[x+w,top],[x+w+dx,top-dy],[x+dx,top-dy]]);
  var fF=P([[x,top],[x+w,top],[x+w,base],[x,base]]);
  var fS=P([[x+w,top],[x+w+dx,top-dy],[x+w+dx,base-dy],[x+w,base]]);
  var op=m.glass?' opacity=".8"':"";
  var g='<path d="'+fS+'" fill="'+m.s+'"'+op+'/><path d="'+fF+'" fill="'+m.f+'"'+op+'/>'
       +'<path d="'+fT+'" fill="'+m.t+'"'+op+'/>';
  if(m.fib) g+='<path d="'+fT+'" fill="url(#fb'+u+')" opacity=".55"/>'
              +'<path d="'+fF+'" fill="url(#fb'+u+')" opacity=".34"/>';
  g+='<path d="'+fF+'" fill="url(#dn'+u+')"/><path d="'+fT+'" fill="url(#lt'+u+')"/>'
    +'<path d="'+fS+'" fill="#000000" opacity=".07"/>'
    +'<g fill="none" stroke="'+m.e+'" stroke-width=".8" stroke-opacity=".5" stroke-linejoin="round">'
    +'<path d="'+fT+'"/><path d="'+fF+'"/><path d="'+fS+'"/></g>'
    +'<path d="M '+n1(x)+" "+n1(top)+" L "+n1(x+w)+" "+n1(top)+'" fill="none" stroke="#FFFFFF" '
    +'stroke-opacity="'+(m.dark?".2":".6")+'" stroke-width="1.3" stroke-linecap="round"/>';
  if(m.glass){
    g+='<clipPath id="gc'+u+"-"+gid+'"><path d="'+fF+'"/></clipPath>'
      +'<g clip-path="url(#gc'+u+"-"+gid+')"><rect class="gloss" x="'+n1(x)+'" y="'+n1(top)+'" width="'
      +n1(w*0.34)+'" height="'+n1(h)+'" fill="#FFFFFF" opacity=".32"/></g>';
  }
  return g;
}

/* Contact shadow: a broad soft pool plus a tight dark core where the object
   actually meets the sweep, both offset down-right away from the light. */
function artShadow(x, base, w, d, u){
  var dx=d*0.62, dy=d*0.34;
  return '<ellipse cx="'+n1(x+w/2+dx*0.5+13)+'" cy="'+n1(base-dy*0.28+7)+'" rx="'+n1(w*0.8+24)
       +'" ry="'+n1(d*0.58+12)+'" fill="url(#sh'+u+')" opacity=".62"/>'
       +'<ellipse cx="'+n1(x+w/2+dx*0.42+4)+'" cy="'+n1(base-dy*0.14+2)+'" rx="'+n1(w*0.56)
       +'" ry="'+n1(d*0.3+4)+'" fill="url(#sh'+u+')" opacity=".9"/>'
       +'<ellipse cx="'+n1(x+w/2+dx*0.34)+'" cy="'+n1(base-dy*0.1)+'" rx="'+n1(w*0.5)
       +'" ry="'+n1(d*0.15+1.5)+'" fill="url(#sh'+u+')" opacity=".95"/>';
}

function artWrap(s,max){
  var w=String(s==null?"":s).split(/\s+/), L=[], c="";
  for(var i=0;i<w.length;i++){
    var t=c?c+" "+w[i]:w[i];
    if(t.length>max&&c){L.push(c);c=w[i];} else c=t;
  }
  if(c)L.push(c);
  return L;
}
function artLines(lines,x,y,lh,attrs){
  return lines.map(function(t,i){
    return '<text x="'+n1(x)+'" y="'+n1(y+i*lh)+'" '+attrs+">"+esc(t)+"</text>";}).join("");
}
function artHead(title,deck,padX){
  return '<g class="hd">'
    + artLines(artWrap(title,34), padX, 88, 42,
        'font-size="34" font-weight="400" letter-spacing="-.6" fill="#232322"')
    + artLines(artWrap(deck,74), padX, 126, 19, 'font-size="14.5" fill="#54524E"')
    + "</g>";
}
function artGround(W,H,u){
  return '<rect width="'+W+'" height="'+H+'" fill="url(#gd'+u+')"/>'
       + '<rect width="'+W+'" height="'+H+'" fill="url(#gl'+u+')"/>';
}
function artGrain(W,H,u){
  return '<rect width="'+W+'" height="'+H+'" filter="url(#gn'+u+')" opacity=".085" '
       + 'style="mix-blend-mode:overlay" pointer-events="none"/>';
}

/* A sequence: solids standing on the sweep in reading order, threaded onto one
   brushed-steel armature that draws itself left to right. */
function artFlow(f,title){
  var u=++ART_SEQ, steps=f.steps||[], n=steps.length||1;
  var W=1080, padX=56, d=30, dx=d*0.62, dy=d*0.34, base=418;
  var colW=(W-padX*2)/n;
  var bw=Math.max(62,Math.min(126,colW-34));
  var gap=Math.max(24,Math.min(46,colW-bw));
  var total=n*bw+(n-1)*gap;
  var x0=(W-total-dx)/2;
  var maxChars=Math.max(10,Math.round(bw/7.2));

  var labels=steps.map(function(st){
    if(st.branch) return st.branch.reduce(function(a,b,j){
      var L=artWrap(b.title,maxChars-2); L[0]="· "+L[0]; return a.concat(L);},[]);
    return artWrap(st.title,maxChars);
  });
  var maxLab=labels.reduce(function(a,l){return Math.max(a,l.length);},1);
  var H=Math.round(base+62+maxLab*19+22);

  var rodY=base-54-dy, rx0=x0+dx-26, rx1=x0+total+dx+26, rlen=rx1-rx0;
  var rod='<g stroke-linecap="round">'
    +'<line class="rod" style="--len:'+n1(rlen)+'" stroke-dasharray="'+n1(rlen)+'" x1="'+n1(rx0)+'" y1="'
      +n1(rodY)+'" x2="'+n1(rx1)+'" y2="'+n1(rodY)+'" stroke="#9AA0A1" stroke-width="7"/>'
    +'<line class="rod" style="--len:'+n1(rlen)+'" stroke-dasharray="'+n1(rlen)+'" x1="'+n1(rx0)+'" y1="'
      +n1(rodY-2.2)+'" x2="'+n1(rx1)+'" y2="'+n1(rodY-2.2)+'" stroke="#D8DBDB" stroke-width="2"/></g>';

  /* One callout per role, not per object: a label repeated down the row says
     nothing the first one did not. */
  var shadows="", objs="", labs="", cues="", ci=0, cued={};
  steps.forEach(function(st,i){
    var x=x0+i*(bw+gap), kind=st.kind||"", top;
    shadows+='<g class="sh" style="--i:'+i+'">'+artShadow(x,base,bw,d,u)+"</g>";
    if(st.branch){
      var bn=st.branch.length, sg=10, sh=Math.min(44,(96-(bn-1)*sg)/bn), g="";
      for(var k=0;k<bn;k++)
        g+=artSolid(x,base-k*(sh+sg),bw,sh,d,artMat(st.branch[k].kind||""),u,i+"-"+k);
      top=base-(bn-1)*(sh+sg)-sh;
      /* blueprint brace: these pieces are in the fixture at the same time */
      g+='<path d="M '+n1(x-14)+" "+n1(top)+" h -6 V "+n1(base)+' h 6" fill="none" stroke="'+ART_BLUE
        +'" stroke-width=".9" stroke-opacity=".55"/>';
      objs+='<g class="obj" style="--i:'+i+'">'+g+"</g>";
    } else {
      var h=kind==="accent"?118:kind==="gate"?100:kind==="input"?76:88;
      top=base-h;
      objs+='<g class="obj" style="--i:'+i+'">'+artSolid(x,base,bw,h,d,artMat(kind),u,i)+"</g>";
      if(ART_CUE[kind]&&!cued[kind]&&ci<3){
        cued[kind]=1;
        var cy0=202+ci*28, lx=x+bw*0.62+dx*0.62, ty=top-dy-4;
        var dir=(x>W*0.55)?-1:1, jog=15*dir, len=Math.abs(ty-cy0)+15;
        cues+='<g class="cue" style="--i:'+i+";--len:"+n1(len)+'">'
          +'<path d="M '+n1(lx)+" "+n1(ty)+" V "+n1(cy0)+" h "+n1(jog)+'" fill="none" stroke="'+ART_BLUE
          +'" stroke-width=".9" stroke-opacity=".7" stroke-dasharray="'+n1(len)+'"/>'
          +'<circle cx="'+n1(lx)+'" cy="'+n1(ty)+'" r="2.6" fill="'+ART_BLUE+'"/>'
          +'<text x="'+n1(lx+jog+4*dir)+'" y="'+n1(cy0+4.5)+'" text-anchor="'+(dir<0?"end":"start")
          +'" font-size="13" font-weight="500" fill="'+ART_BLUE+'">'+esc(ART_CUE[kind])+"</text></g>";
        ci++;
      }
    }
    var cx=x+bw/2+dx*0.5;
    labs+='<g class="lab" style="--i:'+i+'">'
      +'<circle cx="'+n1(cx)+'" cy="'+n1(base+30)+'" r="9.5" fill="none" stroke="'+ART_BLUE
        +'" stroke-width=".9" stroke-opacity=".55"/>'
      +'<text x="'+n1(cx)+'" y="'+n1(base+34.2)+'" text-anchor="middle" font-size="11.5" '
      +'font-weight="600" fill="'+ART_BLUE+'">'+(i+1)+"</text>"
      +artLines(labels[i],cx,base+62,19,
                'text-anchor="middle" font-size="14.5" font-weight="500" fill="'+ART_BLUE+'"')
      +"</g>";
  });

  return '<svg class="zsart" viewBox="0 0 '+W+" "+H+'" preserveAspectRatio="xMidYMid meet" role="img" '
    +'aria-label="'+esc(title||"Diagram")+'">'+artDefs(u)+artGround(W,H,u)
    +artHead(title,f.caption||"",padX)+rod+shadows+objs+cues+labs+artGrain(W,H,u)+"</svg>";
}

/* The wave schedule as a flight of stairs: one tread per wave, the milestones
   that may run together resting on it. Nothing stands on a tread until every
   tread below it is in place. */
function artWaves(waves,title,intro){
  var u=++ART_SEQ, n=(waves||[]).length||1;
  var W=1080, padX=56, H=566, d=26, dx=d*0.62, dy=d*0.34;
  var tw=Math.max(58,Math.min(104,(W-padX*2-dx-30)/n));
  var rise=22, ground=468, hBase=38;
  var x0=(W-(n*tw+dx))/2;

  var shadows="", objs="", labs="";
  (waves||[]).forEach(function(w,i){
    var x=x0+i*tw, h=hBase+i*rise, top=ground-h, last=(i===n-1);
    if(i===0) shadows+='<g class="sh" style="--i:0">'+artShadow(x0,ground,n*tw,d,u)+"</g>";
    var g=artSolid(x,ground,tw,h,d,ART_MAT.plaster,u,"t"+i);
    var cnt=w.length||1, cw=Math.max(24,Math.min(46,(tw-14)/cnt-7));
    var sx=x+dx*0.45+(tw-(cnt*cw+(cnt-1)*7))/2, cb=top-dy*0.45;
    w.forEach(function(id,j){
      var bx=sx+j*(cw+7);
      g+=artSolid(bx,cb,cw,30,d*0.7,last?ART_MAT.clay:ART_MAT.oak,u,"m"+i+"-"+j);
      g+='<text x="'+n1(bx+cw/2)+'" y="'+n1(cb-9)+'" text-anchor="middle" font-size="11" '
        +'font-weight="600" fill="'+(last?"#FFF4EE":"#3A3A38")+'">'+esc(id)+"</text>";
    });
    objs+='<g class="obj" style="--i:'+i+'">'+g+"</g>";
    labs+='<g class="lab" style="--i:'+i+'">'
      +'<circle cx="'+n1(x+tw/2)+'" cy="'+n1(ground+28)+'" r="9.5" fill="none" stroke="'+ART_BLUE
        +'" stroke-width=".9" stroke-opacity=".55"/>'
      +'<text x="'+n1(x+tw/2)+'" y="'+n1(ground+32.2)+'" text-anchor="middle" font-size="11.5" '
      +'font-weight="600" fill="'+ART_BLUE+'">'+(i+1)+"</text></g>";
  });
  /* One callout, anchored to a middle tread where the frame is open — the top
     right is where the tallest tread and its accent block already live. */
  var ci=Math.min(n-1,2), cx=x0+ci*tw+tw*0.07;
  var ty=ground-hBase-ci*rise, cy0=252, len=Math.abs(ty-cy0)+16;
  var cue='<g class="cue" style="--i:'+ci+";--len:"+n1(len)+'">'
    +'<path d="M '+n1(cx)+" "+n1(ty)+" V "+n1(cy0)+' h 16" fill="none" stroke="'+ART_BLUE
    +'" stroke-width=".9" stroke-opacity=".7" stroke-dasharray="'+n1(len)+'"/>'
    +'<circle cx="'+n1(cx)+'" cy="'+n1(ty)+'" r="2.6" fill="'+ART_BLUE+'"/>'
    +'<text x="'+n1(cx+20)+'" y="'+n1(cy0+4.5)+'" font-size="13" font-weight="500" '
    +'fill="'+ART_BLUE+'">Every tread rests on the one below it</text></g>';
  labs+='<g class="lab" style="--i:'+n+'"><text x="'+n1(x0)+'" y="'+n1(ground+62)+'" font-size="13" '
    +'fill="#7A776F">Wave</text></g>';

  return '<svg class="zsart" viewBox="0 0 '+W+" "+H+'" preserveAspectRatio="xMidYMid meet" role="img" '
    +'aria-label="'+esc(title||"Execution waves")+'">'+artDefs(u)+artGround(W,H,u)
    +artHead(title,intro||"",padX)+shadows+objs+cue+labs+artGrain(W,H,u)+"</svg>";
}

/* The key: every object in the picture, numbered, with the words the picture
   cannot hold. Branch members take a letter suffix. */
function artKey(steps){
  var i=0;
  return '<div class="artkey">'+(steps||[]).map(function(st){
    i++;
    var one=function(nm,t,dsc){
      return '<div class="ki"><span class="kn">'+nm+'</span><div><b>'+esc(t)+"</b>"+
        (dsc?"<p>"+rich(dsc)+"</p>":"")+"</div></div>";};
    if(st.branch) return st.branch.map(function(b,j){
      return one(i+String.fromCharCode(97+j), b.title, b.desc);}).join("");
    return one(i, st.title, st.desc);
  }).join("")+"</div>";
}

/* ---------------- section renderers ---------------- */
var R = {};

R.prose = function(s){
  var h="";
  if(s.body) h += s.body.map(function(p){return "<p>"+rich(p)+"</p>";}).join("");
  if(s.highlights) h += '<div class="grid g2" style="margin-top:var(--space-3)">'+s.highlights.map(function(t){
    return '<div class="tile">'+(t.label?'<div class="k">'+esc(t.label)+"</div>":"")+
      "<h4>"+esc(t.title)+"</h4><p>"+rich(t.text)+"</p></div>";}).join("")+"</div>";
  if(s.note) h += '<div class="note '+(s.note.kind||"")+'" style="margin-top:var(--space-3)"><b>'+
    esc(s.note.label||"Note")+"</b> "+rich(s.note.text)+"</div>";
  return h;
};

R.stats = function(s){
  return '<div class="grid g3">'+s.items.map(function(t){
    return '<div class="tile stat"><div class="v">'+esc(t.value)+'</div><div class="l">'+esc(t.label)+"</div>"+
      (t.note?'<div class="n">'+rich(t.note)+"</div>":"")+"</div>";}).join("")+"</div>";
};

R.list = function(s){
  var h = s.intro?'<p class="lede">'+rich(s.intro)+"</p>":"";
  function render(items,ordered){
    var tag = ordered?"ol":"ul";
    return "<"+tag+' class="plain">'+items.map(function(i){
      if(typeof i==="string") return "<li>"+rich(i)+"</li>";
      return "<li><strong>"+esc(i.title)+"</strong>"+(i.text?" — "+rich(i.text):"")+"</li>";
    }).join("")+"</"+tag+">";
  }
  if(s.groups) h += '<div class="grid g2">'+s.groups.map(function(g){
    return '<div class="tile"><div class="k">'+esc(g.label||"")+"</div><h4>"+esc(g.title)+"</h4>"+
      render(g.items,g.ordered)+"</div>";}).join("")+"</div>";
  else h += render(s.items,s.ordered);
  return h;
};

R.defs = function(s){
  return (s.intro?'<p class="lede">'+rich(s.intro)+"</p>":"")+'<dl class="defs">'+s.items.map(function(i){
    return "<div><dt>"+rich(i.term)+"</dt><dd>"+rich(i.def)+"</dd></div>";}).join("")+"</dl>";
};

R.table = function(s){
  var h = s.intro?'<p class="lede">'+rich(s.intro)+"</p>":"";
  var mono = s.mono||[];
  h += '<div class="tblwrap"><table><thead><tr>'+s.columns.map(function(c,i){
    return "<th"+(mono.indexOf(i)>=0?' class="m"':"")+">"+esc(c)+"</th>";}).join("")+"</tr></thead><tbody>";
  h += s.rows.map(function(r){
    return '<tr data-search="'+esc(r.join(" ").toLowerCase())+'">'+r.map(function(c,i){
      return "<td"+(mono.indexOf(i)>=0?' class="m"':"")+">"+rich(c)+"</td>";}).join("")+"</tr>";}).join("");
  return h+"</tbody></table></div>";
};

R.cards = function(s){
  return (s.intro?'<p class="lede">'+rich(s.intro)+"</p>":"")+'<div class="grid '+(s.cols||"g2")+'" data-catalog>'+
    s.items.map(function(t){
      var meta = (t.meta||[]).map(function(m){return "<div><dt>"+esc(m.k)+"</dt><dd>"+rich(m.v)+"</dd></div>";}).join("");
      var tag = t.href ? 'a class="tile lnk" href="'+esc(t.href)+'"' : 'div class="tile"';
      return "<"+tag+' id="'+(t.id||"")+'" data-search="'+esc(searchText(t.id,t.title,t.text,t.kicker))+'">'+
        (t.kicker?'<div class="k">'+esc(t.kicker)+"</div>":"")+
        "<h4>"+(t.id?'<span class="id">'+esc(t.id)+"</span> ":"")+esc(t.title)+"</h4>"+
        (t.text?"<p>"+rich(t.text)+"</p>":"")+
        (meta?'<dl class="metaGrid" style="margin-top:var(--space-2)">'+meta+"</dl>":"")+
        ((t.items||[]).length?'<ul class="ticks" style="margin-top:var(--space-2)">'+
          t.items.map(function(x){return "<li>"+rich(x)+"</li>";}).join("")+"</ul>":"")+
        (t.traces?traceChips(t.traces):"")+(t.href?"</a>":"</div>");}).join("")+"</div>";
};

R.flow = function(s){
  var h = s.intro?'<p class="lede">'+rich(s.intro)+"</p>":"";
  h += (s.flows||[]).map(function(f){
    return '<figure class="artfig"><div class="artwrap">'+artFlow(f, f.name||s.title)+"</div>"+
      artKey(f.steps)+"</figure>";
  }).join("");
  return h;
};

R.code = function(s){
  return (s.intro?'<p class="lede">'+rich(s.intro)+"</p>":"")+(s.blocks||[]).map(function(b){
    return '<div class="codeblock">'+(b.title?'<div class="cap"><b>'+esc(b.title)+"</b>"+
      (b.note?'<span class="muted">'+rich(b.note)+"</span>":"")+"</div>":"")+
      '<pre class="code">'+esc(b.code)+"</pre></div>";}).join("");
};

/* What has changed about a requirement since it was frozen, BELOW the original
   and never in place of it (FR-AMD-04). The original is what every existing
   trace, test and decision was written against, so it is left exactly as it was
   and the amendment is added under a rule — a reader can see both what it said
   and what moved, and the identifier never has to be retired to say so. */
function amended(item){
  var found = item.amendments||[];
  if(!found.length) return "";
  return '<div class="amended"><b>Amended since</b><ul class="ticks">'+
    found.map(function(one){
      return '<li><span class="when mono tiny">'+esc(one.date)+"</span> "+
        rich(one.text)+"</li>";}).join("")+"</ul></div>";
}

R.requirements = function(s){
  var areas = s.areas||[], items = s.items||[];
  var legend = '<div class="chips" style="margin-bottom:var(--space-3)">'+
    ["Must","Should","Could","Won't"].map(function(p){
      return '<button class="chip '+cls(p)+' prio" data-prio="'+p+'" aria-pressed="true">'+esc(p)+" &middot; "+
        items.filter(function(r){return r.priority===p;}).length+"</button>";}).join("")+"</div>";
  var body = areas.map(function(a){
    var rows = items.filter(function(r){return r.area===a.key;});
    return '<div class="group open" data-group>'+
      '<button class="gh" type="button"><span class="car">&#9656;</span><span class="key">'+esc(a.key)+
      '</span><span class="t">'+esc(a.name)+'</span><span class="d">'+rich(a.description||"")+
      '</span><span class="cnt">'+rows.length+"</span></button>"+
      '<div class="gb">'+rows.map(function(r){
        return '<div class="req" id="'+esc(r.id)+'" data-prio="'+esc(r.priority)+'" data-search="'+
          esc(searchText(r.id,r.title,r.text,r.notes,(r.tags||[]).join(" "),
                         (r.amendments||[]).map(function(a){return a.text;}).join(" ")))+'">'+
          '<input class="rev" type="checkbox" data-rev="'+esc(r.id)+'" aria-label="Reviewed '+esc(r.id)+'" />'+
          '<div><div class="hd"><span class="id">'+esc(r.id)+'</span><span class="ttl">'+esc(r.title)+"</span>"+
          (r.tags||[]).map(function(t){return pill(t);}).join("")+"</div>"+
          '<div class="tx">'+rich(r.text)+"</div>"+
          (r.notes?'<div class="nt">'+rich(r.notes)+"</div>":"")+
          amended(r)+
          (r.traces?'<div style="margin-top:var(--space-2)">'+traceChips(r.traces)+"</div>":"")+"</div>"+
          '<div class="side">'+pill(r.priority,cls(r.priority))+
          '<a class="anchor" href="#'+esc(r.id)+'">#</a></div>'+
          "</div>";
      }).join("")+"</div></div>";
  }).join("");
  return legend+'<div data-catalog>'+body+'</div><div class="noRes hidden">No entries match the current filter.</div>';
};

R.stories = function(s){
  return '<div data-catalog>'+(s.items||[]).map(function(st){
    var scn=(st.scenarios||[]).map(function(sc){
      return '<div class="scn"><div class="sid">'+esc(sc.id)+'</div><div class="st">'+esc(sc.title)+"</div>"+
        '<div class="gwt"><b>Given</b><span>'+rich(sc.given)+"</span>"+
        "<b>When</b><span>"+rich(sc.when)+"</span><b>Then</b><span>"+rich(sc.then)+"</span></div></div>";}).join("");
    return '<div class="story" id="'+esc(st.id)+'" data-prio="'+esc(st.priority||"Must")+'" data-search="'+
      esc(searchText(st.id,st.title,st.narrative,JSON.stringify(st.scenarios||[])))+'">'+
      '<div class="sh"><span class="id">'+esc(st.id)+'</span><span class="ttl">'+esc(st.title)+"</span>"+
      pill(st.priority||"Must",cls(st.priority||"Must"))+(st.role?pill(st.role):"")+
      (st.testLayers||[]).map(function(t){return labelled("testLayers",t,"info");}).join("")+
      '<a class="anchor" href="#'+esc(st.id)+'" style="margin-left:auto">#</a></div>'+
      (st.narrative?'<div class="narr">'+rich(st.narrative)+"</div>":"")+
      (st.traces?traceChips(st.traces):"")+scn+
      ((st.verify||[]).length?'<div class="scn"><div class="st">Also verify</div><ul class="ticks">'+
        st.verify.map(function(v){return "<li>"+rich(v)+"</li>";}).join("")+"</ul></div>":"")+
      "</div>";}).join("")+'</div><div class="noRes hidden">No entries match the current filter.</div>';
};

R.usecases = function(s){
  function steps(list,ordered){
    if(!list||!list.length) return '<span class="muted">—</span>';
    return ordered?"<ol>"+list.map(function(i){return "<li>"+rich(i)+"</li>";}).join("")+"</ol>":
      '<ul class="ticks">'+list.map(function(i){return "<li>"+rich(i)+"</li>";}).join("")+"</ul>";
  }
  return '<div data-catalog>'+(s.items||[]).map(function(u){
    return '<div class="story" id="'+esc(u.id)+'" data-prio="'+esc(u.priority||"Must")+'" data-search="'+
      esc(searchText(u.id,u.title,u.goal,u.actor,JSON.stringify(u.main||[])))+'">'+
      '<div class="sh"><span class="id">'+esc(u.id)+'</span><span class="ttl">'+esc(u.title)+"</span>"+
      pill(u.priority||"Must",cls(u.priority||"Must"))+
      '<a class="anchor" href="#'+esc(u.id)+'" style="margin-left:auto">#</a></div>'+
      '<div class="uc">'+
      '<div class="row"><b>Actor</b><span>'+rich(u.actor)+"</span></div>"+
      '<div class="row"><b>Goal</b><span>'+rich(u.goal)+"</span></div>"+
      '<div class="row"><b>Trigger</b><span>'+rich(u.trigger||"—")+"</span></div>"+
      '<div class="row"><b>Preconditions</b><span>'+steps(u.pre)+"</span></div>"+
      '<div class="row"><b>Main flow</b><span>'+steps(u.main,true)+"</span></div>"+
      '<div class="row"><b>Alternates</b><span>'+steps(u.alt)+"</span></div>"+
      '<div class="row"><b>Exceptions</b><span>'+steps(u.exc)+"</span></div>"+
      '<div class="row"><b>Postcondition</b><span>'+rich(u.post||"—")+"</span></div>"+
      (u.traces?'<div class="row"><b>Traces</b><span>'+traceChips(u.traces)+"</span></div>":"")+
      "</div></div>";}).join("")+'</div><div class="noRes hidden">No entries match the current filter.</div>';
};

R.decisions = function(s){
  return '<div data-catalog>'+(s.items||[]).map(function(d){
    return '<div class="story" id="'+esc(d.id)+'" data-search="'+
      esc(searchText(d.id,d.title,d.context,d.decision))+'">'+
      '<div class="sh"><span class="id">'+esc(d.id)+'</span><span class="ttl">'+esc(d.title)+"</span>"+
      pill(d.status||"Accepted","ok")+'<a class="anchor" href="#'+esc(d.id)+'" style="margin-left:auto">#</a></div>'+
      '<div class="adr">'+
      '<div class="row"><b>Context</b><span>'+rich(d.context)+"</span></div>"+
      '<div class="row"><b>Decision</b><div class="dec">'+rich(d.decision)+"</div></div>"+
      '<div class="row"><b>Alternatives</b><span>'+(d.alternatives||[]).map(function(a){
        return "<div>"+rich(a)+"</div>";}).join("")+"</span></div>"+
      '<div class="row"><b>Consequences</b><span>'+(d.consequences||[]).map(function(a){
        return "<div>"+rich(a)+"</div>";}).join("")+"</span></div>"+
      (d.traces?'<div class="row"><b>Traces</b><span>'+traceChips(d.traces)+"</span></div>":"")+
      "</div></div>";}).join("")+'</div><div class="noRes hidden">No entries match the current filter.</div>';
};

R.steps = function(s){
  return (s.intro?'<p class="lede">'+rich(s.intro)+"</p>":"")+'<div data-catalog>'+(s.groups||[]).map(function(g){
    return '<div class="group open" data-group><button class="gh" type="button"><span class="car">&#9656;</span>'+
      '<span class="key">'+esc(g.key||"")+'</span><span class="t">'+esc(g.title)+"</span>"+
      '<span class="d">'+rich(g.intro||"")+'</span><span class="cnt">'+(g.steps||[]).length+" steps</span></button>"+
      '<div class="gb">'+(g.steps||[]).map(function(st){
        var lanes="";
        if(st.body) lanes += '<div>'+st.body.map(function(p){return "<p>"+rich(p)+"</p>";}).join("")+"</div>";
        if(st.commands) lanes += '<div class="lane do"><div class="lh">Do</div><pre class="code">'+
          esc(st.commands.join("\n"))+"</pre></div>";
        if(st.prompt) lanes += '<div class="lane do"><div class="lh">Prompt</div><pre class="code">'+
          esc(st.prompt)+'</pre><button class="btn sm copy" data-copy="'+esc(st.id)+
          '" style="margin-top:var(--space-2)">Copy prompt</button></div>';
        if(st.produces) lanes += '<div class="lane"><div class="lh">Produces</div><ul class="ticks">'+
          st.produces.map(function(p){return "<li>"+rich(p)+"</li>";}).join("")+"</ul></div>";
        if(st.gate) lanes += '<div class="lane gate"><div class="lh">Gate</div><ul class="ticks ok">'+
          st.gate.map(function(p){return "<li>"+rich(p)+"</li>";}).join("")+"</ul></div>";
        if(st.stopif) lanes += '<div class="lane stop"><div class="lh">Stop if</div><ul class="ticks err">'+
          st.stopif.map(function(p){return "<li>"+rich(p)+"</li>";}).join("")+"</ul></div>";
        if(st.why) lanes += '<div class="lane why"><div class="lh">Why</div><p class="tiny">'+rich(st.why)+"</p></div>";
        return '<div class="step" id="'+esc(st.id)+'" data-search="'+
          esc(searchText(st.id,st.title,(st.body||[]).join(" "),(st.commands||[]).join(" ")))+'">'+
          '<div class="sh"><span class="n">'+esc(st.n||"")+'</span><span class="t">'+esc(st.title)+"</span>"+
          (st.owner?pill(st.owner,"info"):"")+'<a class="anchor" href="#'+esc(st.id)+'" style="margin-left:auto">#</a></div>'+
          '<div class="sb">'+lanes+"</div></div>";}).join("")+"</div></div>";
  }).join("")+'</div><div class="noRes hidden">No entries match the current filter.</div>';
};

/* One folded set of execution instructions, on the card of the unit it belongs
   to (FR-EXE-15). Built from `.lane.do`, `pre.code` and `.btn.sm.copy`, which
   the playbook's steps already use, so this needed no new styling beyond making
   the summary look clickable — and `wireCopy` finds the <pre> through the
   button's own parent, so it needed no new script at all.

   Shut by default: 173 sets of instructions rendered open would be a plan
   nobody can find inside its own document. */
function promptFold(id, label, body){
  if(!body) return "";
  /* The copy button lives INSIDE the summary, so it is reachable while the
     fold is shut — taking a prompt without reading it is the common case, and
     an operator should not have to expand five thousand words to get at them.
     `wireCopy` therefore looks for the <pre> in the whole fold rather than in
     the button's own parent, which is the one thing that must move with it. */
  return '<details class="pf" id="'+esc(id)+'">'+
    '<summary><span class="car">&#9656;</span><span class="pft">'+esc(label)+"</span>"+
    '<button class="btn sm copy" type="button">Copy prompt</button></summary>'+
    '<pre class="code">'+esc(body)+"</pre></details>";
}
/* The fold on a unit's own card. The element id is derived from the unit, never
   authored — and the unit's identifier is NOT the item's identifier, because an
   item carrying `id: "M1"` in a prompt list would declare M1 a second time in a
   set where the milestone's own page already declares it. */
function unitPrompt(id, label, body){ return promptFold("prompt-"+id, label, body); }

R.prompts = function(s){
  return (s.intro?'<p class="lede">'+rich(s.intro)+"</p>":"")+
    (s.items||[]).map(function(one){
      return promptFold(one.id, one.title, one.body);
    }).join("");
};

R.milestones = function(s){
  var STAT = s.statuses||{};
  function statChip(id){var m=STAT[id]||{};return pill(m.label||id,m.tone||"");}
  var h = s.intro?'<p class="lede">'+rich(s.intro)+"</p>":"";
  h += '<div data-catalog>'+(s.items||[]).map(function(m){
    var tasks=0, done=0;
    (m.phases||[]).forEach(function(p){(p.tasks||[]).forEach(function(t){tasks++; if(t.status==="passing") done++;});});
    return '<div class="ms" id="'+esc(m.id)+'" data-search="'+esc(searchText(m.id,m.title,m.goal))+'">'+
      '<button class="mh" type="button"><span class="car">&#9656;</span>'+
      '<span class="key id">'+esc(m.id)+'</span><span class="t">'+esc(m.title)+"</span>"+
      statChip(m.status)+'<span class="cnt mono tiny" style="margin-left:auto">'+done+"/"+tasks+" tasks</span></button>"+
      '<div class="mb">'+unitPrompt(m.id, "Execution prompt — "+m.id, m.prompt)+
      '<p class="lede">'+rich(m.goal||"")+"</p>"+
      (m.dependsOn&&m.dependsOn.length?'<div class="chips" style="margin-bottom:var(--space-3)">'+
        '<span class="tiny muted">Depends on</span>'+m.dependsOn.map(function(d){return idChip(d);}).join("")+"</div>":"")+
      (m.traces?'<div style="margin-bottom:var(--space-3)">'+traceChips(m.traces)+"</div>":"")+
      (m.phases||[]).map(function(p){
        return '<div class="ph" id="'+esc(p.id)+'"><button class="phh" type="button">'+
          '<span class="car">&#9656;</span><span class="id">'+esc(p.id)+
          '</span><strong>'+esc(p.title)+"</strong>"+
          (p.dependsOn&&p.dependsOn.length?'<span class="tiny muted">after '+p.dependsOn.join(", ")+"</span>":"")+
          '<span class="cnt mono tiny" style="margin-left:auto">'+(p.tasks||[]).length+" tasks</span>"+
          '</button><div class="phb">'+(p.summary?'<p class="tiny muted">'+rich(p.summary)+"</p>":"")+
          unitPrompt(p.id, "Execution prompt — "+p.id, p.prompt)+
          (p.tasks||[]).map(function(t){
            /* The anchor sits OUTSIDE the header button: an <a> inside a
               <button> is neither valid nor clickable, and making the header a
               real button is what gives the fold its keyboard handling free. */
            return '<div class="task" id="'+esc(t.id)+'" data-prio="'+esc(t.priority||"Must")+'" data-search="'+
              esc(searchText(t.id,t.title,t.summary))+'">'+
              '<div class="thd"><button class="hd" type="button">'+
              '<span class="car">&#9656;</span>'+
              '<span class="id">'+esc(t.id)+'</span><strong>'+esc(t.title)+"</strong>"+
              statChip(t.status)+pill(t.priority||"Must",cls(t.priority||"Must"))+
              (t.autonomy?labelled("autonomy",t.autonomy,"info"):"")+
              (t.layer?labelled("layers",t.layer):"")+
              (t.testLayers||[]).map(function(x){return labelled("testLayers",x);}).join("")+
              '</button><a class="anchor" href="#'+esc(t.id)+'">#</a></div>'+
              '<div class="tb">'+
              unitPrompt(t.id, "Execution prompt — "+t.id, t.prompt)+
              (t.summary?'<p class="tiny muted" style="margin-top:var(--space-2)">'+rich(t.summary)+"</p>":"")+
              (t.tdd?'<div class="tdd"><div class="r"><b>Red</b><span>'+rich(t.tdd.red)+"</span></div>"+
                '<div class="g"><b>Green</b><span>'+rich(t.tdd.green)+"</span></div>"+
                '<div class="f"><b>Refactor</b><span>'+rich(t.tdd.refactor)+"</span></div></div>":"")+
              ((t.criteria||[]).length?'<ul class="crit">'+t.criteria.map(function(c){
                return '<li><span class="box'+(c.done?" on":"")+'"></span>'+
                  '<span class="mono tiny">'+esc(c.id)+"</span><span>"+rich(c.text)+
                  /* Only the human-reviewed criteria are badged: an automated one is the
                     norm, and badging every criterion says nothing. The word still comes
                     from the legend, so it reads as the table spells it. */
                  (c.kind==="human-review"?" "+labelled("criterionKinds",c.kind,"warn"):"")+
                  "</span></li>";}).join("")+"</ul>":"")+
              (t.traces?'<div style="margin-top:var(--space-2)">'+traceChips(t.traces)+"</div>":"")+
              "</div></div>";}).join("")+
          ((p.completion||[]).length?'<div class="note info" style="margin-top:var(--space-3)"><b>Phase exit</b><ul class="ticks">'+
            p.completion.map(function(c){return "<li>"+rich(c)+"</li>";}).join("")+"</ul></div>":"")+
          "</div></div>";}).join("")+
      ((m.exit||[]).length?'<div class="note ok" style="margin-top:var(--space-3)"><b>Milestone exit</b><ul class="ticks ok">'+
        m.exit.map(function(c){return "<li>"+rich(c)+"</li>";}).join("")+"</ul></div>":"")+
      "</div></div>";}).join("")+"</div>";
  return h;
};

R.waves = function(s){
  return '<figure class="artfig"><div class="artwrap">'+artWaves(s.waves,s.title,s.intro)+"</div>"+
    '<div style="margin-top:var(--space-3)">'+(s.waves||[]).map(function(w,i){
      return '<div class="wave"><span class="wn">Wave '+(i+1)+'</span><div class="chips">'+
        w.map(function(id){return idChip(id);}).join("")+"</div></div>";}).join("")+"</div></figure>";
};

R.machine = function(s,specId){
  return '<p class="lede">'+rich(s.intro||"The complete specification below is the document's single source of truth — every section above is rendered from it at load time.")+"</p>"+
    '<div style="display:flex;gap:var(--space-2);margin-bottom:var(--space-3);flex-wrap:wrap">'+
    '<button class="btn sm" id="copySpec">Copy spec JSON</button>'+
    '<button class="btn sm" id="dlSpec">Download .json</button>'+
    '<span class="chip mono">'+esc(specId)+"</span></div>"+
    '<pre class="code spec" id="specOut"></pre>';
};

/* ---------------- page assembly ---------------- */
function buildHero(){
  var h = $("#hero");
  h.innerHTML = '<div class="kicker">'+esc(DOC.kicker||DOC.type||"")+"</div>"+
    "<h1>"+esc(DOC.title)+"</h1>"+
    (DOC.summary?'<p class="lead">'+rich(DOC.summary)+"</p>":"")+
    '<dl class="metaGrid">'+[
      ["Document type",DOC.type],["Version",DOC.version],["Status",DOC.status],
      ["Date",DOC.date],["Owner",DOC.owner],["Scope",DOC.releaseScope]
    ].filter(function(p){return p[1];}).map(function(p){
      return "<div><dt>"+esc(p[0])+"</dt><dd>"+esc(p[1])+"</dd></div>";}).join("")+"</dl>"+
    (DOC.scopeNote?'<div class="note info" style="margin-top:var(--space-4)"><b>Scope</b> '+rich(DOC.scopeNote)+"</div>":"");
}

function buildSections(){
  var main=$("#main"), toc=$("#tocList"), n=0;
  (SPEC.sections||[]).forEach(function(s){
    n++;
    var num=("0"+n).slice(-2);
    var sec=el('<section class="block'+(s.flush?" flush":"")+'" id="'+s.id+'"></section>');
    var head='<div class="sec-head"><span class="num">'+num+'</span><h2>'+esc(s.title)+"</h2>"+
      (s.badge?'<span class="sub">'+esc(s.badge)+"</span>":"")+"</div>";
    var fn=R[s.type];
    sec.innerHTML = head+(s.lede?'<p class="lede">'+rich(s.lede)+"</p>":"")+
      (fn?fn(s,SPEC.__specId):'<p class="muted">Unknown section type: '+esc(s.type)+"</p>");
    main.appendChild(sec);
    toc.appendChild(el('<a href="#'+s.id+'"><span class="n">'+num+"</span><span>"+esc(s.title)+"</span></a>"));
  });
}

/* Two chip lists, same shape, different questions. `siblings` is the document
   set — the ten documents. `parts` is THIS document's own parts, present only
   on a document written across several files, so a reader on one milestone page
   can reach any other and get back to the index (FR-SPC-09). Kept apart because
   putting fourteen milestones into the set list would put them into every other
   document's navigation, where they mean nothing. */
function chipList(label, list){
  if(!list||!list.length) return "";
  return '<span class="tiny muted">'+esc(label)+'</span><div class="docnav">'+
    list.map(function(d){
      return d.current?'<span class="chip accent">'+esc(d.label)+"</span>":
        '<a class="chip" href="'+esc(d.href)+'">'+esc(d.label)+"</a>";}).join("")+"</div>";
}
function buildDocNav(){
  var nav=$("#docnav");
  var html=chipList("This plan", SPEC.parts)+
    (SPEC.parts&&SPEC.parts.length?'<div style="height:var(--space-3)"></div>':"")+
    chipList("Document set", SPEC.siblings);
  if(!html){nav.remove();return;}
  nav.innerHTML=html;
}

/* ---------------- interactivity ---------------- */

/* The accordion, over the plan's three levels of work.
   One rule: opening a unit closes its siblings at the same level, and on
   arrival the first unit at each level is open and every sibling is shut. It is
   applied to milestones, phases and tasks and to nothing else — a specification
   is read end to end and its catalogues stay open, which is the default
   FR-SPC-10 states and the amendment carves the navigated case out of. */
var UNIT = ".ms,.ph,.task";
function levelOf(el){
  return el.classList.contains("ms")?"ms":el.classList.contains("ph")?"ph":"task";
}
function siblingUnits(unit){
  return Array.prototype.filter.call(unit.parentElement.children,function(sib){
    return sib!==unit&&sib.classList.contains(levelOf(unit));});
}
function openOnly(unit){
  siblingUnits(unit).forEach(function(sib){sib.classList.remove("open");});
  unit.classList.add("open");
}
function toggleUnit(unit){
  /* Shutting is only offered when this unit is already the only one open. After
     "expand all", clicking a header means "just this one" rather than "close
     the one thing I clicked", which is what a reader is asking for. */
  var alone=!siblingUnits(unit).some(function(s){return s.classList.contains("open");});
  if(unit.classList.contains("open")&&alone) unit.classList.remove("open");
  else openOnly(unit);
}
function firstOpen(){
  /* Per parent, not per page: the first phase of the milestone AND the first
     task of every phase, so a reader always lands on something readable. */
  $$(UNIT).forEach(function(u){u.classList.remove("open");});
  var seen=[];
  $$(UNIT).forEach(function(u){
    var key=u.parentElement;
    if(seen.indexOf(key)<0){seen.push(key);u.classList.add("open");}
  });
}

function wireGroups(){
  $$("[data-group] > .gh").forEach(function(b){
    b.addEventListener("click",function(){b.parentElement.classList.toggle("open");});
  });
  $$(".ms > .mh,.ph > .phh,.task > .thd > .hd").forEach(function(b){
    var unit=b.closest(UNIT);
    b.addEventListener("click",function(){toggleUnit(unit);});
  });
  firstOpen();
  var ea=$("#expandAll"), ca=$("#collapseAll");
  if(ea) ea.addEventListener("click",function(){
    $$("[data-group],.ms,.ph,.task").forEach(function(g){g.classList.add("open");});});
  if(ca) ca.addEventListener("click",function(){
    $$("[data-group],.ms,.ph,.task").forEach(function(g){g.classList.remove("open");});});
}

var activePrios={};
function applyFilter(){
  var q=($("#filter").value||"").trim().toLowerCase();
  var terms=q.split(/\s+/).filter(Boolean);
  $$("[data-catalog]").forEach(function(cat){
    var shown=0;
    $$("[data-search]",cat).forEach(function(node){
      var hay=node.getAttribute("data-search")||"";
      var okQ=terms.every(function(t){return hay.indexOf(t)>=0;});
      var p=node.getAttribute("data-prio");
      var okP=!p||activePrios[p]!==false;
      var ok=okQ&&okP;
      node.classList.toggle("hidden",!ok);
      if(ok) shown++;
    });
    /* hide a group whose visible children all vanished */
    $$("[data-group]",cat).forEach(function(g){
      var any=$$("[data-search]",g).some(function(n){return !n.classList.contains("hidden");});
      g.classList.toggle("hidden",!any);
    });
    $$(".ms",cat).forEach(function(m){
      var any=$$("[data-search]",m).some(function(n){return !n.classList.contains("hidden");});
      var self=!m.classList.contains("hidden")&&(m.getAttribute("data-search")||"").indexOf(terms.join(" "))>=0;
      m.classList.toggle("hidden",!(any||self||!terms.length));
    });
    /* A match inside a shut unit is a match nobody can see. While the filter
       narrows, every unit still holding something visible is opened; clearing
       it puts the accordion back rather than leaving the page expanded. */
    if(terms.length){
      $$(UNIT,cat).forEach(function(u){
        var self=!u.classList.contains("hidden")&&u.hasAttribute("data-search");
        var any=$$("[data-search]",u).some(function(n){return !n.classList.contains("hidden");});
        u.classList.toggle("open",self||any);
      });
    }
    var nr=cat.parentElement.querySelector(".noRes");
    if(nr) nr.classList.toggle("hidden",shown>0);
  });
  if(!terms.length&&$$(UNIT).length) firstOpen();
}
function wireFilter(){
  var f=$("#filter");
  f.addEventListener("input",applyFilter);
  f.addEventListener("keydown",function(e){if(e.key==="Escape"){f.value="";applyFilter();}});
  document.addEventListener("keydown",function(e){
    if(e.key==="/"&&document.activeElement!==f){e.preventDefault();f.focus();}
  });
  $$(".prio").forEach(function(b){
    var p=b.getAttribute("data-prio"); activePrios[p]=true;
    b.addEventListener("click",function(){
      activePrios[p]=!activePrios[p];
      b.setAttribute("aria-pressed",String(activePrios[p]));
      b.style.opacity=activePrios[p]?"1":".38";
      applyFilter();
    });
  });
}

function wireReview(){
  var boxes=$$(".rev"); if(!boxes.length){var p=$("#progWrap"); if(p) p.remove(); return;}
  var key=NS+":reviewed";
  var saved={};
  try{saved=JSON.parse(localStorage.getItem(key)||"{}");}catch(e){saved={};}
  function paint(){
    var done=boxes.filter(function(b){return b.checked;}).length;
    $("#progDone").textContent=done; $("#progTotal").textContent=boxes.length;
    $("#progBar").style.width=(boxes.length?(done/boxes.length*100):0)+"%";
  }
  boxes.forEach(function(b){
    var id=b.getAttribute("data-rev");
    b.checked=!!saved[id];
    b.closest(".req").classList.toggle("done",b.checked);
    b.addEventListener("change",function(){
      saved[id]=b.checked; if(!b.checked) delete saved[id];
      localStorage.setItem(key,JSON.stringify(saved));
      b.closest(".req").classList.toggle("done",b.checked);
      paint();
    });
  });
  var rst=$("#resetRev");
  if(rst) rst.addEventListener("click",function(){
    localStorage.removeItem(key); saved={};
    boxes.forEach(function(b){b.checked=false;b.closest(".req").classList.remove("done");});
    paint();
  });
  paint();
}

function wireScrollspy(){
  var links=$$("#tocList a");
  var map={}; links.forEach(function(a){map[a.getAttribute("href").slice(1)]=a;});
  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(!e.isIntersecting) return;
      links.forEach(function(a){a.classList.remove("on");});
      var a=map[e.target.id]; if(a){a.classList.add("on");}
    });
  },{rootMargin:"-88px 0px -70% 0px",threshold:0});
  $$("#main > section").forEach(function(s){io.observe(s);});
}

/* The art assembles itself while it is on screen and resets when it leaves, so
   returning to a figure plays it again. The finished state is the default, so a
   browser without IntersectionObserver simply shows the completed model. */
function wireArt(){
  var figs=$$("svg.zsart");
  if(!figs.length||!window.IntersectionObserver) return;
  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(e){e.target.classList.toggle("in",e.isIntersecting);});
  },{threshold:0.2});
  figs.forEach(function(f){io.observe(f);});
}

function wireCopy(){
  function copy(text,btn,label){
    var done=function(){var t=btn.textContent;btn.textContent=label||"Copied";
      setTimeout(function(){btn.textContent=t;},1400);};
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done,done);}
    else{var ta=document.createElement("textarea");ta.value=text;document.body.appendChild(ta);ta.select();
      try{document.execCommand("copy");}catch(e){} document.body.removeChild(ta); done();}
  }
  var pretty=JSON.stringify(SPEC,null,2);
  var out=$("#specOut"); if(out) out.textContent=pretty;
  var cs=$("#copySpec"); if(cs) cs.addEventListener("click",function(){copy(pretty,cs,"Spec copied");});
  var top=$("#copyTop"); if(top) top.addEventListener("click",function(){copy(pretty,top,"Copied");});
  var dl=$("#dlSpec"); if(dl) dl.addEventListener("click",function(){
    var blob=new Blob([pretty],{type:"application/json"});
    var a=document.createElement("a");a.href=URL.createObjectURL(blob);
    a.download=(DOC.slug||"spec")+".json";document.body.appendChild(a);a.click();
    setTimeout(function(){URL.revokeObjectURL(a.href);document.body.removeChild(a);},300);
  });
  $$(".copy").forEach(function(b){
    b.addEventListener("click",function(e){
      /* Inside a <summary>, a click would also toggle the fold. Cancelling the
         event's default action anywhere along its path cancels that toggle, so
         "copy" copies and does not also expand five thousand words. */
      var fold=b.closest("details.pf");
      if(fold){e.preventDefault();e.stopPropagation();}
      var pre=(fold||b.parentElement).querySelector("pre");
      if(pre) copy(pre.textContent,b,"Copied");
    });
  });
}

function wireHash(){
  /* scrollIntoView is unreliable here: the document is built by script after load, and
     an ancestor with overflow:hidden can absorb the scroll. Compute the offset and move
     the window explicitly, allowing for the sticky header. */
  function goTo(t,smooth){
    var y=t.getBoundingClientRect().top+window.pageYOffset-96;
    try{window.scrollTo({top:y,behavior:smooth?"smooth":"instant"});}
    catch(e){window.scrollTo(0,y);}
  }
  function flash(initial){
    var id=location.hash.slice(1); if(!id) return;
    var t=document.getElementById(id); if(!t) return;
    var g=t.closest("[data-group]"); if(g) g.classList.add("open");
    /* Every level between the target and the page, not just the outermost one.
       A deep link to a task used to land on a shut phase inside a shut
       milestone, and the reader saw the header of something else. */
    for(var a=t; a; a=a.parentElement){
      if(a.classList&&(a.classList.contains("ms")||a.classList.contains("ph")||
                       a.classList.contains("task"))) openOnly(a);
    }
    t.classList.add("flash");
    setTimeout(function(){t.classList.remove("flash");},1400);
    goTo(t,!initial);
    /* Late layout — web fonts, expanded groups — can move the target after the first
       jump. Check once and correct rather than trusting a single attempt. */
    setTimeout(function(){
      var r=t.getBoundingClientRect();
      if(r.top<0||r.top>window.innerHeight) goTo(t,false);
    },350);
  }
  window.addEventListener("hashchange",function(){flash(false);});
  if(location.hash){
    if(document.fonts&&document.fonts.ready) document.fonts.ready.then(function(){flash(true);});
    else setTimeout(function(){flash(true);},120);
    setTimeout(function(){flash(true);},400);
  }
}

/* ---------------- boot ---------------- */
buildHero();
buildSections();
buildDocNav();
wireGroups();
wireFilter();
wireReview();
wireScrollspy();
wireArt();
wireCopy();
wireHash();
document.title = DOC.title;
var st=$("#statLine");
if(st) st.textContent = (SPEC.sections||[]).length+" sections";
})();
"""

SKELETON = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__TITLE__</title>
<meta name="description" content="__DESC__" />
<link rel="icon" type="image/svg+xml" href="__FAVICON__" />
__FONTS__
<style>
/* =====================================================================
   __TITLE__
   Styled with the Zero Style design system — tokens inlined verbatim for a
   fully self-contained file. Light theme only (the system defines no dark
   palette). Every section below is rendered at load time from the embedded
   JSON in <script id="__SPEC_ID__">, so the human-readable document and the
   machine-readable one cannot drift apart.
   ===================================================================== */
__TOKENS__
__STRUCT__
</style>
</head>
<body>
<header class="bar">
  <div class="bar-in">
    <a class="brand" href="index.html"><span class="mark">__MARK__</span>Zero-to-Ship<span class="kind">__KIND__</span></a>
    <div class="bar-tools">
      <div class="search"><input id="filter" type="search" placeholder="Filter (press /)" aria-label="Filter document" /></div>
      <button class="btn sm" id="expandAll">Expand all</button>
      <button class="btn sm" id="collapseAll">Collapse all</button>
      <button class="btn sm" id="copyTop">Copy JSON</button>
    </div>
  </div>
</header>

<div class="wrap">
  <nav class="toc" aria-label="Contents">
    <h4>Contents</h4>
    <div class="list" id="tocList"></div>
    <div class="prog" id="progWrap">
      <div class="lab"><span>Reviewed</span><b><span id="progDone">0</span>/<span id="progTotal">0</span></b></div>
      <div class="meter"><i id="progBar"></i></div>
      <button class="btn sm" id="resetRev" style="margin-top:var(--space-2);width:100%">Reset</button>
    </div>
    <div id="docnav" style="margin-top:var(--space-3)"></div>
  </nav>

  <main class="main" id="main">
    <section class="hero" id="heroSec">
      <div class="hero-body" id="hero"></div>
      __HEROLOGO__
    </section>
  </main>
</div>

<footer class="foot">
  <span id="statLine"></span> &middot; Self-contained: this file needs no server, build step, or network beyond its two web fonts.
  &middot; &copy; 2026 Zer&oslash; Effort &middot; Zero-to-Ship (Z2S) Method.
</footer>

<script type="application/json" id="__SPEC_ID__">
__SPEC_JSON__
</script>
<script>
__RUNTIME__
</script>
</body>
</html>
"""


def page(spec, spec_id, kind, desc):
    """Render one self-contained document."""
    import json
    doc = spec.get("document", {})
    spec = dict(spec)
    spec["__specId"] = spec_id
    blob = json.dumps(spec, indent=1, ensure_ascii=False)
    # A literal "</script>" anywhere in the data would terminate the embedding element
    # early — truncating the specification and breaking the page. "<\/" is a valid JSON
    # escape for "</", so this is lossless: parsers see the original characters.
    blob = blob.replace("</", "<\\/")
    html = SKELETON
    html = html.replace("__FONTS__", FONT_LINK)
    html = html.replace("__TOKENS__", TOKENS.strip())
    html = html.replace("__STRUCT__", STRUCT.strip())
    html = html.replace("__RUNTIME__", RUNTIME.replace("__SPEC_ID__", spec_id).strip())
    html = html.replace("__SPEC_JSON__", blob)
    html = html.replace("__SPEC_ID__", spec_id)
    html = html.replace("__MARK__", LOGO_STATIC)
    html = html.replace("__FAVICON__", FAVICON)
    html = html.replace("__HEROLOGO__",
                        '<div class="heroArt" aria-hidden="true">%s</div>' % LOGO_ANIM
                        if doc.get("heroLogo") else "")
    html = html.replace("__TITLE__", doc.get("title", "Zero-to-Ship"))
    html = html.replace("__DESC__", desc)
    html = html.replace("__KIND__", kind)
    return html
