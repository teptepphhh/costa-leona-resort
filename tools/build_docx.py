"""Build the single complete project report (DOCX) with every screenshot, from the same evidence as the website.
Usage: python tools/build_docx.py "<screenshots folder>" "<output.docx>"
"""
import json
import statistics
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "docs" / "img"          # screenshots with e-mail addresses already masked
SHOTS = Path(sys.argv[1])
OUT = Path(sys.argv[2])
CFG = json.loads((ROOT / "tools" / "site_config.json").read_text(encoding="utf-8"))
ev = ROOT / "docs" / "evidence"
leona = json.loads((ev / "eval_local_full_2026-11-26.json").read_text(encoding="utf-8"))
base = json.loads((ev / "eval_baseline_generic_2026-11-26.json").read_text(encoding="utf-8"))
L, B = leona["summary"], base["summary"]
LP, BP = f"{L['passed']}/{L['total']}", f"{B['passed']}/{B['total']}"
L_AVG = statistics.mean(r["ms"] for r in leona["results"]) / 1000
B_AVG = statistics.mean(r["ms"] for r in base["results"]) / 1000
CAP = {}
for line in (SHOTS / "captions.txt").read_text(encoding="utf-8").splitlines():
    parts = [s.strip() for s in line.split(" | ")]
    if len(parts) >= 2 and parts[0].endswith(".png"):
        CAP[parts[0]] = parts[1].replace("Caption: ", "", 1)

NAVY = RGBColor(0x0C, 0x2D, 0x57)
doc = Document()
for s in doc.sections:
    s.left_margin = s.right_margin = Inches(0.9)
    s.top_margin = s.bottom_margin = Inches(0.8)
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(10.5)
for n, sz in (("Heading 1", 20), ("Heading 2", 14), ("Heading 3", 12)):
    h = doc.styles[n]
    h.font.name = "Calibri"
    h.font.size = Pt(sz)
    h.font.color.rgb = NAVY
    h.font.bold = True

FIG = {"n": 0}
FIGMAP = {}


def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_)
    tcPr.append(shd)


def para(text="", bold=False, italic=False, size=None, align=None, color=None, space=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space)
    return p


def rich(text):
    """paragraph with **bold** segments and [[pending]] highlights"""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    import re
    for tok in re.split(r"(\*\*.+?\*\*|\[\[.+?\]\])", text):
        if tok.startswith("**"):
            p.add_run(tok[2:-2]).bold = True
        elif tok.startswith("[["):
            r = p.add_run("[" + tok[2:-2] + "]")
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
        else:
            p.add_run(tok)
    return p


def bullets(items):
    for t in items:
        p = doc.add_paragraph(style="List Bullet")
        import re
        for tok in re.split(r"(\*\*.+?\*\*)", t):
            if tok.startswith("**"):
                p.add_run(tok[2:-2]).bold = True
            else:
                p.add_run(tok)
        p.paragraph_format.space_after = Pt(2)


def table(head, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(head))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)
        shade(c, "0C2D57")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(9.5)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def fig(name, label="", width=6.3, cap=None):
    path = IMG / name
    if not path.exists():
        path = SHOTS / name
    FIG["n"] += 1
    n = FIG["n"]
    FIGMAP[name] = n
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width))
    c = doc.add_paragraph()
    r = c.add_run(f"Figure {n}. ")
    r.bold = True
    r.font.size = Pt(9)
    if label:
        r2 = c.add_run(f"[{label}] ")
        r2.bold = True
        r2.font.size = Pt(9)
    r3 = c.add_run(cap or CAP.get(name, name))
    r3.font.size = Pt(9)
    r3.italic = True
    c.paragraph_format.space_after = Pt(10)


def h(text, level=1):
    doc.add_heading(text, level=level)


# ================================================================================ cover
para("", space=60)
para("SAM10 - Systems Administration and Maintenance", size=13, color=NAVY, bold=True)
para("Final Project Report", size=30, bold=True, color=NAVY, space=2)
para("Costa Leona Resort - Leona front desk", size=20, color=RGBColor(0x0E, 0x61, 0x68), space=18)
para("Build, deploy and run an AI system on AWS", size=13, italic=True, space=40)
table(["Item", "Detail"], [
    ["Student", f"{CFG['student_name']} (working alone)"], ["Student ID", CFG["student_id"]],
    ["Base system", "LibreChat (MIT), https://github.com/danny-avila/LibreChat"],
    ["Live system (HTTPS)", CFG["live_url"]], ["Project website", CFG["site_url"]], ["Presentation video", CFG.get("video_watch_url", "")],
    ["Git repository", CFG["repo_url"]], ["AWS region", "ap-southeast-1 (Singapore)"],
    ["Report date", "27 November 2026"]], [1.8, 4.7])
para("This document collects the project website content and every piece of evidence (screenshots and command output) in one place. "
     "All data in the system is invented; no result or screenshot is fabricated. E-mail addresses were masked.", italic=True, size=9.5)
doc.add_page_break()

