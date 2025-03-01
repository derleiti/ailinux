# AILinux Project Documentation

<p align="center">
  <img src="docs/images/ailinux-logo.png" alt="AILinux Logo" width="200"/>
  <br>
  <em>AI-Powered Log Analysis System</em>
  <br>
  <em>v1.0.0</em>
</p>

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Components Documentation](#3-components-documentation)
   - [3.1 AI Model Module](#31-ai-model-module)
   - [3.2 Flask API Server](#32-flask-api-server)
   - [3.3 WebSocket Server](#33-websocket-server)
   - [3.4 Data Collection Server](#34-data-collection-server)
   - [3.5 Electron Client](#35-electron-client)
4. [Setup and Installation Guide](#4-setup-and-installation-guide)
5. [Configuration Guide](#5-configuration-guide)
6. [User Guide](#6-user-guide)
7. [API Reference](#7-api-reference)
8. [Developer Guide](#8-developer-guide)
9. [Troubleshooting Guide](#9-troubleshooting-guide)
10. [Security Considerations](#10-security-considerations)
11. [Performance Optimization](#11-performance-optimization)
12. [Appendix](#12-appendix)

---

## 1. Introduction

AILinux is a comprehensive log analysis system that leverages artificial intelligence to provide insights into system logs. The project aims to simplify troubleshooting and debugging by processing log files through various AI models, both local and cloud-based, to extract meaningful patterns, identify issues, and suggest potential solutions.

### 1.1 Purpose

The primary goals of AILinux are:

- **Automated Log Analysis**: Reduce the manual effort required to analyze complex system logs
- **Multiple Model Support**: Provide flexibility in choosing AI models based on requirements and constraints
- **Real-time Feedback**: Deliver analysis results quickly through WebSocket connections
- **Cross-platform Compatibility**: Work across different operating systems and environments
- **Privacy-conscious Options**: Support for local models when data privacy is a concern

### 1.2 Target Audience

- **System Administrators**: Monitoring and maintaining servers and infrastructure
- **DevOps Engineers**: Analyzing deployment and operational logs
- **Software Developers**: Debugging application logs during development
- **Security Professionals**: Identifying potential security issues in system logs
- **IT Support Teams**: Resolving user-reported issues through log analysis

### 1.3 System Requirements

#### Server Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: Version 3.8 or higher
- **RAM**: 
  - Minimum: 4GB (with lightweight models)
  - Recommended: 16GB+ (for Hugging Face models)
- **Storage**: 
  - Minimum: 2GB for application and small models
  - Recommended: 10GB+ for multiple models
- **Network**: 
  - Internet connection (for cloud API models)
  - Accessible ports for API and WebSocket servers

#### Client Requirements

- **Operating System**: Linux, macOS, or Windows
- **Node.js**: Version 14 or higher
- **Electron**: Version 18 or higher
- **Network**: Connection to the AILinux server

---

## 2. System Architecture

AILinux follows a client-server architecture with multiple server components working together to provide a complete log analysis solution.

### 2.1 High-Level Architecture

```
┌─────────────────┐     HTTP/WebSocket     ┌──────────────────────────────┐
│                 │<─────────────────────▶│                              │
│  Electron       │                        │  AILinux Server Components   │
│  Client         │                        │                              │
│                 │                        │  ┌────────────┐ ┌──────────┐ │
│  - User         │       REST API         │  │            │ │          │ │
│    Interface    │<─────────────────────▶│  │ Flask API  │ │ AI Model │ │
│  - Settings     │                        │  │  Server    │ │  Module  │ │
│    Management   │                        │  │            │ │          │ │
│  - Log Upload   │                        │  └────────────┘ └──────────┘ │
│  - Results      │                        │                              │
│    Viewer       │                        │  ┌────────────┐ ┌──────────┐ │
│                 │      WebSockets        │  │ WebSocket  │ │   Data   │ │
│                 │<─────────────────────▶│  │   Server    │ │  Server  │ │
│                 │                        │  │            │ │          │ │
└─────────────────┘                        │  └────────────┘ └──────────┘ │
                                           └──────────────────────────────┘
                                                        ▲
                                                        │
                                                        ▼
                                           ┌──────────────────────────────┐
                                           │                              │
                                           │        AI Resources          │
                                           │                              │
                                           │  ┌────────────┐ ┌──────────┐ │
                                           │  │   Local    │ │  Cloud   │ │
                                           │  │   Models   │ │   APIs   │ │
                                           │  │ (GPT4All,  │ │ (OpenAI, │ │
                                           │  │ HuggingFace)│ │  Gemini) │ │
                                           │  └────────────┘ └──────────┘ │
                                           │                              │
                                           └──────────────────────────────┘
```

### 2.2 Component Interactions

- **Client-Server Communication**:
  - REST API for configuration, model selection, and log analysis requests
  - WebSocket connections for real-time updates during analysis

- **Server Component Interactions**:
  - AI Model Module provides analysis capabilities to both the Flask API and WebSocket servers
  - Data Server stores historical analysis for reference and improvement
  - All components share configuration through environment variables

- **External Services**:
  - Cloud API models (OpenAI, Google Gemini) when selected and configured
  - Local model files loaded from disk

### 2.3 Data Flow

1. **Log Submission**:
   - User uploads or pastes log text via the Electron client
   - Log data is sent to the server via REST API or WebSocket

2. **Log Processing**:
   - Server receives the log data and chosen AI model
   - AI Model module formats the prompt and sends to appropriate model

3. **Analysis Generation**:
   - AI model processes the log data and generates analysis
   - Results are returned to the server component

4. **Result Delivery**:
   - Analysis results are sent back to the client
   - Real-time updates provided via WebSocket when available
   - Results are stored in history for future reference

---

## 3. Components Documentation

### 3.1 AI Model Module

The AI Model module (`ai_model.py`) is the core component that provides AI-powered log analysis capabilities. It interfaces with different AI models and handles the preparation, processing, and retrieval of analysis results.

#### 3.1.1 Module Overview

```python
"""AI Model Integration for AILinux.

This module provides interfaces to various AI models for log analysis,
supporting both local models (GPT4All, Hugging Face) and cloud-based APIs (OpenAI, Google Gemini).
"""
```

#### 3.1.2 Key Classes and Functions

- **Model Initialization Functions**:
  - `initialize_gpt4all()`: Sets up the local GPT4All model
  - `initialize_openai()`: Configures the OpenAI API client
  - `initialize_gemini()`: Configures the Google Gemini API client
  - `initialize_huggingface()`: Sets up local Hugging Face models

- **Analysis Functions**:
  - `analyze_log()`: Main function for log analysis using the selected model
  - `create_prompt()`: Formats log text into standardized AI prompts
  - `get_model()`: Retrieves the appropriate model instance

- **Model-Specific Response Functions**:
  - `gpt4all_response()`: Gets analysis from GPT4All
  - `openai_response()`: Gets analysis from OpenAI
  - `gemini_response()`: Gets analysis from Google Gemini
  - `huggingface_response()`: Gets analysis from Hugging Face models

- **Utility Functions**:
  - `get_available_models()`: Returns information about all models

#### 3.1.3 Supported Models

| Model Type | Implementation | Requirements | Advantages | Limitations |
|------------|----------------|--------------|------------|-------------|
| GPT4All    | Local          | Model file (.gguf) | Privacy, No API costs | Limited capabilities compared to cloud models |
| OpenAI     | Cloud API      | API key      | Powerful capabilities | Cost, Internet dependency, Data privacy concerns |
| Google Gemini | Cloud API   | API key      | Strong performance | Cost, Internet dependency, Data privacy concerns |
| Hugging Face | Local/API    | Model files or API key | Flexible deployment | Large storage requirements for local models |

#### 3.1.4 Recommended Improvements

- Add proper timeout handling for model inference to prevent hanging
- Implement model caching for better performance
- Add fallback mechanisms when models fail to respond
- Introduce parallelization for handling multiple analysis requests

### 3.2 Flask API Server

The Flask API Server (`app.py`) provides a RESTful API interface for the AILinux system. It handles HTTP requests for log analysis, configuration management, and system status.

#### 3.2.1 Module Overview

```python
"""AILinux Backend Server for log analysis using AI models.

This module provides a Flask-based API that processes log files using 
various AI models and returns analysis results.
"""
```

#### 3.2.2 Key Endpoints

| Endpoint | Method | Description | Request Format | Response Format |
|----------|--------|-------------|----------------|-----------------|
| `/debug` | POST   | Analyzes log data | JSON with log text, model, and optional instruction | JSON with analysis results |
| `/logs`  | GET    | Retrieves backend logs | Optional limit parameter | JSON with log entries |
| `/models` | GET   | Gets available AI models | None | JSON with model information |
| `/settings` | GET/POST | Gets or updates settings | POST: JSON with settings | GET: JSON with current settings, POST: Success confirmation |
| `/health` | GET   | Server health check | None | JSON with status information |
| `/analysis_history` | GET | Gets historical analyses | None | JSON with analysis history |

#### 3.2.3 Request/Response Examples

**POST /debug Example**:

Request:
```json
{
  "log": "2023-05-01 12:34:56 ERROR Failed to connect to database: Connection refused",
  "model": "gpt4all",
  "instruction": "Focus on potential network issues"
}
```

Response:
```json
{
  "analysis": "## Log Analysis\n\nThis log entry indicates a database connection failure. The error 'Connection refused' typically means the database server is not accepting connections, which could be due to:\n\n1. The database service is not running\n2. A firewall is blocking the connection\n3. The database is configured to listen on a different port or interface\n\n### Recommendations:\n\n- Check if the database service is running\n- Verify network connectivity to the database server\n- Check firewall settings on both the client and server\n- Confirm the database connection string has the correct host and port",
  "processing_time": 1.45,
  "model": "gpt4all"
}
```

**GET /models Example**:

Response:
```json
{
  "models": [
    {
      "name": "gpt4all",
      "available": true,
      "type": "local",
      "file": "Meta-Llama-3-8B-Instruct.Q4_0.gguf"
    },
    {
      "name": "openai",
      "available": true,
      "type": "api",
      "model": "gpt-4"
    },
    {
      "name": "gemini",
      "available": false,
      "type": "api",
      "model": "gemini-pro"
    },
    {
      "name": "huggingface",
      "available": true,
      "type": "local",
      "model": "mistralai/Mistral-7B-Instruct-v0.2"
    }
  ]
}
```

#### 3.2.4 Recommended Improvements

- Add proper request size limits
- Implement rate limiting
- Add authentication for API endpoints
- Improve error handling and validation

### 3.3 WebSocket Server

The WebSocket Server (`websocketserv.py`) provides real-time communication between the client and server for log analysis. It enables streaming updates and interactive analysis sessions.

#### 3.3.1 Module Overview

```python
"""WebSocket server for AILinux.

This module provides a WebSocket server for real-time communication between
the frontend and backend components of AILinux.
"""
```

#### 3.3.2 Message Types

| Message Type | Direction | Purpose | Format |
|--------------|-----------|---------|--------|
| `authentication` | Client → Server | Initial connection authentication | Client info and optional API key |
| `authentication` | Server → Client | Authentication result | Success status and client ID |
| `ping` | Client → Server | Connection testing | Timestamp |
| `pong` | Server → Client | Connection confirmation | Timestamp |
| `analyze_log` | Client → Server | Request log analysis | Log text, model, and optional instruction |
| `request_received` | Server → Client | Analysis request acknowledgment | Request ID and status |
| `analysis_status` | Server → Client | Analysis progress updates | Request ID and status |
| `analysis_result` | Server → Client | Final analysis results | Request ID, analysis text, processing time, model |
| `get_models` | Client → Server | Request available models | None |
| `models_info` | Server → Client | Available models information | List of model details |
| `server_status` | Client → Server | Request server status | None |
| `server_status` | Server → Client | Server status information | Uptime, connected clients, active sessions |
| `error` | Server → Client | Error information | Error message and code |

#### 3.3.3 Connection Flow

1. **Initial Connection**:
   - Client connects to WebSocket server
   - Client sends `authentication` message with client information
   - Server validates authentication (if API key is required)
   - Server responds with `authentication` result

2. **Analysis Request**:
   - Client sends `analyze_log` message with log content
   - Server responds with `request_received` acknowledgment
   - Server periodically sends `analysis_status` updates
   - Server sends final `analysis_result` when complete

3. **Keep-alive**:
   - Client periodically sends `ping` messages
   - Server responds with `pong` messages
   - Server tracks client activity and removes inactive clients

#### 3.3.4 Recommended Improvements

- Improve SSL certificate verification
- Enhance error recovery and reconnection logic
- Add support for binary message formats for efficiency
- Implement proper connection pools for handling many clients

### 3.4 Data Collection Server

The Data Collection Server (`data_server.py`) stores and manages log data, analysis results, and system information. It provides a central repository for historical analysis and data mining.

#### 3.4.1 Module Overview

```python
"""
AILinux Data Collection Server

This server application collects and stores data sent from AILinux clients.
It provides a REST API for data upload and a WebSocket server for real-time updates.
"""
```

#### 3.4.2 Key Classes and Functions

- **DataStorage**: Manages database operations for storing logs and analysis results
  - `store_log()`: Stores log entries in the database
  - `store_analysis()`: Stores analysis results in the database
  - `store_data()`: Stores generic data in the database
  - `get_logs()`: Retrieves logs with optional filtering

#### 3.4.3 Database Schema

The data server uses SQLite with the following tables:

**logs**:
- `id`: Text (Primary Key)
- `timestamp`: Text (ISO format)
- `source`: Text
- `level`: Text
- `message`: Text
- `metadata`: Text (JSON)

**analysis_results**:
- `id`: Text (Primary Key)
- `timestamp`: Text (ISO format)
- `log_id`: Text (Foreign Key to logs.id)
- `model`: Text
- `analysis`: Text
- `metadata`: Text (JSON)

**collected_data**:
- `id`: Text (Primary Key)
- `timestamp`: Text (ISO format)
- `data_type`: Text
- `content`: Text
- `metadata`: Text (JSON)

#### 3.4.4 Recommended Improvements

- Complete implementation of missing functions
- Implement proper connection pooling for SQLite
- Add support for more advanced database systems (PostgreSQL, MySQL)
- Implement data retention policies and cleanup

### 3.5 Electron Client

The Electron Client provides a cross-platform desktop application for interacting with the AILinux server components. It offers a user-friendly interface for submitting logs, viewing analysis results, and managing configuration.

#### 3.5.1 Main Features

- **Connection Management**: Connect to API and WebSocket servers
- **Log Input**: Text area and file upload for log content
- **Model Selection**: Choose from available AI models
- **Analysis Display**: View formatted analysis results
- **Settings Management**: Configure application preferences

#### 3.5.2 UI Components

- **Connection Panel**: Server URL configuration and connection status
- **Model Selection Panel**: AI model selection and model information
- **Log Input Panel**: Text input, file upload, and custom instructions
- **Analysis Results Panel**: Formatted display of analysis results
- **Settings Modal**: Application preferences and configuration

#### 3.5.3 Client-Side Functions

- **APIClient**: Handles REST API communication
  - `request()`: Generic method for API requests
  - `checkHealth()`: Verifies server availability
  - `getModels()`: Retrieves available models
  - `analyzeLog()`: Submits log for analysis
  - `getSettings()`, `updateSettings()`: Manages settings

- **WebSocketClient**: Handles WebSocket communication
  - `connect()`, `disconnect()`: Manages server connection
  - `send()`: Sends WebSocket messages
  - `on()`, `off()`: Event registration
  - `analyzeLog()`: Submits log for analysis
  - `ping()`: Connection testing

#### 3.5.4 Recommended Improvements

- Add offline mode support
- Implement log file preprocessing/filtering
- Add support for batch analysis of multiple logs
- Improve accessibility features
- Add support for dark mode / light mode themes

---

## 4. Setup and Installation Guide

### 4.1 Server Installation

#### 4.1.1 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning repository)
- Internet connection (for downloading dependencies)

#### 4.1.2 Installation Steps

1. **Clone or download the repository**:
   ```bash
   git clone https://github.com/yourusername/ailinux.git
   cd ailinux/server
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Linux/macOS
   python -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create necessary directories**:
   ```bash
   mkdir -p logs models/huggingface
   ```

5. **Create a .env file with configuration**:
   ```bash
   # Use your favorite text editor
   nano .env
   ```
   
   Add the following content (modify as needed):
   ```
   # Server configuration
   FLASK_HOST=0.0.0.0
   FLASK_PORT=8081
   WS_HOST=0.0.0.0
   WS_PORT=8082
   FLASK_DEBUG=False
   
   # Model paths and API keys
   OPENAI_API_KEY=your_openai_key_here
   GEMINI_API_KEY=your_gemini_key_here
   HUGGINGFACE_API_KEY=your_huggingface_key_here
   LLAMA_MODEL_PATH=./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf
   HUGGINGFACE_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.2
   HUGGINGFACE_CACHE_DIR=./models/huggingface
   
   # Default settings
   DEFAULT_MODEL=gpt4all
   ```

6. **Download required model files** (if using local models):
   
   For GPT4All:
   ```bash
   # Create models directory if it doesn't exist
   mkdir -p models
   
   # Download a model (example)
   wget -O models/Meta-Llama-3-8B-Instruct.Q4_0.gguf https://gpt4all.io/models/Meta-Llama-3-8B-Instruct.Q4_0.gguf
   ```
   
   Note: Model URLs may change over time. Visit the [GPT4All website](https://gpt4all.io/models/index.html) for current download links.

7. **Test the installation**:
   ```bash
   python ai_model.py
   ```
   
   This should display information about available models.

### 4.2 Client Installation

#### 4.2.1 Prerequisites

- Node.js 14 or higher
- npm (Node.js package manager)
- Git (optional, for cloning repository)

#### 4.2.2 Installation Steps

1. **Navigate to the client directory**:
   ```bash
   cd ../client
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure the client**:
   Create or modify `config.json`:
   ```json
   {
     "serverUrl": "http://localhost:8081",
     "wsUrl": "ws://localhost:8082",
     "defaultModel": "gpt4all",
     "theme": "light"
   }
   ```

4. **Build the application** (if needed):
   ```bash
   npm run build
   ```

5. **Start the development version**:
   ```bash
   npm start
   ```

### 4.3 Running the System

#### 4.3.1 Starting the Server Components

Start each server component in a separate terminal window (keep the virtual environment activated in each):

1. **Start the Flask API Server**:
   ```bash
   cd ailinux/server
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   python app.py
   ```

2. **Start the WebSocket Server**:
   ```bash
   cd ailinux/server
   source venv/bin/activate
   python websocketserv.py
   ```

3. **Start the Data Collection Server** (optional):
   ```bash
   cd ailinux/server
   source venv/bin/activate
   python data_server.py
   ```

#### 4.3.2 Starting the Client

```bash
cd ailinux/client
npm start
```

This will launch the Electron application. Use the connection panel to connect to your running servers.

#### 4.3.3 Verifying the Installation

1. Connect to the server using the client interface
2. Verify that available models are displayed
3. Try analyzing a simple log message
4. Check server logs for any errors or warnings

---

## 5. Configuration Guide

### 5.1 Server Configuration

AILinux server components are configured using environment variables, typically loaded from a `.env` file in the server directory.

#### 5.1.1 Core Server Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `FLASK_HOST` | Host address for the Flask API server | `0.0.0.0` | `localhost` |
| `FLASK_PORT` | Port for the Flask API server | `8081` | `9000` |
| `WS_HOST` | Host address for the WebSocket server | `0.0.0.0` | `localhost` |
| `WS_PORT` | Port for the WebSocket server | `8082` | `9001` |
| `FLASK_DEBUG` | Enable Flask debug mode | `False` | `True` |
| `ENVIRONMENT` | Environment type | `development` | `production` |

#### 5.1.2 AI Model Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DEFAULT_MODEL` | Default model to use for analysis | `gpt4all` | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | `""` | `sk-...` |
| `GEMINI_API_KEY` | Google Gemini API key | `""` | `AIza...` |
| `HUGGINGFACE_API_KEY` | Hugging Face API key | `""` | `hf_...` |
| `LLAMA_MODEL_PATH` | Path to the GPT4All model file | `Meta-Llama-3-8B-Instruct.Q4_0.gguf` | `./models/custom-model.gguf` |
| `HUGGINGFACE_MODEL_ID` | Hugging Face model ID | `mistralai/Mistral-7B-Instruct-v0.2` | `gpt2` |
| `HUGGINGFACE_CACHE_DIR` | Directory for Hugging Face models | `./models/huggingface` | `/data/models` |

#### 5.1.3 WebSocket Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `WS_USE_SSL` | Enable SSL for WebSocket | `False` | `True` |
| `WS_SSL_CERT` | Path to SSL certificate | `""` | `/etc/certs/cert.pem` |
| `WS_SSL_KEY` | Path to SSL key | `""` | `/etc/certs/key.pem` |
| `WEBSOCKET_API_KEY` | API key for WebSocket authentication | `""` | `secret-key` |
| `WS_RATE_LIMIT` | Rate limit for WebSocket messages (seconds) | `1.0` | `0.5` |
| `WS_MAX_MESSAGE_SIZE` | Maximum WebSocket message size (bytes) | `1048576` | `5242880` |

#### 5.1.4 Data Server Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DATA_DIR` | Directory for collected data | `./collected_data` | `/data/ailinux` |
| `DB_PATH` | Path to SQLite database | `./collected_data/ailinux_data.db` | `/data/db.sqlite` |
| `SERVER_HTTP_PORT` | Port for data server HTTP API | `8081` | `9002` |
| `SERVER_WS_PORT` | Port for data server WebSocket | `8082` | `9003` |

### 5.2 Client Configuration

The Electron client is configured through the settings UI or by editing the `config.json` file.

#### 5.2.1 Available Settings

| Setting | Description | Default | Options |
|---------|-------------|---------|---------|
| `serverUrl` | URL for the Flask API server | `http://localhost:8081` | Any valid URL |
| `wsUrl` | URL for the WebSocket server | `ws://localhost:8082` | Any valid WebSocket URL |
| `defaultModel` | Default AI model to use | `gpt4all` | `gpt4all`, `openai`, `gemini`, `huggingface` |
| `theme` | UI theme | `light` | `light`, `dark`, `system` |
| `maxLogSize` | Maximum log size (bytes) | `100000` | Any positive integer |
| `huggingfaceModelId` | Hugging Face model ID | `mistralai/Mistral-7B-Instruct-v0.2` | Any valid model ID |

#### 5.2.2 Configuration File Example

```json
{
  "serverUrl": "http://localhost:8081",
  "wsUrl": "ws://localhost:8082",
  "defaultModel": "gpt4all",
  "theme": "system",
  "maxLogSize": 500000,
  "huggingfaceModelId": "mistralai/Mistral-7B-Instruct-v0.2"
}
```

### 5.3 Advanced Configuration

#### 5.3.1 Running Behind a Proxy

To run AILinux behind a reverse proxy (like Nginx or Apache):

1. Set the `FLASK_HOST` and `WS_HOST` to `localhost` or `127.0.0.1`
2. Configure your proxy to forward requests to the appropriate ports
3. If using SSL termination at the proxy, set `WS_USE_SSL=False`

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name ailinux.example.com;

    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://localhost:8082;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### 5.3.2 Using Custom Models

To use a custom model with the Hugging Face integration:

1. Set `HUGGINGFACE_MODEL_ID` to your model's ID
2. Ensure the model is compatible with text generation tasks
3. Adjust memory settings if needed for larger models

#### 5.3.3 Security Hardening

For production deployments:

1. Set `FLASK_DEBUG=False`
2. Generate and set a strong `WEBSOCKET_API_KEY`
3. Configure SSL with proper certificates
4. Restrict access using firewall rules
5. Run server components with least privilege

---

## 6. User Guide

### 6.1 Getting Started

#### 6.1.1 Launching the Application

1. Ensure the server components are running
2. Start the Electron client application
3. Configure connection settings to point to your server
4. Click "Connect" to establish a connection

#### 6.1.2 User Interface Overview

The AILinux client interface is divided into several panels:

- **Left Side**:
  - Connection Panel: Server URLs and connection status
  - Model Selection: Choose which AI model to use
  - Log Input: Text area and file upload options

- **Right Side**:
  - Analysis Results: Displays the AI-generated analysis
  - Status Indicators: Shows processing status and timing

- **Top**:
  - Header: Application title and version
  - Settings: Access to application preferences

- **Bottom**:
  - Footer: Status information and attribution

### 6.2 Analyzing Logs

#### 6.2.1 Submitting Logs

There are two ways to submit logs for analysis:

**Text Input**:
1. Paste log content into the text area
2. Select the desired AI model
3. Add any custom instructions (optional)
4. Click "Analyze Log"

**File Upload**:
1. Click "Browse..." to select a log file
2. The file content will be loaded into the text area
3. Select the desired AI model
4. Click "Analyze Log"

#### 6.2.2 Viewing Results

Once analysis is complete, the results will appear in the Analysis Results panel:

- The analysis includes a summary of the log
- Error identification and potential causes
- Suggested solutions or next steps
- The results are formatted with Markdown for readability

#### 6.2.3 Understanding Analysis Output

The AI analysis typically includes:

1. **Summary Section**: Overview of what the log contains
2. **Issues Identified**: List of errors, warnings, or problems
3. **Root Cause Analysis**: Potential causes of the issues
4. **Recommendations**: Suggested actions to resolve problems
5. **Additional Context**: Related information that might be useful

### 6.3 Managing Settings

#### 6.3.1 Accessing Settings

Click the settings icon (gear) in the top right corner to open the settings modal.

#### 6.3.2 Available Settings

- **Theme**: Choose between light, dark, or system theme
- **Default Model**: Set the default AI model
- **Hugging Face Model ID**: Configure the Hugging Face model
- **Maximum Log Size**: Set the maximum size for log analysis

#### 6.3.3 Saving Settings

Click "Save Changes" to apply and save the settings both locally and on the server (if connected).

### 6.4 Advanced Usage

#### 6.4.1 Custom Instructions

Use the "Custom Instructions" field to give specific guidance to the AI model:

- "Focus on network-related issues"
- "Identify security vulnerabilities"
- "Analyze performance bottlenecks"
- "Check for configuration errors"

#### 6.4.2 Model Selection

Choose the appropriate model based on your needs:

- **GPT4All**: Good for privacy, works offline, but slower
- **OpenAI**: Excellent analysis quality, requires API key and internet
- **Gemini**: Google's alternative to OpenAI, different strengths
- **Hugging Face**: Customizable model selection, can run locally or via API

#### 6.4.3 Handling Large Logs

For very large logs:

1. Consider preprocessing to extract relevant sections
2. Focus on error messages and surrounding context
3. Split into multiple smaller analyses if needed
4. Use more powerful models for complex logs

---

## 7. API Reference

### 7.1 REST API Endpoints

#### 7.1.1 Log Analysis

**Endpoint**: `/debug`  
**Method**: POST  
**Description**: Analyze log data using AI models

**Request Body**:
```json
{
  "log": "string (required) - Log text to analyze",
  "model": "string (optional) - Model name to use",
  "instruction": "string (optional) - Custom instruction"
}
```

**Response**:
```json
{
  "analysis": "string - Analysis results",
  "processing_time": "number - Processing time in seconds",
  "model": "string - Model used for analysis"
}
```

**Error Responses**:
- 400: Invalid request (missing log text)
- 500: Server error during processing

#### 7.1.2 Models Information

**Endpoint**: `/models`  
**Method**: GET  
**Description**: Get information about available AI models

**Response**:
```json
{
  "models": [
    {
      "name": "string - Model name",
      "available": "boolean - Whether model is available",
      "type": "string - Local or API",
      "file": "string (optional) - Model file path",
      "model": "string (optional) - Model identifier",
      "error": "string (optional) - Error message if unavailable"
    }
  ]
}
```

#### 7.1.3 Server Logs

**Endpoint**: `/logs`  
**Method**: GET  
**Description**: Get server logs

**Query Parameters**:
- `limit`: Integer (optional) - Maximum number of log lines to return

**Response**:
```json
{
  "logs": [
    "string - Log line",
    "string - Log line",
    ...
  ]
}
```

#### 7.1.4 Settings Management

**Endpoint**: `/settings`  
**Method**: GET  
**Description**: Get current settings

**Response**:
```json
{
  "default_model": "string - Default model name",
  "max_log_size": "number - Maximum log size",
  "theme": "string - UI theme",
  "huggingface_model_id": "string - Hugging Face model ID"
}
```

**Endpoint**: `/settings`  
**Method**: POST  
**Description**: Update settings

**Request Body**:
```json
{
  "default_model": "string (optional) - Default model name",
  "max_log_size": "number (optional) - Maximum log size",
  "theme": "string (optional) - UI theme",
  "huggingface_model_id": "string (optional) - Hugging Face model ID"
}
```

**Response**:
```json
{
  "status": "string - Success status",
  "message": "string - Confirmation message"
}
```

#### 7.1.5 Health Check

**Endpoint**: `/health`  
**Method**: GET  
**Description**: Server health check

**Response**:
```json
{
  "status": "string - Server status",
  "environment": "string - Deployment environment",
  "version": "string - Server version",
  "server_time": "number - Server timestamp"
}
```

### 7.2 WebSocket API

#### 7.2.1 Connection and Authentication

**Message Type**: `authentication`  
**Direction**: Client → Server  
**Description**: Authenticate with the server

**Message Format**:
```json
{
  "type": "authentication",
  "auth_key": "string (optional) - API key if required",
  "client_type": "string - Client type identifier",
  "user_agent": "string - Client user agent",
  "version": "string - Client version"
}
```

**Response**:
```json
{
  "type": "authentication",
  "status": "string - Success or failure",
  "client_id": "string - Assigned client ID if successful",
  "message": "string - Status message"
}
```

#### 7.2.2 Log Analysis

**Message Type**: `analyze_log`  
**Direction**: Client → Server  
**Description**: Request log analysis

**Message Format**:
```json
{
  "type": "analyze_log",
  "log": "string - Log text to analyze",
  "model": "string - Model to use",
  "instruction": "string (optional) - Custom instruction"
}
```

**Response Sequence**:

1. Request acknowledgment:
```json
{
  "type": "request_received",
  "request_id": "string - Unique request identifier",
  "message": "string - Acknowledgment message"
}
```

2. Status updates (multiple, optional):
```json
{
  "type": "analysis_status",
  "request_id": "string - Request identifier",
  "status": "string - Current status"
}
```

3. Final result:
```json
{
  "type": "analysis_result",
  "request_id": "string - Request identifier",
  "analysis": "string - Analysis results",
  "processing_time": "number - Processing time in seconds",
  "model": "string - Model used"
}
```

#### 7.2.3 Model Information

**Message Type**: `get_models`  
**Direction**: Client → Server  
**Description**: Request available models

**Message Format**:
```json
{
  "type": "get_models"
}
```

**Response**:
```json
{
  "type": "models_info",
  "models": [
    {
      "name": "string - Model name",
      "available": "boolean - Whether model is available",
      "type": "string - Local or API",
      "file": "string (optional) - Model file path",
      "model": "string (optional) - Model identifier",
      "error": "string (optional) - Error message if unavailable"
    }
  ]
}
```

#### 7.2.4 Connection Maintenance

**Message Type**: `ping`  
**Direction**: Client → Server  
**Description**: Connection testing

**Message Format**:
```json
{
  "type": "ping",
  "timestamp": "number - Client timestamp"
}
```

**Response**:
```json
{
  "type": "pong",
  "timestamp": "number - Server timestamp"
}
```

#### 7.2.5 Error Handling

**Message Type**: `error`  
**Direction**: Server → Client  
**Description**: Error information

**Message Format**:
```json
{
  "type": "error",
  "message": "string - Error message",
  "code": "number - Error code",
  "request_id": "string (optional) - Related request ID"
}
```

### 7.3 Data Server API (Partial Implementation)

The Data Server provides endpoints for storing and retrieving data, logs, and analysis results. The implementation is incomplete in the provided code, but includes these core functions:

- Storage of log entries
- Storage of analysis results
- Storage of generic data
- Retrieval of logs with filtering

---

## 8. Developer Guide

### 8.1 Project Structure

The AILinux project follows this structure:

```
ailinux/
├── server/
│   ├── ai_model.py      # AI model integration
│   ├── app.py           # Flask API server
│   ├── data_server.py   # Data collection server
│   ├── websocketserv.py # WebSocket server
│   ├── requirements.txt # Python dependencies
│   └── .env             # Environment configuration
│
├── client/
│   ├── index.html       # Electron client UI
│   ├── main.js          # Electron main process
│   ├── preload.js       # Electron preload script
│   ├── renderer.js      # Electron renderer logic
│   ├── package.json     # Node.js dependencies
│   └── config.json      # Client configuration
│
├── logs/                # Log directory
├── models/              # Model files directory
└── README.md            # Project README
```

### 8.2 Adding a New AI Model

To add support for a new AI model:

1. **Update the AI Model Module**:
   - Add initialization function in `ai_model.py`:
     ```python
     def initialize_new_model():
         """Initialize the new AI model.
         
         Returns:
             New model instance or None if initialization fails
         """
         try:
             # Model-specific initialization
             return model_instance
         except Exception as e:
             logger.error(f"Error initializing new model: {str(e)}")
             return None
     ```

2. **Add response function**:
   ```python
   def new_model_response(prompt: str) -> str:
       """Get a response from the new model.
       
       Args:
           prompt: The prompt to send to the model
           
       Returns:
           Model response as a string
       """
       model = initialize_new_model()
       if not model:
           raise ModelNotInitializedError("New model could not be initialized")
       
       try:
           # Model-specific implementation
           response = model.generate(prompt)
           return response
       except Exception as e:
           logger.exception(f"Error with new model: {str(e)}")
           raise
   ```

3. **Update get_model function**:
   ```python
   def get_model(model_name: str):
       # Existing code...
       
       if model_name == "new_model":
           return initialize_new_model()
       elif model_name == "gpt4all":
           # Existing code...
   ```

4. **Update get_available_models function**:
   ```python
   def get_available_models():
       models = []
       
       # Existing models...
       
       # New model
       models.append({
           "name": "new_model",
           "available": True,  # Or check availability
           "type": "local",    # Or "api"
           "model": "new_model_identifier"
       })
       
       return models
   ```

5. **Update the analyze_log function**:
   ```python
   def analyze_log(log_text: str, model_name: str = DEFAULT_MODEL, instruction: Optional[str] = None) -> str:
       # Existing code...
       
       try:
           if model_name == "new_model":
               response = new_model_response(prompt)
           elif model_name == "gpt4all":
               # Existing code...
   ```

6. **Update environment variables in `.env`**:
   ```
   NEW_MODEL_PATH=/path/to/model
   NEW_MODEL_API_KEY=your_api_key_if_needed
   ```

### 8.3 Extending the Client UI

To add new features to the Electron client UI:

1. **Add new HTML elements** to `index.html`
2. **Add new JavaScript functions** to handle the feature
3. **Update the event handlers** to connect UI elements to functionality
4. **Update the state management** to store new feature data

Example - Adding a "Save Analysis" feature:

```html
<!-- Add button to the UI -->
<button id="save-analysis-btn" class="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors">Save Analysis</button>
```

```javascript
// Add function to save analysis
async function saveAnalysis() {
    if (!elements.resultContent.textContent) {
        showToast('No analysis to save', 'warning');
        return;
    }
    
    // Create filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `analysis_${timestamp}.md`;
    
    // Get content
    const content = elements.resultContent.innerHTML;
    
    try {
        // Use Electron's dialog to save file
        const { dialog } = require('electron').remote;
        const path = await dialog.showSaveDialog({
            title: 'Save Analysis',
            defaultPath: filename,
            filters: [
                { name: 'Markdown', extensions: ['md'] },
                { name: 'Text', extensions: ['txt'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });
        
        if (path.filePath) {
            // Use fs to write file
            const fs = require('fs');
            fs.writeFileSync(path.filePath, content);
            showToast('Analysis saved successfully', 'success');
        }
    } catch (error) {
        console.error('Failed to save analysis:', error);
        showToast('Failed to save analysis', 'error');
    }
}

// Add event listener
elements.saveAnalysisBtn = document.getElementById('save-analysis-btn');
elements.saveAnalysisBtn.addEventListener('click', saveAnalysis);
```

### 8.4 Adding Custom Prompts

To add support for custom analysis prompts:

1. **Update the create_prompt function** in `ai_model.py`:

```python
def create_prompt(log_text: str, instruction: Optional[str] = None, template: Optional[str] = None) -> str:
    """Create a standardized prompt for log analysis.
    
    Args:
        log_text: The log text to analyze
        instruction: Optional specific instruction to override default
        template: Optional prompt template to use
        
    Returns:
        Formatted prompt string
    """
    default_instruction = """Analyze the following log and provide insights:
1. Summarize what the log is showing
2. Identify any errors or warnings
3. Suggest potential solutions if problems are found
"""
    
    instruction = instruction or default_instruction
    
    if template:
        # Use the provided template, replacing placeholders
        return template.replace("{instruction}", instruction).replace("{log_text}", log_text)
    
    # Default template
    return f"""{instruction}

LOG:
{log_text}

ANALYSIS:
"""
```

2. **Add API endpoint** to `app.py` for managing templates:

```python
@app.route('/templates', methods=['GET'])
def get_templates():
    """Get available prompt templates.
    
    Returns:
        JSON response with templates
    """
    templates_file = os.path.join(os.path.dirname(__file__), 'templates.json')
    
    try:
        if os.path.exists(templates_file):
            with open(templates_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            return jsonify({"templates": templates})
        else:
            # Return default templates
            default_templates = [
                {
                    "id": "default",
                    "name": "Default Analysis",
                    "template": "{instruction}\n\nLOG:\n{log_text}\n\nANALYSIS:"
                },
                {
                    "id": "security",
                    "name": "Security Analysis",
                    "template": "Analyze the following log for security issues only:\n\nLOG:\n{log_text}\n\nSECURITY ANALYSIS:"
                },
                {
                    "id": "performance",
                    "name": "Performance Analysis",
                    "template": "Analyze the following log for performance issues only:\n\nLOG:\n{log_text}\n\nPERFORMANCE ANALYSIS:"
                }
            ]
            return jsonify({"templates": default_templates})
    except Exception as e:
        logger.exception(f"Error getting templates: {str(e)}")
        return jsonify({"error": str(e)}), 500
```

3. **Update the client** to support template selection:

```html
<!-- Add template selector to UI -->
<div class="mb-4">
    <label class="block text-sm font-medium mb-1" for="template-select">Analysis Template</label>
    <select id="template-select" class="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600">
        <option value="default">Default Analysis</option>
        <option value="security">Security Analysis</option>
        <option value="performance">Performance Analysis</option>
    </select>
</div>
```

```javascript
// Update analyze log function
async function analyzeLog() {
    const logText = elements.logInput.value.trim();
    if (!logText) {
        showToast('Please enter log text or upload a file', 'warning');
        return;
    }
    
    const modelName = elements.modelSelect.value;
    const instruction = elements.customInstruction.value.trim() || null;
    const templateId = elements.templateSelect.value;
    
    showAnalysisLoader();
    
    try {
        if (state.wsClient && state.wsClient.connected) {
            // Use WebSocket for real-time updates
            state.wsClient.analyzeLog(logText, modelName, instruction, templateId);
        } else if (state.apiClient) {
            // Fall back to REST API
            const result = await state.apiClient.analyzeLog(logText, modelName, instruction, templateId);
            showAnalysisResults(result.model, result.analysis, result.processing_time);
        } else {
            throw new Error('Not connected to any server');
        }
    } catch (error) {
        console.error('Analysis error:', error);
        showToast(`Analysis failed: ${error.message}`, 'error');
        elements.analysisStatus.textContent = 'Analysis failed';
        elements.analysisLoader.classList.add('hidden');
        elements.analysisPlaceholder.classList.remove('hidden');
    }
}
```

### 8.5 Performance Optimization

To improve the performance of AILinux:

1. **Implement model caching**:
   ```python
   # Add to ai_model.py
   _model_cache = {}
   
   def get_model_with_cache(model_name: str, max_age: int = 3600):
       """Get model with caching.
       
       Args:
           model_name: Name of the model
           max_age: Maximum cache age in seconds
           
       Returns:
           Model instance
       """
       current_time = time.time()
       
       # Check if model is in cache and not expired
       if model_name in _model_cache:
           cache_time, model = _model_cache[model_name]
           if current_time - cache_time < max_age:
               return model
       
       # Get new model instance
       model = get_model(model_name)
       
       # Cache the model
       _model_cache[model_name] = (current_time, model)
       
       return model
   ```

2. **Implement request pooling**:
   ```python
   # Add to app.py
   from concurrent.futures import ThreadPoolExecutor
   
   # Create thread pool
   executor = ThreadPoolExecutor(max_workers=4)
   
   @app.route('/debug', methods=['POST'])
   def debug():
       # Existing code...
       
       # Submit to thread pool instead of blocking
       future = executor.submit(
           analyze_log, 
           log_text, 
           model_name, 
           instruction
       )
       
       try:
           # Wait for result with timeout
           response = future.result(timeout=60)
           
           # Rest of existing code...
       except TimeoutError:
           return jsonify({
               "error": "Analysis timed out",
               "message": "The analysis took too long to complete"
           }), 504
   ```

3. **Optimize WebSocket message handling**:
   ```python
   # Use a message queue for WebSocket processing
   import queue
   
   # Create message queue
   message_queue = queue.Queue()
   
   # Add worker thread
   def message_worker():
       while True:
           try:
               # Get message from queue
               websocket, client_id, message_data = message_queue.get()
               
               # Process message
               asyncio.run(handle_message(websocket, client_id, message_data))
           except Exception as e:
               logger.exception(f"Error in message worker: {str(e)}")
           finally:
               message_queue.task_done()
   
   # Start worker threads
   for _ in range(4):
       threading.Thread(target=message_worker, daemon=True).start()
   
   # Modify connection handler
   async def connection_handler(websocket, path):
       # Existing authentication code...
       
       async for message in websocket:
           # Rate limiting code...
           
           try:
               message_data = json.loads(message)
               
               # Put message in queue instead of processing directly
               message_queue.put((websocket, client_id, message_data))
           except json.JSONDecodeError:
               # Error handling...
   ```

---

## 9. Troubleshooting Guide

### 9.1 Server Issues

#### 9.1.1 Server Won't Start

**Symptoms**:
- Error message when starting a server component
- Server exits immediately after starting

**Possible Causes and Solutions**:

1. **Port already in use**:
   ```
   Error: [Errno 98] Address already in use
   ```
   
   **Solution**:
   - Check if another process is using the port:
     ```bash
     lsof -i :8081  # Replace with your port
     ```
   - Change the port in `.env` file
   - Terminate the other process if appropriate

2. **Missing dependencies**:
   ```
   ImportError: No module named 'flask'
   ```
   
   **Solution**:
   - Ensure virtual environment is activated
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```

3. **Environment configuration issue**:
   ```
   FileNotFoundError: [Errno 2] No such file or directory: '.env'
   ```
   
   **Solution**:
   - Create `.env` file with required configuration
   - Ensure the file is in the correct directory

4. **Permission issues**:
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   
   **Solution**:
   - Check directory and file permissions
   - Run with appropriate privileges for port binding (if using ports below 1024)

#### 9.1.2 Model Loading Failures

**Symptoms**:
- Error messages about model initialization
- Models shown as unavailable in `/models` endpoint

**Possible Causes and Solutions**:

1. **Missing model files**:
   ```
   Model file not found at: ./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf
   ```
   
   **Solution**:
   - Download the required model files
   - Update `LLAMA_MODEL_PATH` in `.env` to point to the correct file

2. **Insufficient memory**:
   ```
   RuntimeError: CUDA out of memory
   ```
   
   **Solution**:
   - Use a smaller model
   - Reduce batch size or model parameters
   - Run on a machine with more memory

3. **Missing API keys**:
   ```
   Warning: No OpenAI API key found in environment
   ```
   
   **Solution**:
   - Add the required API keys to `.env` file
   - Verify API key validity

4. **GPU issues**:
   ```
   CUDA error: no kernel image is available for execution on the device
   ```
   
   **Solution**:
   - Check GPU compatibility
   - Update GPU drivers
   - Force CPU mode if needed:
     ```python
     os.environ["CUDA_VISIBLE_DEVICES"] = ""
     ```

### 9.2 Client Issues

#### 9.2.1 Connection Problems

**Symptoms**:
- Unable to connect to server
- "Disconnected" status remains after clicking Connect

**Possible Causes and Solutions**:

1. **Server not running**:
   ```
   Error: Failed to fetch
   ```
   
   **Solution**:
   - Verify server components are running
   - Check server logs for errors

2. **Incorrect URLs**:
   ```
   Error: Connection failed: Invalid URL
   ```
   
   **Solution**:
   - Check server URLs in the connection panel
   - Ensure protocol is correct (http:// or ws://)

3. **Network/Firewall issues**:
   ```
   Error: Connection timed out
   ```
   
   **Solution**:
   - Check network connectivity
   - Verify firewall settings allow connections
   - Try connecting to localhost if on same machine

4. **CORS issues**:
   ```
   Access to fetch at 'http://server:8081' from origin 'electron://app' has been blocked by CORS policy
   ```
   
   **Solution**:
   - Ensure CORS is properly configured on the server
   - Check that Flask-CORS is installed and configured

#### 9.2.2 Analysis Problems

**Symptoms**:
- Analysis fails or returns errors
- Unexpected analysis results

**Possible Causes and Solutions**:

1. **Log size too large**:
   ```
   Error: Log size exceeds maximum (120000 > 100000)
   ```
   
   **Solution**:
   - Reduce log size by focusing on relevant sections
   - Increase maximum log size in settings

2. **Model errors**:
   ```
   Error: Analysis failed: Model not initialized
   ```
   
   **Solution**:
   - Check model availability in server
   - Select a different model
   - Review server logs for model-specific errors

3. **Timeout issues**:
   ```
   Error: Analysis timed out after 60 seconds
   ```
   
   **Solution**:
   - Try a faster model (GPT4All can be slow on large logs)
   - Reduce log size
   - Increase server timeout settings

4. **Rendering issues**:
   ```
   Error: Failed to render analysis
   ```
   
   **Solution**:
   - Check if analysis content is valid Markdown
   - Ensure client libraries (marked.js, highlight.js) are loaded

### 9.3 Reading Logs

The server components write logs to several files:

- **Flask API**: `backend.log`
- **WebSocket Server**: `websocket_server.log`
- **AI Model Module**: `ai_model.log`
- **Data Server**: `data_server.log`

When troubleshooting issues, check these logs for error messages and warnings.

**Example log analysis**:

1. **Identifying the issue**:
   ```
   2024-03-01 12:34:56 - ERROR - AIModel - Error initializing GPT4All: Model file not found at: ./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf
   ```

2. **Finding related messages**:
   ```
   2024-03-01 12:34:55 - INFO - AIModel - Loading GPT4All model from: ./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf
   2024-03-01 12:34:56 - WARNING - AIModel - Model file not found at: ./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf
   2024-03-01 12:34:56 - INFO - AIModel - Checking if model exists in directory: ./models
   ```

3. **Resolving based on logs**:
   The issue is that the model file is missing. Download the file to the correct location.

### 9.4 Common Error Messages

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `No module named 'flask'` | Missing dependency | Install requirements with pip |
| `Model file not found at: ./models/...` | Missing model file | Download model file to specified path |
| `API key not found in environment` | Missing API configuration | Add API key to `.env` file |
| `Address already in use` | Port conflict | Change port or stop conflicting process |
| `SSL error` | SSL configuration issue | Check certificate and key files |
| `Connection refused` | Server not running or wrong URL | Verify server is running and URL is correct |
| `Unauthorized` | Missing or invalid API key | Provide correct API key |
| `Rate limit reached` | Too many requests | Slow down request rate |
| `Message too large` | Log size exceeds limit | Reduce log size or increase limit |

---

## 10. Security Considerations

### 10.1 API Authentication

The WebSocket server supports API key authentication, which should be enabled in production environments:

1. **Generate a secure API key**:
   ```bash
   openssl rand -hex 32
   ```

2. **Add to `.env` file**:
   ```
   WEBSOCKET_API_KEY=your_generated_key_here
   ```

3. **Configure the client to use the key**:
   Update the WebSocket client to include the key in authentication:
   ```javascript
   state.wsClient.send({
       type: 'authentication',
       auth_key: 'your_generated_key_here',
       client_type: 'electron',
       user_agent: navigator.userAgent,
       version: '1.0.0'
   });
   ```

4. **Consider implementing authentication for the REST API**:
   The Flask API currently doesn't have authentication. Add a middleware:
   ```python
   @app.before_request
   def authenticate():
       if request.endpoint != 'health':  # Skip auth for health check
           api_key = request.headers.get('X-API-Key')
           if api_key != os.getenv("API_KEY"):
               return jsonify({"error": "Unauthorized"}), 401
   ```

### 10.2 SSL/TLS Configuration

For production environments, enable SSL/TLS:

1. **Generate certificates**:
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```

2. **Configure in `.env`**:
   ```
   WS_USE_SSL=True
   WS_SSL_CERT=/path/to/cert.pem
   WS_SSL_KEY=/path/to/key.pem
   ```

3. **Update client URLs** to use secure protocols:
   - `https://` instead of `http://`
   - `wss://` instead of `ws://`

### 10.3 Data Protection

When processing sensitive logs:

1. **Use local models** instead of cloud APIs to keep data on-premises

2. **Implement data retention policies**:
   - Add automatic cleanup of old logs
   - Provide options to purge analysis history

3. **Sanitize sensitive information**:
   ```python
   def sanitize_log(log_text: str) -> str:
       """Remove sensitive information from logs.
       
       Args:
           log_text: Original log text
           
       Returns:
           Sanitized log text
       """
       # Remove IP addresses
       log_text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]', log_text)
       
       # Remove email addresses
       log_text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', log_text)
       
       # Remove API keys (common formats)
       log_text = re.sub(r'sk-[A-Za-z0-9]{48}', '[REDACTED_API_KEY]', log_text)
       log_text = re.sub(r'api_key=\w+', 'api_key=[REDACTED]', log_text)
       
       return log_text
   ```

4. **Encrypt sensitive data in storage**:
   ```python
   from cryptography.fernet import Fernet
   
   def encrypt_data(data: str, key: bytes) -> str:
       """Encrypt sensitive data.
       
       Args:
           data: Data to encrypt
           key: Encryption key
           
       Returns:
           Encrypted data as string
       """
       f = Fernet(key)
       return f.encrypt(data.encode()).decode()
   
   def decrypt_data(encrypted_data: str, key: bytes) -> str:
       """Decrypt sensitive data.
       
       Args:
           encrypted_data: Encrypted data
           key: Encryption key
           
       Returns:
           Decrypted data
       """
       f = Fernet(key)
       return f.decrypt(encrypted_data.encode()).decode()
   ```

### 10.4 Input Validation

Implement strict input validation to prevent injection attacks:

```python
def validate_log_input(log_text: str, max_size: int = 100000) -> bool:
    """Validate log text input.
    
    Args:
        log_text: Log text to validate
        max_size: Maximum allowed size
        
    Returns:
        True if valid, False otherwise
    """
    # Check size
    if len(log_text) > max_size:
        return False
    
    # Check for potentially malicious patterns
    malicious_patterns = [
        r'<script>',
        r'exec\(',
        r'eval\(',
        r'system\(',
        r'import os;'
    ]
    
    for pattern in malicious_patterns:
        if re.search(pattern, log_text, re.IGNORECASE):
            return False
    
    return True
```

### 10.5 Rate Limiting

Implement rate limiting to prevent abuse:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/debug', methods=['POST'])
@limiter.limit("10 per minute")
def debug():
    # Existing code...
```

---

## 11. Performance Optimization

### 11.1 Model Caching

Implement model caching to avoid repeatedly loading models:

```python
class ModelCache:
    """Cache for AI models to improve performance."""
    
    def __init__(self, max_size=5, ttl=3600):
        """Initialize the model cache.
        
        Args:
            max_size: Maximum number of models to cache
            ttl: Time-to-live in seconds
        """
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key):
        """Get a model from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Model or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        timestamp, model = self.cache[key]
        
        # Check if expired
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        return model
    
    def put(self, key, model):
        """Add a model to the cache.
        
        Args:
            key: Cache key
            model: Model to cache
        """
        # Evict oldest entry if full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
            del self.cache[oldest_key]
        
        self.cache[key] = (time.time(), model)
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()

# Create global cache
model_cache = ModelCache()

def get_model_cached(model_name: str):
    """Get a model with caching.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Model instance
    """
    # Try to get from cache first
    model = model_cache.get(model_name)
    if model:
        return model
    
    # Initialize model
    model = get_model(model_name)
    
    # Cache for future use
    if model:
        model_cache.put(model_name, model)
    
    return model
```

### 11.2 Request Pooling

Implement a thread pool for handling multiple requests:

```python
from concurrent.futures import ThreadPoolExecutor

# Create a thread pool
thread_pool = ThreadPoolExecutor(max_workers=4)

@app.route('/debug', methods=['POST'])
def debug():
    # Existing code...
    
    # Submit to thread pool
    future = thread_pool.submit(analyze_log, log_text, model_name, instruction)
    
    try:
        # Wait for result with timeout
        response = future.result(timeout=60)
        
        # Save the analysis to a history file for reference
        save_analysis_history(log_text, response, model_name)
        
        # Calculate and log processing time
        elapsed_time = time.time() - start_time
        logger.info(f"Log analysis completed in {elapsed_time:.2f} seconds")

        # Return analysis response
        return jsonify({
            "analysis": response,
            "processing_time": elapsed_time,
            "model": model_name
        })
    except TimeoutError:
        logger.error("Analysis timed out")
        return jsonify({
            "error": "Analysis timed out",
            "message": "The analysis took too long to complete"
        }), 504
```

### 11.3 Database Optimization

For the Data Server, implement database optimizations:

```python
class DatabaseOptimizer:
    """Optimize database performance."""
    
    def __init__(self, db_path):
        """Initialize the optimizer.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
    
    def optimize(self):
        """Run database optimizations."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Run VACUUM to rebuild the database
            cursor.execute("VACUUM")
            
            # Analyze for better query planning
            cursor.execute("ANALYZE")
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            if result[0] != "ok":
                logger.warning(f"Database integrity check failed: {result[0]}")
            
            # Set journal mode to WAL for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            
            conn.commit()
            logger.info("Database optimization completed")
        except sqlite3.Error as e:
            logger.error(f"Database optimization error: {e}")
        finally:
            conn.close()
    
    def create_indices(self):
        """Create indices for better query performance."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Create indices
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source)",
                "CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)",
                "CREATE INDEX IF NOT EXISTS idx_analysis_timestamp ON analysis_results(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_analysis_model ON analysis_results(model)",
                "CREATE INDEX IF NOT EXISTS idx_data_timestamp ON collected_data(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_data_type ON collected_data(data_type)"
            ]
            
            for index in indices:
                cursor.execute(index)
            
            conn.commit()
            logger.info("Database indices created")
        except sqlite3.Error as e:
            logger.error(f"Error creating indices: {e}")
        finally:
            conn.close()
```

### 11.4 Client-Side Optimization

Optimize the Electron client:

```javascript
// Implement virtual scrolling for large results
function createVirtualScroller(container, itemHeight, renderItem) {
    const state = {
        items: [],
        visibleItems: [],
        startIndex: 0,
        endIndex: 0,
        scrollTop: 0,
        viewportHeight: 0
    };
    
    // Update visible items based on scroll position
    function updateVisibleItems() {
        const scrollTop = container.scrollTop;
        const viewportHeight = container.clientHeight;
        
        const startIndex = Math.floor(scrollTop / itemHeight);
        const numVisible = Math.ceil(viewportHeight / itemHeight) + 1;
        const endIndex = Math.min(startIndex + numVisible, state.items.length);
        
        // Only update DOM if necessary
        if (startIndex !== state.startIndex || endIndex !== state.endIndex) {
            state.startIndex = startIndex;
            state.endIndex = endIndex;
            
            // Clear container
            container.innerHTML = '';
            
            // Set container height
            const totalHeight = state.items.length * itemHeight;
            container.style.height = `${totalHeight}px`;
            
            // Create items in view
            for (let i = startIndex; i < endIndex; i++) {
                const item = state.items[i];
                const itemEl = renderItem(item, i);
                itemEl.style.position = 'absolute';
                itemEl.style.top = `${i * itemHeight}px`;
                itemEl.style.width = '100%';
                container.appendChild(itemEl);
            }
        }
    }
    
    // Add scroll listener
    container.addEventListener('scroll', updateVisibleItems);
    
    // Resize observer
    const resizeObserver = new ResizeObserver(() => {
        state.viewportHeight = container.clientHeight;
        updateVisibleItems();
    });
    resizeObserver.observe(container);
    
    // Return controller
    return {
        setItems(items) {
            state.items = items;
            updateVisibleItems();
        },
        refresh() {
            updateVisibleItems();
        },
        destroy() {
            container.removeEventListener('scroll', updateVisibleItems);
            resizeObserver.disconnect();
        }
    };
}

// Use for analysis results
const resultScroller = createVirtualScroller(
    document.getElementById('analysis-results'),
    30, // item height in pixels
    (item, index) => {
        const div = document.createElement('div');
        div.textContent = item;
        return div;
    }
);

// Use for long logs
elements.logInput.addEventListener('input', debounce(function() {
    // Only render visible lines
    const lines = this.value.split('\n');
    if (lines.length > 1000) {
        // Use virtual scrolling for very large logs
        this.style.height = `${Math.min(500, lines.length * 20)}px`;
    }
}, 300));

// Debounce function to avoid excessive updates
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}
```

### 11.5 WebSocket Optimization

Improve WebSocket performance:

```python
# Add message compression
import zlib

def compress_message(message: str) -> bytes:
    """Compress a WebSocket message.
    
    Args:
        message: Message string
        
    Returns:
        Compressed bytes
    """
    return zlib.compress(message.encode())

def decompress_message(data: bytes) -> str:
    """Decompress a WebSocket message.
    
    Args:
        data: Compressed bytes
        
    Returns:
        Decompressed string
    """
    return zlib.decompress(data).decode()

# Use for large messages
async def send_compressed(websocket, message_data):
    """Send a compressed message over WebSocket.
    
    Args:
        websocket: WebSocket connection
        message_data: Message data
    """
    json_data = json.dumps(message_data)
    
    # Only compress if message is large enough
    if len(json_data) > 1024:
        # Flag message as compressed
        header = {"compressed": True}
        compressed_data = compress_message(json_data)
        
        # Send header as JSON and data as binary
        await websocket.send(json.dumps(header))
        await websocket.send(compressed_data)
    else:
        # Send normally
        await websocket.send(json_data)
```

---

## 12. Appendix

### 12.1 Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_HOST` | Host for the Flask API server | `0.0.0.0` | No |
| `FLASK_PORT` | Port for the Flask API server | `8081` | No |
| `FLASK_DEBUG` | Enable Flask debug mode | `False` | No |
| `ENVIRONMENT` | Environment type | `development` | No |
| `WS_HOST` | Host for the WebSocket server | `0.0.0.0` | No |
| `WS_PORT` | Port for the WebSocket server | `8082` | No |
| `WS_USE_SSL` | Enable SSL for WebSocket | `False` | No |
| `WS_SSL_CERT` | Path to SSL certificate | `""` | If `WS_USE_SSL=True` |
| `WS_SSL_KEY` | Path to SSL key | `""` | If `WS_USE_SSL=True` |
| `WEBSOCKET_API_KEY` | API key for WebSocket authentication | `""` | No |
| `WS_RATE_LIMIT` | Rate limit for WebSocket messages (seconds) | `1.0` | No |
| `WS_MAX_MESSAGE_SIZE` | Maximum WebSocket message size (bytes) | `1048576` | No |
| `DEFAULT_MODEL` | Default model to use | `gpt4all` | No |
| `OPENAI_API_KEY` | OpenAI API key | `""` | For OpenAI model |
| `GEMINI_API_KEY` | Google Gemini API key | `""` | For Gemini model |
| `HUGGINGFACE_API_KEY` | Hugging Face API key | `""` | For some Hugging Face models |
| `LLAMA_MODEL_PATH` | Path to the GPT4All model file | `Meta-Llama-3-8B-Instruct.Q4_0.gguf` | For GPT4All model |
| `HUGGINGFACE_MODEL_ID` | Hugging Face model ID | `mistralai/Mistral-7B-Instruct-v0.2` | For Hugging Face model |
| `HUGGINGFACE_CACHE_DIR` | Directory for Hugging Face models | `./models/huggingface` | No |
| `DATA_DIR` | Directory for collected data | `./collected_data` | No |
| `DB_PATH` | Path to SQLite database | `./collected_data/ailinux_data.db` | No |
| `SERVER_HTTP_PORT` | Port for data server HTTP API | `8081` | No |
| `SERVER_WS_PORT` | Port for data server WebSocket | `8082` | No |

### 12.2 API Response Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | Successful analysis |
| 400 | Bad Request | Missing log text |
| 401 | Unauthorized | Invalid API key |
| 413 | Payload Too Large | Log size exceeds limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Model error |
| 504 | Gateway Timeout | Analysis timed out |

### 12.3 WebSocket Error Codes

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Invalid JSON |
| 401 | Unauthorized | Authentication failed |
| 408 | Request Timeout | Authentication timeout |
| 413 | Payload Too Large | Message too large |
| 429 | Too Many Requests | Rate limit reached |
| 500 | Internal Server Error | Processing error |

### 12.4 Dependencies

**Server Dependencies**:
- Flask: Web framework
- Flask-CORS: Cross-origin resource sharing
- websockets: WebSocket server
- python-dotenv: Environment variable loading
- GPT4All: Local model integration
- openai: OpenAI API client
- google-generativeai: Google Gemini API client
- transformers: Hugging Face model framework
- torch: PyTorch for Hugging Face models
- sqlite3: Database integration

**Client Dependencies**:
- Electron: Desktop application framework
- Node.js: JavaScript runtime
- marked: Markdown parsing
- highlight.js: Syntax highlighting
- Tailwind CSS: Styling framework

### 12.5 Glossary

| Term | Definition |
|------|------------|
| API | Application Programming Interface |
| CORS | Cross-Origin Resource Sharing |
| GPT4All | Local implementation of GPT models |
| Hugging Face | Repository and framework for machine learning models |
| LLM | Large Language Model |
| OpenAI | Company providing AI services |
| REST | Representational State Transfer |
| SQLite | Serverless database engine |
| SSL/TLS | Secure Sockets Layer/Transport Layer Security |
| WebSocket | Protocol providing full-duplex communication channels |
| AI | Artificial Intelligence |
| UI | User Interface |

### 12.6 References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Electron Documentation](https://www.electronjs.org/docs)
- [GPT4All Repository](https://github.com/nomic-ai/gpt4all)
- [Hugging Face Documentation](https://huggingface.co/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Google Gemini Documentation](https://ai.google.dev/docs)
- [WebSockets Documentation](https://websockets.readthedocs.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

### 12.7 Contributing Guidelines

We welcome contributions to the AILinux project! Here's how you can help:

1. **Reporting Bugs**:
   - Use the issue tracker
   - Include detailed steps to reproduce
   - Provide log output if possible

2. **Suggesting Features**:
   - Describe the feature in detail
   - Explain the use case
   - Consider implementation complexity

3. **Submitting Code**:
   - Fork the repository
   - Create a feature branch
   - Follow coding style guidelines
   - Write tests for new features
   - Submit a pull request

4. **Coding Style**:
   - Follow PEP 8 for Python code
   - Use descriptive variable names
   - Add docstrings for functions and classes
   - Keep functions small and focused
   - Add type annotations

5. **Testing**:
   - Write unit tests for new features
   - Ensure existing tests pass
   - Test on different platforms if possible

Thank you for contributing to AILinux!
