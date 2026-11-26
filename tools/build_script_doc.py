"""Build the presentation video script as a Word document (opens in Google Docs)."""
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = sys.argv[1]
NAVY, RED, GREEN, BLUE = RGBColor(0x0C, 0x2D, 0x57), RGBColor(0xB3, 0x26, 0x1E), RGBColor(0x0B, 0x6B, 0x3A), RGBColor(0x1F, 0x6F, 0xB5)
d = Document()
for s in d.sections:
    s.left_margin = s.right_margin = Inches(0.9)
    s.top_margin = s.bottom_margin = Inches(0.8)
d.styles["Normal"].font.name = "Calibri"
d.styles["Normal"].font.size = Pt(11.5)
for n, sz in (("Heading 1", 22), ("Heading 2", 15), ("Heading 3", 12.5)):
    h = d.styles[n]
    h.font.name = "Calibri"
    h.font.size = Pt(sz)
    h.font.color.rgb = NAVY
    h.font.bold = True


def shade(cell, hexv):
    pr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hexv)
    pr.append(sh)


def p(text="", bold=False, italic=False, color=None, size=None, after=6):
    para = d.add_paragraph()
    r = para.add_run(text)
    r.bold, r.italic = bold, italic
    if color:
        r.font.color.rgb = color
    if size:
        r.font.size = Pt(size)
    para.paragraph_format.space_after = Pt(after)
    return para


def bullets(items):
    for t in items:
        para = d.add_paragraph(style="List Bullet")
        para.add_run(t)
        para.paragraph_format.space_after = Pt(2)


def table(head, rows, widths, hfill="0C2D57"):
    t = d.add_table(rows=1, cols=len(head))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(255, 255, 255)
        shade(c, hfill)
    for row in rows:
        cs = t.add_row().cells
        for i, v in enumerate(row):
            cs[i].text = ""
            cs[i].paragraphs[0].add_run(v).font.size = Pt(10)
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Inches(w)
    d.add_paragraph().paragraph_format.space_after = Pt(2)


d.add_heading("Presentation video script", 1)
p("Costa Leona Resort (Leona front desk) - SAM10 Final Project - target 7:00 (allowed 5 to 8 minutes)", bold=True, color=NAVY, size=13)
p("Speak in English (the video is part of the submission). Read it naturally; do not memorise. Notes in italics are for you only.", italic=True)

d.add_heading("The story in one line", 2)
p("\"Operations is the assignment: I took an open-source AI chat, made it mine, put it on AWS, and then ran it - monitored, backed up, secured and automated - and fixed it when it broke.\"", italic=True)

d.add_heading("Plan at a glance", 2)
table(["Time", "Part", "On screen", "Main message"], [
    ["0:00-0:35", "1. Intro and roadmap", "Website home", "Who I am, what the system is, what I will show"],
    ["0:35-1:45", "2. The system", "Website System page, then LIVE site", "The reskin is real, answers come from my own data, one honest failure"],
    ["1:45-2:35", "3. AWS design", "Website AWS design diagram", "Where everything runs; how a question travels"],
    ["2:35-3:30", "4. Monitoring", "LIVE CloudWatch dashboard, alarms, Gmail alert", "I know when it is unhealthy, and an alert reached me"],
    ["3:30-4:20", "5. Backup and restore", "LIVE S3 versions, website restore figures", "Backups are proven by a restore"],
    ["4:20-5:00", "6. Security", "LIVE IAM users, website security table", "MFA, role, no keys, nothing public"],
    ["5:00-6:15", "7. Automation and incident", "Website Incident page", "Two unattended jobs; one fault found, fixed, prevented"],
    ["6:15-7:00", "8. Results and close", "Website Results, Next steps", "Numbers, the honest gap, what next"]], [0.9, 1.5, 2.0, 2.5])

