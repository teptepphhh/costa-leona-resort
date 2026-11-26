# Executed by build_site.py (shares its globals). Page bodies; every number comes from evidence or config.
LP = f"{L['passed']}/{L['total']}"
BP = f"{B['passed']}/{B['total']}"
L_AVG, B_AVG = round(avg(leona["results"])), round(avg(base["results"]))
L_MED, B_MED = round(med(leona["results"])), round(med(base["results"]))
runs_b = "".join(f"<li>{html.escape(x)}</li>" for x in CFG["backup_runs"])
runs_s = "".join(f"<li>{html.escape(x)}</li>" for x in CFG["smoke_runs"])
cost_after = CFG["cost_after"] or PENDING
pii = CFG["pii_result"] or PENDING

# ----------------------------------------------------------------------------------------------- 1 SUMMARY
page("index.html", "Executive summary", f"""
<h2>Executive summary</h2>
<p><strong>What it is.</strong> Costa Leona Resort is a <em>fictional</em> beach resort. <strong>Leona</strong> is its virtual front-desk
assistant: guests ask in plain English or Filipino about rooms, prices, check-in and check-out, house rules or how to get there, and Leona answers
from six short resort documents. It never books, charges or decides anything about a person - it is informational only. It is a reskin of the open-source
chat application <a href="https://github.com/danny-avila/LibreChat">LibreChat</a> and runs on Amazon Web Services (AWS) at
<a href="{LIVE}">{LIVE}</a> (HTTPS).</p>
<p><strong>What was wrong with how it was run.</strong> The starting point was an unmodified chat application on a laptop. It knew nothing about the resort
(it answered only <b>{BP}</b> of my 30 test questions correctly), nobody would be told if it broke, nothing was backed up, its keys lived in a local file,
the AWS account was set up with the all-powerful root login, and there was no record of who changed what.</p>
<p><strong>What I changed.</strong> I gave it its own identity, knowledge and wording; deployed it to AWS behind HTTPS; moved every key into AWS Parameter
Store; turned on multi-factor authentication and switched to a normal user that borrows admin rights only when needed; recorded all account activity in
CloudTrail; built a dashboard and eight alarms that e-mail me; automated hourly database backups and hourly test questions; proved a restore works; and
deliberately broke the server (a full disk), found the cause, fixed it and wrote a runbook.</p>
<p><strong>What improved</strong> (measured, details on the <a href="results.html">Results</a> page):</p>
<ul>
<li>Answer quality on the same 30 questions: <b>{BP} ({100*B['passed']/B['total']:.0f}%) &rarr; {LP} ({100*L['passed']/L['total']:.0f}%)</b>.</li>
<li>Alarms: 0 &rarr; 8, all e-mailing me. A real alert reached my inbox <b>3 min 34 s</b> after the fault began; the fault was fixed <b>7 min 11 s</b> later.</li>
<li>Backups: none &rarr; hourly to S3, with a tested restore that took <b>25 seconds</b>.</li>
<li>Secrets stored in files in the repository: <b>0</b> (all in Parameter Store).</li>
</ul>
<div class="box"><strong>Honest limits.</strong> One small server in one Availability Zone; MongoDB runs without a password inside a private Docker network;
GuardDuty is not available on this account plan; the quality score uses a simple keyword matcher on questions I wrote myself. These are discussed on the
<a href="well-architected.html">Well-Architected</a> and <a href="next-steps.html">Next steps</a> pages.</div>
<h2>Presentation video</h2>
{video_block()}
<h2>Where to find things</h2>
<table><tr><th>Page</th><th>What it contains</th></tr>
<tr><td><a href="infrastructure.html">AWS design</a></td><td>Diagram, services, how a question travels</td></tr>
<tr><td><a href="system.html">System + card</a></td><td>Base system, reskin, data, model, three test questions, quality number, system card</td></tr>
<tr><td><a href="baseline.html">Baseline</a></td><td>The environment before I touched it</td></tr>
<tr><td><a href="well-architected.html">Well-Architected</a></td><td>Six pillars, verdicts, the gap I would fix first</td></tr>
<tr><td><a href="operations.html">Monitor, backup, secure</a></td><td>Dashboard, alarms, real alert, restore result, security before/after</td></tr>
<tr><td><a href="incident.html">Automation + incident</a></td><td>Two scheduled jobs, the disk-full fault, root cause, runbook</td></tr>
<tr><td><a href="results.html">Results</a></td><td>Before/after numbers, graphs, cost</td></tr>
<tr><td><a href="next-steps.html">Next steps</a></td><td>Prioritised ideas</td></tr>
<tr><td><a href="declaration.html">Declaration</a></td><td>Credits, licences, AI-use statement, signed declaration</td></tr></table>
""")

