"""Final printable presentation script: what to click (left) and what to say (right).
Outputs a Word file and a print-ready HTML (converted to PDF with Edge in the caller)."""
import html
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT_DOCX, OUT_HTML = sys.argv[1], sys.argv[2]

TABS = [
    ("Tab 1", "Project website: https://teptepphhh.github.io/costa-leona-resort/  (browser zoom 110%)"),
    ("Tab 2", "Live system: https://d3s6rxkesmrq3z.cloudfront.net  (already signed in; never show the password)"),
    ("Tab 3", "AWS Console > CloudWatch > Dashboards > CostaLeona  (time range 12h)"),
    ("Tab 4", "AWS Console > CloudWatch > Alarms > All alarms"),
    ("Tab 5", "AWS Console > S3 > costaleona-377141957329-content > knowledge/  (switch Show versions ON)"),
    ("Tab 6", "AWS Console > IAM > Users > stephanie-ops"),
    ("Tab 7", "AWS Console > EC2 > Security Groups > costaleona-web > Inbound rules"),
    ("Tab 8", "Gmail: the e-mail 'ALARM: costaleona-disk-high', scrolled to the TOP only"),
]
DONT = ("Never show: the Gemini key or Google AI Studio, the guest password, Parameter Store values, your personal e-mail address, "
        "the bottom of AWS e-mails (unsubscribe link), the .env file, authenticator codes, billing/card pages, the other course's EC2 instance.")