d.add_heading("BAWAL IPAKITA (never show on screen)", 2)
tb = d.add_table(rows=1, cols=1)
tb.style = "Table Grid"
c = tb.rows[0].cells[0]
shade(c, "FDE8E6")
c.text = ""
items = [
    "Gemini API key: do NOT open Google AI Studio (it lists the key and your other projects). Use the masked screenshot on the website instead.",
    "The guest-desk password and any Parameter Store VALUE: never click 'Show decrypted value', never run get-parameter with --with-decryption. The parameter NAMES are fine.",
    "Your personal e-mail address: not in the Gmail inbox list, not in the Google account menu, not in any command (for example ALERT_EMAIL=...), not on the root 'Security credentials' page.",
    "The bottom of any AWS Notifications e-mail: the unsubscribe link contains your e-mail and the subscription id. Show only the alarm details, never scroll to the bottom. Safer: use the masked screenshots on the website.",
    "The .env file, VS Code or Notepad with .env, or any terminal that prints it. It contains keys.",
    "Authenticator codes, QR codes, saved-password or autofill pop-ups, the browser profile or password manager.",
    "Billing pages with payment methods or card details (the Credits widget on the console home is fine).",
    "Anything from other courses: the other EC2 instance in the instance list (filter by tag Project = SAM10, or use the website figure), other budgets, other AI Studio projects.",
    "Any real person's data. Everything in the system is invented; keep it that way in the chat you type.",
]
first = True
for t in items:
    para = c.paragraphs[0] if first else c.add_paragraph()
    first = False
    r = para.add_run("X  " + t)
    r.font.size = Pt(10.5)
    r.font.color.rgb = RED
d.add_paragraph().paragraph_format.space_after = Pt(2)
p("OK to show: the CloudFront URL, the account number, instance and bucket names, alarm names, parameter names, the website, the CloudWatch and S3 consoles, the masked screenshots on the website.", color=GREEN, bold=True)

d.add_heading("Before you press record (10 minutes)", 2)
bullets([
    "Sign in to AWS as stephanie-ops, switch role to SAM10-Admin, region Singapore. Use a clean browser window (no bookmarks bar, no extension icons).",
    "Tab 1: website home (https://teptepphhh.github.io/costa-leona-resort/). Zoom the browser to 110% so the text is readable in the video.",
    "Tab 2: live system https://d3s6rxkesmrq3z.cloudfront.net, already signed in as the guest-desk user (never show the password).",
    "Tab 3: CloudWatch dashboard CostaLeona, range 12 h. Tab 4: CloudWatch Alarms.",
    "Tab 5: S3 bucket costaleona-377141957329-content with 'List versions' ON (knowledge/ folder).",
    "Tab 6: IAM users page (stephanie-ops with MFA). Tab 7: EC2 security group costaleona-web (one inbound rule).",
    "Tab 8: Gmail, already open on the 'ALARM costaleona-disk-high' e-mail, scrolled to the alarm details only.",
    "Turn off notifications (Windows Focus Assist). Close chat apps. Keep water nearby.",
])

d.add_heading("The script", 1)


def seg(title, time, screen, say, bridge):
    d.add_heading(f"{title}   [{time}]", 2)
    p("ON SCREEN: " + screen, bold=True, color=NAVY, size=10.5, after=2)
    for s in say:
        if s.startswith("["):
            p(s, italic=True, color=BLUE, size=10.5, after=2)
        else:
            p(s, after=6)
    if bridge:
        p("BRIDGE -> " + bridge, bold=True, color=GREEN, size=10.5, after=8)


seg("1. Introduction and roadmap", "0:00-0:35", "Website home page", [
    "Hello, I am Stephanie Joy Revano, working alone on the SAM10 final project.",
    "This is Costa Leona Resort, a fictional beach resort, and Leona, its AI front-desk assistant. I took the open-source application LibreChat, made it my own, deployed it on AWS, and then operated it.",
    "Operations is the point of this project, so I will show you six things: the system, the AWS design, how I monitor it, how I protect the data, how I secure it, and what happened when I broke it on purpose."],
    "First, the system itself.")
