# AILinux Project File Structure

## Overview

This document provides a detailed overview of the AILinux project file structure based on the actual files present in the codebase. It serves as a reference for developers working on the project.

## Root Directory Structure

```
/home/zombie/ailinux/
├── .github/workflows/      # GitHub CI/CD configuration
├── backend/                # Server-side logic and AI processing
├── client/                 # Client-side utilities and helper scripts
├── frontend/               # User interface components
├── logs/                   # Application logs
├── hierarchy_analysis.log  # Analysis of directory structure
├── large_files.json        # Tracking of large files in the project
├── LICENSE                 # Project license
├── optimization.log        # Code optimization logs
├── README.md               # Project documentation
├── requirements.txt        # Project-wide Python dependencies
├── SECURITY.md             # Security guidelines
└── structure.txt           # Project structure overview
```

## Backend Directory

The backend directory contains the server-side logic, AI model integration, and API endpoints.

```
/home/zombie/ailinux/backend/
├── ai_model.py             # AI model integration core (GPT4All, OpenAI, Gemini, HuggingFace)
├── app.py                  # Flask REST API server for log analysis
├── backend.js              # Express-based Node.js backend server
├── backend.log             # Backend server logs
├── gpt4all/                # GPT4All model-specific implementations
│   └── app.py              # GPT4All command line interface
├── gpt4allinit.py          # GPT4All initialization and setup script
├── hugging.py              # Hugging Face model search and exploration utility
├── huggingface.py          # Hugging Face model integration and management
├── package-lock.json       # Node.js dependency lock file
├── requirements.txt        # Python dependencies for backend
└── websocketserv.py        # WebSocket server for real-time communication
```

## Frontend Directory

The frontend directory contains the user interface components, primarily using Electron for desktop application functionality.

```
/home/zombie/ailinux/frontend/
├── aiineraction.html       # AI interaction web interface
├── config.js               # Configuration management and settings
├── config.py               # Python configuration loader
├── default.json            # Default configuration settings
├── frontend.log            # Frontend application logs
├── gemini-api-setup.js     # Google Gemini API configuration
├── importexport.js         # Settings import/export utility
├── index.html              # Main application HTML interface
├── llama.html              # LLaMA model interface
├── log.html                # Log viewer interface
├── logmanager.js           # Log management utility
├── main.js                 # Electron main process
├── package.json            # Frontend Node.js dependencies
├── package-lock.json       # Frontend dependency lock file
├── preload.js              # Electron preload script for secure IPC
├── requirements.txt        # Python dependencies for frontend
├── settings.html           # Settings management interface
└── twitchbot.py            # Twitch integration bot
```

## Client Directory

The client directory contains utilities and scripts for managing the application, file synchronization, and development tools.

```
/home/zombie/ailinux/client/
├── adjust_hierarchy_with_debugger.py  # Directory structure fix utility
├── alphaos.py                         # WebSocket client implementation
├── analyze.py                         # Code analysis utility
├── bigfiles.py                        # Large file finder (Python implementation)
├── bigfiles.sh                        # Large file finder (Shell implementation)
├── cleanup.py                         # Code cleanup and maintenance utility
├── file-sync-client.py                # File synchronization with remote server
├── package.json                       # Client-side Node.js dependencies
├── package-lock.json                  # Client-side dependency lock file
├── postcode.sh                        # Code analysis and reporting script
├── postlog.sh                         # Log collection and aggregation script
├── requirements.txt                   # Python dependencies for client utilities
├── start.js                           # Application starter script (Node.js)
├── start.sh                           # Application startup shell script
├── uploadready.py                     # GitHub upload preparation utility
└── websocket_client.py                # WebSocket client for backend communication
```

## GitHub Workflows

```
/home/zombie/ailinux/.github/workflows/
└── pylint.yml              # Automated Python code quality checks with Pylint
```

## Key File Descriptions

### Backend

- **ai_model.py**: Core module that provides interfaces to multiple AI models including GPT4All, OpenAI, Google Gemini, and Hugging Face. Handles model initialization, prompt creation, and inference.

- **app.py**: Flask-based REST API server that exposes endpoints for log analysis, model management, and system status monitoring.

- **websocketserv.py**: WebSocket server implementation for real-time communication between frontend and backend, supporting features like streaming log analysis.

### Frontend

- **index.html**: Main application interface with tabs for log analysis, model selection, log viewing, and system status.

- **main.js**: Electron main process that manages application windows, handles IPC (Inter-Process Communication), and integrates with native OS features.

- **preload.js**: Secure bridge between renderer and main processes in Electron, exposing a limited API to the frontend.

### Client

- **start.js**: Main application starter that launches both backend and frontend processes with proper environment configuration.

- **file-sync-client.py**: Manages synchronization of files between local and remote servers with support for different sync modes.

- **uploadready.py**: Prepares the codebase for GitHub uploads, managing large files and directory structure.

## Dependencies

The project has separate dependency files for different components:

- **Root requirements.txt**: Project-wide Python dependencies
- **Backend requirements.txt**: Backend-specific Python dependencies
- **Frontend requirements.txt**: Frontend-specific Python dependencies
- **Client requirements.txt**: Client utilities Python dependencies
- **package.json files**: Node.js dependencies for respective components

## Development Workflow

### Local Development

1. Run `node start.js local` to start the application in local mode
2. Backend API will be available at http://localhost:8081
3. WebSocket server will be available at ws://localhost:8082
4. Electron frontend will launch automatically

### Remote Deployment

1. Run `node start.js remote` to connect to remote server (derleiti.de)
2. Backend API will be available at https://derleiti.de:8081
3. WebSocket server will be available at wss://derleiti.de:8082

## AI Models

The system supports multiple AI models for log analysis:

- **GPT4All**: Local inference with GGUF models
- **OpenAI**: Cloud-based API using GPT models
- **Google Gemini**: Google's Gemini Pro model
- **Hugging Face**: Various open-source models like Mistral
