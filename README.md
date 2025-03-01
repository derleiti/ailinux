# AILinux: AI-Powered Log Analysis and System Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Electron Version](https://img.shields.io/badge/Electron-18+-green.svg)](https://www.electronjs.org/)

## 🚀 Project Overview

AILinux is a comprehensive, AI-powered system intelligence platform designed to revolutionize log analysis, system monitoring, and intelligent assistance. By leveraging multiple AI models and advanced technologies, AILinux provides deep insights, proactive problem-solving, and seamless cross-platform support.

## 🌟 Key Features

### 🤖 Advanced AI Integration
- Multiple AI Model Support
  - Local Models: GPT4All, Hugging Face
  - Cloud Models: OpenAI, Google Gemini
- Intelligent Log Analysis
- Contextual System Insights
- Adaptive Problem Solving

### 🔍 Log Management
- Real-time Log Processing
- Multi-format Log Support
- Detailed Error Diagnostics
- Predictive Troubleshooting

### 💻 System Intelligence
- Resource Monitoring
- Performance Optimization Suggestions
- Security Threat Detection
- Automated Reporting

### 🌐 Cross-Platform Compatibility
- Desktop Client (Electron)
- Server-Side Processing
- WebSocket Real-Time Communication
- RESTful API Support

## 📋 Prerequisites

### Server Requirements
- Python 3.8+
- Flask
- WebSocket Support
- AI Model Dependencies

### Client Requirements
- Node.js 14+
- Electron 18+
- Modern Web Browser

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/derleiti/ailinux.git
cd ailinux
```

### 2. Server Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Client Setup
```bash
cd client
npm install
```

### 4. Configuration
Create a `.env` file with your configuration:
```
# AI Model Settings
OPENAI_API_KEY=your_openai_key
HUGGINGFACE_API_KEY=your_huggingface_key
DEFAULT_MODEL=gpt4all

# Server Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=8081
```

## 🚀 Running the Application

### Start Backend Services
```bash
# Start Flask API
python backend/app.py

# Start WebSocket Server
python backend/websocket-server.py
```

### Launch Electron Client
```bash
cd client
npm start
```

## 🔒 Security Features
- SSL/TLS Support
- API Key Authentication
- Secure WebSocket Connections
- Log Anonymization

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License
MIT License - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments
- GPT4All
- Hugging Face
- OpenAI
- Google AI
- Electron
- Flask

---

<p align="center">
  Made with ❤️ by the AILinux Team
</p>
