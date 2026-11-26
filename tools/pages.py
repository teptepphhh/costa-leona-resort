# Executed by build_site.py (shares its globals). Page bodies; every number comes from evidence or config.
LP = f"{L['passed']}/{L['total']}"
BP = f"{B['passed']}/{B['total']}"
LPC, BPC = f"{100*L['passed']/L['total']:.0f}%", f"{100*B['passed']/B['total']:.0f}%"
L_AVG, B_AVG = round(avg(leona["results"])), round(avg(base["results"]))
L_MED, B_MED = round(med(leona["results"])), round(med(base["results"]))
runs_b = "".join(f"<li>{html.escape(x)}</li>" for x in CFG["backup_runs"])
runs_s = "".join(f"<li>{html.escape(x)}</li>" for x in CFG["smoke_runs"])
cost_after = CFG["cost_after"] or PENDING
pii = CFG["pii_result"] or PENDING
host = LIVE.replace("https://", "")

# =========================================================================================== 1 OVERVIEW
page("index.html", "Executive summary", f"""
<section class="hero"><div>
<span class="eyebrow">SAM10 final project &middot; build, deploy and run an AI system</span>
<h1>Meet Leona, the <em>front desk</em> of Costa Leona Resort.</h1>
<p class="lead">An open-source AI chat reskinned into a resort assistant, deployed on AWS and run like a real service: monitored, backed up, secured and documented. Everything on this site is backed by evidence from the running system.</p>
<div class="cta"><a class="btn" href="{LIVE}">Try Leona live {ICON['arrow']}</a><a class="btn ghost" href="#video">Watch the presentation {ICON['arrow']}</a></div></div>
<div class="mock"><div class="frame"><div class="bar2"><i></i><i></i><i></i><span>{host}</span></div>
<img src="img/hero_chat.png" alt="Leona answering a guest question on the live AWS deployment"></div>
<div class="chip c1">{icon('shield')}<div><b>HTTPS via CloudFront</b>Only CloudFront can reach the server</div></div>
<div class="chip c2">{icon('db')}<div><b>Answers from S3</b>Six invented resort documents</div></div></div></section>

<div class="strip">{stat(LP, "test questions answered correctly", f"generic model: {BP}")}{stat("8", "alarms e-mail the operator", "dashboard + log groups")}
{stat("3m 34s", "to detect a real fault", "fixed 7 min 11 s later")}{stat("25 s", "tested database restore", "hourly backups to S3")}</div>

<div class="feats">
<div class="feat">{icon('shield')}<div><b>Secure by design</b><span>MFA, role-based admin, secrets in Parameter Store, CloudTrail, no SSH.</span></div></div>
<div class="feat">{icon('pulse')}<div><b>Monitored</b><span>Dashboard, eight alarms and a request log with outcome and timing.</span></div></div>
<div class="feat">{icon('db')}<div><b>Backed up and restored</b><span>Hourly dumps, versioned content, two restores tested.</span></div></div>
<div class="feat">{icon('gear')}<div><b>Automated</b><span>Scheduled backups and test questions, all code in Git.</span></div></div></div>

<div class="sechead"><div><span class="eyebrow">Executive summary</span><h2>The project in plain English</h2></div></div>
<div class="grid two">
<div class="panel"><span class="eyebrow">What it is</span><h3>A virtual front desk</h3><p>Costa Leona Resort is a <em>fictional</em> beach resort. <b>Leona</b> answers guests' questions about rooms, prices, check-in and check-out, house rules and directions, in English or Filipino, using six short resort documents. It never books, charges or decides anything about a person.</p></div>
<div class="panel"><span class="eyebrow">What was wrong</span><h3>How it was run before</h3><p>The starting point was an unmodified chat application on a laptop. It knew nothing about the resort (only <b>{BP}</b> of my 30 test questions answered correctly), nobody would be told if it broke, nothing was backed up, its keys lived in a local file, the AWS account was set up with the all-powerful root login, and nothing recorded who changed what.</p></div>
<div class="panel"><span class="eyebrow">What I changed</span><h3>Reskin, deploy, operate</h3><p>New identity, knowledge and wording; deployed behind HTTPS; every key moved into Parameter Store; MFA and a normal user that borrows admin rights only when needed; CloudTrail; a dashboard and eight e-mail alarms; hourly automated backups and test questions; a proven restore; and a deliberately created disk-full fault that I found, fixed, prevented and wrote a runbook for.</p></div>
<div class="panel"><span class="eyebrow">What improved</span><h3>Measured results</h3><ul>
<li>Quality on the same 30 questions: <b>{BP} ({BPC}) &rarr; {LP} ({LPC})</b></li><li>Alarms: <b>0 &rarr; 8</b>, a real alert reached my inbox 3 min 34 s after the fault began</li>
<li>Backups: none &rarr; hourly, restore in <b>25 s</b></li><li>Secrets in the repository: <b>0</b></li></ul></div></div>
<div class="box"><b>Honest limits.</b> One small server in one Availability Zone; MongoDB has no password inside its private Docker network; GuardDuty is unavailable on this account plan; the quality score is a keyword match on questions I wrote myself. See <a href="well-architected.html">the review</a> and <a href="next-steps.html">next steps</a>.</div>

<div class="sechead" id="video"><div><span class="eyebrow">Presentation</span><h2>Watch the walkthrough</h2></div><p>The reskin, the system running in AWS, the dashboard and alarms, the restore and the fault.</p></div>
{video_block()}

<div class="sechead"><div><span class="eyebrow">Explore</span><h2>Everything, with the evidence beside each claim</h2></div></div>
<div class="grid three">
{card("infrastructure.html","AWS infrastructure design","The diagram of every service and how a question travels to the model and back.","architecture.svg","Design")}
{card("system.html","The system and its card","Base system, reskin, data, model, three test questions and the honest quality number.","11_reskin_chat_answer.png","System")}
{card("operations.html","Monitor, back up, secure","Dashboard, alarms, the real alert, restore results and the security controls.","28_cloudwatch_dashboard_before_incident.png","Operate")}
{card("incident.html","Automation and the incident","Two scheduled jobs, the disk-full fault, root cause, fix and runbook.","30_alert_email_disk_high.png","Incident")}
{card("results.html","Before and after","The same measurements on both sides, with graphs and cost.","chart_quality.png","Results")}
{card("baseline.html","The baseline","The environment before I touched it, measured.","05_baseline_inventory_cloudshell.png","Baseline")}</div>
<div class="linkrow"><a href="well-architected.html">Well-Architected review</a><a href="next-steps.html">What I would do next</a><a href="declaration.html">Credits &amp; declaration</a><a href="{CFG['repo_url']}">Git repository</a></div>
""")

