# Costa Leona Resort - Leona Front Desk (SAM10 Final Project)

Leona is a virtual front-desk assistant for **Costa Leona Resort**, a *fictional* beach resort. Guests ask about rooms, check-in times, amenities, house rules and directions. The system is informational only: it never books, charges or decides anything about a person.

- Student: Stephanie Joy Revano (working alone, 100% of the individual mark)
- Course: SAM10 - Systems Administration and Maintenance
- AWS region: ap-southeast-1 (Singapore), one region, one database

## Credits and licence of the base system
| Item | Detail |
|---|---|
| Base system | LibreChat v0.8.9 |
| Source | https://github.com/danny-avila/LibreChat |
| Author | Danny Avila and the LibreChat contributors |
| Licence | MIT - https://github.com/danny-avila/LibreChat/blob/main/LICENSE |
| What it did originally | A ChatGPT-style multi-provider chat interface with user accounts |

LibreChat is used unmodified as a container image. This repository contains only the reskin and operations code (configuration, branding, gateway, knowledge base, automation). The MIT licence permits this, and attribution is kept here and on the project website.

## What was changed (the reskin)
1. **Identity** - new name, sun-and-waves logo, teal/gold theme, favicon, tab title, wording (`librechat.yaml`, `branding/`).
2. **Data** - six invented resort documents in `knowledge/` (no real data). On AWS they are read from S3.
3. **Domain language** - the assistant, welcome text, rules and footer speak hotel front-desk language (`gateway/app.py`, `librechat.yaml`).
4. **AWS integration** - S3 (knowledge base), SSM Parameter Store SecureString (model key and gateway token), CloudWatch custom metrics, SNS alerts, EventBridge schedules.

## Architecture
`Guest -> HTTPS -> CloudFront/ALB -> EC2 (LibreChat + Leona gateway + MongoDB in Docker) -> Gemini API (external, free tier)`
The gateway reads the knowledge base from S3, reads the model key from SSM, logs every request as one JSON line and publishes CloudWatch metrics. See the project website for the diagram.

## Run locally
```
cp .env.example .env      # fill in values; .env is git-ignored
docker compose up -d --build
# open http://localhost:3081
```

## Security rules followed
- No secrets in code, config or git history. `.env` is git-ignored; on AWS the secrets live in SSM Parameter Store.
- Only invented data is stored or sent to the third-party model.

## Contribution log (solo)
| Date | Work |
|---|---|
| 2026-11-26 | Budget alert, root MFA, IAM user with MFA, region choice, baseline inventory |
| 2026-11-26 | LibreChat running locally, original screenshots, reskin (logo, theme, knowledge base, gateway) |

*(Updated as work progresses.)*