# ----------------------------------------------------------------------------------------------- 2 INFRA
page("infrastructure.html", "AWS infrastructure design", f"""
<h2>AWS infrastructure design</h2>
<p>One AWS account, one region (<code>ap-southeast-1</code>, Singapore), one small server. Everything carries the tags <code>Project=SAM10</code>.
The whole build is scripted in <code>infra/</code> in the repository, so it can be rebuilt, not just restored.</p>
<figure><a href="img/architecture.svg"><img src="img/architecture.svg" alt="AWS infrastructure design diagram"></a>
<figcaption><span class="ev">E-18</span> Infrastructure design: where every part runs and how a question travels from the guest to the model and back (steps 1-8).</figcaption></figure>
<h3>What runs where</h3>
<table><tr><th>Layer</th><th>Service</th><th>What it is for</th></tr>
<tr><td>Networking / HTTPS</td><td>Amazon CloudFront (default certificate)</td><td>Gives a free HTTPS address (<code>*.cloudfront.net</code>). The only thing allowed to reach the server.</td></tr>
<tr><td>Networking</td><td>EC2 security group <code>costaleona-web</code></td><td>One rule: TCP 80 from the CloudFront prefix list. No SSH, no 0.0.0.0/0.</td></tr>
<tr><td>Compute</td><td>EC2 <code>t3.small</code>, Amazon Linux 2023, 20 GB encrypted gp3, IMDSv2</td><td>Runs three Docker containers: LibreChat (the reskinned user interface), the Leona gateway, and MongoDB.</td></tr>
<tr><td>Database</td><td>MongoDB 8 in a container with a Docker volume</td><td>Users and chat history. Not published to any network port. Backed up hourly to S3.</td></tr>
<tr><td>Storage</td><td>Amazon S3 (versioned, encrypted, private)</td><td><code>knowledge/</code> holds the six resort documents Leona reads; <code>backups/mongo/</code> holds the hourly dumps (kept 14 days).</td></tr>
<tr><td>Configuration and secrets</td><td>Systems Manager Parameter Store</td><td>SecureString parameters for the model key, the app secrets and the gateway token, read at runtime.</td></tr>
<tr><td>Operations</td><td>CloudWatch (dashboard, 8 alarms, 5 log groups), SNS, EventBridge + SSM Run Command, CloudTrail, AWS Budgets</td><td>See the <a href="operations.html">operations</a> and <a href="incident.html">automation</a> pages.</td></tr>
<tr><td>External</td><td>Google Gemini API (free tier)</td><td>The language model. It runs outside AWS; no AWS AI service is used.</td></tr></table>
<h3>How a question travels</h3>
<ol><li>The guest types a question; the browser sends it over HTTPS to CloudFront.</li>
<li>CloudFront forwards it to the EC2 instance on port 80.</li>
<li>LibreChat passes the chat to the Leona gateway.</li>
<li>The gateway reads the model key from Parameter Store and the six documents from S3 (refreshed every 5 minutes) and builds the prompt.</li>
<li>The gateway calls the Gemini API.</li>
<li>The answer streams back through LibreChat to the guest.</li>
<li>The gateway writes one log line (question, duration, success, version) and sends metrics to CloudWatch. If anything goes wrong, an alarm e-mails me through SNS.</li></ol>
<div class="box"><strong>Pillar trade-off.</strong> I optimised for <b>Security</b> and <b>Operational Excellence</b> (least privilege, no secrets in code, everything
monitored and scripted). I deliberately accepted <b>Reliability</b> as the weaker pillar: a single server in a single Availability Zone is cheap and simple, and
the hourly tested backups mean a failure costs minutes, not days. Five other things I chose <em>not</em> to build, to stay small: a load balancer, RDS,
multi-region, Kubernetes, and fine-tuning.</div>
{fig("15_deploy_complete_cloudfront_url.png","E-02")}
{fig("38_compute_network_evidence_part1.png","E-12")}
""")

