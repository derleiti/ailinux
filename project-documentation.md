# AILinux: AI-Powered Log Analysis and Debugging

AILinux is a comprehensive tool that combines modern technologies to provide AI-powered log analysis and debugging capabilities. This document provides an overview of the improved codebase and instructions for getting started.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Improvements](#key-improvements)
4. [Setup and Installation](#setup-and-installation)
5. [Usage Guide](#usage-guide)
6. [AI Models](#ai-models)
7. [Configuration](#configuration)
8. [Development Guidelines](#development-guidelines)

## Overview

AILinux is designed to help developers and system administrators analyze logs and debug issues efficiently using AI models. The system integrates multiple AI models, including OpenAI's GPT-4, LLaMA (local model), and Google Gemini, to provide comprehensive insights into log data.

### Core Features

- **AI-powered log analysis**: Process and interpret error logs for faster debugging
- **Multi-model support**: Use online services (OpenAI, Google Gemini) or offline models (LLaMA) 
- **Interactive UI**: User-friendly Electron interface for log input and analysis
- **WebSocket integration**: Real-time communication for immediate responses
- **Unified configuration**: Centralized settings management across components

## Architecture

AILinux follows a client-server architecture:

- **Frontend**: Electron-based desktop application
- **Backend**: Flask-based server for processing logs with AI models
- **Communication**: REST API and WebSockets for data exchange

### Component Overview

```
AILinux/
├── backend/               # Server-side code
│   ├── app.py            # Flask server
│   ├── ai_model.py       # AI model integration
│   └── logs/             # Log storage
├── frontend/             # Client-side code
│   ├── main.js           # Electron main process
│   ├── preload.js        # Secure IPC bridge
│   ├── index.html        # Main UI
│   └── settings.html     # Configuration UI
├── config.js             # Unified configuration system
├── start.sh              # Startup script
└── logs/                 # Application logs
```

## Key Improvements

The improved codebase incorporates several enhancements:

1. **Unified Configuration System**
   - Centralized configuration with environment variable support
   - User-specific settings stored in platform-appropriate locations
   - Consistent API across frontend and backend

2. **Enhanced Error Handling**
   - Comprehensive try-catch blocks throughout the codebase
   - Detailed error logging with context information
   - User-friendly error messages in the UI

3. **Modular AI Model Integration**
   - Pluggable model architecture for easy addition of new AI services
   - Graceful fallbacks when specific models are unavailable
   - Environment variables for API keys and model paths

4. **Improved User Experience**
   - Responsive, mobile-friendly UI with dark mode support
   - Real-time feedback during AI processing
   - Enhanced log display with syntax highlighting

5. **Robust Startup Process**
   - Dependency checking during startup
   - Clear error messages for missing requirements
   - Logging of startup process for easier troubleshooting

## Setup and Installation

### Prerequisites

- Python 3.8+ and pip
- Node.js 16+ and npm
- For local AI: 8GB+ RAM and sufficient disk space for models

### Installation Steps

1. **Clone the repository**

```bash
git clone https://github.com/your-username/ailinux.git
cd ailinux
```

2. **Install backend dependencies**

```bash
cd backend
pip install -r requirements.txt
cd ..
```

3. **Install frontend dependencies**

```bash
cd frontend
npm install
cd ..
```

4. **Configure environment variables**

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
LLAMA_MODEL_PATH=path/to/llama/model
```

5. **Start the application**

```bash
./start.sh
```

## Usage Guide

### Analyzing Logs

1. Start AILinux using `./start.sh`
2. In the main interface, select your preferred AI model from the dropdown
3. Paste your log or error message into the text area
4. Click "Analyze" or press Enter
5. Review the AI's analysis in the chat window

### Loading Log Files

1. Click "Load Log File" in the Debug Tools panel
2. Select a log file from your system
3. The log content will be loaded into the input area
4. Click "Analyze" to process the log

### Configuration

1. Click the "Settings" button in the header
2. Configure API keys for various AI services
3. Adjust application settings as needed
4. Click "Save" to apply changes

## AI Models

AILinux supports the following AI models:

### LLaMA (Local)

- **Advantages**: Works offline, complete privacy, no API costs
- **Disadvantages**: Requires more system resources, potentially slower
- **Setup**: Download the model file and set `LLAMA_MODEL_PATH` in the `.env` file

### ChatGPT (OpenAI)

- **Advantages**: Powerful language model, continuously improved
- **Disadvantages**: Requires internet, API costs, potential privacy concerns
- **Setup**: Get an API key from OpenAI and set `OPENAI_API_KEY` in the `.env` file

### Google Gemini

- **Advantages**: Competitive performance, potentially cheaper than OpenAI
- **Disadvantages**: Requires internet, API costs, potential privacy concerns
- **Setup**: Get an API key from Google and set `GEMINI_API_KEY` in the `.env` file

## Configuration

The unified configuration system provides several ways to configure AILinux:

1. **Environment Variables**: Set in `.env` file or system environment
2. **User Configuration**: Stored in a user-specific location based on OS
3. **Command-line Arguments**: Override config values at startup (planned feature)

### Configuration Categories

- **AI Model Settings**: API keys, model paths, default model
- **Server Settings**: Host, port, CORS settings
- **Frontend Settings**: Window size, theme, UI preferences
- **Logging Settings**: Log levels, file locations, rotation policy
- **Feature Flags**: Toggle experimental features

## Development Guidelines

### Backend Development

- Follow PEP 8 style guidelines for Python code
- Add proper docstrings to all modules and functions
- Include type hints where appropriate
- Write unit tests for new functionality
- Use the logging module instead of print statements

### Frontend Development

- Follow standard JavaScript/HTML/CSS best practices
- Use ES6+ features but ensure compatibility
- Implement responsive design for all UI components
- Handle errors gracefully with user-friendly messages
- Use the IPC bridge for main process communication

### Documentation

- Document new features in code comments
- Update README.md with significant changes
- Maintain this documentation with new functionality
- Include examples for complex features

## License

AILinux is available under the MIT License. See the LICENSE file for more details.

---

Thank you for using or contributing to AILinux! If you have questions or encounter issues, please open an issue on GitHub.
