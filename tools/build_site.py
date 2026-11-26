"""Build the Costa Leona project website (static, GitHub Pages) from real evidence.

Usage:  python tools/build_site.py "<path to screenshots folder>"
Reads   screenshots/*.png + captions.txt, docs/evidence/*.json, tools/site_config.json
Writes  docs/*.html, docs/style.css, docs/img/*  (screenshots re-saved with e-mail addresses masked)
Nothing here invents results: every number comes from the evidence files or from config values that the
operator copied from a real console/CLI output.
"""
import html
import json
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
            out[parts[0]] = parts[1].replace("Caption: ", "", 1)
    return out


CAP = captions()


def fig(name, label="", frame="browser"):
    cap = CAP.get(name, name)
    tag = f'<span class="ev">{html.escape(label)}</span>' if label else ""
    dots = '<div class="bar"><i></i><i></i><i></i></div>' if frame else ""
    return (f'<figure class="shot">{dots}<a href="img/{name}"><img src="img/{name}" alt="{html.escape(cap[:110])}" loading="lazy"></a>'
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
cats = [c for c in ["fact", "policy", "rule", "unknown", "out_of_scope", "safety"] if c in catL]
NAVY, TEAL, GOLD, AQUA = "#0c2d57", "#0E6168", "#E0A630", "#3bb8c9"


def charts():
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig_, ax = plt.subplots(figsize=(8, 4.2))
    xs = range(len(cats))
    w = 0.38
    bb = [100 * catB[c][0] / catB[c][1] for c in cats]
    ll = [100 * catL[c][0] / catL[c][1] for c in cats]
    ax.bar([x - w / 2 for x in xs], bb, w, label=f"Generic model, no resort knowledge ({B['passed']}/{B['total']})", color="#c9d6e3")
    ax.bar([x + w / 2 for x in xs], ll, w, label=f"Leona with knowledge base ({L['passed']}/{L['total']})", color=NAVY)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{c.replace('_', ' ')}\n(n={catL[c][1]})" for c in cats], fontsize=9)
    ax.set_ylabel("questions passed (%)")
    ax.set_ylim(0, 115)
    ax.set_title("Same 30 questions, same model, same day (2026-11-26)", fontsize=11, color=NAVY)
    ax.legend(loc="upper right", fontsize=8.5, frameon=False, ncol=1)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig_.tight_layout()
    fig_.savefig(IMG / "chart_quality.png", dpi=150)
    plt.close(fig_)

    pts = [("fault starts\n03:34:44", 0), ("disk 100%\n03:36:17", 93), ("ALARM e-mail\n03:38:18", 214),
           ("fix complete\n03:45:29", 645), ("OK e-mail\n03:47:18", 754)]
    fig_, ax = plt.subplots(figsize=(8, 2.7))
    ax.hlines(0, 0, 754, color=AQUA, linewidth=4)
    for i, (lab, t) in enumerate(pts):
        ax.plot(t, 0, "o", color=GOLD if i in (0, 1) else NAVY, markersize=10, zorder=3)
        ax.text(t, 0.35 if i % 2 == 0 else -0.55, lab, ha="center", va="bottom" if i % 2 == 0 else "top", fontsize=8.5, color=NAVY)
    ax.annotate("", xy=(214, -1.25), xytext=(0, -1.25), arrowprops=dict(arrowstyle="<->", color="#556"))
    ax.text(107, -1.4, "time to detect 3 min 34 s", ha="center", va="top", fontsize=8.5)
    ax.annotate("", xy=(645, -1.25), xytext=(214, -1.25), arrowprops=dict(arrowstyle="<->", color="#556"))
    ax.text(430, -1.4, "time to fix 7 min 11 s (from alarm)", ha="center", va="top", fontsize=8.5)
    ax.set_xlim(-60, 830)
    ax.set_ylim(-2.1, 1.3)
    ax.axis("off")
    ax.set_title("Disk-full incident, 26 Nov 2026 (seconds since fault start, UTC)", fontsize=10, color=NAVY)
    fig_.tight_layout()
    fig_.savefig(IMG / "chart_incident.png", dpi=150)
    plt.close(fig_)


# --- 3. design system + page frame -----------------------------------------------------------------------------
PAGES = [("index.html", "Overview"), ("infrastructure.html", "AWS design"), ("system.html", "System"),
         ("baseline.html", "Baseline"), ("well-architected.html", "Review"), ("operations.html", "Operate"),
         ("incident.html", "Incident"), ("results.html", "Results"), ("next-steps.html", "Next steps"),
         ("declaration.html", "Declaration")]
LIVE = CFG["live_url"]

ICON = {
    "shield": '<svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 4.5-3.2 8.2-8 9-4.8-.8-8-4.5-8-9V6l8-3z"/><path d="M8.5 12l2.5 2.5L15.5 10"/></svg>',
    "pulse": '<svg viewBox="0 0 24 24"><path d="M3 12h4l2.5-6 4 12 2.5-6H21"/></svg>',
    "db": '<svg viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/></svg>',
    "gear": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    "wave": '<svg viewBox="0 0 24 24"><path d="M2 9c2.5-3 4.5-3 7 0s4.5 3 7 0 4.5-3 6 0M2 16c2.5-3 4.5-3 7 0s4.5 3 7 0 4.5-3 6 0"/></svg>',
}


def icon(n):
    return f'<span class="ico">{ICON[n]}</span>'


def pill(kind, text):
    return f'<span class="pill {kind}">{html.escape(text)}</span>'


def stat(num, label, note=""):
    n = f'<small>{html.escape(note)}</small>' if note else ""
    return f'<div class="stat"><b>{num}</b><span>{html.escape(label)}</span>{n}</div>'


def card(href, title, text, img=None, tag=""):
    th = f'<div class="thumb"><img src="img/{img}" alt="" loading="lazy"></div>' if img else ""
    tg = f'<span class="eyebrow">{html.escape(tag)}</span>' if tag else ""
    return (f'<a class="card" href="{href}">{th}<div class="cbody">{tg}<h3>{html.escape(title)}</h3><p>{text}</p>'
            f'<span class="more">Open {ICON["arrow"]}</span></div></a>')


def page(fname, title, body, eyebrow="", lead=""):
    nav = "".join(f'<a href="{f}"{" class=cur" if f == fname else ""}>{html.escape(t)}</a>' for f, t in PAGES)
    head = ""
    if fname != "index.html":
        head = (f'<section class="phero"><div class="wrap"><span class="eyebrow">{html.escape(eyebrow)}</span><h1>{html.escape(title)}</h1>'
                f'<p>{lead}</p></div><svg class="wavebot" viewBox="0 0 1440 60" preserveAspectRatio="none"><path d="M0 30c240 40 480 40 720 0s480-40 720 0v30H0z"/></svg></section>')
    out = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | Costa Leona Resort - SAM10</title><meta name="description" content="Costa Leona Resort front-desk assistant: a reskinned LibreChat deployed, monitored, backed up and secured on AWS (SAM10 final project).">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css"><link rel="icon" href="img/favicon-32x32.png"></head><body>
<header class="top"><div class="wrap bar"><a class="brand" href="index.html"><img src="img/logo-512.png" alt=""><span><b>Costa Leona</b><small>Resort &middot; SAM10</small></span></a>
<input type="checkbox" id="mt" class="mt"><label for="mt" class="burger" aria-label="Menu"><i></i><i></i><i></i></label>
<nav>{nav}</nav><a class="btn small" href="{LIVE}">Try Leona {ICON["arrow"]}</a></div></header>
{head}<main class="wrap">{body}</main>
<footer><div class="wrap fcols"><div><b>Costa Leona Resort</b><p>A fictional resort. Leona is an AI assistant for general questions only; please confirm important details with the front desk.</p></div>
<div><b>Project</b><p><a href="{CFG['repo_url']}">Git repository</a><br><a href="{LIVE}">Live system</a><br><a href="declaration.html">Credits &amp; declaration</a></p></div>
<div><b>Built on</b><p><a href="https://github.com/danny-avila/LibreChat">LibreChat</a> (MIT) &middot; AWS &middot; Google Gemini free tier</p></div></div>
<div class="wrap copy">SAM10 - Systems Administration and Maintenance, Final Project. All data and people are invented.</div></footer></body></html>"""
    (DOCS / fname).write_text(out, encoding="utf-8")


CSS = """
:root{--navy:#0c2d57;--ink:#26384f;--muted:#5d6f86;--blue:#1f6fb5;--aqua:#3bb8c9;--teal:#0E6168;--gold:#E0A630;--line:#dbe6f0;--mist:#eef7fb;--r:20px;
--shadow:0 12px 34px rgba(12,45,87,.09);--sans:"Inter",system-ui,"Segoe UI",Arial,sans-serif;--head:"Plus Jakarta Sans","Inter",system-ui,Arial,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:16px/1.7 var(--sans);color:var(--ink);background:linear-gradient(180deg,#e8f5fb 0,#f6fbfd 520px,#fff 900px) no-repeat,#fff}
.wrap{width:min(1160px,92vw);margin:0 auto}a{color:var(--blue)}img{max-width:100%}
h1,h2,h3{font-family:var(--head);color:var(--navy);line-height:1.15;letter-spacing:-.02em}
h2{font-size:clamp(1.6rem,2.6vw,2.15rem);margin:2.4em 0 .5em}h3{font-size:1.2rem;margin:1.8em 0 .4em}
.eyebrow{display:inline-block;font:700 .72rem/1 var(--head);letter-spacing:.14em;text-transform:uppercase;color:var(--aqua);margin-bottom:10px}
/* top bar */
.top{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.88);backdrop-filter:blur(10px);border-bottom:1px solid rgba(12,45,87,.07)}
.top .bar{display:flex;align-items:center;gap:22px;height:72px}.brand{white-space:nowrap;display:flex;align-items:center;gap:11px;text-decoration:none;color:var(--navy)}
.brand img{width:44px;height:44px}.brand span{display:flex;flex-direction:column;line-height:1.1}.brand b{font:800 1.08rem var(--head)}.brand small{font-size:.72rem;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}
.top nav{display:flex;gap:2px;margin:0 auto}.top nav a{white-space:nowrap;color:var(--ink);text-decoration:none;font-weight:500;font-size:.88rem;padding:8px 11px;border-radius:999px}
.top nav a:hover{background:var(--mist)}.top nav a.cur{background:var(--navy);color:#fff}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--navy);color:#fff;text-decoration:none;font:700 .95rem var(--head);padding:14px 26px;border-radius:999px;box-shadow:0 8px 20px rgba(12,45,87,.25);transition:.2s}
.btn:hover{transform:translateY(-2px);background:#12427c}.btn svg{width:18px;height:18px;stroke:#fff}.btn.small{padding:10px 18px;font-size:.85rem;white-space:nowrap}
.btn.ghost{background:#fff;color:var(--navy);box-shadow:inset 0 0 0 2px var(--navy)}.btn.ghost svg{stroke:var(--navy)}.btn.ghost:hover{background:var(--mist)}
svg{fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.mt,.burger{display:none}
/* hero */
.hero{padding:70px 0 40px;display:grid;grid-template-columns:1.02fr 1fr;gap:46px;align-items:center}
.hero h1{font-size:clamp(2.3rem,4.7vw,3.9rem);margin:0 0 18px;font-weight:800}.hero h1 em{font-style:normal;color:var(--aqua)}
.hero p.lead{font-size:1.14rem;color:var(--muted);max-width:34em;margin:0 0 28px}.hero .cta{display:flex;gap:14px;flex-wrap:wrap}
.mock{position:relative}.mock .frame{background:#fff;border-radius:26px 130px 26px 26px;overflow:hidden;box-shadow:0 30px 70px rgba(12,45,87,.22);border:6px solid #fff}
.mock .frame .bar2{height:30px;background:#eef3f8;display:flex;align-items:center;gap:6px;padding:0 14px}.bar2 i{width:9px;height:9px;border-radius:50%;background:#c4d1de}
.bar2 span{margin-left:10px;font-size:.72rem;color:#6a7d92;background:#fff;border-radius:99px;padding:2px 12px}
.mock img{display:block;width:100%;height:360px;object-fit:cover;object-position:top left}
.chip{position:absolute;background:#fff;border-radius:16px;padding:12px 16px;box-shadow:var(--shadow);font-size:.82rem;display:flex;gap:10px;align-items:center;max-width:250px}
.chip b{display:block;color:var(--navy);font:700 .86rem var(--head)}.chip .ico{width:34px;height:34px;flex:none}
.chip.c1{left:-26px;bottom:34px}.chip.c2{right:-8px;bottom:-22px}
.ico{display:grid;place-items:center;width:46px;height:46px;border-radius:14px;background:var(--mist);color:var(--blue)}.ico svg{width:24px;height:24px}
/* stats strip */
.strip{background:#fff;border-radius:24px;box-shadow:var(--shadow);padding:26px 18px;display:grid;grid-template-columns:repeat(4,1fr);margin:34px 0 10px}
.stat{padding:2px 26px;border-left:1px solid var(--line);display:flex;flex-direction:column}.stat:first-child{border-left:0}
.stat b{font:800 2.2rem/1.1 var(--head);color:var(--navy)}.stat span{font-weight:600;color:var(--ink)}.stat small{color:var(--muted);font-size:.8rem}
.feats{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:34px 0}.feat{display:flex;gap:14px;align-items:flex-start}.feat b{display:block;color:var(--navy);font:700 1rem var(--head)}.feat span{font-size:.86rem;color:var(--muted);line-height:1.45}
/* cards */
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}.grid.three{grid-template-columns:repeat(3,1fr)}.grid.two{grid-template-columns:repeat(2,1fr)}
.card{display:block;background:#fff;border-radius:var(--r);box-shadow:var(--shadow);overflow:hidden;text-decoration:none;color:var(--ink);transition:.25s;border:1px solid rgba(12,45,87,.05)}
.card:hover{transform:translateY(-6px);box-shadow:0 22px 50px rgba(12,45,87,.16)}
.thumb{height:150px;overflow:hidden;background:var(--mist)}.thumb img{width:100%;height:100%;object-fit:cover;object-position:top left;transition:.4s}.card:hover .thumb img{transform:scale(1.05)}
.cbody{padding:18px 20px 20px}.cbody h3{margin:0 0 6px;font-size:1.12rem}.cbody p{margin:0 0 12px;font-size:.9rem;color:var(--muted);line-height:1.5}
.more{display:inline-flex;gap:6px;align-items:center;font:700 .82rem var(--head);color:var(--blue)}.more svg{width:16px;height:16px}
.sechead{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin:70px 0 24px}.sechead h2{margin:0}.sechead p{max-width:32em;color:var(--muted);margin:6px 0 0}
.band{background:linear-gradient(120deg,#0c2d57,#12508a 60%,#1b7fa8);color:#dbeaf7;border-radius:30px;padding:46px;margin:60px 0;display:grid;grid-template-columns:1.1fr 1fr;gap:36px;position:relative;overflow:hidden}
.band h2{color:#fff;margin:0 0 12px}.band p{margin:0 0 12px}.band .eyebrow{color:#8fe1ee}.band ul{margin:0;padding-left:1.1em}.band li{margin:.35em 0}
.band::after{content:"";position:absolute;right:-90px;top:-90px;width:300px;height:300px;border-radius:50%;background:rgba(255,255,255,.07)}
/* page hero */
.phero{position:relative;padding:62px 0 74px;background:linear-gradient(135deg,#0c2d57,#145c93 65%,#2b9fbd);color:#fff;overflow:hidden}
.phero .eyebrow{color:#8fe1ee}.phero h1{color:#fff;margin:0 0 12px;font-size:clamp(2rem,3.6vw,3rem);font-weight:800}.phero p{max-width:42em;margin:0;color:#d9ebf7;font-size:1.08rem}
.wavebot{position:absolute;left:0;bottom:-1px;width:100%;height:46px;fill:#fff;stroke:none}
main.wrap{padding-bottom:70px}
/* content */
.lead2{font-size:1.1rem;color:var(--muted)}
.box{background:#fff;border-radius:var(--r);box-shadow:var(--shadow);border-left:6px solid var(--gold);padding:18px 24px;margin:22px 0}
.box.blue{border-left-color:var(--aqua)}
table{border-collapse:separate;border-spacing:0;width:100%;margin:18px 0 26px;font-size:.92rem;background:#fff;border-radius:16px;overflow:hidden;box-shadow:var(--shadow)}
th{background:var(--navy);color:#fff;text-align:left;font:700 .8rem var(--head);letter-spacing:.04em;text-transform:uppercase;padding:13px 15px}
td{padding:12px 15px;border-top:1px solid #e8eff6;vertical-align:top}tr:nth-child(even) td{background:#f8fbfd}
.pill{display:inline-block;border-radius:999px;font:700 .72rem var(--head);padding:4px 11px;letter-spacing:.03em}
.pill.good{background:#dcf5e7;color:#0b6b3a}.pill.adeq{background:#fdf0cf;color:#8a5d00}.pill.gap{background:#fde3e1;color:#b3261e}
td.good{color:#0b6b3a;font-weight:600}td.gap{color:#b3261e;font-weight:600}
figure.shot{margin:22px 0;background:#fff;border-radius:18px;box-shadow:var(--shadow);overflow:hidden;border:1px solid rgba(12,45,87,.06)}
figure.shot .bar{display:flex;gap:6px;padding:10px 14px;background:#eef3f8}.bar i{width:10px;height:10px;border-radius:50%;background:#c4d1de}
figure.shot img{display:block;width:100%;height:auto}figure.shot figcaption{font-size:.83rem;color:var(--muted);padding:12px 18px 14px;line-height:1.5}
.ev{display:inline-block;background:var(--gold);color:#3a2a00;border-radius:6px;padding:1px 8px;font:800 .7rem var(--head);margin-right:8px;letter-spacing:.04em}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.pending{background:#fff4f3;border:2px dashed #d9534f;color:#8a1f18;padding:18px;border-radius:14px}
.video{position:relative;padding-bottom:56.25%;height:0;border-radius:22px;overflow:hidden;box-shadow:var(--shadow);margin:14px 0}.video iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
code,pre{font-family:"Cascadia Mono",Consolas,monospace;font-size:.85rem}code{background:#eaf2f8;border-radius:6px;padding:2px 6px;color:#12427c}
pre{background:#0d1b2e;color:#d6e4f5;border-radius:16px;padding:20px 22px;overflow:auto;white-space:pre-wrap;line-height:1.55;box-shadow:var(--shadow)}
.tl{list-style:none;margin:22px 0;padding:0;border-left:3px solid var(--aqua);margin-left:8px}.tl li{position:relative;padding:0 0 18px 26px}
.tl li::before{content:"";position:absolute;left:-10px;top:5px;width:16px;height:16px;border-radius:50%;background:#fff;border:4px solid var(--navy)}
.tl li.hot::before{border-color:var(--gold)}.tl b{font-family:var(--head);color:var(--navy)}.tl time{display:block;font-size:.8rem;color:var(--muted)}
.pillar{background:#fff;border-radius:var(--r);box-shadow:var(--shadow);padding:22px 24px;margin:16px 0;display:grid;grid-template-columns:210px 1fr 150px;gap:22px;align-items:start}
.pillar h3{margin:0;font-size:1.1rem}.pillar .ask{font-size:.84rem;color:var(--muted);margin-top:4px;line-height:1.4}.pillar .v{display:flex;flex-direction:column;gap:8px;font-size:.78rem;color:var(--muted)}
.pillar p{margin:0;font-size:.93rem}
figure.chart{background:#fff;border-radius:20px;box-shadow:var(--shadow);padding:16px;margin:22px 0}figure.chart img{display:block;margin:auto}figure.chart figcaption{font-size:.83rem;color:var(--muted);margin-top:8px}
.panel{background:#fff;border-radius:var(--r);box-shadow:var(--shadow);padding:26px 28px;border:1px solid rgba(12,45,87,.05)}
.panel h3{margin:0 0 8px;font-size:1.15rem}.panel p{margin:0 0 .6em}.panel ul{margin:.3em 0;padding-left:1.1em}
.linkrow{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0}.linkrow a{background:#fff;border-radius:999px;padding:9px 18px;text-decoration:none;font:600 .88rem var(--head);color:var(--navy);box-shadow:var(--shadow)}
.linkrow a:hover{background:var(--navy);color:#fff}
.pillars-head{display:grid;grid-template-columns:210px 1fr 150px;gap:22px;padding:0 24px;font:700 .72rem var(--head);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:24px}
/* footer */
footer{background:var(--navy);color:#b8cde4;margin-top:40px;padding:52px 0 22px;font-size:.9rem}footer a{color:#8fe1ee}
.fcols{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px}footer b{color:#fff;font:700 1rem var(--head)}footer p{line-height:1.8}
.copy{border-top:1px solid rgba(255,255,255,.12);margin-top:30px;padding-top:16px;font-size:.8rem;color:#8ba5c2}
@media(max-width:1180px){.top nav{display:none;position:absolute;top:72px;left:0;right:0;background:#fff;flex-direction:column;padding:10px 4vw;box-shadow:var(--shadow)}
.mt:checked~nav{display:flex}.burger{display:flex;flex-direction:column;gap:5px;margin-left:auto;cursor:pointer;padding:8px}.burger i{width:24px;height:2.5px;background:var(--navy);border-radius:2px}}
@media(max-width:1020px){.hero{grid-template-columns:1fr}.grid{grid-template-columns:repeat(2,1fr)}.grid.three{grid-template-columns:1fr 1fr}.strip,.feats{grid-template-columns:1fr 1fr}.stat{border:0;padding:12px}
.band{grid-template-columns:1fr;padding:30px}.pillar{grid-template-columns:1fr}.cols{grid-template-columns:1fr}.chip.c1{left:8px}.chip.c2{right:8px}}
@media(max-width:620px){.grid,.grid.three,.strip,.feats,.fcols{grid-template-columns:1fr}.hero{padding-top:36px}.sechead{display:block}table{display:block;overflow-x:auto}}
"""


def video_block():
    if CFG.get("video_embed_url"):
        return (f'<div class="video"><iframe src="{CFG["video_embed_url"]}" title="Costa Leona presentation" '
                'allowfullscreen loading="lazy"></iframe></div>')
    return f'<div class="pending">{PENDING} Recorded presentation (5-8 minutes) will be embedded here.</div>'


def build():
    process_images()
    for n in ("logo-512.png", "favicon-32x32.png"):
        src = ROOT / "branding" / n
        if src.exists():
            Image.open(src).save(IMG / n)
    charts()
    hero = Image.open(SHOTS / "19_live_aws_chat_https.png").convert("RGB")
    hero = hero.crop((0, 56, hero.width, hero.height))
    hero.resize((1400, round(hero.height * 1400 / hero.width)), Image.LANCZOS).save(IMG / "hero_chat.png", optimize=True)
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    exec(open(ROOT / "tools" / "pages.py", encoding="utf-8").read(), globals())


if __name__ == "__main__":
    build()
    left = [f.name for f in DOCS.glob("*.html") if PENDING in f.read_text(encoding="utf-8")]
    print("built", len(list(DOCS.glob("*.html"))), "pages; pages still containing", PENDING, ":", left or "none")