# ----------------------------------------------------------------------------------------------- 3 SYSTEM
page("system.html", "Your system and the system card", f"""
<h2>Your system</h2>
<h3>Base system and credit</h3>
<table><tr><th>Item</th><th>Detail</th></tr>
<tr><td>Name / version</td><td>LibreChat (container image <code>librechat-dev:latest</code> pulled 2026-11-26; source v0.8.9 reviewed locally)</td></tr>
<tr><td>Source</td><td><a href="https://github.com/danny-avila/LibreChat">https://github.com/danny-avila/LibreChat</a></td></tr>
<tr><td>Author</td><td>Danny Avila and the LibreChat contributors</td></tr>
<tr><td>Licence</td><td>MIT (<a href="https://github.com/danny-avila/LibreChat/blob/main/LICENSE">LICENSE</a>): reuse, modification and rebranding allowed with the copyright notice kept</td></tr>
<tr><td>What it did originally</td><td>A ChatGPT-style chat interface for many model providers, with user accounts</td></tr></table>
<h3>The reskin</h3>
<table><tr><th>Part</th><th>Original</th><th>Mine</th><th>Why</th></tr>
<tr><td>Name / branding</td><td>"LibreChat", feather logo, green theme</td><td>"Costa Leona Resort", sun-and-waves logo, teal/gold theme, favicon, browser title</td><td>A stranger must not recognise the original</td></tr>
<tr><td>Data / content</td><td>None - it knows nothing about any business</td><td>Six invented resort documents (about, rooms and rates, policies, amenities and dining, house rules, getting here and FAQ), 7.6 KB, stored in S3</td><td>The data must be my own and contain no real people</td></tr>
<tr><td>Wording / prompts</td><td>Generic assistant, generic welcome text</td><td>Persona "Leona", hotel front-desk language, welcome text, footer disclaimer, strict "answer only from the knowledge" system prompt in the gateway</td><td>Domain language belongs to the resort world</td></tr>
<tr><td>Interface</td><td>Model picker, presets, agents, prompts, memories, web search</td><td>One fixed "Leona - Front Desk" assistant; all other features hidden; self-sign-up closed on AWS</td><td>Fewer ways to misuse it; simpler to operate</td></tr>
<tr><td>AWS services</td><td>None</td><td>S3 (content, backups), Parameter Store (secrets), CloudWatch (metrics, logs), SNS (alerts), EventBridge + SSM (schedules)</td><td>At least one integration beyond hosting</td></tr></table>
<div class="cols">{fig("09_original_login_branding.png","E-05")}{fig("10_reskin_signup_page.png","E-01")}</div>
<div class="cols">{fig("08_local_original_generic_answer.png","E-05")}{fig("11_reskin_chat_answer.png","E-01")}</div>
{fig("19_live_aws_chat_https.png","E-01 / E-02")}
<p>Live URL: <a href="{LIVE}">{LIVE}</a>. The model behind it is Google Gemini (<code>gemini-3.5-flash-lite</code>, falling back to <code>gemini-3.5-flash</code>)
through a <b>free-tier</b> key that belongs to its own Google project and can be revoked without affecting anything else.</p>
{fig("06_model_key_free_tier.png","")}
<h3>Three test questions (two working, one failing)</h3>
<table><tr><th>#</th><th>Question</th><th>Answer (as returned)</th><th>Verdict</th></tr>
<tr><td>T1</td><td>What time is check-in, and how do I get there from Manila?</td><td>"Standard check-in time is at 2:00 PM." plus the driving route, the bus route and the Friday/Saturday shuttle (PHP 700)</td><td class="good">Correct, all facts match the documents</td></tr>
<tr><td>T2</td><td>Are pets allowed?</td><td>"Pets are not allowed at Costa Leona Resort, except for registered service animals."</td><td class="good">Correct</td></tr>
<tr><td>T3</td><td>We are 2 adults and 2 children aged 7 and 9. Which room should we book and how much per night?</td><td>Recommended the Lioness Family Villa (PHP 9,500) and said it "accommodates up to 4 adults and 1 child", without flagging that two children exceed that limit</td><td class="gap">Fails: unsafe recommendation, should have asked the front desk to confirm</td></tr></table>
<p>Other honest observations: asked "Where is the pool?", Leona correctly says it has no information on the pool's location (a gap in my documents, not a
wrong answer); asked about Christmas Day it said the resort is open because the front desk is open 24 hours, which the documents do not actually state
(an over-inference); and on the first live try the Gemini service answered <b>HTTP 503 "high demand"</b>, a failure outside my control. Raw outputs:
<a href="evidence/live_test_questions_2026-11-26.md">live_test_questions_2026-11-26.md</a>.</p>
<div class="cols">{fig("27_live_chat_three_questions.png","E-03")}{fig("07_local_original_gemini_503.png","E-03")}</div>
<h3>How good is it? (E-04)</h3>
<div class="box"><strong>The one number: {LP} correct ({100*L['passed']/L['total']:.0f}%)</strong> on 30 labelled questions, against <b>{BP} ({100*B['passed']/B['total']:.0f}%)</b>
for the same model with no resort knowledge. Measured with <code>eval/run_eval.py</code>, which asks each question and passes an answer only if it contains the
required fact(s) listed in <code>eval/questions.csv</code> (for example "1,200" for the late check-out fee). Categories: 18 facts, 3 policies, 3 rules,
3 unknown-to-the-system, 1 out-of-scope booking request, 2 safety.</div>
<p><b>Caveats, stated plainly:</b> I wrote the questions, so they match my documents; a keyword match cannot judge tone or subtle mistakes (T3 above would
pass a keyword test for "9,500"); and 30 questions is a small sample. Results: <a href="evidence/eval_local_full_2026-11-26.json">Leona</a>,
<a href="evidence/eval_baseline_generic_2026-11-26.json">baseline</a>. A scheduled 5-question subset of the same script runs every hour on AWS
(<a href="incident.html">automation</a>).</p>

<h2>System card</h2>
<h3>1. What it does</h3><p>Leona answers guests' questions about Costa Leona Resort (a fictional beach resort): room types and prices, check-in and check-out, amenities,
house rules and directions. It only reads six documents and replies in English or Filipino.</p>
<h3>2. Who uses it, and who must not</h3>
<ul><li><b>Intended users:</b> prospective and current guests asking general questions.</li>
<li><b>Explicitly NOT for:</b> medical, legal or emergency advice; making, changing or paying for bookings; any decision about an identifiable person (grading, ranking, eligibility, discipline);
anyone who would share ID, card or health details in the chat.</li></ul>
<h3>3. Base system</h3><p>LibreChat, https://github.com/danny-avila/LibreChat, Danny Avila and contributors, MIT licence. Originally a multi-provider chat interface.</p>
<h3>4. What was changed (the reskin)</h3><p>See the reskin table above.</p>
<h3>5. Data</h3>
<ul><li><b>Where it came from:</b> written by me for this project; no source, no licence issues. Repository folder <code>knowledge/</code>.</li>
<li><b>Size and format:</b> six Markdown files, 7,612 bytes in total.</li>
<li><b>Anything personal in it:</b> No - all invented (names, phone numbers, e-mail addresses and prices are fictional; the e-mail domain is <code>.example</code>).</li>
<li><b>Anything sent to a third-party AI service:</b> each question plus the six documents, sent to the Google Gemini API. Only invented content is ever sent; the free tier's terms may allow the provider to retain prompts, which is why no real data is used. Personal-data check: {pii}</li></ul>
<h3>6. How good it is</h3>
<ul><li><b>The one number:</b> {LP} on my test set.</li><li><b>How measured:</b> keyword scoring script, see above.</li>
<li><b>Test cases:</b> 30 (facts, policies, rules, questions the documents cannot answer, a booking request, two safety prompts).</li>
<li><b>An example it gets wrong:</b> T3, the family of two adults and two children recommended into a villa limited to one child.</li></ul>
<h3>7. How it is served</h3>
<ul><li><b>Where it runs:</b> EC2 t3.small, ap-southeast-1c, Docker; HTTPS through CloudFront.</li>
<li><b>What calls it:</b> <code>{LIVE}</code> (browser); internally LibreChat calls <code>http://gateway:8080/v1/chat/completions</code> with a bearer token.</li>
<li><b>Model:</b> Google Gemini <code>gemini-3.5-flash-lite</code> (fallback <code>gemini-3.5-flash</code>), free tier.</li>
<li><b>If the model or service is unavailable:</b> the gateway retries up to 3 times, then returns an error to the user ("Model provider error, please try again") and counts an <code>AnswersFailed</code> metric; a failure rate above 5% over 15 minutes e-mails me. Seen for real: HTTP 503 from Gemini.</li></ul>
<h3>8. Limitations and risks</h3>
<ul><li><b>Cannot do:</b> book, change, or pay; know anything outside the six documents (it should say so); give medical or legal advice; guarantee that its arithmetic or capacity checks are right.</li>
<li><b>What could go wrong with the data:</b> out-of-date or missing facts give wrong or empty answers (for example the pool location is not documented); model over-inference (Christmas opening).</li>
<li><b>Misuse:</b> a guest could try to make it reveal its instructions or ignore its rules; the system prompt forbids it and a test question covers it, but it is not a security boundary. Sign-up is closed on AWS to protect the free model quota.</li>
<li><b>A user must always check:</b> prices, dates, room capacity and policies with the front desk before relying on them.</li></ul>
<h3>9. Operational summary</h3>
<ul><li><b>Code:</b> <a href="{CFG['repo_url']}">{CFG['repo_url']}</a></li><li><b>Backups:</b> MongoDB hourly to S3 (kept 14 days); documents versioned in S3 and in Git.</li>
<li><b>Healthy means:</b> eight CloudWatch alarms are OK, hourly test questions pass at 80% or more.</li><li><b>Contact:</b> the operator named on the <a href="declaration.html">declaration</a>.</li></ul>
""")

