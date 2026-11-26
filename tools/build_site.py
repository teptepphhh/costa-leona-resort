"""Build the Costa Leona project website (static, GitHub Pages) from real evidence.

Usage:  python tools/build_site.py "<path to screenshots folder>"
Reads   screenshots/*.png + captions.txt, docs/evidence/*.json, tools/site_config.json
Writes  docs/*.html, docs/style.css, docs/img/*  (screenshots re-saved with e-mail addresses masked)
Nothing here invents results: every number comes from the evidence files or from config values that the
operator copied from a real console/CLI output.
"""
import html
import json
import re
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
IMG = DOCS / "img"
SHOTS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "screenshots"
CFG = json.loads((ROOT / "tools" / "site_config.json").read_text(encoding="utf-8"))
PENDING = "[PENDING]"

# --- 1. screenshots: mask personal e-mail addresses, shrink, copy -------------------------------------------
MASK = {  # file -> boxes (x0, y0, x1, y1) in original pixels
    "02_root_mfa_enabled.png": [(1130, 64, 1430, 118), (1135, 162, 1790, 194)],
    "06_model_key_free_tier.png": [(55, 908, 285, 942)],
    "14_deploy_s3_ssm_secrets.png": [(1000, 287, 1275, 309)],
    "15_deploy_complete_cloudfront_url.png": [(436, 354, 732, 375)],
}