# =========================================================================================== 2 INFRA
page("infrastructure.html", "AWS infrastructure design", f"""
<figure class="shot"><a href="img/architecture.svg"><img src="img/architecture.svg" alt="AWS infrastructure design diagram"></a>
<figcaption><span class="ev">E-18</span> Where every part runs and how a question travels from the guest to the model and back (steps 1-8).</figcaption></figure>
<div class="grid two">
<div class="panel"><span class="eyebrow">Pillars</span><h3>What I optimised, and what I accepted</h3><p>I optimised for <b>Security</b> and <b>Operational Excellence</b>: least privilege, no secrets in code, everything monitored and scripted. I deliberately accepted <b>Reliability</b> as the weaker pillar: one server in one Availability Zone is cheap and simple, and tested hourly backups mean a failure costs minutes, not days.</p></div>
<div class="panel"><span class="eyebrow">Kept small</span><h3>What I chose not to build</h3><p>No load balancer, no RDS, no multi-region, no Kubernetes, no fine-tuning. One account, one region, one instance. The whole build is scripted in <code>infra/</code>, so it can be rebuilt, not just restored.</p></div></div>
<h2>What runs where</h2>
<table><tr><th>Layer</th><th>Service</th><th>What it is for</th></tr>
<tr><td>Networking / HTTPS</td><td>Amazon CloudFront (default certificate)</td><td>Free HTTPS address (<code>*.cloudfront.net</code>); the only thing allowed to reach the server.</td></tr>
<tr><td>Networking</td><td>EC2 security group <code>costaleona-web</code></td><td>One rule: TCP 80 from the CloudFront prefix list. No SSH, no 0.0.0.0/0.</td></tr>
<tr><td>Compute</td><td>EC2 <code>t3.small</code>, Amazon Linux 2023, 20 GB encrypted gp3, IMDSv2</td><td>Three Docker containers: LibreChat (the reskinned interface), the Leona gateway, MongoDB.</td></tr>
<tr><td>Database</td><td>MongoDB 8 container, Docker volume</td><td>Users and chat history. No published port. Backed up hourly to S3.</td></tr>
<tr><td>Storage</td><td>Amazon S3 (versioned, encrypted, private)</td><td><code>knowledge/</code> holds the six documents Leona reads; <code>backups/mongo/</code> holds hourly dumps (kept 14 days).</td></tr>
<tr><td>Config and secrets</td><td>Systems Manager Parameter Store</td><td>SecureString parameters for the model key, app secrets and gateway token, read at runtime.</td></tr>
<tr><td>Operations</td><td>CloudWatch, SNS, EventBridge + SSM Run Command, CloudTrail, AWS Budgets</td><td>Dashboard, 8 alarms, 5 log groups, e-mail alerts, schedules, audit trail, cost alert.</td></tr>
<tr><td>External model</td><td>Google Gemini API, free tier</td><td>The language model, outside AWS; no AWS AI service is used.</td></tr></table>
<h2>How a question travels</h2>
<ol><li>The guest types a question; the browser sends it over HTTPS to CloudFront.</li><li>CloudFront forwards it to the EC2 instance on port 80.</li>
<li>LibreChat passes the chat to the Leona gateway.</li><li>The gateway reads the model key from Parameter Store and the six documents from S3 (refreshed every 5 minutes) and builds the prompt.</li>
<li>The gateway calls the Gemini API.</li><li>The answer streams back through LibreChat to the guest.</li>
<li>The gateway writes one log line (question, duration, success, version) and sends metrics to CloudWatch; if something is wrong, an alarm e-mails me through SNS.</li></ol>
<div class="cols">{fig("15_deploy_complete_cloudfront_url.png","E-02")}{fig("38_compute_network_evidence_part1.png","E-12")}</div>
""", "WS-A - Infrastructure design", "One account, one region (ap-southeast-1), one small server. Every resource is tagged Project=SAM10 and built by scripts in Git.")