# ----------------------------------------------------------------------------------------------- 4 BASELINE
page("baseline.html", "Baseline", f"""
<h2>Baseline: the environment before I touched it</h2>
<p>Measured on 2026-11-26 before any deployment. Two things existed: an AWS account with one running server that belongs to <em>another</em> course project
(not mine, not touched, excluded from every automation by tag), and the unmodified LibreChat that I ran on my laptop.</p>
<table><tr><th>Area</th><th>Baseline</th><th>Evidence</th></tr>
<tr><td>AWS inventory (ap-southeast-1)</td><td>1 unrelated EC2 instance; no RDS; no S3 buckets; no Elastic IPs</td><td>screenshot below</td></tr>
<tr><td>Account set-up</td><td>Root login enabled with MFA; no IAM user for daily work; no budget alert; free-plan credits USD 117.40 remaining</td><td>screenshots below</td></tr>
<tr><td>The AI system</td><td>Original LibreChat on a laptop, original name and logo, no resort knowledge: <b>{BP}</b> of the 30 test questions correct; asked "What time is check-in?" it answers generically ("usually 3:00 PM")</td><td><a href="evidence/eval_baseline_generic_2026-11-26.json">baseline eval</a>, screenshots</td></tr>
<tr><td>Monitoring and alerts</td><td>None</td><td>-</td></tr>
<tr><td>Backups</td><td>None</td><td>-</td></tr>
<tr><td>Secrets</td><td>Model key and app secrets in a local <code>.env</code> file</td><td>-</td></tr>
<tr><td>Audit trail</td><td>No CloudTrail trail for this project</td><td>-</td></tr>
<tr><td>Automation, runbooks</td><td>None</td><td>-</td></tr></table>
<div class="cols">{fig("04_signed_in_as_iam_user_credits.png","")}{fig("05_baseline_inventory_cloudshell.png","")}</div>
<div class="cols">{fig("01_budget_alert_created.png","")}{fig("09_original_login_branding.png","E-05")}</div>
{fig("08_local_original_generic_answer.png","E-05")}
""")

