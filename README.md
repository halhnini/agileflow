# ⚡ AgileFlow

**Sprint intelligence that runs itself.**

AgileFlow automates stand-ups, tracks sprint health, detects tech debt, and generates AI-powered insights — so your team can just code.

## Features

| Module | What It Does |
|---|---|
| 📊 AI Activity Analysis | Generates async stand-ups from commit history |
| 🔄 Smart Board Sync | Maps commits to tickets with 95% confidence |
| ❤️ Health Score | Real-time project health (0-100) |
| 🛡️ Tech Debt Sentinel | Auto-generates refactor tickets from diff analysis |
| 📈 Velocity Forecast | Predicts sprint risk with scope recommendations |
| 🧠 AI Sprint Narrative | LLM-powered natural language sprint reports |

## Quick Start

```bash
# Run with mock AI (no API key needed)
docker build -t agileflow ./ghost_scrum_master
docker run --rm agileflow

# Run with a real LLM
docker run --rm \
  -e LLM_PROVIDER=gemini \
  -e LLM_API_KEY=your-key \
  agileflow
```

## Supported LLM Providers

| Provider | Env Variable | Default Model |
|---|---|---|
| OpenAI | `LLM_PROVIDER=openai` | gpt-4o-mini |
| Google Gemini | `LLM_PROVIDER=gemini` | gemini-2.0-flash |
| Ollama (local) | `LLM_PROVIDER=ollama` | llama3 |
| Mock (demo) | `LLM_PROVIDER=mock` | — |

## Project Structure

```
├── ghost_scrum_master/     # Core engine
│   ├── main.py             # Unified dashboard (v5.0)
│   ├── Dockerfile          # Production container
│   ├── core/
│   │   ├── llm_client.py   # Provider-agnostic LLM interface
│   │   ├── ai_analyser.py  # AI reasoning engine
│   │   ├── predictive.py   # Health scoring
│   │   ├── debt_sentinel.py # Tech debt detection
│   │   └── velocity.py     # Sprint forecasting
│   └── mocks/              # Demo data
└── landing/                # Marketing site
    ├── index.html
    └── style.css
```

## License

MIT