# =========================================================================================== 3 SYSTEM
page("system.html", "The system and its card", f"""
<h2>Base system and credit</h2>
<table><tr><th>Item</th><th>Detail</th></tr>
<tr><td>Name / version</td><td>LibreChat (container image <code>librechat-dev:latest</code> pulled 2026-11-26; source v0.8.9 reviewed locally)</td></tr>
<tr><td>Source</td><td><a href="https://github.com/danny-avila/LibreChat">https://github.com/danny-avila/LibreChat</a></td></tr>
<tr><td>Author</td><td>Danny Avila and the LibreChat contributors</td></tr>
<tr><td>Licence</td><td>MIT (<a href="https://github.com/danny-avila/LibreChat/blob/main/LICENSE">LICENSE</a>): reuse, modification and rebranding allowed with the copyright notice kept</td></tr>
<tr><td>What it did originally</td><td>A ChatGPT-style chat interface for many model providers, with user accounts</td></tr></table>
<h2>The reskin: before and after</h2>
<div class="cols">{fig("09_original_login_branding.png","E-05")}{fig("10_reskin_signup_page.png","E-01")}</div>
<div class="cols">{fig("08_local_original_generic_answer.png","E-05")}{fig("11_reskin_chat_answer.png","E-01")}</div>
<table><tr><th>Part</th><th>Original</th><th>Mine</th><th>Why</th></tr>
<tr><td>Name / branding</td><td>"LibreChat", feather logo, green theme</td><td>"Costa Leona Resort", sun-and-waves logo, teal theme, favicon, browser title</td><td>A stranger must not recognise the original</td></tr>
<tr><td>Data / content</td><td>None: it knows nothing about any business</td><td>Six invented resort documents (7.6 KB), stored in S3</td><td>Data must be my own, with no real people</td></tr>
<tr><td>Wording / prompts</td><td>Generic assistant and welcome text</td><td>Persona "Leona", front-desk language, welcome text, footer disclaimer, strict "answer only from the knowledge" prompt</td><td>Domain language belongs to the resort world</td></tr>
<tr><td>Interface</td><td>Model picker, presets, agents, prompts, memories, web search</td><td>One fixed "Leona - Front Desk" assistant; other features hidden; self-sign-up closed on AWS</td><td>Fewer ways to misuse; simpler to operate</td></tr>
<tr><td>AWS services</td><td>None</td><td>S3 (content, backups), Parameter Store (secrets), CloudWatch, SNS, EventBridge + SSM</td><td>At least one integration beyond hosting</td></tr></table>
{fig("19_live_aws_chat_https.png","E-01 / E-02")}
<p>Live URL: <a href="{LIVE}">{LIVE}</a>. The model is Google Gemini (<code>gemini-3.5-flash-lite</code>, falling back to <code>gemini-3.5-flash</code>) through a <b>free-tier</b> key that belongs to its own Google project and can be revoked without affecting anything else.</p>
{fig("06_model_key_free_tier.png","")}
<h2>Three test questions: two working, one failing</h2>
<table><tr><th>#</th><th>Question</th><th>Answer (as returned)</th><th>Verdict</th></tr>
<tr><td>T1</td><td>What time is check-in, and how do I get there from Manila?</td><td>"Standard check-in time is at 2:00 PM." plus the driving route, the bus route and the Friday/Saturday shuttle (PHP 700)</td><td class="good">Correct: every fact matches the documents</td></tr>
<tr><td>T2</td><td>Are pets allowed?</td><td>"Pets are not allowed at Costa Leona Resort, except for registered service animals."</td><td class="good">Correct</td></tr>
<tr><td>T3</td><td>We are 2 adults and 2 children aged 7 and 9. Which room should we book and how much per night?</td><td>Recommended the Lioness Family Villa (PHP 9,500) and said it "accommodates up to 4 adults and 1 child", without flagging that two children exceed that limit</td><td class="gap">Fails: unsafe recommendation; should have referred to the front desk</td></tr></table>
<p>Other honest observations: asked "Where is the pool?", Leona correctly says it has no information (a gap in my documents, not a wrong answer); asked about Christmas Day it said the resort is open because the front desk is open 24 hours, which the documents do not state (an over-inference); and the first live try hit <b>HTTP 503 "high demand"</b> from the Gemini service, outside my control. Raw outputs: <a href="evidence/live_test_questions_2026-11-26.md">live_test_questions_2026-11-26.md</a>.</p>
<div class="cols">{fig("27_live_chat_three_questions.png","E-03")}{fig("07_local_original_gemini_503.png","E-03")}</div>
<h2>How good is it?</h2>
<div class="box blue"><b>The one number: {LP} correct ({LPC})</b> on 30 labelled questions, against <b>{BP} ({BPC})</b> for the same model without the resort knowledge. Measured with <code>eval/run_eval.py</code>, which asks each question and passes an answer only if it contains the required fact(s) in <code>eval/questions.csv</code> (for example "1,200" for the late check-out fee). Mix: 18 facts, 3 policies, 3 rules, 3 questions the documents cannot answer, 1 booking request, 2 safety prompts.</div>
<p><b>Caveats:</b> I wrote the questions, so they match my documents; a keyword match cannot judge subtle mistakes (T3 would pass a keyword test for "9,500"); 30 questions is a small sample. Data: <a href="evidence/eval_local_full_2026-11-26.json">Leona</a>, <a href="evidence/eval_baseline_generic_2026-11-26.json">baseline</a>. A 5-question subset runs every hour on AWS.</p>
<h2>System card</h2>
<div class="grid two">
<div class="panel"><span class="eyebrow">1</span><h3>What it does</h3><p>Leona answers guests' questions about Costa Leona Resort (fictional): room types and prices, check-in and check-out, amenities, house rules and directions. It reads six documents and replies in English or Filipino.</p></div>
<div class="panel"><span class="eyebrow">2</span><h3>Who uses it, and who must not</h3><p><b>Intended:</b> prospective and current guests asking general questions.<br><b>Explicitly NOT for:</b> medical, legal or emergency advice; making, changing or paying for bookings; any decision about an identifiable person (grading, ranking, eligibility, discipline); anyone about to share ID, card or health details in the chat.</p></div>
<div class="panel"><span class="eyebrow">3</span><h3>Base system</h3><p>LibreChat, github.com/danny-avila/LibreChat, Danny Avila and contributors, MIT licence. Originally a multi-provider chat interface with accounts.</p></div>
<div class="panel"><span class="eyebrow">4</span><h3>What was changed</h3><p>Identity, data, wording, interface and AWS services: see the reskin table above.</p></div>
<div class="panel"><span class="eyebrow">5</span><h3>Data</h3><ul><li><b>Source:</b> written by me for this project; folder <code>knowledge/</code>.</li><li><b>Size:</b> six Markdown files, 7,612 bytes.</li><li><b>Anything personal:</b> No - all invented (the e-mail domain is <code>.example</code>).</li>
<li><b>Sent to a third-party AI service:</b> each question plus the six documents go to the Gemini API; only invented content is ever sent (free-tier terms may allow the provider to retain prompts, which is why no real data is used). Personal-data check: {pii}</li></ul></div>
<div class="panel"><span class="eyebrow">6</span><h3>How good it is</h3><ul><li><b>The one number:</b> {LP} on my test set, via a keyword-scoring script.</li><li><b>Cases:</b> 30 (facts, policies, rules, unknowns, a booking request, safety).</li><li><b>Gets wrong:</b> T3, the family of two adults and two children sent to a villa limited to one child.</li></ul></div>
<div class="panel"><span class="eyebrow">7</span><h3>How it is served</h3><ul><li><b>Runs on:</b> EC2 t3.small, ap-southeast-1c, Docker; HTTPS via CloudFront.</li><li><b>Called by:</b> <code>{host}</code> (browser); LibreChat calls the gateway at <code>/v1/chat/completions</code> with a bearer token.</li><li><b>Model:</b> Gemini <code>gemini-3.5-flash-lite</code>, free tier.</li><li><b>If unavailable:</b> 3 retries, then "Model provider error, please try again"; the failure counts toward an alarm (&gt;5% in 15 min). Seen for real: HTTP 503.</li></ul></div>
<div class="panel"><span class="eyebrow">8</span><h3>Limitations and risks</h3><ul><li><b>Cannot:</b> book, change or pay; know anything outside the six documents; guarantee its arithmetic or capacity checks.</li><li><b>Data risk:</b> missing or stale facts give wrong or empty answers (the pool location is undocumented); model over-inference.</li><li><b>Misuse:</b> a guest could try to override its rules; the prompt forbids it but it is not a security boundary.</li><li><b>Always check:</b> prices, dates, capacity and policies with the front desk.</li></ul></div>
<div class="panel"><span class="eyebrow">9</span><h3>Operational summary</h3><ul><li><b>Code:</b> <a href="{CFG['repo_url']}">{CFG['repo_url'].replace('https://','')}</a></li><li><b>Backups:</b> MongoDB hourly to S3 (14 days); documents versioned and in Git.</li><li><b>Healthy means:</b> eight alarms OK and the hourly test at 80% or more.</li><li><b>Contact:</b> the operator on the <a href="declaration.html">declaration</a>.</li></ul></div></div>
""", "WS-A - Reskin and deploy", "Base system, what was changed, the data, the model, three honest test questions, the one quality number and the system card.")