# (title, time, [(do, say), ...])
PARTS = [
    ("PART 1 - Introduction", "0:00 - 0:35", [
        ("TAB 1 (website home).\nLet the first screen sit there. When you say 'six things', move the mouse slowly along the top menu.",
         "Hello, I am Stephanie Joy Revano, working alone on the SAM10 final project. This is Costa Leona Resort, a fictional beach resort, and Leona, its AI front-desk assistant. I took the open-source app LibreChat, made it my own, put it on AWS, and ran it like a real service. I will show you the system, how it is built, how I monitor, back up and secure it, and what happened when I deliberately broke it. First, what a guest sees.")]),
    ("PART 2 - The system", "0:35 - 1:45", [
        ("TAB 1 > click 'System' in the top menu > scroll to 'The reskin: before and after'.\nPoint to the LEFT pictures (original), then the RIGHT pictures (mine).",
         "On the left is the original LibreChat: a feather logo, a green theme, and a generic answer. It says check-in is usually 3 PM, because it knows nothing about my resort. On the right is mine: a new name, logo, colours and wording, and six invented resort documents in S3. Nothing here is real. The base system is LibreChat by Danny Avila, MIT licence, credited on the site."),
        ("TAB 2 (live system).\nPoint to the address bar (https).\nClick the chat box, type:\nWhat time is check-in, and can I check out late?\nPress Enter. Wait for the answer and point to it.",
         "This is the live system on AWS, over HTTPS. I will ask: what time is check-in, and can I check out late?  ...  It answers from my documents: two p.m., and late check-out costs 1,200 pesos."),
        ("TAB 1 > 'System' page > scroll down to the 'Three test questions' table.\nPoint to the third row (the red one).",
         "I also tested its limits. For a family with two adults and two children, Leona recommended a villa that fits only one child, without a warning. That is a real failure, and it is on the website. Overall it answers 30 of my 30 test questions, against 9 for the generic version, though I wrote the questions myself.")]),
    ("PART 3 - AWS design", "1:45 - 2:35", [
        ("TAB 1 > click 'AWS design' in the top menu. The diagram is at the top.\nWith the mouse follow the path: Guest > CloudFront > the EC2 box > Gemini on the right.",
         "Behind that is this design: one AWS account, one region, Singapore. A guest reaches CloudFront, which gives me free HTTPS, and CloudFront is the only thing allowed to reach my EC2 server. The server runs three containers: LibreChat, my Leona gateway, and MongoDB, which is not exposed to the internet. For each question, the gateway reads the model key from Parameter Store and my documents from S3, calls the Gemini API outside AWS, and returns the answer. It also logs every request and sends metrics to CloudWatch. I optimised for security and operations, and accepted reliability as my weaker pillar: one server, one zone.")]),
    ("PART 4 - Monitoring", "2:35 - 3:30", [
        ("TAB 3 (CloudWatch dashboard CostaLeona).\nPoint to the top row (requests, errors, response time), then the bottom row (CPU, disk, memory).",
         "A design is only useful if I know when it breaks. This is my CloudWatch dashboard, with real data: requests, failed answers, response time, CPU, disk and memory, and an hourly test pass rate."),
        ("TAB 4 (CloudWatch Alarms > All alarms).\nPoint to the list of eight alarms.",
         "I have eight alarms. For example, the disk alarm fires above 85 percent for two minutes, because a chat system that logs every request can fill a small disk fast. In my incident it took 93 seconds."),
        ("TAB 8 (Gmail alarm e-mail).\nShow ONLY the top: the title, 'OK -> ALARM', and the time 03:38:18 UTC. Do NOT scroll down.",
         "Every alarm e-mails me. This is a real alert from my incident, at 03:38 UTC. Every request is also logged, with the question, duration, outcome and version.")]),
    ("PART 5 - Backup and restore", "3:30 - 4:20", [
        ("TAB 5 (S3 > knowledge/, Show versions ON).\nPoint to the 'Version ID' column and to the two entries for 05_house_rules.md.",
         "Knowing about a problem is half the job; the other half is recovering. My documents are in a versioned S3 bucket, so an old copy is never lost. The database is MongoDB, and an automatic job dumps it to S3 every hour and keeps the dumps for 14 days."),
        ("TAB 1 > click 'Operate' in the top menu > scroll to 'Restore tests'.\nPoint to the two restore screenshots and to the words 'RESULT PASS'.",
         "A backup you have never restored is only a hope, so I tested it. I restored the latest backup into an empty MongoDB container: the counts matched the live database and the guest account came back. The restore took seven seconds, the whole procedure 25. I also deleted a document from S3 and restored it from its previous version, with the same checksum. So I can lose up to one hour of chat history, and a database restore takes about half a minute.")]),
    ("PART 6 - Security", "4:20 - 5:00", [
        ("TAB 6 (IAM > Users > stephanie-ops).\nPoint to 'Enabled with MFA'.",
         "Protecting data also means controlling access. MFA is on the root account and on my IAM user. I do not use an administrator login: I switch into an admin role only when I need it, and that role requires MFA too."),
        ("TAB 7 (EC2 security group costaleona-web, Inbound rules): point to the single rule.\nThen TAB 1 > 'Operate' > scroll to the 'Security' table.",
         "There are no keys in the code or git history: the model key and secrets are encrypted parameters in Parameter Store. CloudTrail records who did what, the disk and S3 are encrypted, and the only inbound rule is CloudFront on port 80. Two honest gaps: GuardDuty is not available on this account plan, and MongoDB has no password inside its private network. That is what I would fix first.")]),
    ("PART 7 - Automation and the incident", "5:00 - 6:15", [
        ("TAB 1 > click 'Incident' in the top menu.\nThe automation table with timestamps is at the top: point to the two runs of each job.",
         "Those controls are the plan. Here is what happened when something actually broke. First, two automations run without me: an hourly backup, and an hourly set of test questions that e-mails me if the pass rate drops below 80 percent. Each has run on its own at least twice, at 02:58 and 03:58 UTC."),
        ("Scroll down to the timeline chart, then to the grey 'Root cause' box.\nPoint to the three times: 03:34:44, 03:38:18, 03:45:29.",
         "Then the incident, which I created on purpose. The fault started at 03:34:44 UTC, the disk was full at 03:36, and the alarm e-mailed me at 03:38: three minutes thirty-four seconds to detect. I found one 11-gigabyte log file, written by a file handler with no rotation. That was the root cause."),
        ("Scroll down to 'Fix and prevention', then to the Runbook box.",
         "I trimmed the file, added a log rotation rule, and tested it: a 144-megabyte log rotated down to zero. It was fixed seven minutes eleven seconds after the alarm, and the runbook is here so someone else can repeat it. The site kept answering throughout, so the alarm warned me before any guest saw an error.")]),
    ("PART 8 - Results and close", "6:15 - 7:00", [
        ("TAB 1 > click 'Results' in the top menu.\nPoint to the four big numbers at the top, then the before/after table.",
         "To finish, the results. On the same 30 questions and the same model, the generic version scored 9 and Leona scored 30. Alarms went from none to eight, backups from none to hourly with a tested restore, and there are no secrets in the repository. The cost is covered by the account credits and recorded on the site."),
        ("TAB 1 > click 'Next steps' in the top menu.\nPoint to idea number 1.",
         "Next, I would add a password to MongoDB, then automatic recovery and snapshots, and rate limiting to protect the model quota. Thank you for watching. Everything is on the project website, and the code is in the Git repository.")]),
]

words = sum(len(s.split()) for _, _, steps in PARTS for _, s in steps)

# ----------------------------------------------------------------------------- Word
d = Document()
for s in d.sections:
    s.left_margin = s.right_margin = Inches(0.7)
    s.top_margin = s.bottom_margin = Inches(0.7)
d.styles["Normal"].font.name = "Calibri"
d.styles["Normal"].font.size = Pt(11.5)
NAVY = RGBColor(0x0C, 0x2D, 0x57)


def shade(cell, hexv):
    pr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hexv)
    pr.append(sh)