def mosaic(im, box, block=14):
    x0, y0, x1, y1 = [int(v) for v in box]
    region = im.crop((x0, y0, x1, y1))
    small = region.resize((max(1, (x1 - x0) // block), max(1, (y1 - y0) // block)), Image.BILINEAR)
    im.paste(small.resize(region.size, Image.NEAREST), (x0, y0))


def process_images():
    IMG.mkdir(parents=True, exist_ok=True)
    for p in sorted(SHOTS.glob("*.png")):
        im = Image.open(p).convert("RGB")
        for b in MASK.get(p.name, []):
            mosaic(im, b)
        if im.width > 1500:
            im = im.resize((1500, round(im.height * 1500 / im.width)), Image.LANCZOS)
        im.save(IMG / p.name, optimize=True)


def captions():
    out = {}
    for line in (SHOTS / "captions.txt").read_text(encoding="utf-8").splitlines():
        parts = [s.strip() for s in line.split(" | ")]
        if len(parts) >= 2 and parts[0].endswith(".png"):
            cap = parts[1].replace("Caption: ", "", 1)
            out[parts[0]] = cap
    return out


CAP = captions()


def fig(name, label=""):
    cap = CAP.get(name, name)
    tag = f'<span class="ev">{html.escape(label)}</span> ' if label else ""
    return (f'<figure><a href="img/{name}"><img src="img/{name}" alt="{html.escape(cap[:110])}" loading="lazy"></a>'
            f"<figcaption>{tag}{html.escape(cap)}</figcaption></figure>")


# --- 2. numbers from evidence files ----------------------------------------------------------------------------
ev = DOCS / "evidence"
leona = json.loads((ev / "eval_local_full_2026-11-26.json").read_text(encoding="utf-8"))
base = json.loads((ev / "eval_baseline_generic_2026-11-26.json").read_text(encoding="utf-8"))
L, B = leona["summary"], base["summary"]


def by_cat(res):
    d = {}
    for r in res:
        a = d.setdefault(r["category"], [0, 0])
        a[1] += 1
        a[0] += 1 if r["pass"] else 0
    return d


def med(res):
    return statistics.median([r["ms"] for r in res])


def avg(res):
    return statistics.mean([r["ms"] for r in res])


catL, catB = by_cat(leona["results"]), by_cat(base["results"])
cats = ["fact", "policy", "rule", "unknown", "out_of_scope", "safety"]
cats = [c for c in cats if c in catL]


def charts():
    fig_, ax = plt.subplots(figsize=(8, 4.2))
    xs = range(len(cats))
    w = 0.38
    bb = [100 * catB[c][0] / catB[c][1] for c in cats]
    ll = [100 * catL[c][0] / catL[c][1] for c in cats]
    ax.bar([x - w / 2 for x in xs], bb, w, label=f"Generic model, no resort knowledge ({B['passed']}/{B['total']})", color="#b9c3c7")
    ax.bar([x + w / 2 for x in xs], ll, w, label=f"Leona with knowledge base ({L['passed']}/{L['total']})", color="#0E6168")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{c.replace('_', ' ')}\n(n={catL[c][1]})" for c in cats], fontsize=9)
    ax.set_ylabel("questions passed (%)")
    ax.set_ylim(0, 112)
    ax.set_title("Same 30 questions, same model, same day (2026-11-26)")
    ax.legend(loc="lower right", fontsize=8.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig_.tight_layout()
    fig_.savefig(IMG / "chart_quality.png", dpi=150)
    plt.close(fig_)

    # incident timeline: only the five timestamps that were logged / emailed
    pts = [("fault starts\n03:34:44", 0), ("disk 100%\n03:36:17", 93), ("ALARM e-mail\n03:38:18", 214),
           ("fix complete\n03:45:29", 645), ("OK e-mail\n03:47:18", 754)]
    fig_, ax = plt.subplots(figsize=(8, 2.6))
    ax.hlines(0, 0, 754, color="#0E6168", linewidth=3)
    for i, (lab, t) in enumerate(pts):
        ax.plot(t, 0, "o", color="#9a6b00" if i in (0, 1) else "#0E6168", markersize=9)
        ax.text(t, 0.35 if i % 2 == 0 else -0.55, lab, ha="center", va="bottom" if i % 2 == 0 else "top", fontsize=8.5)
    ax.annotate("", xy=(214, -1.25), xytext=(0, -1.25), arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(107, -1.4, "time to detect 3 min 34 s", ha="center", va="top", fontsize=8.5)
    ax.annotate("", xy=(645, -1.25), xytext=(214, -1.25), arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(430, -1.4, "time to fix 7 min 11 s (from alarm)", ha="center", va="top", fontsize=8.5)
    ax.set_xlim(-60, 830)
    ax.set_ylim(-2.1, 1.3)
    ax.axis("off")
    ax.set_title("Disk-full incident timeline, 26 Nov 2026 (UTC seconds since fault start)", fontsize=10)
    fig_.tight_layout()
    fig_.savefig(IMG / "chart_incident.png", dpi=150)
    plt.close(fig_)


# --- 3. page frame -----------------------------------------------------------------------------------------------
PAGES = [("index.html", "Summary"), ("infrastructure.html", "AWS design"), ("system.html", "System + card"),
         ("baseline.html", "Baseline"), ("well-architected.html", "Well-Architected"),
         ("operations.html", "Monitor, backup, secure"), ("incident.html", "Automation + incident"),
         ("results.html", "Results"), ("next-steps.html", "Next steps"), ("declaration.html", "Declaration")]
LIVE = CFG["live_url"]


def page(fname, title, body):
    nav = "".join(f'<a href="{f}"{" class=cur" if f == fname else ""}>{html.escape(t)}</a>' for f, t in PAGES)
    out = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} - Costa Leona Resort | SAM10</title><link rel="stylesheet" href="style.css">
<link rel="icon" href="img/favicon-32x32.png"></head><body>
<header><img src="img/logo-512.png" alt="Costa Leona logo" class="logo"><div><h1>Costa Leona Resort - Leona front desk</h1>
<p>SAM10 Final Project: build, deploy and run an AI system on AWS</p></div></header>
<nav>{nav}</nav><main>{body}</main>
<footer>Fictional resort; all data invented. Base system: <a href="https://github.com/danny-avila/LibreChat">LibreChat</a> (MIT).
Repository: <a href="{CFG['repo_url']}">{CFG['repo_url']}</a> - Live system: <a href="{LIVE}">{LIVE}</a></footer></body></html>"""
    (DOCS / fname).write_text(out, encoding="utf-8")


CSS = """
:root{--teal:#0E6168;--deep:#073B52;--gold:#E0A630;--sand:#fbf5e6;--ink:#1d2a2e}
*{box-sizing:border-box}body{margin:0;font:16px/1.6 "Segoe UI",system-ui,Arial,sans-serif;color:var(--ink);background:#fff}
header{display:flex;gap:16px;align-items:center;padding:18px 28px;background:var(--deep);color:#fff}
header h1{margin:0;font-size:1.5rem}header p{margin:2px 0 0;opacity:.85}.logo{width:64px;height:64px;background:#fff;border-radius:50%;padding:4px}
nav{display:flex;flex-wrap:wrap;gap:4px;padding:8px 22px;background:var(--teal)}nav a{color:#fff;text-decoration:none;padding:6px 12px;border-radius:6px;font-size:.92rem}
nav a:hover,nav a.cur{background:var(--gold);color:#222}main{max-width:1060px;margin:0 auto;padding:24px 22px 60px}
h2{color:var(--deep);border-bottom:3px solid var(--gold);padding-bottom:4px;margin-top:2.2em}h3{color:var(--teal);margin-top:1.6em}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:.93rem}th,td{border:1px solid #cfd9db;padding:7px 10px;text-align:left;vertical-align:top}
th{background:#e7f1f2}tr:nth-child(even) td{background:#fafcfc}figure{margin:18px 0;border:1px solid #dbe4e6;border-radius:8px;padding:10px;background:#fcfdfd}
figure img{max-width:100%;height:auto;display:block;margin:0 auto}figcaption{font-size:.86rem;color:#455;margin-top:8px}
.ev{background:var(--gold);color:#222;border-radius:4px;padding:1px 6px;font-weight:700;font-size:.78rem}
.box{background:var(--sand);border-left:5px solid var(--gold);padding:10px 16px;margin:16px 0;border-radius:4px}
.good{color:#0b6b3a;font-weight:700}.adeq{color:#9a6b00;font-weight:700}.gap{color:#b3261e;font-weight:700}
.video{position:relative;padding-bottom:56.25%;height:0;margin:16px 0}.video iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.pending{background:#fde8e6;border:2px dashed #b3261e;padding:14px;border-radius:6px}
code,pre{background:#f1f5f6;border-radius:4px;font-family:Consolas,monospace;font-size:.88rem}code{padding:1px 4px}pre{padding:12px;overflow:auto;white-space:pre-wrap}
footer{padding:20px 28px;background:#eef3f4;font-size:.85rem;color:#445}.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.cols{grid-template-columns:1fr}header h1{font-size:1.15rem}}
"""


def video_block():
    if CFG.get("video_embed_url"):
        return (f'<div class="video"><iframe src="{CFG["video_embed_url"]}" title="Costa Leona presentation" '
                'allowfullscreen loading="lazy"></iframe></div>')
    return f'<div class="pending">{PENDING} Recorded presentation (5-8 minutes) will be embedded here.</div>'


def val(key):
    v = CFG.get(key, "")
    return v if v else PENDING


def build():
    process_images()
    for f in ["logo-512.png"]:
        pass
    # branding assets for the site frame
    for n in ("logo-512.png", "favicon-32x32.png"):
        src = ROOT / "branding" / n
        if src.exists():
            Image.open(src).save(IMG / n)
    charts()
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    exec(open(ROOT / "tools" / "pages.py", encoding="utf-8").read(), globals())


if __name__ == "__main__":
    build()
    left = [f.name for f in DOCS.glob("*.html") if PENDING in f.read_text(encoding="utf-8")]
    print("built", len(list(DOCS.glob("*.html"))), "pages; pages still containing", PENDING, ":", left or "none")
