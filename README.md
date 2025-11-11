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
- **06-deployment-and-running.md**: How to run and deploy the system
- **07-prompt-compliance-check.md**: Compliance check with original requirements
- **08-google-sheets-schema.md**: Detailed Google Sheets schema with column names
- **09-llm-prompts.md**: LLM prompt templates for each agent
- **10-api-integrations.md**: External API integration details (Gemini, Sheets, LinkedIn, SMTP)
- **11-daily-report-format.md**: Daily report format and examples

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
   - Copy `config/env.example.txt` to `.env` and fill in your values
   - Copy `config/agents.yaml.example` to `config/agents.yaml` and adjust as needed

3. Set up Google Sheets credentials

4. Run all agents (one command):
```bash
python main.py
```

**Note**: This single command starts all three agents (Sales Manager, Lead Finder, Outreach) in parallel. They run continuously until stopped (Ctrl+C). See `docs/06-deployment-and-running.md` for details.

## Features

- **Three AI Agents**: Sales Manager (coordination), Lead Finder (prospecting), Outreach (messaging)
- **LLM Integration**: Google Gemini Preview API for intelligent decisions and message generation
- **Inter-Agent Communication**: File-based message queue (no servers needed)
- **Shared State Management**: Google Sheets as database, SQLite + local files for state
- **Automated Lead Classification**: Speaker/Sponsor classification with quality scoring
- **Personalised Messages**: LLM-generated messages with context from other agents
- **Response Analysis**: Sentiment and intent detection using LLM (10% error rate acceptable)
- **Rate-Limited Outreach**: 30-50 messages/day, compliance with LinkedIn ToS
- **Daily Reports**: Comprehensive performance reports with Agent Self-Review section
- **Context Sharing**: Agents share knowledge and context for better decisions
- **No External Servers**: All storage is local (SQLite + files)

## Requirements

- Python 3.10+
- **No external servers needed** - all storage is local (SQLite + files)
- Google Sheets API access
- LinkedIn automation service (Dripify or Gojiberry)
- Google Gemini Preview API access
- SMTP email access for reports

## License

Proprietary - InG Internal Use Only