# =========================================================================================== 4 BASELINE
page("baseline.html", "The baseline", f"""
<p class="lead2">Measured on 2026-11-26 before any deployment. Two things existed: an AWS account with one running server that belongs to <em>another</em> course project (not mine, untouched, excluded from every automation by tag), and the unmodified LibreChat that I ran on my laptop.</p>
<table><tr><th>Area</th><th>Baseline</th></tr>
<tr><td>AWS inventory (ap-southeast-1)</td><td>1 unrelated EC2 instance; no RDS; no S3 buckets; no Elastic IPs</td></tr>
<tr><td>Account set-up</td><td>Root login with MFA; no IAM user for daily work; no budget alert; free-plan credits USD 117.40</td></tr>
<tr><td>The AI system</td><td>Original LibreChat on a laptop, original name and logo, no resort knowledge: <b>{BP}</b> test questions correct; asked "What time is check-in?" it answers generically ("usually 3:00 PM")</td></tr>
<tr><td>Monitoring and alerts</td><td>None</td></tr><tr><td>Backups</td><td>None</td></tr>
<tr><td>Secrets</td><td>Model key and app secrets in a local <code>.env</code> file</td></tr>
<tr><td>Audit trail</td><td>No CloudTrail trail for this project</td></tr><tr><td>Automation, runbooks</td><td>None</td></tr></table>
<div class="cols">{fig("04_signed_in_as_iam_user_credits.png","")}{fig("05_baseline_inventory_cloudshell.png","")}</div>
<div class="cols">{fig("01_budget_alert_created.png","")}{fig("09_original_login_branding.png","E-05")}</div>
{fig("08_local_original_generic_answer.png","E-05")}
<p>Generic-model results on the 30 questions: <a href="evidence/eval_baseline_generic_2026-11-26.json">evidence file</a>.</p>
""", "Baseline", "The environment before I touched it.")

# =========================================================================================== 5 WA
def prow(name, ask, does, p1, p2):
    k = {"good": "good", "adequate": "adeq", "gap": "gap"}
    return (f'<div class="pillar"><div><h3>{name}</h3><div class="ask">{ask}</div></div><p>{does}</p>'
            f'<div class="v"><span>Pass 1</span>{pill(k[p1[0]], p1[1])}<span>Pass 2</span>{pill(k[p2[0]], p2[1])}</div></div>')

page("well-architected.html", "Well-Architected review", f"""
<p class="lead2">I made a first pass when the deployment first worked (2026-11-26, about 03:00 UTC) to decide what to build next, and a second after the incident. Verdicts are my own assessment against the framework's questions; I did not use the AWS Well-Architected Tool.</p>
<div class="pillars-head"><span>Pillar</span><span>What my system actually does</span><span>Verdicts</span></div>
{prow("Operational Excellence","Run and monitor, automate changes, keep improving.","Dashboard, 8 alarms to e-mail, request log with outcome and version, two scheduled automations, everything deployed by scripts in Git, a tested runbook. A fault was found, fixed and prevented.",("adequate","adequate: no runbook, no rotation"),("good","good"))}
{prow("Security","MFA, least privilege, no secrets in code, audit trail.","MFA on root and the IAM user; admin only through a temporary role; secrets in Parameter Store; CloudTrail; encryption at rest; reachable only via CloudFront; no SSH; IMDSv2. Gaps: MongoDB has no password (private network only), CloudFront-to-origin is HTTP, GuardDuty unavailable.",("adequate","adequate: no CloudTrail yet"),("adequate","adequate"))}
{prow("Reliability","Work when it should, recover when it does not.","Hourly backups, one tested database restore (25 s) and one tested content restore (versioning), alarms on CPU, status, disk, memory and errors. One server in one Availability Zone, no automatic failover.",("gap","gap: no tested restore"),("adequate","adequate"))}
{prow("Performance Efficiency","Right-sized for the load, with a number.",f"t3.small: CPU peaked at 40% and memory at 70% in the observed hour; average answer time {L_AVG/1000:.1f} s (median {L_MED/1000:.1f} s) over 30 questions, dominated by the external model; alarm at a 10 s average.",("adequate","adequate"),("adequate","adequate"))}
{prow("Cost Optimization","Pay for what you use: tags, budget alert, nothing idle.","Zero-spend budget alert created first; every resource tagged; smallest viable instance; 14-day log retention; S3 lifecycle on backups; free model tier; CloudFront price class 100. The public IPv4 address is billed but needed.",("good","good"),("good","good"))}
{prow("Sustainability","Smaller footprint: no idle or oversized resources.","One small instance, no load balancer or database service, logs capped by retention and rotation (the runaway log was the incident), jobs limited to hourly. Shut-down plan documented.",("adequate","adequate"),("adequate","adequate"))}
<div class="box"><b>The one gap I would fix first: MongoDB authentication.</b> Today any process on the instance's private Docker network can read or change every user and chat without a password. It is not reachable from the internet, so the risk is low, but it is the cheapest high-value fix (a password in Parameter Store and a changed connection string) and it protects the most sensitive data the system holds. Single-AZ reliability is the second gap, accepted on purpose.</div>
<h2>What changed between the two passes</h2>
<ul><li><b>Operational Excellence:</b> adequate &rarr; good (runbook, log rotation, tested alert path).</li><li><b>Reliability:</b> gap &rarr; adequate (two restore tests).</li>
<li><b>Security:</b> stayed adequate. CloudTrail was added, but the Mongo and HTTP-origin gaps remain and GuardDuty could not be enabled.</li></ul>
{fig("20_cloudtrail_logging_guardduty_unavailable.png","E-17")}
""", "WS-A - Well-Architected", "The six pillars, one verdict each (good, adequate or gap) and the one gap I would fix first.")