seg("2. The system: reskin and live demo", "0:35-1:45", "Website System page (original versus mine), then the LIVE site", [
    "On the left is the original LibreChat: a feather logo, a green theme, and a generic answer. It told me check-in is 'usually 3 PM' because it knows nothing about my resort.",
    "On the right is mine: a new name, a new logo, my own colours and wording, and six invented resort documents stored in S3. Nothing is real; there are no real people in the data. The base system is LibreChat by Danny Avila, MIT licence, credited on the site.",
    "[switch to the LIVE site and point to the HTTPS address bar]",
    "This is the deployed system on AWS over HTTPS. I will ask: 'What time is check-in, and can I check out late?'",
    "[wait for the answer, then read it]",
    "It answers from my documents: two p.m., and late check-out is 1,200 pesos if requested the day before.",
    "I also tested its limits. On my third test question, a family with two adults and two children, Leona recommended a villa that fits only one child, without warning. That is a real failure, and it is on the website. My quality number is 30 out of 30 on my test set, against 9 out of 30 for the generic version, with the caveat that I wrote the questions."],
    "That is what the guest sees. Now let me show you where it runs.")
seg("3. AWS infrastructure design", "1:45-2:35", "Website AWS design page: the diagram", [
    "One account, one region: Singapore. A guest reaches CloudFront, which gives me free HTTPS. CloudFront is the only thing allowed to reach my EC2 server: the security group has a single rule, port 80 from CloudFront, and no SSH.",
    "[point along the diagram, left to right]",
    "On the server there are three Docker containers: LibreChat, my Leona gateway, and MongoDB, which has no published port.",
    "When a guest asks a question, LibreChat sends it to the gateway. The gateway reads the model key from Parameter Store and the six documents from S3, and calls the Gemini API, which is outside AWS and on the free tier. The answer comes back, and the gateway logs the request and sends metrics to CloudWatch.",
    "I optimised for security and operations. I accepted reliability as my weaker pillar: one server, one zone."],
    "Now: how do I know it is healthy?")
seg("4. Monitoring", "2:35-3:30", "LIVE CloudWatch dashboard, then Alarms, then the Gmail alert (alarm details only)", [
    "This is my CloudWatch dashboard with real data: requests, failed answers, response time, CPU, disk, memory, and the pass rate of an hourly test.",
    "[switch to Alarms]",
    "I have eight alarms. For example, disk above 85 percent for two minutes. The guideline suggests an hour, but a chat system that logs every request can fill a small disk fast. In my incident it took 93 seconds.",
    "[switch to Gmail and show the alarm details, not the bottom of the e-mail]",
    "Every alarm e-mails me. This is a real alert: the disk alarm at 03:38 UTC. Every request is also logged as one line with the question, duration, success and version, with 14-day retention."],
    "An alert is only useful if I can recover. Backups next.")
seg("5. Backup and restore", "3:30-4:20", "LIVE S3 bucket (versions), then the website restore figures", [
    "The database is MongoDB in a container. An automatic job dumps it to S3 every hour and keeps it for 14 days. The documents live in a versioned S3 bucket.",
    "[S3: show the versions toggle]",
    "A backup you have never restored is only a hope, so I tested it. I took a fresh backup, started an empty MongoDB container, and restored it. Live and restored counts were identical and the guest account came back. The restore took seven seconds, 25 seconds for the whole procedure.",
    "[show the restore figure on the website]",
    "I also deleted a document from S3 and brought it back from its previous version, with the same checksum.",
    "So my recovery point is up to one hour, and my measured database recovery time is 25 seconds. Rebuilding the whole server from scripts I estimate at 15 to 20 minutes. That one I did not measure."],
    "Next, how the account itself is protected.")