# ================================================================================ 1 summary
h("1. Executive summary")
rich("**What it is.** Costa Leona Resort is a fictional beach resort. **Leona** is its virtual front-desk assistant: guests ask in plain English or Filipino about rooms, prices, check-in and check-out, house rules and directions, and Leona answers from six short resort documents. It never books, charges or decides anything about a person. It is a reskin of the open-source chat application LibreChat and runs on Amazon Web Services at " + CFG["live_url"] + ".")
rich(f"**What was wrong with how it was run.** The starting point was an unmodified chat application on a laptop. It knew nothing about the resort (only {BP} of my 30 test questions were answered correctly), nobody would be told if it broke, nothing was backed up, its keys lived in a local file, the AWS account was set up with the root login, and I had no audit trail of my own beyond AWS's default 90-day event history.")
rich("**What I changed.** I gave it its own identity, knowledge and wording; deployed it to AWS behind HTTPS; moved every key into Parameter Store; turned on multi-factor authentication and switched to a normal user that borrows admin rights only through a role; enabled CloudTrail; built a dashboard and eight alarms that e-mail me; automated hourly database backups and hourly test questions; proved a restore works; and deliberately created a disk-full fault that I found, fixed, prevented and wrote a runbook for.")
rich("**What improved** (measured; see section 9):")
bullets([f"Answer quality on the same 30 questions: **{BP} ({100*B['passed']/B['total']:.0f}%) to {LP} ({100*L['passed']/L['total']:.0f}%)**.",
         "Alarms: **0 to 8**, all e-mailing me. A real alert reached my inbox **3 min 34 s** after the fault began; the fault was fixed **7 min 11 s** later.",
         "Backups: none to hourly to S3, with a tested restore that took **25 seconds**.",
         "Secret values stored in the repository or its history: **0**."])
rich("**Honest limits.** One small server in one Availability Zone; MongoDB runs without a password inside a private Docker network; GuardDuty is not available on this account plan; the quality score is a keyword match on questions I wrote myself.")
rich("Presentation video: " + (CFG.get("video_watch_url") or "[[video link to be added]]"))

# ================================================================================ 2 design
h("2. AWS infrastructure design")
para("One AWS account, one region, one small server. Every resource is tagged Project=SAM10 and built by the scripts in the repository (infra/).")
fig("architecture.png", "E-18", 6.5, "Infrastructure design: where every part runs and how a question travels from the guest to the model and back (steps 1-8).")
table(["Layer", "Service", "What it is for"], [
    ["Networking / HTTPS", "Amazon CloudFront (default certificate)", "Free HTTPS address (*.cloudfront.net); the only thing allowed to reach the server."],
    ["Networking", "EC2 security group costaleona-web", "One rule: TCP 80 from the CloudFront prefix list. No SSH, no 0.0.0.0/0."],
    ["Compute", "EC2 t3.small, Amazon Linux 2023, 20 GB encrypted gp3, IMDSv2", "Three Docker containers: LibreChat, the Leona gateway, MongoDB."],
    ["Database", "MongoDB 8 container, Docker volume", "Users and chat history. No published port. Backed up hourly to S3."],
    ["Storage", "Amazon S3 (versioned, encrypted, private)", "knowledge/ holds the six documents; backups/mongo/ holds hourly dumps (14 days)."],
    ["Config and secrets", "Systems Manager Parameter Store", "SecureString parameters for the model key, app secrets and gateway token."],
    ["Operations", "CloudWatch, SNS, EventBridge + SSM Run Command, CloudTrail, AWS Budgets", "Dashboard, 8 alarms, 5 log groups, e-mail alerts, schedules, audit trail, cost alert."],
    ["External model", "Google Gemini API, free tier", "The language model, outside AWS; no AWS AI service is used."]], [1.3, 2.3, 2.9])
h("How a question travels", 3)
for i, t in enumerate([
        "The guest types a question; the browser sends it over HTTPS to CloudFront.", "CloudFront forwards it to the EC2 instance on port 80.",
        "LibreChat passes the chat to the Leona gateway.",
        "The gateway reads the model key from Parameter Store and the six documents from S3 and builds the prompt.",
        "The gateway calls the Gemini API.", "The answer streams back through LibreChat to the guest.",
        "The gateway writes one log line (question, duration, success, version) and sends metrics to CloudWatch; an alarm e-mails me through SNS if something is wrong."], 1):
    para(f"{i}. {t}", space=2)
rich("**Pillar trade-off.** I optimised for Security and Operational Excellence. I deliberately accepted Reliability as the weaker pillar: one server in one Availability Zone is cheap and simple, and tested hourly backups mean a failure costs minutes, not days. I chose not to build a load balancer, RDS, multi-region, Kubernetes or fine-tuning.")
fig("15_deploy_complete_cloudfront_url.png", "E-02")
fig("16_ssm_restart_success.png", "", 6.0)

# ================================================================================ 3 system
h("3. The system and the system card")
h("3.1 Base system and credit", 2)
table(["Item", "Detail"], [
    ["Name / version", "LibreChat (container image librechat-dev:latest pulled 2026-11-26; source v0.8.9 reviewed locally)"],
    ["Source", "https://github.com/danny-avila/LibreChat"], ["Author", "Danny Avila and the LibreChat contributors"],
    ["Licence", "MIT (https://github.com/danny-avila/LibreChat/blob/main/LICENSE): reuse, modification and rebranding allowed with the copyright notice kept"],
    ["What it did originally", "A ChatGPT-style chat interface for many model providers, with user accounts"]], [1.6, 4.9])