# ----------------------------------------------------------------------------------------------- 5 WA
page("well-architected.html", "Well-Architected review", f"""
<h2>Well-Architected review</h2>
<p>I made a first pass when the deployment first worked (2026-11-26, ~03:00 UTC) to decide what to build next, and a second pass after the incident
(WS-F). Verdicts: <span class="good">good</span>, <span class="adeq">adequate</span>, <span class="gap">gap</span>. These are my own assessments against the
framework's questions (I did not use the AWS Well-Architected Tool).</p>
<table><tr><th>Pillar</th><th>What the framework asks for</th><th>What my system actually does</th><th>Pass 1</th><th>Pass 2</th></tr>
<tr><td><b>Operational Excellence</b></td><td>Run and monitor, automate changes, keep improving</td>
<td>Dashboard, 8 alarms to e-mail, request log with outcome and version, two scheduled automations, everything deployed by scripts in Git, a tested runbook. Fault found, fixed and prevented.</td>
<td class="adeq">adequate: no runbook, no rotation</td><td class="good">good</td></tr>
<tr><td><b>Security</b></td><td>MFA, least privilege, no secrets in code, audit trail, data protection</td>
<td>MFA on root and the IAM user; admin only through a temporary role; secrets in Parameter Store; CloudTrail; encryption at rest; instance reachable only via CloudFront; no SSH; IMDSv2. Gaps: MongoDB has no password (private network only), CloudFront-to-origin hop is HTTP, GuardDuty unavailable.</td>
<td class="adeq">adequate: no CloudTrail yet</td><td class="adeq">adequate</td></tr>
<tr><td><b>Reliability</b></td><td>Work when it should, recover when it does not</td>
<td>Hourly backups, one tested database restore (25 s) and one tested content restore (versioning), alarms on CPU, status, disk, memory, errors. One server in one Availability Zone with no automatic failover.</td>
<td class="gap">gap: no tested restore</td><td class="adeq">adequate</td></tr>
<tr><td><b>Performance Efficiency</b></td><td>Right-sized resources, responsive under load, with a number</td>
<td>t3.small: CPU peaked at 40% and memory at 70% in the observed hour; average answer time {L_AVG/1000:.1f} s (median {L_MED/1000:.1f} s) over 30 questions, dominated by the external model; alarm at 10 s average.</td>
<td class="adeq">adequate</td><td class="adeq">adequate</td></tr>
<tr><td><b>Cost Optimization</b></td><td>Pay for what you use: tags, budget alert, nothing idle</td>
<td>Zero-spend budget alert created first; every resource tagged <code>Project=SAM10</code>; smallest viable instance; log retention 14 days; S3 lifecycle on backups; free model tier; CloudFront price class 100. The public IPv4 address is billed but needed.</td>
<td class="good">good</td><td class="good">good</td></tr>
<tr><td><b>Sustainability</b></td><td>Smaller footprint: no idle instances, no oversizing, no runaway jobs</td>
<td>One small instance, no load balancer or database service, logs capped by retention and rotation (the runaway log was the incident), jobs limited to hourly. Shut-down plan documented.</td>
<td class="adeq">adequate</td><td class="adeq">adequate</td></tr></table>
<div class="box"><strong>The one gap I would fix first: MongoDB authentication.</strong> Today any process on the instance's private Docker network can read or change
every user and chat without a password. It is not reachable from the internet, so the risk is low, but it is the cheapest high-value fix (a password in Parameter
Store and a changed connection string) and it protects the most sensitive data the system holds. Single-AZ reliability is the second gap, accepted on purpose.</div>
<h3>What changed between the two passes</h3>
<ul><li>Operational Excellence: adequate &rarr; good (runbook, log rotation, tested alert path).</li>
<li>Reliability: gap &rarr; adequate (two restore tests).</li>
<li>Security: stayed adequate: CloudTrail was added, but the Mongo and HTTP-origin gaps remain and GuardDuty could not be enabled.</li></ul>
{fig("20_cloudtrail_logging_guardduty_unavailable.png","E-17")}
""")

