# AILinux Project File Structure (2025 Edition)

## Overview

This document provides a comprehensive overview of the AILinux project structure, highlighting the organization and relationships between different components.

## Root Directory

```
/ailinux/
├── .github/                  # GitHub workflow configurations
├── client/                   # Electron client application
│   ├── frontend/             # User interface components
│   ├── backend/              # Client-side backend logic
│   ├── config/               # Configuration management
│   └── assets/               # Static assets and resources
│
├── server/                   # Backend server components
│   ├── backend/              # Core server-side logic
│   │   ├── ai_model.py       # AI model management
│   │   ├── app.py            # Flask API server
│   │   ├── websocket_server.py # Real-time WebSocket server
│   │   └── data_server.py    # Data collection and storage
│   │
│   ├── models/               # AI model files and configurations
│   └── logs/                 # Server-side log storage
│
├── devtools/                 # Development and maintenance scripts
│   ├── code_optimizer.py     # Code quality and optimization tools
│   ├── file_analyzer.py      # Project structure analysis
│   └── sync_tools.py         # Repository synchronization utilities
│
├── docs/                     # Project documentation
│   ├── architecture.md       # System architecture details
│   ├── deployment.md         # Deployment guidelines
│   └── contribution.md       # Contribution guidelines
│
├── tests/                    # Testing frameworks and test suites
│   ├── unit/                 # Unit testing
│   ├── integration/          # Integration testing
│   └── performance/          # Performance benchmark tests
│
├── scripts/                  # Utility and setup scripts
│   ├── setup.sh              # Project setup script
│   ├── start.sh              # Application startup script
│   └── install_dependencies.py # Dependency management
│
├── config/                   # Global configuration files
│   ├── .env.example          # Environment configuration template
│   └── settings.json         # Default application settings
│
└── requirements.txt          # Python dependencies
```

## Detailed Component Breakdown

### Client Application (`/client`)

#### Frontend (`/client/frontend`)
- User interface components
- Electron-based desktop application
- Configuration management
- Static assets

#### Backend (`/client/backend`)
- Local processing logic
- AI model interaction
- Electron preload and main process scripts

### Server Components (`/server`)

#### Backend (`/server/backend`)
- Flask REST API server
- WebSocket communication server
- AI model management module
- Data collection and storage

#### Models (`/server/models`)
- Local AI model storage
- Model configuration files
- Cached model weights

### Development Tools (`/devtools`)
- Code optimization scripts
- File analysis utilities
- Repository synchronization tools

### Documentation (`/docs`)
- Comprehensive project documentation
- Architecture descriptions
- Deployment guidelines
- Contribution instructions

### Testing (`/tests`)
- Unit tests
- Integration tests
- Performance benchmarks

### Configuration (`/config`)
- Environment configuration templates
- Default application settings

## AI Model Support

### Local Models
- GPT4All
- Hugging Face Transformers
- Custom local model support

### Cloud Models
- OpenAI GPT
- Google Gemini
- Anthropic Claude

## Key Configuration Files

- `.env`: Environment-specific configurations
- `requirements.txt`: Python dependencies
- `package.json`: Node.js dependencies and scripts
- `pyproject.toml`: Python project metadata

## Electron Configuration

- `main.js`: Electron main process
- `preload.js`: Secure context bridge
- `renderer.js`: Rendering process logic

## Development Workflow

1. Local Setup
   - Clone repository
   - Install dependencies
   - Configure environment
   - Run development server

2. Testing
   - Unit tests
   - Integration tests
   - Performance benchmarks

3. Deployment
   - Build Electron application
   - Package server components
   - Configure production environment

---

<p align="center">
  Last Updated: March 2025
  <br>
  Maintained by AILinux Development Team
</p>