h("3.2 The reskin: original versus mine", 2)
fig("09_original_login_branding.png", "E-05", 5.2)
fig("10_reskin_signup_page.png", "E-01", 5.2)
fig("08_local_original_generic_answer.png", "E-05", 6.0)
fig("11_reskin_chat_answer.png", "E-01", 6.0)
table(["Part", "Original", "Mine", "Why"], [
    ["Name / branding", "LibreChat, feather logo, green theme", "Costa Leona Resort, sun-and-waves logo, teal theme, favicon, browser title", "A stranger must not recognise the original"],
    ["Data / content", "None", "Six invented resort documents (7.6 KB) in S3", "Data must be my own, with no real people"],
    ["Wording / prompts", "Generic assistant", "Persona Leona, front-desk language, welcome text, footer, strict answer-only-from-knowledge prompt", "Domain language belongs to the resort world"],
    ["Interface", "Model picker, presets, agents, prompts, memories, web search", "One fixed Leona - Front Desk assistant; everything else hidden; sign-up closed on AWS", "Fewer ways to misuse; simpler to operate"],
    ["AWS services", "None", "S3, Parameter Store, CloudWatch, SNS, EventBridge + SSM", "At least one integration beyond hosting"]], [1.1, 1.5, 2.6, 1.3])
fig("19_live_aws_chat_https.png", "E-01 / E-02", 6.0)
fig("06_model_key_free_tier.png", "", 6.0)
h("3.3 Three test questions (two working, one failing)", 2)
table(["#", "Question", "Answer (as returned)", "Verdict"], [
    ["T1", "What time is check-in, and how do I get there from Manila?", "Standard check-in time is at 2:00 PM; then the driving route, the bus route and the Friday/Saturday shuttle (PHP 700).", "Correct"],
    ["T2", "Are pets allowed?", "Pets are not allowed at Costa Leona Resort, except for registered service animals.", "Correct"],
    ["T3", "We are 2 adults and 2 children aged 7 and 9. Which room should we book and how much per night?", "Recommended the Lioness Family Villa (PHP 9,500), saying it accommodates up to 4 adults and 1 child, without flagging that two children exceed the limit.", "FAILS: unsafe recommendation"]], [0.4, 2.0, 3.0, 1.1])
rich("Other observations: asked 'Where is the pool?', Leona correctly says it has no information (a gap in my documents); asked about Christmas Day it inferred that the resort is open because the front desk is open 24 hours (an over-inference); the first live try hit an HTTP 503 'high demand' from the Gemini service.")
fig("27_live_chat_three_questions.png", "E-03", 6.0)
fig("07_local_original_gemini_503.png", "E-03", 5.6)
h("3.4 How good is it? (E-04)", 2)
rich(f"**The one number: {LP} correct ({100*L['passed']/L['total']:.0f}%)** on 30 labelled questions, against {BP} ({100*B['passed']/B['total']:.0f}%) for the same model without the resort knowledge. Measured with eval/run_eval.py, which passes an answer only if it contains the required fact(s) listed in eval/questions.csv. Caveats: I wrote the questions; a keyword match cannot judge subtle mistakes (T3 would pass a keyword test for '9,500'); 30 questions is a small sample.")
h("3.5 System card (Appendix C)", 2)
for title, body in [
    ("1. What it does", "Leona answers guests' questions about Costa Leona Resort (fictional): room types and prices, check-in and check-out, amenities, house rules and directions. It reads six documents and replies in English or Filipino."),
    ("2. Who uses it, and who must not", "Intended users: prospective and current guests asking general questions. Explicitly NOT for: medical, legal or emergency advice; making, changing or paying for bookings; any decision about an identifiable person (grading, ranking, eligibility, discipline); anyone about to share ID, card or health details in the chat."),
    ("3. Base system", "LibreChat, https://github.com/danny-avila/LibreChat, Danny Avila and contributors, MIT licence. Originally a multi-provider chat interface with accounts."),
    ("4. What was changed", "Identity, data, wording, interface and AWS services (table in 3.2)."),
    ("5. Data", "Written by me for this project (folder knowledge/); six Markdown files, 7,612 bytes. Anything personal: No - all invented. Sent to a third-party AI service: each question plus the six documents go to the Gemini API; only invented content is ever sent (free-tier terms may allow the provider to retain prompts, which is why no real data is used). Personal-data check: " + CFG["pii_result"]),
    ("6. How good it is", f"The one number: {LP} on my test set (keyword scoring script, 30 cases: facts, policies, rules, unknowns, a booking request, safety). An example it gets wrong: test T3, the family of two adults and two children recommended into a villa limited to one child."),
    ("7. How it is served", "Runs on EC2 t3.small, ap-southeast-1c, Docker; HTTPS through CloudFront at " + CFG["live_url"] + ". LibreChat calls the gateway at /v1/chat/completions with a bearer token. Model: Google Gemini gemini-3.5-flash-lite (fallback gemini-3.5-flash), free tier. If unavailable: 3 retries, then 'Model provider error, please try again'; a failure rate above 5% over 15 minutes e-mails me. Seen for real: HTTP 503."),
    ("8. Limitations and risks", "Cannot book, change or pay; cannot know anything outside the six documents; no guarantee its arithmetic or capacity checks are right. Missing or stale facts give wrong or empty answers (the pool location is undocumented). A guest could try to override its rules; the prompt forbids it but it is not a security boundary. A user must always check prices, dates, capacity and policies with the front desk."),
    ("9. Operational summary", "Code: " + CFG["repo_url"] + ". Backups: MongoDB hourly to S3 (14 days); documents versioned and in Git. Healthy means eight alarms OK and the hourly test at 80% or more. Contact: the operator named on the declaration.")]:
    rich(f"**{title}.** {body}")