# =========================================================================================== 6 OPERATE
alarm_rows = """
<tr><td>costaleona-cpu-high</td><td>EC2 CPUUtilization</td><td>&gt;85% for 10 min</td><td>Appendix A value: a stuck process or runaway loop looks like this.</td></tr>
<tr><td>costaleona-status-check-failed</td><td>EC2 StatusCheckFailed</td><td>&gt;0 for 1 min</td><td>The instance itself is unhealthy.</td></tr>
<tr><td>costaleona-disk-high</td><td>CWAgent disk_used_percent</td><td>&gt;85% for 2 min</td><td>Changed from Appendix A's 1 hour: a chat system that logs every request can fill a small disk in minutes (it took 93 s in my incident).</td></tr>
<tr><td>costaleona-memory-high</td><td>CWAgent mem_used_percent</td><td>&gt;90% for 5 min</td><td>Containers may be killed by the kernel.</td></tr>
<tr><td>costaleona-response-slow</td><td>CostaLeona ResponseTimeMs</td><td>average &gt;10 s for 5 min</td><td>Changed from 3 s: the external model alone takes 1-9 s, so 10 s is where guests give up.</td></tr>
<tr><td>costaleona-answers-failed</td><td>failed / (failed + succeeded)</td><td>&gt;5% over 15 min</td><td>Appendix A: the system is up but not working (for example a Gemini 503 storm).</td></tr>
<tr><td>costaleona-empty-answers</td><td>CostaLeona EmptyAnswer</td><td>&gt;0 in 30 min</td><td>The knowledge base is probably missing or unreadable.</td></tr>
<tr><td>costaleona-passrate-low</td><td>CostaLeona PassRate (smoke)</td><td>&lt;80% per hour</td><td>Answer quality dropped though nothing is technically broken.</td></tr>"""
rl = fig(CFG["request_log_img"], "E-09") if CFG["request_log_img"] else f'<div class="pending">{PENDING} Request-log screenshot (E-09) to be added.</div>'
page("operations.html", "Monitor, back up, secure", f"""
<h2>Monitoring</h2>
<p>The dashboard shows requests answered, failed and empty answers, response time, EC2 CPU, disk, memory, the scheduled test pass rate and the alarm states. I chose these because they separate "the machine is unhealthy" (CPU, disk, memory) from "the product is broken" (failed or empty answers, low pass rate).</p>
{fig("28_cloudwatch_dashboard_before_incident.png","E-06")}
<h3>Eight alarms, all e-mailing me through SNS</h3>
<p>Appendix A rows for a load balancer and RDS do not apply (I run neither), so I swapped in the equivalents for what I do run.</p>
<table><tr><th>Alarm</th><th>Metric</th><th>Threshold</th><th>Why this value</th></tr>{alarm_rows}</table>
<div class="cols">{fig("17_alarms_dashboard_created.png","E-07")}{fig("31_alarms_list_disk_in_alarm.png","E-07")}</div>
<h3>Proof that an alert reached me</h3>
<p>This is a real alarm raised by the disk-full fault in <a href="incident.html">the incident</a>: fault at 03:34:44 UTC, alarm at 03:38:18 UTC. I acted on it (fixed at 03:45:29) and the "OK" message followed at 03:47:18.</p>
<div class="cols">{fig("30_alert_email_disk_high.png","E-08")}{fig("36_alert_email_disk_ok_resolved.png","E-08")}</div>
{fig("26_sns_subscription_confirmed.png","")}
<h3>Request log</h3>
<p>Every request is one JSON line: time, request id, the question, duration in milliseconds, success, empty, HTTP status, model and application version (release plus a hash of the knowledge base). Log groups for the gateway, LibreChat, MongoDB, the request log and the automation log all have a 14-day retention. Sample (local run, same code):</p>
<pre>{{"ts": "2026-11-26T02:26:25+0000", "request_id": "8db0af35c237", "question": "What time is check-in?", "duration_ms": 6837, "success": true, "empty": false, "status": 200, "model": "gemini-3.5-flash-lite", "version": "1.0.0+kb.01604f0c", "error": ""}}</pre>
{rl}{fig("39_log_groups_schedules_evidence_part2.png","E-09")}

<h2>Backup and restore</h2>
<h3>What would have to be restored</h3>
<table><tr><th>Item</th><th>Where it lives</th><th>How it is protected</th></tr>
<tr><td>Database (users and chats)</td><td>MongoDB volume on the instance</td><td>Hourly <code>mongodump</code> to S3 (<code>backups/mongo/</code>), kept 14 days (requirement: 7). No RDS is used.</td></tr>
<tr><td>S3 content (six documents)</td><td>S3 bucket <code>knowledge/</code></td><td>Versioning enabled; second copy in Git</td></tr>
<tr><td>Configuration and secrets</td><td>Parameter Store; Git (<code>infra/</code>, compose files)</td><td>Everything but the model key is regenerated by <code>deploy.sh</code>; the model key is re-created in Google AI Studio</td></tr>
<tr><td>The server itself</td><td>EC2, CloudFront, security group, IAM roles</td><td>Rebuilt from <code>infra/deploy.sh</code>, not restored</td></tr></table>
{fig("21_s3_versioning_backups_evidence.png","E-10")}
<h3>Restore tests</h3>
<ul><li><b>Database:</b> a fresh backup (14,804 bytes) was taken, an empty MongoDB container started, the backup restored from S3: 65 documents restored, 0 failed. Live and restored counts were identical (users 1, conversations 1, messages 2), and the guest-desk account was present. Restore step 7 s, whole procedure 25 s.</li>
<li><b>Content:</b> a document was deleted from S3 (5 of 6 left) and brought back by removing the delete marker; the SHA-256 before and after was identical.</li></ul>
<div class="cols">{fig("23_restore_test_db_part1.png","E-11")}{fig("24_restore_test_db_part2_pass.png","E-11")}</div>
{fig("25_restore_test_content_s3_versioning.png","E-11")}
<div class="box"><b>RPO and RTO.</b> RPO: up to one hour of chat history could be lost (hourly backups); the documents lose nothing (versioned and in Git). RTO: restoring the database took 25 seconds in the test; rebuilding the whole stack from scratch with the scripts is estimated at 15-20 minutes (an estimate, not measured end to end).</div>

<h2>Security</h2>
<h3>Each control and the risk it addresses</h3>
<table><tr><th>Control</th><th>Risk addressed</th><th>Evidence</th></tr>
<tr><td>MFA on the root user and the IAM user</td><td>A stolen password alone cannot open the account.</td><td>E-12</td></tr>
<tr><td>Own IAM user; admin only by assuming <code>SAM10-AdminRole</code> (MFA required)</td><td>No shared or standing administrator login; powerful rights exist only briefly.</td><td>E-12</td></tr>
<tr><td>Model key and app secrets in Parameter Store (SecureString), read at runtime</td><td>A leaked repository or screenshot never exposes a key; I scanned every git commit for my secret values before the first push (0 hits).</td><td>E-13</td></tr>
<tr><td>Only invented data, plus a personal-data check on the request log</td><td>Nothing personal can leave the account to the third-party model. Result: {pii}</td><td>E-13</td></tr>
<tr><td>MongoDB has no published port; security group allows only CloudFront on port 80; no SSH</td><td>The database is not open to the internet and there is no remote-login door to attack.</td><td>E-12</td></tr>
<tr><td>Scoped roles: instance role limited to one bucket and <code>/costaleona/*</code>; schedule role limited to tagged instances; model key in its own free-tier project</td><td>A compromised component can do only its own job. (Google AI Studio keys have no expiry option, so the key is revocable instead.)</td><td>E-12</td></tr>
<tr><td>CloudTrail trail in ap-southeast-1 with log validation</td><td>I can see who did what and when.</td><td>E-12</td></tr>
<tr><td>Encryption at rest (encrypted EBS volume, S3 AES-256); IMDSv2 required</td><td>Stolen disks or snapshots, and metadata-credential theft, give nothing readable.</td><td>E-12</td></tr>
<tr><td>Self-sign-up closed on AWS</td><td>Strangers cannot burn the free model quota.</td><td>repo</td></tr></table>
<div class="cols">{fig("02_root_mfa_enabled.png","E-12")}{fig("03_iam_user_mfa_enabled.png","E-12")}</div>
<div class="cols">{fig("12_admin_role_created_root_cloudshell.png","E-12")}{fig("13_role_switched_sam10_admin.png","E-12")}</div>
{fig("22_iam_mfa_ssm_params_cloudtrail.png","E-12 / E-13")}{fig("14_deploy_s3_ssm_secrets.png","E-13")}
<h3>Before and after: problems found and fixed</h3>
<table><tr><th>Problem found</th><th>Before</th><th>After</th></tr>
<tr><td>Secrets in a file</td><td>Model key and app secrets in a local <code>.env</code> during development</td><td>All in Parameter Store SecureString; repo ignores <code>.env</code>; 0 secret values in git history</td></tr>
<tr><td>Setup done as root</td><td>Budget, MFA and the admin role were created with the root login</td><td>Daily work as an MFA-protected IAM user; admin only through the assumed role; root has MFA and no access keys</td></tr>
<tr><td>No audit trail</td><td>No trail for this project</td><td>CloudTrail logging since 03:04 UTC</td></tr>
<tr><td>Unbounded log growth (found in the incident)</td><td>Request log grew without limit</td><td>logrotate hourly, 100 MB cap, 3 copies</td></tr></table>
<p><b>Known gaps I did not fix:</b> MongoDB without a password inside the private network; plain HTTP between CloudFront and the origin (protected by the prefix-list rule); GuardDuty could not be enabled (the account plan returned <code>SubscriptionRequiredException</code>).</p>
""", "WS-B, WS-C, WS-D", "Dashboard and alarms, a real alert, backup and restore results, and the security controls each explained in one sentence.")