# ----------------------------------------------------------------------------------------------- 6 OPERATIONS
alarm_rows = """
<tr><td>costaleona-cpu-high</td><td>EC2 CPUUtilization</td><td>&gt;85% for 10 min</td><td>Appendix A value: a stuck process or runaway loop looks like this.</td></tr>
<tr><td>costaleona-status-check-failed</td><td>EC2 StatusCheckFailed</td><td>&gt;0 for 1 min</td><td>The instance itself is unhealthy.</td></tr>
<tr><td>costaleona-disk-high</td><td>CWAgent disk_used_percent</td><td>&gt;85% for 2 min</td><td>Changed from Appendix A's 1 hour: a chat system that logs every request can fill a small disk in minutes (it took 93 s in my incident).</td></tr>
<tr><td>costaleona-memory-high</td><td>CWAgent mem_used_percent</td><td>&gt;90% for 5 min</td><td>Containers may be killed by the kernel.</td></tr>
<tr><td>costaleona-response-slow</td><td>CostaLeona ResponseTimeMs</td><td>average &gt;10 s for 5 min</td><td>Changed from 3 s: the external model alone takes 1-9 s, so 10 s is where guests give up.</td></tr>
<tr><td>costaleona-answers-failed</td><td>failed / (failed + succeeded)</td><td>&gt;5% over 15 min</td><td>Appendix A: the system is up but not working (for example a Gemini 503 storm).</td></tr>
<tr><td>costaleona-empty-answers</td><td>CostaLeona EmptyAnswer</td><td>&gt;0 in 30 min</td><td>The knowledge base is probably missing or unreadable.</td></tr>
<tr><td>costaleona-passrate-low</td><td>CostaLeona PassRate (smoke)</td><td>&lt;80% per hour</td><td>Answer quality dropped even though nothing is technically broken.</td></tr>"""
rl = f"{fig(CFG['request_log_img'], 'E-09')}" if CFG["request_log_img"] else f'<div class="pending">{PENDING} Request-log screenshot (E-09) to be added.</div>'
page("operations.html", "Monitoring, backup and restore, security", f"""
<h2>Monitoring</h2>
<p>The dashboard shows requests answered, failed and empty answers, response time, EC2 CPU, disk, memory, the scheduled test pass rate and the alarm states.
I chose these because they separate "the machine is unhealthy" (CPU, disk, memory) from "the product is broken" (failed or empty answers, low pass rate).</p>
{fig("28_cloudwatch_dashboard_before_incident.png","E-06")}
<h3>Alarms (8, all e-mail me through SNS)</h3>
<p>Appendix A rows for a load balancer and RDS do not apply (I run neither), so I swapped in the equivalents for what I do run.</p>
<table><tr><th>Alarm</th><th>Metric</th><th>Threshold</th><th>Why this value</th></tr>{alarm_rows}</table>
<div class="cols">{fig("17_alarms_dashboard_created.png","E-07")}{fig("31_alarms_list_disk_in_alarm.png","E-07")}</div>
<h3>Proof that an alert reached me</h3>
<p>The e-mail below is a real alarm raised by the disk-full fault in <a href="incident.html">the incident</a>: fault at 03:34:44 UTC, alarm at 03:38:18 UTC.
It was acted on (fixed at 03:45:29) and the "OK" message followed at 03:47:18.</p>
<div class="cols">{fig("30_alert_email_disk_high.png","E-08")}{fig("36_alert_email_disk_ok_resolved.png","E-08")}</div>
{fig("26_sns_subscription_confirmed.png","")}
<h3>Request log</h3>
<p>Every request is one JSON line: time, request id, the question, duration in milliseconds, success, empty, HTTP status, model and application version
(release plus a hash of the knowledge base). Log groups for the gateway, LibreChat, MongoDB, the request log and the automation log all have a 14-day retention.
Sample (local run, same code):</p>
<pre>{{"ts": "2026-11-26T02:26:25+0000", "request_id": "8db0af35c237", "question": "What time is check-in?", "duration_ms": 6837, "success": true, "empty": false, "status": 200, "model": "gemini-3.5-flash-lite", "version": "1.0.0+kb.01604f0c", "error": ""}}</pre>
{rl}{fig("39_log_groups_schedules_evidence_part2.png","E-09")}

<h2>Backup and restore</h2>
<h3>What would have to be restored</h3>
<table><tr><th>Item</th><th>Where it lives</th><th>How it is protected</th></tr>
<tr><td>Database (users and chats)</td><td>MongoDB volume on the instance</td><td>Hourly <code>mongodump</code> to S3 (<code>backups/mongo/</code>), kept 14 days (requirement: 7). No RDS is used.</td></tr>
<tr><td>S3 content (six documents)</td><td>S3 bucket <code>knowledge/</code></td><td>Versioning enabled; second copy in Git</td></tr>
<tr><td>Configuration and secrets</td><td>Parameter Store; Git (<code>infra/</code>, compose files)</td><td>Everything but the model key is regenerated by <code>deploy.sh</code>; the model key is re-created in Google AI Studio</td></tr>
<tr><td>The server itself</td><td>EC2 + CloudFront + security group + IAM roles</td><td>Rebuilt from <code>infra/deploy.sh</code> (not restored)</td></tr></table>
{fig("21_s3_versioning_backups_evidence.png","E-10")}
<h3>Restore tests (E-11)</h3>
<ul><li><b>Database:</b> a fresh backup (14,804 bytes) was taken, an empty MongoDB container started, the backup restored from S3: 65 documents restored, 0 failed. Live and restored counts were identical (users=1, conversations=1, messages=2), and the guest-desk account was present. Restore step 7 s, whole procedure 25 s.</li>
<li><b>Content:</b> a document was deleted from S3 (5 of 6 left) and brought back by removing the delete marker; the SHA-256 before and after was identical.</li></ul>
<div class="cols">{fig("23_restore_test_db_part1.png","E-11")}{fig("24_restore_test_db_part2_pass.png","E-11")}</div>
{fig("25_restore_test_content_s3_versioning.png","E-11")}
<div class="box"><strong>RPO and RTO.</strong> RPO: up to one hour of chat history could be lost (hourly backups); the documents lose nothing (versioned and in Git).
RTO: restoring the database took 25 seconds in the test; rebuilding the whole stack from scratch with the scripts is estimated at 15-20 minutes (an estimate - not measured end to end).</div>

<h2>Security</h2>
<h3>Each control and the risk it addresses</h3>
<table><tr><th>Control</th><th>Risk addressed (one sentence)</th><th>Evidence</th></tr>
<tr><td>MFA on the root user and on the IAM user</td><td>A stolen password alone cannot open the account.</td><td>E-12</td></tr>
<tr><td>Own IAM user; admin only by assuming <code>SAM10-AdminRole</code> (MFA required)</td><td>No shared or standing administrator login; powerful rights exist only briefly.</td><td>E-12</td></tr>
<tr><td>Model key and app secrets in Parameter Store (SecureString), read at runtime</td><td>A leaked repository or screenshot never exposes a key; I scanned every git commit for my secret values before the first push (0 hits).</td><td>E-13</td></tr>
<tr><td>Only invented data + personal-data check on the request log</td><td>Nothing personal can leave the account to the third-party model. Result: {pii}</td><td>E-13</td></tr>
<tr><td>MongoDB has no published port; the security group allows only CloudFront on port 80; no SSH</td><td>The database is not open to the internet and there is no remote-login door to attack.</td><td>E-12</td></tr>
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
<p><b>Known gaps I did not fix:</b> MongoDB without a password inside the private network; plain HTTP between CloudFront and the origin (protected by the prefix-list rule);
GuardDuty could not be enabled (the account plan returned <code>SubscriptionRequiredException</code>).</p>
{fig("38_compute_network_evidence_part1.png","E-12")}
""")