# ================================================================================ 4 baseline
h("4. Baseline: the environment before I touched it")
rich("Measured on 2026-11-26 before any deployment. An AWS account with one running server that belongs to another course project (untouched, excluded from every automation by tag), and the unmodified LibreChat on my laptop.")
table(["Area", "Baseline"], [
    ["AWS inventory (ap-southeast-1)", "1 unrelated EC2 instance; no RDS; no S3 buckets; no Elastic IPs"],
    ["Account set-up", "Root login with MFA; no IAM user for daily work; one zero-spend budget left over from another project (I added the SAM10 budget on day one); free-plan credits USD 117.40"],
    ["The AI system", f"Original LibreChat on a laptop, no resort knowledge: {BP} test questions correct; asked 'What time is check-in?' it answers generically"],
    ["Monitoring, backups, automation, audit trail", "None"], ["Secrets", "Model key and app secrets in a local .env file"]], [2.0, 4.5])
fig("04_signed_in_as_iam_user_credits.png", "", 6.0)
fig("05_baseline_inventory_cloudshell.png", "", 6.0)
fig("01_budget_alert_created.png", "E-16", 6.0)

# ================================================================================ 5 WA
h("5. Well-Architected review")
rich("Pass 1 describes the system as it stood when the deployment first worked (2026-11-26, about 03:00 UTC): running and reachable, but before CloudTrail, the restore tests, log rotation and the runbook. I wrote it up afterwards from the evidence timeline, not in real time, and used it to decide what to build next. Pass 2 was made after the incident. Verdicts are my own assessment (I did not use the AWS Well-Architected Tool).")
table(["Pillar", "What my system actually does", "Pass 1", "Pass 2"], [
    ["Operational Excellence", "Dashboard, 8 alarms, request log, two scheduled automations, scripts in Git, tested runbook; fault found, fixed, prevented.", "adequate", "good"],
    ["Security", "MFA, temporary admin role, secrets in Parameter Store, CloudTrail, encryption at rest, CloudFront-only access, no SSH, IMDSv2. Gaps: MongoDB without password (private network), HTTP origin hop, GuardDuty unavailable.", "adequate (no CloudTrail yet)", "adequate"],
    ["Reliability", "Hourly backups, tested database restore (25 s) and content restore, alarms. One server, one Availability Zone.", "gap (no tested restore)", "adequate"],
    ["Performance Efficiency", f"t3.small: CPU peak 40%, memory peak 70%; average answer {L_AVG:.1f} s, dominated by the external model; alarm at 10 s.", "adequate", "adequate"],
    ["Cost Optimization", "Zero-spend budget alert first, tags, smallest viable instance, 14-day log retention, S3 lifecycle, free model tier.", "good", "good"],
    ["Sustainability", "One small instance, no load balancer or database service, log rotation, hourly jobs.", "adequate", "adequate"]], [1.3, 3.5, 0.9, 0.8])
rich("**The one gap I would fix first: MongoDB authentication.** Any process on the instance's private Docker network can read or change every user and chat without a password. It is not reachable from the internet, so the risk is low, but it is the cheapest high-value fix and it protects the most sensitive data the system holds.")
fig("20_cloudtrail_logging_guardduty_unavailable.png", "E-17", 6.2)

# ================================================================================ 6 operate
h("6. Monitoring, backup and restore, security")
h("6.1 Monitoring", 2)
rich("The dashboard separates 'the machine is unhealthy' (CPU, disk, memory) from 'the product is broken' (failed or empty answers, low pass rate).")
fig("28_cloudwatch_dashboard_before_incident.png", "E-06", 6.4)
table(["Alarm", "Metric", "Threshold", "Why this value"], [
    ["cpu-high", "EC2 CPUUtilization", ">85% for 10 min", "Appendix A value; stuck process or runaway loop"],
    ["status-check-failed", "EC2 StatusCheckFailed", ">0 for 1 min", "Instance unhealthy"],
    ["disk-high", "CWAgent disk_used_percent", ">85% for 2 min", "Changed from 1 hour: a chat system that logs every request can fill a small disk in minutes (93 s in my incident)"],
    ["memory-high", "CWAgent mem_used_percent", ">90% for 5 min", "Containers may be killed"],
    ["response-slow", "ResponseTimeMs", "average >10 s for 5 min", "Changed from 3 s: the external model alone takes 1-9 s"],
    ["answers-failed", "failed / (failed + succeeded)", ">5% over 15 min", "Up but not working (e.g. a Gemini 503 storm)"],
    ["empty-answers", "EmptyAnswer", ">0 in 30 min", "Knowledge base missing or unreadable"],
    ["passrate-low", "PassRate (smoke)", "<80% per hour", "Quality dropped though nothing is technically broken"]], [1.2, 1.7, 1.3, 2.3])