# =========================================================================================== 7 INCIDENT
page("incident.html", "Automation and the incident", f"""
<h2>Automation</h2>
<p>Two automations run with nobody touching them. EventBridge fires a rule, SSM Run Command runs a script on the instance (only instances tagged <code>Project=SAM10</code> and <code>Role=web</code>), and the script writes one timestamped line to <code>/var/log/leona-automation.log</code> (shipped to CloudWatch Logs). Code: <code>automation/backup.sh</code>, <code>automation/smoketest.sh</code> and <code>infra/automation.sh</code> in the <a href="{CFG['repo_url']}">repository</a>.</p>
<div class="grid two"><div class="panel"><span class="eyebrow">Automation 1</span><h3>Database backup, every hour</h3><p>Dumps MongoDB, streams it to S3, logs the size.</p></div>
<div class="panel"><span class="eyebrow">Automation 2</span><h3>Test-question run, every hour</h3><p>Asks Leona 5 test questions, publishes the pass rate to CloudWatch, e-mails me if it falls below 80%.</p></div></div>
<p>Hourly instead of nightly so that two unattended runs fit inside the project window; in production the backup would stay hourly and the test run could be nightly.</p>
<table><tr><th>Backup runs (timestamps)</th><th>Test-question runs (timestamps)</th></tr><tr><td><ul>{runs_b}</ul></td><td><ul>{runs_s}</ul></td></tr></table>
<div class="cols">{fig("18_automation_rules_scheduled.png","E-14")}{fig("21_s3_versioning_backups_evidence.png","E-14")}</div>

<h2>The incident: disk full</h2>
<p>Fault chosen from Appendix E ("disk full"). I created it on purpose in my own account: I appended synthetic lines to the application's request log until the root disk was full, then watched my own monitoring notice.</p>
<figure class="chart"><img src="img/chart_incident.png" alt="incident timeline"><figcaption>Incident timeline (UTC), from SSM output and the alarm e-mails.</figcaption></figure>
<ul class="tl">
<li class="hot"><b>03:34:44</b><time>Fault started</time>Disk 47%, 11 GB free.</li>
<li class="hot"><b>03:36:17</b><time>Disk full</time>100%, 38 MB free.</li>
<li><b>03:38:18</b><time>Alarm fired, e-mail received (noticed)</time><b>Time to detect: 3 min 34 s.</b></li>
<li><b>03:41:54</b><time>Investigation started</time>Largest directory and file found.</li>
<li><b>03:45:29</b><time>Fixed</time>Disk back to 47%. <b>Time to fix: 7 min 11 s</b> from the alarm.</li>
<li><b>03:47:18</b><time>Alarm back to OK</time>Resolution e-mail received.</li></ul>
<h3>What I saw</h3>
<p>The site kept answering at 100% disk: a latent outage, surviving on the last 38 MB, with writes (logs, new chats) one step from failing. The alarm gave me the warning before any guest saw an error.</p>
<div class="cols">{fig("29_incident_fault_started_disk_full.png","E-15")}{fig("32_live_site_during_incident.png","E-15")}</div>
{fig("34_dashboard_during_incident.png","E-15")}
<h3>Root cause</h3>
<div class="box"><b>The application request log (<code>requests.log</code>) was written by a plain file handler with no rotation and no size limit, so it grew without bound (11 GB of the 20 GB disk), which filled the root disk.</b> Evidence: <code>du</code> ranks that one file at 11 GB (MongoDB 209 MB, containers 2.3 MB); no logrotate rule mentions it; <code>app.py</code> lines 51-52 show the handler.</div>
{fig("33_incident_investigation_root_cause.png","E-15")}
<h3>Fix and prevention</h3>
<ul><li><b>Fix:</b> trim the log to its last 2,000 lines: disk 100% &rarr; 47%.</li>
<li><b>Prevention:</b> a logrotate rule (rotate above 100 MB, keep 3 compressed copies, <code>copytruncate</code>) with the timer set to hourly; also part of <code>infra/start.sh</code>, so any rebuilt server has it. The root-cause metric already has an alarm (disk used &gt;85%).</li>
<li><b>Verification:</b> a test run rotated a 144 MB log to 0 bytes; the alarm cleared at 03:47:18.</li></ul>
{fig("35_incident_fix_and_prevention.png","E-15")}{fig("37_dashboard_after_recovery.png","E-15")}
<h3>Runbook</h3>
<pre># RUNBOOK: root disk filling up (disk-high alarm)
Owner: operator   Last tested: 2026-11-26 (during the incident)   Takes: 10 minutes   Ask: -

1. WHAT THIS IS FOR
Free disk space on the web instance before the app stops saving chats and logs.

2. HOW YOU KNOW YOU NEED IT
E-mail "ALARM: costaleona-disk-high" (disk used above 85%), or the dashboard disk tile is red.
Command that shows it:  df -h /

3. WHAT IT AFFECTS
Guests: at 100% the site may stop saving chats or fail on the next write. Until then they notice nothing.

4. HOW TO DO IT
Step 1: from AWS CloudShell run  bash infra/run_on_instance.sh incident/02_investigate.sh
        -> you should see which directory is biggest (here /opt/leona/logs/gateway, one file requests.log)
Step 2: bash infra/run_on_instance.sh incident/03_fix.sh
        -> you should see the disk percentage drop and "FIX_DONE"

5. HOW TO CHECK IT WORKED
- [ ] df -h / shows well below 85%
- [ ] ask Leona "What time is check-in?" and get "2:00 PM"
- [ ] OK e-mail for costaleona-disk-high within about 5 minutes; no new alarms for 10 minutes

6. HOW TO UNDO IT
03_fix.sh keeps the last 2,000 log lines and only touches requests.log; rotated copies are in /opt/leona/logs/gateway.
Remove /etc/logrotate.d/leona only if rotation itself misbehaves.

7. GOTCHAS
- AWS CLI v2 pages long output with "less": press q, or set AWS_PAGER="".
- Do not delete files in /var/lib/docker by hand; MongoDB data lives there.
- CloudShell paste can fail in some browsers; type the short commands instead.

8. CHANGE HISTORY
2026-11-26 - created after the disk-full incident; log rotation added to infra/start.sh.</pre>
""", "WS-E, WS-F", "Two scheduled automations, and one fault: found, explained, fixed, prevented and written up as a runbook.")

