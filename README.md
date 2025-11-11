# InG LinkedIn Outreach Automation Agent

Automated LinkedIn outreach agent for identifying and contacting potential speakers and sponsors for tech events.

## Project Structure

```
InG_agents/
├── docs/                          # Documentation
│   ├── 01-use-cases.md           # Use cases for business analyst
│   ├── 02-technical-solution.md  # Technical solution for architect
│   ├── 03-technical-specification.md  # Technical spec for programmer
│   └── 04-test-plan.md           # Test plan for QA engineer
├── src/                           # Source code
│   ├── core/                     # Core business logic
│   │   ├── prospect_classifier.py
│   │   ├── message_generator.py
│   │   └── rate_limiter.py
│   ├── integrations/             # External service integrations
│   │   ├── google_sheets_io.py
│   │   ├── linkedin_sender.py
│   │   └── email_service.py
│   └── utils/                     # Utility modules
│       ├── config_loader.py
│       ├── logger.py
│       └── validators.py
├── tests/                         # Test suite
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── config/                        # Configuration files
│   ├── config.yaml
│   ├── templates.yaml
│   └── .env.example
├── logs/                          # Application logs
├── main.py                        # Main entry point
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Documentation

All project documentation is located in the `docs/` directory:

- **01-use-cases.md**: Business use cases and requirements for analysts
- **02-technical-solution.md**: Architecture and technical solution for architects
- **03-technical-specification.md**: Detailed implementation specification for developers
- **04-test-plan.md**: Test plan and methodology for QA engineers

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

- Automated lead classification (Speakers/Sponsors)
- Personalised message generation
- Rate-limited LinkedIn outreach
- Google Sheets integration for lead management
- Daily activity reports via email
- Comprehensive error handling and logging

## Requirements

- Python 3.10+
- Google Sheets API access
- LinkedIn automation service (Dripify or Gojiberry)
- SMTP email access for reports

## License

Proprietary - InG Internal Use Only
