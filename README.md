# AILinux: AI-Powered Log Analysis System
https://derleiti.de/
AILinux is a comprehensive system for analyzing log files using various AI models. It provides both local and cloud-based analysis options, allowing users to leverage powerful models for debugging, monitoring, and troubleshooting.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

- **Multiple AI Model Support**:
  - Local models: GPT4All, Hugging Face
  - Cloud APIs: OpenAI, Google Gemini
  
- **Real-time Analysis**:
  - WebSocket-based real-time updates
  - Detailed insights with suggested solutions
  
- **Cross-Platform**:
  - Server component works on Linux, macOS, and Windows
  - Electron-based client for desktop environments
  
- **Flexible Configuration**:
  - Environment-based settings
  - Support for custom prompts and instructions
  
- **Security**:
  - SSL/TLS support for secure connections
  - API key authentication
  
- **Performance**:
  - Asynchronous processing for handling multiple requests
  - Connection pooling and rate limiting

## 🏗️ System Architecture

AILinux consists of several components that work together:

```
AILinux
├── Server Components
│   ├── app.py - Flask-based HTTP API
│   ├── websocketserv.py - WebSocket server for real-time updates
│   ├── ai_model.py - AI model integration module
│   └── data_server.py - Data collection and storage module
│
└── Client Components
    └── Electron App - Cross-platform desktop client
```

## 📋 Requirements

### Server Requirements

- Python 3.8+
- Required Python packages (see `requirements.txt`)
- One or more AI models:
  - Local: GPT4All or Hugging Face models
  - API keys for OpenAI or Google Gemini (optional)

### Client Requirements

- Node.js 14+
- Electron 18+
- Internet connection to server

## 🚀 Installation

### Server Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ailinux.git
   cd ailinux/server
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
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

4. Create necessary directories:
   ```bash
   mkdir -p logs models/huggingface
   ```

### Client Installation

1. Navigate to the client directory:
   ```bash
   cd ../client
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## 🔧 Usage

### Running the Server

Start all server components:

```bash
# Start the Flask API server
python app.py

# Start the WebSocket server (in a separate terminal)
python websocketserv.py

# Start the Data Collection server (optional, in a separate terminal)
python data_server.py
```

### Running the Client

```bash
# From the client directory
npm start
```

## 📝 Configuration Options

### Server Configuration

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `FLASK_HOST` | Host for the Flask API server | `0.0.0.0` |
| `FLASK_PORT` | Port for the Flask API server | `8081` |
| `WS_HOST` | Host for the WebSocket server | `0.0.0.0` |
| `WS_PORT` | Port for the WebSocket server | `8082` |
| `FLASK_DEBUG` | Enable/disable Flask debug mode | `False` |
| `DEFAULT_MODEL` | Default AI model to use | `gpt4all` |
| `OPENAI_API_KEY` | OpenAI API key | `""` |
| `GEMINI_API_KEY` | Google Gemini API key | `""` |
| `HUGGINGFACE_API_KEY` | Hugging Face API key | `""` |
| `LLAMA_MODEL_PATH` | Path to the GPT4All model file | `"Meta-Llama-3-8B-Instruct.Q4_0.gguf"` |
| `HUGGINGFACE_MODEL_ID` | Hugging Face model ID | `"mistralai/Mistral-7B-Instruct-v0.2"` |
| `HUGGINGFACE_CACHE_DIR` | Directory for Hugging Face models | `"./models/huggingface"` |
| `WS_USE_SSL` | Enable/disable SSL for WebSocket | `False` |
| `WS_SSL_CERT` | Path to SSL certificate | `""` |
| `WS_SSL_KEY` | Path to SSL key | `""` |
| `WEBSOCKET_API_KEY` | API key for WebSocket authentication | `""` |
| `WS_RATE_LIMIT` | Rate limit for WebSocket messages (seconds) | `1.0` |
| `WS_MAX_MESSAGE_SIZE` | Maximum WebSocket message size (bytes) | `1048576` |

### Client Configuration

Configuration is done through the settings UI in the client application.

## 🔍 Log Analysis Features

AILinux provides comprehensive log analysis capabilities:

1. **Summary Generation** - High-level overview of log content
2. **Error Detection** - Identification of errors and warnings
3. **Root Cause Analysis** - Suggestions for underlying causes
4. **Solution Recommendations** - Possible fixes for identified issues
5. **Pattern Recognition** - Identification of recurring problems

## 🛠️ Troubleshooting

### Common Issues

#### Server Won't Start

- Check if the port is already in use
- Ensure Python and all dependencies are installed
- Verify that the `.env` file exists with correct configurations

#### Model Loading Issues

- Ensure model files are downloaded and in the correct directory
- Check permissions on the model directory
- Verify that you have sufficient RAM for model loading

#### Client Connection Problems

- Verify server is running and accessible
- Check network firewall settings
- Ensure correct URLs are configured in the client

### Logs

Server logs are stored in the following locations:

- Flask API: `./backend.log`
- WebSocket Server: `./websocket_server.log`
- AI Model: `./ai_model.log`
- Data Server: `./data_server.log`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [GPT4All](https://github.com/nomic-ai/gpt4all) for local model support
- [Hugging Face](https://huggingface.co/) for model hosting and APIs
- [OpenAI](https://openai.com/) and [Google Gemini](https://ai.google.dev/) for cloud AI services
- [Flask](https://flask.palletsprojects.com/) and [WebSockets](https://websockets.readthedocs.io/) for server infrastructure
- [Electron](https://www.electronjs.org/) for the desktop client framework

---

<p align="center">
  Made with ❤️ by the AILinux Team
</p>