fig("17_alarms_dashboard_created.png", "E-07", 5.8)
fig("31_alarms_list_disk_in_alarm.png", "E-07", 6.2)
fig("26_sns_subscription_confirmed.png", "", 6.4)
rich("**Proof that an alert reached me.** A real alarm raised by the disk-full fault in section 7: fault 03:34:44 UTC, alarm 03:38:18 UTC, fixed 03:45:29 UTC, OK message 03:47:18 UTC.")
fig("30_alert_email_disk_high.png", "E-08", 6.4)
fig("36_alert_email_disk_ok_resolved.png", "E-08", 6.4)
rich("**Every alarm tested.** Only the disk alarm has fired for a real fault. To prove the e-mail path of the other seven I sent a planned notification test (infra/test_alarms.sh sets each alarm to ALARM with set-alarm-state, labelled as a test, not a fault). Each alarm e-mailed me and then returned to its true state with an OK e-mail.")
fig("44_alarm_notification_test_sent.png", "E-07", 5.8)
fig("45_alarm_test_emails_inbox.png", "E-08", 6.5)
fig("46_alarm_test_email_reason.png", "E-08", 6.5)
rich("**Request log.** Every request is one JSON line: time, request id, question, duration, success, empty, status, model and version. Log groups for the gateway, LibreChat, MongoDB, the request log and the automation log have 14-day retention.")
fig("42_cloudwatch_request_log.png", "E-09", 6.4)
fig("39_log_groups_schedules_evidence_part2.png", "E-09", 5.0)
h("6.2 Backup and restore", 2)
table(["Item to restore", "Where it lives", "How it is protected"], [
    ["Database (users, chats)", "MongoDB volume on the instance", "Hourly mongodump to S3 (backups/mongo/), kept 14 days (requirement 7). No RDS."],
    ["S3 content (six documents)", "S3 bucket knowledge/", "Versioning enabled; second copy in Git"],
    ["Configuration and secrets", "Parameter Store; Git (infra/, compose files)", "Rebuilt by deploy.sh; the model key is re-created in Google AI Studio"],
    ["The server itself", "EC2, CloudFront, security group, IAM roles", "Rebuilt from infra/deploy.sh, not restored"]], [1.7, 2.2, 2.6])
fig("21_s3_versioning_backups_evidence.png", "E-10", 5.4)
fig("23_restore_test_db_part1.png", "E-11", 6.4)
fig("24_restore_test_db_part2_pass.png", "E-11", 5.2)
fig("25_restore_test_content_s3_versioning.png", "E-11", 5.6)
rich("**RPO and RTO.** RPO: up to one hour of chat history could be lost (hourly backups); the documents lose nothing (versioned and in Git). RTO: restoring the database took 25 seconds in the test; rebuilding the whole stack from scratch with the scripts is estimated at 15-20 minutes (an estimate, not measured end to end).")
h("6.3 Security", 2)
table(["Control", "Risk addressed", "Evidence"], [
    ["MFA on root and the IAM user", "A stolen password alone cannot open the account.", "E-12"],
    ["Own IAM user; admin only by assuming SAM10-AdminRole (MFA required)", "No shared or standing administrator login.", "E-12"],
    ["Secrets in Parameter Store (SecureString), read at runtime", "A leaked repository or screenshot never exposes a key; every git commit was scanned for my secret values before the first push (0 hits).", "E-13"],
    ["Only invented data; personal-data check on the request log", "Nothing personal can leave the account. " + CFG["pii_result"], "E-13"],
    ["MongoDB without published port; security group only CloudFront:80; no SSH", "The database is not open to the internet; no remote-login door.", "E-12"],
    ["Scoped roles (instance, schedule); model key in its own free-tier project", "A compromised component can do only its own job. (AI Studio keys have no expiry option; the key is revocable.)", "E-12"],
    ["CloudTrail trail with log validation", "I can see who did what and when.", "E-12"],
    ["Encrypted EBS volume, S3 AES-256, IMDSv2 required", "Stolen disks or metadata-credential theft give nothing readable.", "E-12"],
    ["Self-sign-up closed on AWS", "Strangers cannot burn the free model quota.", "repo"]], [2.4, 3.3, 0.8])
fig("02_root_mfa_enabled.png", "E-12", 6.0)
fig("03_iam_user_mfa_enabled.png", "E-12", 6.0)
fig("12_admin_role_created_root_cloudshell.png", "E-12", 6.0)
fig("13_role_switched_sam10_admin.png", "E-12", 5.6)
fig("22_iam_mfa_ssm_params_cloudtrail.png", "E-12 / E-13", 6.2)
fig("14_deploy_s3_ssm_secrets.png", "E-13", 6.2)
fig("38_compute_network_evidence_part1.png", "E-12", 6.2)
fig("40_pii_check_zero_hits.png", "", 6.0)
table(["Problem found", "Before", "After"], [
    ["Secrets in a file", "Model key and app secrets in a local .env during development", "All in Parameter Store SecureString; 0 secret values in git history"],
    ["Setup done as root", "Budget, MFA and admin role created with the root login", "Daily work as an MFA IAM user; admin only through the assumed role"],
    ["No audit trail", "No trail for this project", "CloudTrail logging since 03:04 UTC"],
    ["Unbounded log growth (found in the incident)", "Request log grew without limit", "logrotate hourly, 100 MB cap, 3 copies"]], [1.8, 2.4, 2.3])