# ----------------------------------------------------------------------------------------------- 7 INCIDENT
page("incident.html", "Automation and the incident", f"""
<h2>Automation</h2>
<p>Two automations run with nobody touching them. EventBridge fires a rule, SSM Run Command runs a script on the instance (only instances tagged
<code>Project=SAM10</code> and <code>Role=web</code>), and the script writes one timestamped line to <code>/var/log/leona-automation.log</code> (shipped to CloudWatch Logs).
Code: <code>automation/backup.sh</code>, <code>automation/smoketest.sh</code>, <code>infra/automation.sh</code> in the <a href="{CFG['repo_url']}">repository</a>.</p>
<table><tr><th>Automation</th><th>Schedule</th><th>What it does</th></tr>
<tr><td>1. Database backup</td><td>every hour</td><td>Dumps MongoDB, streams it to S3, logs the size.</td></tr>
<tr><td>2. Test-question run</td><td>every hour</td><td>Asks Leona 5 test questions, publishes the pass rate to CloudWatch, e-mails me if it is below 80%.</td></tr></table>
<p>Hourly instead of nightly so that two unattended runs fit inside the project window; in production the backup would stay hourly and the test run could be nightly.</p>
<h3>Runs (timestamps)</h3>
<table><tr><th>Backup runs</th><th>Test-question runs</th></tr><tr><td><ul>{runs_b}</ul></td><td><ul>{runs_s}</ul></td></tr></table>
<div class="cols">{fig("18_automation_rules_scheduled.png","E-14")}{fig("21_s3_versioning_backups_evidence.png","E-14")}</div>

<h2>The incident: disk full</h2>
<p>Fault chosen from Appendix E ("disk full"). I created it on purpose, in my own account: I appended synthetic lines to the application's request log until
the root disk was full, then watched my own monitoring notice.</p>
<figure><img src="img/chart_incident.png" alt="incident timeline"><figcaption>Incident timeline (UTC, from SSM output and alarm e-mails).</figcaption></figure>
<table><tr><th>Event</th><th>Time (UTC, 26 Nov 2026)</th></tr>
<tr><td>Fault started</td><td>03:34:44 (disk 47%, 11 GB free)</td></tr><tr><td>Disk 100% (38 MB free)</td><td>03:36:17</td></tr>
<tr><td>Alarm fired, e-mail received (noticed)</td><td>03:38:18 &rarr; <b>time to detect 3 min 34 s</b></td></tr>
<tr><td>Investigation started</td><td>03:41:54</td></tr><tr><td>Fixed (disk 47%)</td><td>03:45:29 &rarr; <b>time to fix 7 min 11 s</b> from the alarm</td></tr>
<tr><td>Alarm back to OK</td><td>03:47:18</td></tr></table>
<h3>What I saw</h3>
<p>The site kept answering at 100% disk: a latent outage, surviving on the last 38 MB, with writes (logs, new chats) one step from failing. The alarm gave
me the warning before any guest saw an error.</p>
<div class="cols">{fig("29_incident_fault_started_disk_full.png","E-15")}{fig("32_live_site_during_incident.png","E-15")}</div>
{fig("34_dashboard_during_incident.png","E-15")}
<h3>Root cause</h3>
<p><b>The application request log (<code>requests.log</code>) was written by a plain file handler with no rotation and no size limit, so it grew without bound
(11 GB of the 20 GB disk), which filled the root disk.</b> Evidence: <code>du</code> ranks that one file at 11 GB (MongoDB 209 MB, containers 2.3 MB); no logrotate rule mentions it;
<code>app.py</code> lines 51-52 show the handler.</p>
{fig("33_incident_investigation_root_cause.png","E-15")}
<h3>Fix and prevention</h3>
<ul><li><b>Fix:</b> trim the log to its last 2,000 lines: disk 100% &rarr; 47%.</li>
<li><b>Prevention:</b> logrotate rule (rotate above 100 MB, keep 3 compressed copies, <code>copytruncate</code>), timer set to hourly; also part of <code>infra/start.sh</code> so any rebuilt server has it. The root-cause metric already has an alarm (disk used &gt;85%).</li>
<li><b>Verification:</b> test run rotated a 144 MB log to 0 bytes; the alarm cleared at 03:47:18.</li></ul>
{fig("35_incident_fix_and_prevention.png","E-15")}
{fig("37_dashboard_after_recovery.png","E-15")}
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
""")

# ----------------------------------------------------------------------------------------------- 8 RESULTS
rows_cat = "".join(f"<tr><td>{c.replace('_',' ')}</td><td>{catB[c][0]}/{catB[c][1]}</td><td>{catL[c][0]}/{catL[c][1]}</td></tr>" for c in cats)
page("results.html", "Results", f"""
<h2>Results: before and after</h2>
<p>Method: the <b>same</b> 30 questions, the <b>same</b> model (<code>gemini-3.5-flash-lite</code>), the <b>same</b> script, run on 2026-11-26 (Leona run finished
02:30 UTC; generic-baseline run finished 03:02 UTC). "Before" is the model with no resort knowledge (what the unmodified application can offer); "after" is Leona.</p>
<table><tr><th>Measure</th><th>Before</th><th>After</th><th>Period / how measured</th></tr>
<tr><td>Answer quality (30 labelled questions)</td><td>{BP} ({100*B['passed']/B['total']:.0f}%)</td><td><b>{LP} ({100*L['passed']/L['total']:.0f}%)</b></td><td>eval script, 2026-11-26</td></tr>
<tr><td>Average answer time</td><td>{B_AVG/1000:.1f} s (median {B_MED/1000:.1f} s)</td><td>{L_AVG/1000:.1f} s (median {L_MED/1000:.1f} s)</td><td>same script and questions; Leona sends six documents with every question, so it is slower, and its run included Gemini retries</td></tr>
<tr><td>Alarms that e-mail me</td><td>0</td><td>8</td><td>2026-11-26</td></tr>
<tr><td>Time to detect a full disk</td><td>not detected (no monitoring)</td><td>3 min 34 s</td><td>incident, 2026-11-26</td></tr>
<tr><td>Time to fix</td><td>n/a</td><td>7 min 11 s from the alarm</td><td>incident, 2026-11-26</td></tr>
<tr><td>Backups / tested restore</td><td>none</td><td>hourly; restore in 25 s</td><td>2026-11-26</td></tr>
<tr><td>Secret values in the repository or its history</td><td>keys in a local file</td><td>0</td><td>scanned before the first push</td></tr>
<tr><td>Cost (E-16)</td><td>{html.escape(CFG['cost_before'])}</td><td>{html.escape(cost_after)}</td><td>AWS console, credits are used first</td></tr></table>
<figure><img src="img/chart_quality.png" alt="quality by category"><figcaption><span class="ev">E-04</span> Questions passed by category: generic model vs Leona.
Table of the same data below.</figcaption></figure>
<table><tr><th>Category</th><th>Generic</th><th>Leona</th></tr>{rows_cat}</table>
<div class="box"><strong>Caveats.</strong> The questions are mine; a keyword matcher cannot see subtle errors (see test T3); the latency numbers are small samples and depend on the external
model's load that day. The hourly scheduled test on AWS (5 questions) is the live health measure of the deployed system.</div>
<h3>Cost</h3>
<p>All spending is covered by the account's free-plan credits. Controls: a zero-spend AWS Budgets alert created first, tags on every resource, the smallest viable instance, 14-day log retention,
and a shut-down plan on the <a href="declaration.html">last page</a>. Idle cost of this design is mostly the instance, the public IPv4 address and CloudFront requests.</p>
{fig("01_budget_alert_created.png","E-16")}{fig("04_signed_in_as_iam_user_credits.png","E-16")}
""")