def cell_text(cell, text, bold=False, size=11, color=None):
    cell.text = ""
    first = True
    for line in text.split("\n"):
        para = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        para.paragraph_format.space_after = Pt(3)
        r = para.add_run(line)
        r.bold = bold
        r.font.size = Pt(size)
        if color:
            r.font.color.rgb = color


h = d.add_heading("Video script - Costa Leona Resort", 1)
for r in h.runs:
    r.font.color.rgb = NAVY
para = d.add_paragraph()
para.add_run("About 7 minutes. Left column: what to click and point at. Right column: what to say (read it naturally).").italic = True

d.add_heading("Open these 8 tabs before you record", 2)
t = d.add_table(rows=0, cols=2)
t.style = "Table Grid"
for k, v in TABS:
    row = t.add_row().cells
    cell_text(row[0], k, True, 10.5)
    cell_text(row[1], v, False, 10.5)
    row[0].width, row[1].width = Inches(0.8), Inches(6.3)
p = d.add_paragraph()
r = p.add_run(DONT)
r.bold = True
r.font.size = Pt(10)
r.font.color.rgb = RGBColor(0xB3, 0x26, 0x1E)
d.add_page_break()

for title, time, steps in PARTS:
    hh = d.add_heading(f"{title}   ({time})", 2)
    hh.paragraph_format.keep_with_next = True
    tb = d.add_table(rows=1, cols=2)
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_text(tb.rows[0].cells[0], "WHAT TO CLICK / SHOW", True, 10, RGBColor(255, 255, 255))
    cell_text(tb.rows[0].cells[1], "WHAT TO SAY", True, 10, RGBColor(255, 255, 255))
    shade(tb.rows[0].cells[0], "0C2D57")
    shade(tb.rows[0].cells[1], "0C2D57")
    for do, say in steps:
        row = tb.add_row().cells
        cell_text(row[0], do, False, 10.5, RGBColor(0x1F, 0x4E, 0x8C))
        shade(row[0], "EAF3FB")
        cell_text(row[1], say, False, 11.5)
    for rw in tb.rows:
        rw.cells[0].width, rw.cells[1].width = Inches(2.5), Inches(4.6)
    d.add_paragraph().paragraph_format.space_after = Pt(4)
d.save(OUT_DOCX)

# ----------------------------------------------------------------------------- HTML (print to PDF)
css = """
@page{size:A4;margin:14mm 13mm}
body{font:12.5px/1.5 Calibri,"Segoe UI",Arial,sans-serif;color:#1d2a2e}
h1{color:#0c2d57;font-size:24px;margin:0 0 4px}h2{color:#0c2d57;font-size:16px;margin:16px 0 6px;border-bottom:2px solid #E0A630;padding-bottom:3px}
.sub{font-style:italic;margin-bottom:10px}table{border-collapse:collapse;width:100%;margin-bottom:10px;page-break-inside:auto}
tr{page-break-inside:avoid}th{background:#0c2d57;color:#fff;text-align:left;padding:5px 8px;font-size:11px;letter-spacing:.05em}
td{border:1px solid #b9c7d6;padding:7px 9px;vertical-align:top}td.do{background:#eaf3fb;color:#1f4e8c;width:36%;font-size:12px}td.say{font-size:13.5px;line-height:1.55}
.tabs td:first-child{font-weight:700;width:60px}.dont{color:#b3261e;font-weight:700;font-size:11.5px;margin-top:8px}
.part{page-break-inside:avoid}.pb{page-break-before:always}
"""
out = [f"<!doctype html><meta charset=utf-8><title>Video script</title><style>{css}</style>",
       "<h1>Video script - Costa Leona Resort</h1>",
       "<div class=sub>About 7 minutes. Left column: what to click and point at. Right column: what to say (read it naturally).</div>",
       "<h2>Open these 8 tabs before you record</h2><table class=tabs>"]
for k, v in TABS:
    out.append(f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>")
out.append(f"</table><div class=dont>{html.escape(DONT)}</div>")
for i, (title, time, steps) in enumerate(PARTS):
    cls = "part pb" if i in (0,) else "part"
    out.append(f"<div class='{cls}'><h2>{html.escape(title)} &nbsp; ({html.escape(time)})</h2><table><tr><th>WHAT TO CLICK / SHOW</th><th>WHAT TO SAY</th></tr>")
    for do, say in steps:
        out.append(f"<tr><td class=do>{html.escape(do).replace(chr(10), '<br>')}</td><td class=say>{html.escape(say)}</td></tr>")
    out.append("</table></div>")
open(OUT_HTML, "w", encoding="utf-8").write("\n".join(out))
print("saved", OUT_DOCX, OUT_HTML, "| spoken words:", words, "| at 140 wpm ~", round(words / 140, 1), "min")