# =========================================================================================== 8 RESULTS
rows_cat = "".join(f"<tr><td>{c.replace('_',' ')}</td><td>{catB[c][0]}/{catB[c][1]}</td><td>{catL[c][0]}/{catL[c][1]}</td></tr>" for c in cats)
page("results.html", "Results: before and after", f"""
<p class="lead2">Method: the <b>same</b> 30 questions, the <b>same</b> model (<code>gemini-3.5-flash-lite</code>), the <b>same</b> script, run on 2026-11-26 (Leona run finished 02:30 UTC; generic-baseline run finished 03:02 UTC). "Before" is the model with no resort knowledge, which is what the unmodified application can offer; "after" is Leona.</p>
<div class="strip">{stat(LP, "after: questions correct", f"before: {BP}")}{stat("8", "alarms", "before: 0")}{stat("3m 34s", "time to detect", "before: not detected")}{stat("7m 11s", "time to fix", "from the alarm")}</div>
<table><tr><th>Measure</th><th>Before</th><th>After</th><th>Period / how measured</th></tr>
<tr><td>Answer quality (30 labelled questions)</td><td>{BP} ({BPC})</td><td><b>{LP} ({LPC})</b></td><td>eval script, 2026-11-26</td></tr>
<tr><td>Average answer time</td><td>{B_AVG/1000:.1f} s (median {B_MED/1000:.1f} s)</td><td>{L_AVG/1000:.1f} s (median {L_MED/1000:.1f} s)</td><td>same script and questions; Leona sends six documents with every question, so it is slower, and its run included Gemini retries</td></tr>
<tr><td>Alarms that e-mail me</td><td>0</td><td>8</td><td>2026-11-26</td></tr>
<tr><td>Time to detect a full disk</td><td>not detected (no monitoring)</td><td>3 min 34 s</td><td>incident, 2026-11-26</td></tr>
<tr><td>Time to fix</td><td>n/a</td><td>7 min 11 s from the alarm</td><td>incident, 2026-11-26</td></tr>
<tr><td>Backups / tested restore</td><td>none</td><td>hourly; restore in 25 s</td><td>2026-11-26</td></tr>
<tr><td>Secret values in the repository or its history</td><td>keys in a local file</td><td>0</td><td>scanned before the first push</td></tr>
<tr><td>Cost (E-16)</td><td>{html.escape(CFG['cost_before'])}</td><td>{html.escape(cost_after)}</td><td>AWS console; credits are used first</td></tr></table>
<figure class="chart"><img src="img/chart_quality.png" alt="quality by category"><figcaption><span class="ev">E-04</span> Questions passed by category: generic model vs Leona.</figcaption></figure>
<table><tr><th>Category</th><th>Generic model</th><th>Leona</th></tr>{rows_cat}</table>
<div class="box"><b>Caveats.</b> The questions are mine; a keyword matcher cannot see subtle errors (see test T3); the latency numbers are small samples and depend on the external model's load that day. The hourly 5-question test on AWS is the live health measure of the deployed system.</div>
<h2>Cost</h2>
<p>All spending is covered by the account's free-plan credits. Controls: a zero-spend AWS Budgets alert created first, tags on every resource, the smallest viable instance, 14-day log retention and a shut-down plan on the <a href="declaration.html">last page</a>. Idle cost of this design is mostly the instance, its public IPv4 address and CloudFront requests.</p>
<div class="cols">{fig("01_budget_alert_created.png","E-16")}{fig("04_signed_in_as_iam_user_credits.png","E-16")}</div>
""", "WS-G - Results", "Before and after, measured the same way over the same period, with the cost as one of the numbers.")