# ----------------------------------------------------------------------------------------------- 9 NEXT
page("next-steps.html", "What I would do next", """
<h2>What I would do next</h2>
<ol>
<li><b>MongoDB authentication</b> (the gap named in the Well-Architected review): store a database password in Parameter Store and require it, plus a secret header so only CloudFront can talk to the origin. About one hour.</li>
<li><b>Automatic recovery and off-instance copies:</b> daily EBS snapshots with Data Lifecycle Manager and an auto-recovery alarm on the instance; later a second Availability Zone behind a load balancer. This lifts Reliability from adequate to good.</li>
<li><b>Deploy from Git automatically:</b> a GitHub Actions workflow that runs the tests and then the SSM command that already pulls and restarts the stack, so a change to <code>main</code> updates the running system.</li>
<li><b>Better quality measurement:</b> grow the labelled set well past 30 questions written by someone else, add checks for capacity and arithmetic (the failing test T3), and add a thumbs-up/down feedback metric from real guests.</li>
<li><b>Protect the free model quota:</b> rate limiting or AWS WAF in front of CloudFront, and an alarm on request volume, so a loop or a bot cannot burn the quota or, on a paid key, the budget.</li>
</ol>
""")

# ----------------------------------------------------------------------------------------------- 10 DECLARATION
sid = CFG["student_id"] or PENDING
ddate = CFG["declaration_date"] or PENDING
page("declaration.html", "Declaration, credits and clean-up", f"""
<h2>Credits and licences</h2>
<ul><li><b>LibreChat</b> - Danny Avila and contributors, MIT licence, <a href="https://github.com/danny-avila/LibreChat">github.com/danny-avila/LibreChat</a>. Used as an unmodified container image; the reskin is configuration, branding and the gateway in my repository.</li>
<li><b>Google Gemini API</b> - free tier under Google's terms of use.</li>
<li>Logo, knowledge-base documents, scripts and website text: written for this project (see the AI statement below). AWS documentation was used as reference.</li></ul>
<h2>Use of an AI tool</h2>
<p>I used Claude (Anthropic) through Claude Code to write the scripts, configuration, gateway code, website text and diagram, and to suggest what to check. I verified everything
by running it in my own AWS account, reading the real command output, and taking every screenshot myself; no result or screenshot on this site was invented.</p>
<h2>Clean-up plan</h2>
<p>After marking: terminate the EC2 instance, delete the CloudFront distribution, the S3 buckets (empty them first), the Parameter Store parameters, the EventBridge rules,
the CloudWatch alarms, dashboard and log groups, the CloudTrail trail, the SNS topic and the IAM roles, revoke the Google AI Studio key, then confirm nothing is left and tell the instructor.</p>
<h2>Declaration (Appendix H)</h2>
<div class="box"><p>We confirm that the work submitted for SAM10 - Systems Administration and Maintenance, Final Project - is our own, except where clearly identified as borrowed,
based on an existing open project, or as AI-assisted. We confirm that:</p><ul>
<li>the base system we built on is identified and credited, and we have complied with its licence;</li>
<li>the system described on our website and in our repository exists and can be demonstrated;</li>
<li>all data and content used in the system is invented, and contains no real patient, student or staff information;</li>
<li>our AI system does not make consequential decisions about identifiable people;</li>
<li>all evidence submitted is authentic and has not been altered to misrepresent results;</li>
<li>no AWS credentials, API keys or passwords are included in this submission, including in the history of our repository; and</li>
<li>we have read and accept the academic integrity and ethics requirements of this course.</li></ul>
<p><b>Student name:</b> {CFG['student_name']} &nbsp; <b>Student ID:</b> {sid}<br><b>Signature:</b> ______________________ &nbsp; <b>Date:</b> {ddate}</p>
<p><em>Working alone: one signatory.</em> E-mail addresses visible in a few screenshots were masked before publication.</p></div>
""")
