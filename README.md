# InG AI Sales Department - Multi-Agent LinkedIn Outreach System

AI-powered sales department with three specialised agents: **Sales Manager Agent** (coordinates operations), **Lead Finder Agent** (discovers prospects), and **Outreach Agent** (sends messages and analyses responses). Human team focuses on deal closure.

## Project Structure

```
InG_agents/
├── docs/                          # Documentation (condensed versions)
│   ├── 01-use-cases.md           # Use cases for business analyst (~160 lines)
│   ├── 02-technical-solution.md  # Technical solution for architect (~250 lines)
│   ├── 03-technical-specification.md  # Technical spec for programmer (~280 lines)
│   ├── 04-test-plan.md           # Test plan for QA engineer (~160 lines)
│   └── 05-agent-context-management.md  # Context management (~200 lines)
├── src/                           # Source code
│   ├── agents/                    # AI agents
│   │   ├── sales_manager_agent.py
│   │   ├── lead_finder_agent.py
│   │   └── outreach_agent.py
│   ├── core/                     # Core business logic
│   ├── integrations/             # External service integrations
│   ├── communication/            # Inter-agent communication
│   └── utils/                     # Utility modules
├── tests/                         # Test suite
├── config/                        # Configuration files
├── logs/                          # Application logs
├── main.py                        # Main entry point
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Documentation

All project documentation is located in the `docs/` directory (condensed versions, ~200-300 lines each):

- **01-use-cases.md**: Business use cases and requirements for analysts
- **02-technical-solution.md**: Architecture and technical solution for architects
- **03-technical-specification.md**: Implementation specification for developers
- **04-test-plan.md**: Test plan and methodology for QA engineers
- **05-agent-context-management.md**: How agents preserve and share context

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (see `config/.env.example`)

3. Set up Google Sheets credentials

4. Run the agent:
```bash
python main.py
```

## Features

- **Three AI Agents**: Sales Manager (coordination), Lead Finder (prospecting), Outreach (messaging)
- **LLM Integration**: OpenAI/Anthropic for intelligent decisions and message generation
- **Inter-Agent Communication**: Redis message queue for coordination
- **Shared State Management**: Google Sheets as database, Redis for caching
- **Automated Lead Classification**: Speaker/Sponsor classification with quality scoring
- **Personalised Messages**: LLM-generated messages with context from other agents
- **Response Analysis**: Sentiment and intent detection using LLM
- **Rate-Limited Outreach**: 30-50 messages/day, compliance with LinkedIn ToS
- **Daily Reports**: Comprehensive performance reports with insights
- **Context Sharing**: Agents share knowledge and context for better decisions

## Requirements

- Python 3.10+
- Redis server (for message queue)
- Google Sheets API access
- LinkedIn automation service (Dripify or Gojiberry)
- LLM API access (OpenAI or Anthropic)
- SMTP email access for reports

## License

Proprietary - InG Internal Use Only