seg("6. Security", "4:20-5:00", "LIVE IAM users page, then the website security table, then the security group", [
    "MFA is on the root user and on my own IAM user. I do not use an administrator login: I switch into a role, SAM10-AdminRole, only when needed, and the role requires MFA.",
    "[IAM: show stephanie-ops with MFA]",
    "There are no keys in the code or in the git history. The model key and the application secrets are encrypted parameters in Parameter Store, read at runtime. CloudTrail records who did what, the disk and S3 are encrypted, and the database is not open to the internet.",
    "[security group: one rule, CloudFront only]",
    "Two honest gaps: GuardDuty is not available on this account plan, and MongoDB has no password inside its private network. That is the first thing I would fix."],
    "Now the part I was most curious about: what happens when it breaks.")
seg("7. Automation and the incident", "5:00-6:15", "Website Incident page: automation table, timeline chart, root cause, runbook", [
    "Two automations run without me: an hourly database backup, and an hourly set of test questions that publishes a pass rate and e-mails me if it falls below 80 percent. Their timestamps are on the page: 02:58 and 03:58 UTC, all successful.",
    "[show the timeline chart]",
    "Then the fault, which I created on purpose: the application's request log had no rotation. It started at 03:34:44 UTC, the disk was full at 03:36, and the alarm e-mailed me at 03:38:18. Detected in 3 minutes 34 seconds.",
    "I investigated and found one 11-gigabyte log file and a plain file handler with no rotation. That is the root cause. I trimmed the file, installed a logrotate rule and tested it: a 144-megabyte log rotated to zero. Fixed at 03:45, 7 minutes 11 seconds after the alarm. The runbook is on this page so someone else can repeat it.",
    "The site kept answering the whole time, so the alarm warned me before any guest saw an error."],
    "Let me finish with the numbers.")
seg("8. Results and close", "6:15-7:00", "Website Results page, then Next steps", [
    "Same 30 questions, same model: 9 correct before, 30 correct with Leona. I wrote the questions myself, so a keyword match cannot catch every mistake.",
    "Alarms from none to eight. Backups from none to hourly, with a tested restore. Zero secrets in the repository. The cost is covered by the account credits and recorded on the site.",
    "[show Next steps]",
    "Next, I would add MongoDB authentication, automatic recovery and snapshots, automatic deployment from Git, better quality measurement, and rate limiting to protect the model quota.",
    "Thank you. Everything I showed is on the project website, and the code is in the Git repository."],
    None)

d.add_heading("Numbers to remember", 2)
table(["What", "Number"], [
    ["Quality (same 30 questions)", "9/30 generic, 30/30 Leona (I wrote the questions)"],
    ["Alarms / log retention", "8 alarms, 14-day retention"],
    ["Time to detect / fix", "3 min 34 s / 7 min 11 s (fault 03:34:44, alarm 03:38:18, fixed 03:45:29 UTC)"],
    ["Restore", "7 s restore step, 25 s whole database procedure; RPO up to 1 hour; full rebuild about 15-20 min (estimate)"],
    ["Automation runs (UTC)", "backup 02:58 and 03:58; test questions 02:58, 03:58 and 04:58"],
    ["Cost", "credits USD 117.40 to 117.24 (about 0.16 used)"],
    ["Stack", "LibreChat (MIT) + gateway + MongoDB on EC2 t3.small, CloudFront HTTPS, S3, SSM, CloudWatch, SNS, EventBridge"]], [2.0, 4.9], "0E6168")

d.add_heading("Delivery tips", 2)
bullets([
    "Pace: about 140 words per minute. If you run long, shorten part 3 (diagram) and part 6 (security); if short, slow down at the restore and the incident.",
    "Record in parts (1-2, 3-4, 5-6, 7-8) and join them, so a mistake is cheap to redo. Windows Game Bar: Win + Alt + R.",
    "If a live page does not load, switch to the same screenshot on the website: every claim is there with its caption.",
    "Pause one second at each BRIDGE line; it tells the marker where you are going next.",
    "After recording: watch it once, check that nothing from the BAWAL list appears, upload to YouTube as Unlisted, and send me the link.",
])
d.save(OUT)
print("saved", OUT)