rich("**Known gaps I did not fix:** MongoDB without a password inside the private network; plain HTTP between CloudFront and the origin (protected by the prefix-list rule); GuardDuty could not be enabled (SubscriptionRequiredException on this account plan). At start-up, infra/start.sh renders the LibreChat application secrets from Parameter Store into /opt/leona/.env on the instance (mode 600, never in Git); the Gemini key is never written to disk, because the gateway reads it from Parameter Store itself.")

# ================================================================================ 7 automation + incident
h("7. Automation and the incident")
h("7.1 Automation (E-14)", 2)
rich("Two automations run with nobody touching them. EventBridge fires a rule, SSM Run Command runs a script on the instance (only instances tagged Project=SAM10 and Role=web), and the script writes one timestamped line to /var/log/leona-automation.log (shipped to CloudWatch Logs). Code: automation/backup.sh, automation/smoketest.sh, infra/automation.sh. Hourly instead of nightly so that two unattended runs fit inside the project window.")
table(["Automation", "Schedule", "Run timestamps (UTC)"], [
    ["1. MongoDB backup to S3", "every hour", "; ".join(CFG["backup_runs"])],
    ["2. Test-question run (pass rate to CloudWatch, e-mail if below 80%)", "every hour", "; ".join(CFG["smoke_runs"])]], [2.3, 0.9, 3.3])
fig("18_automation_rules_scheduled.png", "E-14", 5.0)
fig("41_automation_two_unattended_runs.png", "E-14", 6.4)
h("7.2 The incident: disk full (E-15)", 2)
rich("Fault chosen from Appendix E ('disk full'), created on purpose in my own account: synthetic lines were appended to the application's request log until the root disk was full, then I watched my own monitoring notice.")
table(["Event", "Time (UTC, 26 Nov 2026)"], [
    ["Fault started (disk 47%, 11 GB free)", "03:34:44"], ["Disk full (100%, 38 MB free)", "03:36:17"],
    ["Alarm fired, e-mail received (noticed) - time to detect 3 min 34 s", "03:38:18"], ["Investigation started", "03:41:54"],
    ["Fixed (disk 47%) - time to fix 7 min 11 s from the alarm", "03:45:29"], ["Alarm back to OK", "03:47:18"]], [4.6, 1.9])
fig("chart_incident.png", "", 5.8, "Incident timeline (UTC), from SSM output and the alarm e-mails.")
rich("**What I saw.** The site kept answering at 100% disk: a latent outage, surviving on the last 38 MB, with writes one step from failing. The alarm gave me the warning before any guest saw an error.")
fig("29_incident_fault_started_disk_full.png", "E-15", 5.6)
fig("32_live_site_during_incident.png", "E-15", 6.0)
fig("34_dashboard_during_incident.png", "E-15", 6.4)
rich("**Root cause.** The application request log (requests.log) was written by a plain file handler with no rotation and no size limit, so it grew without bound (11 GB of the 20 GB disk), which filled the root disk. Evidence: du ranks that one file at 11 GB (MongoDB 209 MB, containers 2.3 MB); no logrotate rule mentions it; app.py lines 51-52 show the handler.")
fig("33_incident_investigation_root_cause.png", "E-15", 6.4)
rich("**Fix and prevention.** Fix: trim the log to its last 2,000 lines (disk 100% to 47%). Prevention: a logrotate rule (rotate above 100 MB, keep 3 compressed copies, copytruncate) with an hourly timer, also part of infra/start.sh so any rebuilt server has it; the root-cause metric already has an alarm (disk used >85%). Verification: a test run rotated a 144 MB log to 0 bytes; the alarm cleared at 03:47:18.")
fig("35_incident_fix_and_prevention.png", "E-15", 6.0)
fig("37_dashboard_after_recovery.png", "E-15", 6.4)
h("7.3 Runbook (Appendix D)", 2)
RUN = """RUNBOOK: root disk filling up (disk-high alarm)
Owner: operator    Last tested: 2026-11-26 (during the incident)    Takes: 10 minutes

1. WHAT THIS IS FOR
Free disk space on the web instance before the app stops saving chats and logs.

2. HOW YOU KNOW YOU NEED IT
E-mail "ALARM: costaleona-disk-high" (disk used above 85%), or the dashboard disk tile is red.
Command that shows it:  df -h /

3. WHAT IT AFFECTS
Guests: at 100% the site may stop saving chats or fail on the next write. Until then they notice nothing.

4. HOW TO DO IT
Step 1: in AWS CloudShell run  bash infra/run_on_instance.sh incident/02_investigate.sh
        -> you should see which directory is biggest (here /opt/leona/logs/gateway, one file requests.log)
Step 2: bash infra/run_on_instance.sh incident/03_fix.sh
        -> you should see the disk percentage drop and FIX_DONE

5. HOW TO CHECK IT WORKED
[ ] df -h / shows well below 85%
[ ] ask Leona "What time is check-in?" and get "2:00 PM"
[ ] OK e-mail for costaleona-disk-high within about 5 minutes; no new alarms for 10 minutes

6. HOW TO UNDO IT
03_fix.sh keeps the last 2,000 log lines and only touches requests.log; rotated copies are in /opt/leona/logs/gateway.
Remove /etc/logrotate.d/leona only if rotation itself misbehaves.

7. GOTCHAS
- AWS CLI v2 pages long output with less: press q, or set AWS_PAGER="".
- Do not delete files in /var/lib/docker by hand; MongoDB data lives there.
- CloudShell paste can fail in some browsers; type the short commands instead.

8. CHANGE HISTORY
2026-11-26 - created after the disk-full incident; log rotation added to infra/start.sh."""
for line in RUN.split("\n"):
    p = doc.add_paragraph()
    r = p.add_run(line)
    r.font.name = "Consolas"
    r.font.size = Pt(8.5)
    p.paragraph_format.space_after = Pt(0)

