"""Build the clean presentation script (what to show + what to say) as a Word document."""
import sys

from docx import Document
from docx.shared import Inches, Pt, RGBColor

OUT = sys.argv[1]
NAVY, BLUE = RGBColor(0x0C, 0x2D, 0x57), RGBColor(0x1F, 0x6F, 0xB5)
d = Document()
for s in d.sections:
    s.left_margin = s.right_margin = Inches(1)
    s.top_margin = s.bottom_margin = Inches(0.9)
d.styles["Normal"].font.name = "Calibri"
d.styles["Normal"].font.size = Pt(12.5)
for n, sz in (("Heading 1", 22), ("Heading 2", 15)):
    h = d.styles[n]
    h.font.name = "Calibri"
    h.font.size = Pt(sz)
    h.font.color.rgb = NAVY
    h.font.bold = True


def show(text):
    p = d.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("SHOW:  ")
    r.bold = True
    r.font.color.rgb = BLUE
    r2 = p.add_run(text)
    r2.bold = True
    r2.font.color.rgb = BLUE


def say(text):
    p = d.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run("SAY:  ")
    r.bold = True
    p.add_run(text)


d.add_heading("Video script - Costa Leona Resort", 1)

PARTS = [
    ("Part 1 - Introduction", "0:00 - 0:35", [
        ("Website home page",
         "Hello, I am Stephanie Joy Revano, working alone on the SAM10 final project. This is Costa Leona Resort, a fictional beach resort, and Leona, its AI front-desk assistant. I took the open-source application LibreChat, made it my own, deployed it on AWS, and then operated it. Operations is the point of this project, so I will show you six things: the system, the AWS design, how I monitor it, how I protect the data, how I secure it, and what happened when I broke it on purpose. First, the system itself.")]),
    ("Part 2 - The system", "0:35 - 1:45", [
        ("Website, System page: the original LibreChat next to my version",
         "On the left is the original LibreChat: a feather logo, a green theme, and a generic answer. It told me check-in is usually 3 PM, because it knows nothing about my resort. On the right is mine: a new name, a new logo, my own colours and wording, and six invented resort documents stored in S3. Nothing is real, and there are no real people in the data. The base system is LibreChat by Danny Avila, MIT licence, credited on the site."),
        ("The live system in the browser (point to the HTTPS address bar), then type: What time is check-in, and can I check out late?",
         "This is the deployed system on AWS, over HTTPS. I will ask: what time is check-in, and can I check out late? It answers from my documents: two p.m., and late check-out is 1,200 pesos if requested the day before."),
        ("Website, System page: the three test questions table",
         "I also tested its limits. On my third test question, a family with two adults and two children, Leona recommended a villa that fits only one child, without warning. That is a real failure, and it is on the website. My quality number is 30 out of 30 on my test set, against 9 out of 30 for the generic version, with the caveat that I wrote the questions. That is what the guest sees. Now let me show you where it runs.")]),
    ("Part 3 - AWS design", "1:45 - 2:35", [
        ("Website, AWS design page: the diagram (point along it, left to right)",
         "One account, one region: Singapore. A guest reaches CloudFront, which gives me free HTTPS. CloudFront is the only thing allowed to reach my EC2 server: the security group has a single rule, port 80 from CloudFront, and no SSH. On the server there are three Docker containers: LibreChat, my Leona gateway, and MongoDB, which has no published port. When a guest asks a question, LibreChat sends it to the gateway. The gateway reads the model key from Parameter Store and the six documents from S3, and calls the Gemini API, which is outside AWS and on the free tier. The answer comes back, and the gateway logs the request and sends metrics to CloudWatch. I optimised for security and operations, and I accepted reliability as my weaker pillar: one server, one zone. Now, how do I know it is healthy?")]),
    ("Part 4 - Monitoring", "2:35 - 3:30", [
        ("AWS Console, CloudWatch dashboard CostaLeona",
         "This is my CloudWatch dashboard with real data: requests, failed answers, response time, CPU, disk, memory, and the pass rate of an hourly test."),
        ("AWS Console, CloudWatch Alarms page",
         "I have eight alarms. For example, disk above 85 percent for two minutes. The guideline suggests an hour, but a chat system that logs every request can fill a small disk fast. In my incident it took 93 seconds."),
        ("The alert e-mail: show only the alarm details at the top, not the bottom of the e-mail",
         "Every alarm e-mails me. This is a real alert: the disk alarm at 03:38 UTC. Every request is also logged as one line with the question, duration, success and version, with 14-day retention. An alert is only useful if I can recover, so backups next.")]),
    ("Part 5 - Backup and restore", "3:30 - 4:20", [
        ("AWS Console, S3 bucket: turn on Show versions",
         "The database is MongoDB in a container. An automatic job dumps it to S3 every hour and keeps it for 14 days. The documents live in this versioned S3 bucket."),
        ("Website, Backup and restore section: the restore test screenshots",
         "A backup you have never restored is only a hope, so I tested it. I took a fresh backup, started an empty MongoDB container, and restored it. Live and restored counts were identical, and the guest account came back. The restore took seven seconds, 25 seconds for the whole procedure. I also deleted a document from S3 and brought it back from its previous version, with the same checksum. So my recovery point is up to one hour, and my measured database recovery time is 25 seconds. Rebuilding the whole server from scripts I estimate at 15 to 20 minutes, which I did not measure. Next, how the account itself is protected.")]),
    ("Part 6 - Security", "4:20 - 5:00", [
        ("AWS Console, IAM users page (stephanie-ops with MFA)",
         "MFA is on the root user and on my own IAM user. I do not use an administrator login. I switch into a role, SAM10-AdminRole, only when needed, and the role requires MFA."),
        ("Website, security table, then the EC2 security group (one rule, CloudFront only)",
         "There are no keys in the code or in the git history. The model key and the application secrets are encrypted parameters in Parameter Store, read at runtime. CloudTrail records who did what, the disk and S3 are encrypted, and the database is not open to the internet. Two honest gaps: GuardDuty is not available on this account plan, and MongoDB has no password inside its private network. That is the first thing I would fix. Now, what happens when it breaks.")]),
    ("Part 7 - Automation and the incident", "5:00 - 6:15", [
        ("Website, Incident page: the automation table with timestamps",
         "Two automations run without me: an hourly database backup, and an hourly set of test questions that publishes a pass rate and e-mails me if it falls below 80 percent. Their timestamps are here: 02:58 and 03:58 UTC, all successful."),
        ("Website, Incident page: the timeline chart, then the root cause",
         "Then the fault, which I created on purpose: the application's request log had no rotation. It started at 03:34:44 UTC, the disk was full at 03:36, and the alarm e-mailed me at 03:38:18. Detected in 3 minutes 34 seconds. I investigated and found one 11-gigabyte log file and a plain file handler with no rotation. That is the root cause."),
        ("Website, Incident page: fix and prevention, then the runbook",
         "I trimmed the file, installed a logrotate rule and tested it: a 144-megabyte log rotated to zero. Fixed at 03:45, 7 minutes 11 seconds after the alarm. The runbook is here, so someone else can repeat it. The site kept answering the whole time, so the alarm warned me before any guest saw an error. Let me finish with the numbers.")]),
    ("Part 8 - Results and close", "6:15 - 7:00", [
        ("Website, Results page: the before and after table",
         "Same 30 questions, same model: 9 correct before, 30 correct with Leona. I wrote the questions myself, so a keyword match cannot catch every mistake. Alarms from none to eight. Backups from none to hourly, with a tested restore. Zero secrets in the repository. The cost is covered by the account credits and recorded on the site."),
        ("Website, Next steps page",
         "Next, I would add MongoDB authentication, automatic recovery and snapshots, automatic deployment from Git, better quality measurement, and rate limiting to protect the model quota. Thank you. Everything I showed is on the project website, and the code is in the Git repository.")]),
]

for title, time, steps in PARTS:
    d.add_heading(f"{title}   ({time})", 2)
    for sh, sy in steps:
        show(sh)
        say(sy)

d.save(OUT)
print("saved", OUT)