# =========================================================================================== 9 NEXT
page("next-steps.html", "What I would do next", """
<div class="grid two">
<div class="panel"><span class="eyebrow">1 - Security</span><h3>MongoDB authentication</h3><p>The gap named in the review: store a database password in Parameter Store and require it, plus a secret header so only CloudFront can talk to the origin. About one hour.</p></div>
<div class="panel"><span class="eyebrow">2 - Reliability</span><h3>Automatic recovery and off-instance copies</h3><p>Daily EBS snapshots with Data Lifecycle Manager and an auto-recovery alarm on the instance; later a second Availability Zone behind a load balancer. This lifts Reliability from adequate to good.</p></div>
<div class="panel"><span class="eyebrow">3 - Operations</span><h3>Deploy from Git automatically</h3><p>A GitHub Actions workflow that runs the tests and then the SSM command that already pulls and restarts the stack, so a change to <code>main</code> updates the running system.</p></div>
<div class="panel"><span class="eyebrow">4 - Quality</span><h3>Better measurement</h3><p>Grow the labelled set well past 30 questions written by someone else, add checks for capacity and arithmetic (the failing test T3), and add a thumbs-up/down feedback metric from real guests.</p></div>
<div class="panel"><span class="eyebrow">5 - Cost</span><h3>Protect the model quota</h3><p>Rate limiting or AWS WAF in front of CloudFront and an alarm on request volume, so a loop or a bot cannot burn the free quota or, on a paid key, the budget.</p></div></div>
""", "WS-G - Next steps", "Five realistic ideas, in priority order.")

# =========================================================================================== 10 DECLARATION
sid = CFG["student_id"] or PENDING
ddate = CFG["declaration_date"] or PENDING
page("declaration.html", "Credits, AI use and declaration", f"""
<div class="grid two">
<div class="panel"><span class="eyebrow">Credits and licences</span><h3>Built on other people's work</h3><ul>
<li><b>LibreChat</b>: Danny Avila and contributors, MIT licence, <a href="https://github.com/danny-avila/LibreChat">github.com/danny-avila/LibreChat</a>. Used as an unmodified container image; the reskin is configuration, branding and the gateway in my repository.</li>
<li><b>Google Gemini API</b>: free tier under Google's terms of use.</li><li>Logo, resort documents, scripts and website text were made for this project. AWS documentation was used as reference.</li></ul></div>
<div class="panel"><span class="eyebrow">Use of an AI tool</span><h3>Declared and verified</h3><p>I used Claude (Anthropic) through Claude Code to write the scripts, configuration, gateway code, website text and diagram, and to suggest what to check. I verified everything by running it in my own AWS account and reading the real command output; every screenshot is from my own session, and no result on this site was invented.</p></div></div>
<h2>Clean-up plan</h2>
<p>After marking: terminate the EC2 instance, delete the CloudFront distribution, the S3 buckets (empty them first), the Parameter Store parameters, the EventBridge rules, the CloudWatch alarms, dashboard and log groups, the CloudTrail trail, the SNS topic and the IAM roles, revoke the Google AI Studio key, then confirm nothing is left and tell the instructor.</p>
<h2>Declaration (Appendix H)</h2>
<div class="box"><p>We confirm that the work submitted for SAM10 - Systems Administration and Maintenance, Final Project - is our own, except where clearly identified as borrowed, based on an existing open project, or as AI-assisted. We confirm that:</p><ul>
<li>the base system we built on is identified and credited, and we have complied with its licence;</li><li>the system described on our website and in our repository exists and can be demonstrated;</li>
<li>all data and content used in the system is invented, and contains no real patient, student or staff information;</li><li>our AI system does not make consequential decisions about identifiable people;</li>
<li>all evidence submitted is authentic and has not been altered to misrepresent results;</li>
<li>no AWS credentials, API keys or passwords are included in this submission, including in the history of our repository; and</li>
<li>we have read and accept the academic integrity and ethics requirements of this course.</li></ul>
<p><b>Student name:</b> {CFG['student_name']} &nbsp; <b>Student ID:</b> {sid}<br><b>Signature:</b> ______________________ &nbsp; <b>Date:</b> {ddate}</p>
<p><em>Working alone: one signatory.</em> E-mail addresses visible in a few screenshots were masked before publication.</p></div>
""", "Appendix H", "Credits, licences, the AI-use statement, the clean-up plan and the signed declaration.")