# ================================================================================ 8 results
h("8. Results: before and after")
rich("Method: the same 30 questions, the same model (gemini-3.5-flash-lite) and the same script, run on 2026-11-26 (Leona run finished 02:30 UTC; generic-baseline run finished 03:02 UTC). 'Before' is the model without resort knowledge, which is what the unmodified application can offer; 'after' is Leona.")
table(["Measure", "Before", "After", "Period / how measured"], [
    ["Answer quality (30 labelled questions)", f"{BP} ({100*B['passed']/B['total']:.0f}%)", f"{LP} ({100*L['passed']/L['total']:.0f}%)", "eval script, 2026-11-26"],
    ["Average answer time", f"{B_AVG:.1f} s", f"{L_AVG:.1f} s", "same script and questions; Leona sends six documents with every question and its run included Gemini retries"],
    ["Alarms that e-mail me", "0", "8", "2026-11-26"], ["Time to detect a full disk", "not detected", "3 min 34 s", "incident, 2026-11-26"],
    ["Time to fix", "n/a", "7 min 11 s from the alarm", "incident, 2026-11-26"], ["Backups / tested restore", "none", "hourly; restore in 25 s", "2026-11-26"],
    ["Secret values in repository or history", "keys in a local file", "0", "scanned before the first push"],
    ["Monthly cost / credits (E-16)", CFG["cost_before"], CFG["cost_after"] or "[to be completed]", "AWS console; credits are used first"]], [1.7, 1.3, 1.4, 2.1])
fig("chart_quality.png", "E-04", 5.8, "Questions passed by category: generic model versus Leona (same 30 questions, same model, same day).")
rich("**Caveats.** The questions are mine; a keyword matcher cannot see subtle errors (test T3); latency numbers are small samples and depend on the external model's load that day. The hourly 5-question test on AWS is the live health measure.")
rich("**Cost.** All spending is covered by the account's free-plan credits. Controls: a zero-spend budget alert created first, tags on every resource, the smallest viable instance, 14-day log retention and a shut-down plan (section 11). The disk-full incident's synthetic log flood was also shipped to CloudWatch Logs by the agent, which adds ingestion cost; the final figure is recorded above once billing data is available.")
fig("43_cost_credits_after.png", "E-16", 6.2)
rich("**A cost side effect of the incident.** Late on 26 November AWS sent a Free Tier alert: CloudWatch data processing had reached 5 GB of its 5 GB monthly allowance. This is consistent with the 11 GB synthetic log flood of the disk-full test being shipped to CloudWatch Logs by the agent. The flood is over and the normal log volume is a few kilobytes an hour, so no further growth is expected; any overage is covered by the account credits. Lesson for the runbook: a log-fill test also costs log-ingestion money, so cap or exclude the file during such a test.")
fig("47_free_tier_cloudwatch_alert.png", "E-16", 6.2)

# ================================================================================ 9 next
h("9. What I would do next")
for t in ["**MongoDB authentication** (the gap named in the review): a database password in Parameter Store plus a secret header so only CloudFront can reach the origin. About one hour.",
          "**Automatic recovery and off-instance copies:** daily EBS snapshots with Data Lifecycle Manager and an auto-recovery alarm; later a second Availability Zone behind a load balancer.",
          "**Deploy from Git automatically:** a GitHub Actions workflow that tests and then runs the SSM command that already pulls and restarts the stack.",
          "**Better quality measurement:** a larger labelled set written by someone else, capacity and arithmetic checks (test T3), and a thumbs-up/down feedback metric.",
          "**Protect the model quota:** rate limiting or AWS WAF in front of CloudFront and an alarm on request volume."]:
    rich("- " + t)

# ================================================================================ 10 evidence index
h("10. Evidence checklist (Appendix B)")
def f(*names):
    return ", ".join(f"Fig. {FIGMAP[n]}" for n in names if n in FIGMAP)
