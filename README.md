# ⚡ AgileFlow

**Sprint intelligence that runs itself.**

AgileFlow automates stand-ups, tracks sprint health, detects tech debt, and generates AI-powered insights — so your team can just code.

## Quick Start

```bash
# Pull and scan your project (Pro/Team license)
docker run -v /your/project:/repo \
  -e LICENSE_KEY=YOUR_KEY \
  agileflow/engine --repo /repo

# Demo mode (no license needed)
docker run --rm agileflow/engine --demo
```

## Features

| Module | Tier | What It Does |
|---|---|---|
| 📊 AI Activity Analysis | Free | Generates async stand-ups from commits |
| 🔄 Smart Board Sync | Free | Maps commits to tickets (95% confidence) |
| ❤️ Health Score | Free | Real-time project health (0-100) |
| 🛡️ Tech Debt Sentinel | Pro | Auto-generates refactor tickets |
| 📈 Velocity Forecast | Pro | Predicts sprint risk |
| 🧠 AI Sprint Narrative | Pro | LLM-powered natural language reports |
| 🔗 Integrations | Team | Slack, Discord, GitHub |

## Pricing

| Plan | Price | Repos | Key Features |
|---|---|---|---|
| **Free** | $0/mo | 2 | Activity, Board Sync, Health |
| **Pro** | $29/mo | 10 | + Debt, Velocity, Narrative |
| **Team** | $99/mo | Unlimited | + Integrations, Priority Support |

## How It Works

```
Pay via Stripe → Get LICENSE_KEY → Run Docker → Get insights
```

Your code **never leaves your machine**. AgileFlow runs locally inside a Docker container — it reads your git history and outputs analysis to your terminal. No cloud. No data sent anywhere.

## Supported LLM Providers

| Provider | Env Variable | Default Model |
|---|---|---|
| Google Gemini | `LLM_PROVIDER=gemini` | gemini-2.0-flash |
| OpenAI | `LLM_PROVIDER=openai` | gpt-4o-mini |
| Ollama (local) | `LLM_PROVIDER=ollama` | llama3 |
| Mock (demo) | `LLM_PROVIDER=mock` | — |

## Project Structure

```
├── ghost_scrum_master/         # Core engine (Docker distribution)
│   ├── main.py                 # CLI entry point (v6.0)
│   ├── Dockerfile              # Production container
│   ├── core/
│   │   ├── git_scanner.py      # Real git repo analysis
│   │   ├── board_scanner.py    # Auto-discover tickets from commits
│   │   ├── license.py          # License key validation + tier gating
│   │   ├── llm_client.py       # Provider-agnostic LLM interface
│   │   ├── ai_analyser.py      # AI reasoning engine
│   │   ├── predictive.py       # Health scoring
│   │   ├── debt_sentinel.py    # Tech debt detection
│   │   └── velocity.py         # Sprint forecasting
│   └── mocks/                  # Demo data
└── landing/                    # Marketing site
    ├── index.html              # Landing page with Stripe checkout
    ├── style.css               # Premium dark-mode design
    ├── success.html            # Post-purchase onboarding
    └── cancel.html             # Cancellation page
```

## Security

- **Code stays local** — Docker runs on your machine, nothing uploaded
- **License key validation** — Invalid/expired keys blocked at startup
- **Docker distribution** — Source code bundled in image layers, not exposed
- **No telemetry** — Zero data collection

## License

Proprietary. See [pricing](https://agileflow.dev/pricing).