table(["ID", "What", "Where"], [
    ["E-01", "Reskinned interface with a realistic question and answer", f("10_reskin_signup_page.png", "11_reskin_chat_answer.png", "19_live_aws_chat_https.png")],
    ["E-02", "URL of the deployed system", f("15_deploy_complete_cloudfront_url.png", "19_live_aws_chat_https.png")],
    ["E-03", "Three test questions including one failure", f("27_live_chat_three_questions.png", "07_local_original_gemini_503.png") + " and section 3.3"],
    ["E-04", "Quality measurement: script and result", f("chart_quality.png") + " and section 3.4; eval/run_eval.py"],
    ["E-05", "Original system next to the reskin", f("09_original_login_branding.png", "08_local_original_generic_answer.png")],
    ["E-06", "Dashboard with real data", f("28_cloudwatch_dashboard_before_incident.png", "34_dashboard_during_incident.png", "37_dashboard_after_recovery.png")],
    ["E-07", "Alarms", f("17_alarms_dashboard_created.png", "31_alarms_list_disk_in_alarm.png")],
    ["E-08", "Alert e-mail with date and time", f("30_alert_email_disk_high.png", "36_alert_email_disk_ok_resolved.png")],
    ["E-09", "Sample of the request log", f("42_cloudwatch_request_log.png", "39_log_groups_schedules_evidence_part2.png")],
    ["E-10", "Backup settings", f("21_s3_versioning_backups_evidence.png")],
    ["E-11", "Restore output and check", f("23_restore_test_db_part1.png", "24_restore_test_db_part2_pass.png", "25_restore_test_content_s3_versioning.png")],
    ["E-12", "MFA enabled, IAM users", f("02_root_mfa_enabled.png", "03_iam_user_mfa_enabled.png", "12_admin_role_created_root_cloudshell.png", "13_role_switched_sam10_admin.png", "22_iam_mfa_ssm_params_cloudtrail.png", "38_compute_network_evidence_part1.png")],
    ["E-13", "Secrets in Parameter Store", f("14_deploy_s3_ssm_secrets.png", "22_iam_mfa_ssm_params_cloudtrail.png")],
    ["E-14", "Two automations running with timestamps", f("18_automation_rules_scheduled.png", "41_automation_two_unattended_runs.png")],
    ["E-15", "Logs and commands from the fault investigation", f("29_incident_fault_started_disk_full.png", "33_incident_investigation_root_cause.png", "35_incident_fix_and_prevention.png")],
    ["E-16", "Cost before and after", f("01_budget_alert_created.png", "04_signed_in_as_iam_user_credits.png", "43_cost_credits_after.png")],
    ["E-17", "Well-Architected review", "Section 5; " + f("20_cloudtrail_logging_guardduty_unavailable.png")],
    ["E-18", "AWS infrastructure design diagram", f("architecture.png")]], [0.6, 3.0, 2.9])

# ================================================================================ 11 declaration
h("11. Credits, AI use, clean-up and declaration")
bullets(["**LibreChat** - Danny Avila and contributors, MIT licence, https://github.com/danny-avila/LibreChat. Used as an unmodified container image; the reskin is configuration, branding and the gateway in my repository.",
         "**Google Gemini API** - free tier under Google's terms of use.",
         "Logo, resort documents, scripts and website text were made for this project. AWS documentation was used as reference."])
rich("**Use of an AI tool.** I used Claude (Anthropic) through Claude Code to write the scripts, configuration, gateway code, website and report text and the diagram, and to suggest what to check. I verified everything by running it in my own AWS account and reading the real command output; every screenshot is from my own session, and no result in this report was invented.")
rich("**Clean-up plan.** After marking: terminate the EC2 instance, delete the CloudFront distribution, the S3 buckets (empty them first), the Parameter Store parameters, the EventBridge rules, the CloudWatch alarms, dashboard and log groups, the CloudTrail trail, the SNS topic and the IAM roles, revoke the Google AI Studio key, confirm nothing is left and tell the instructor.")
h("Declaration (Appendix H)", 2)
para("We confirm that the work submitted for SAM10 - Systems Administration and Maintenance, Final Project - is our own, except where clearly identified as borrowed, based on an existing open project, or as AI-assisted. We confirm that:")
bullets(["the base system we built on is identified and credited, and we have complied with its licence;",
         "the system described on our website and in our repository exists and can be demonstrated;",
         "all data and content used in the system is invented, and contains no real patient, student or staff information;",
         "our AI system does not make consequential decisions about identifiable people;",
         "all evidence submitted is authentic and has not been altered to misrepresent results;",
         "no AWS credentials, API keys or passwords are included in this submission, including in the history of our repository; and",
         "we have read and accept the academic integrity and ethics requirements of this course."])
para("")
rich(f"**Student name:** {CFG['student_name']}        **Student ID:** {CFG['student_id']}")
rich("**Signature:** ______________________        **Date:** " + (CFG["declaration_date"] or "[[date]]"))

# footer
for s in doc.sections:
    p = s.footer.paragraphs[0]
    p.text = "SAM10 Final Project - Costa Leona Resort - " + CFG["student_name"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs:
        r.font.size = Pt(8)
doc.save(OUT)
print("saved", OUT, "figures:", FIG["n"])
