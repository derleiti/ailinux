import React, { useState, useEffect, useRef } from 'react';

const GPT4AllInterface = () => {
  const [logs, setLogs] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [systemInfo, setSystemInfo] = useState(null);
  const [modelStatus, setModelStatus] = useState('loading');
  const [selectedFile, setSelectedFile] = useState(null);
  const [conversations, setConversations] = useState([]);
  const chatLogRef = useRef(null);

  // Fetch system info and model status on component mount
  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        // Replace with actual API endpoint
        const response = await fetch('http://localhost:8081/system');
        if (response.ok) {
          const data = await response.json();
          setSystemInfo(data);
        }
      } catch (error) {
        console.error('Error fetching system status:', error);
      }
    };

    const checkModelStatus = async () => {
      try {
        // Replace with actual API endpoint
        const response = await fetch('http://localhost:8081/models');
        if (response.ok) {
          const data = await response.json();
          const gpt4all = data.models.find(model => model.name === 'gpt4all');
          setModelStatus(gpt4all?.available ? 'ready' : 'error');
        }
      } catch (error) {
        console.error('Error checking model status:', error);
        setModelStatus('error');
      }
    };

    fetchSystemStatus();
    checkModelStatus();

    // Fetch recent logs
    fetchRecentLogs();
  }, []);

  // Scroll to bottom when conversations change
  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [conversations]);

  const fetchRecentLogs = async () => {
    try {
      // Replace with actual API endpoint
      const response = await fetch('http://localhost:8081/logs?limit=5');
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const handleInputChange = (e) => {
    setInputText(e.target.value);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setInputText(e.target.result);
      };
      reader.readAsText(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setInputText(e.target.result);
      };
      reader.readAsText(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const analyzeLog = async () => {
    if (!inputText.trim()) {
      alert('Please enter log text or upload a log file');
      return;
    }

    setIsAnalyzing(true);
    
    // Add user message to conversation
    const userMessage = {
      role: 'user',
      content: inputText.length > 150 
        ? `${inputText.substring(0, 150)}... [${inputText.length} characters]` 
        : inputText
    };
    
    setConversations([...conversations, userMessage]);

    try {
      // Make API call to backend for log analysis
      const response = await fetch('http://localhost:8081/debug', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          log: inputText,
          model: 'gpt4all',
          instruction: 'Analyze this log file and provide insights about errors or issues.'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Add AI response to conversation
        setConversations([
          ...conversations, 
          userMessage,
          {
            role: 'assistant',
            content: data.analysis,
            metadata: {
              processingTime: data.processing_time,
              model: data.model
            }
          }
        ]);
        
        // Keep input text for reference or clear it based on preference
        // setInputText('');
      } else {
        // Handle error response
        const errorText = await response.text();
        setConversations([
          ...conversations,
          userMessage,
          {
            role: 'assistant',
            content: `Error analyzing log: ${errorText || 'Unknown error'}`,
            error: true
          }
        ]);
      }
    } catch (error) {
      console.error('Error analyzing log:', error);
      setConversations([
        ...conversations,
        userMessage,
        {
          role: 'assistant',
          content: `Error connecting to backend: ${error.message}`,
          error: true
        }
      ]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-6xl mx-auto p-4 gap-4">
      {/* Status Bar */}
      <div className="flex items-center justify-between bg-gray-100 dark:bg-gray-800 rounded-lg p-3 text-sm">
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-2 ${
            modelStatus === 'ready' ? 'bg-green-500' : 
            modelStatus === 'loading' ? 'bg-yellow-500' : 'bg-red-500'
          }`}></div>
          <span>GPT4All: {
            modelStatus === 'ready' ? 'Ready' : 
            modelStatus === 'loading' ? 'Loading...' : 'Error'
          }</span>
        </div>
        {systemInfo && (
          <div className="flex gap-4">
            <span>CPU: {systemInfo.cpu}%</span>
            <span>RAM: {systemInfo.ram}%</span>
          </div>
        )}
      </div>

      {/* Chat/Log Area */}
      <div className="flex-grow border border-gray-300 dark:border-gray-700 rounded-lg overflow-hidden flex flex-col">
        <div 
          ref={chatLogRef}
          className="flex-grow p-4 overflow-y-auto bg-white dark:bg-gray-900"
        >
          {conversations.length === 0 ? (
            <div className="text-center text-gray-500 dark:text-gray-400 py-8">
              <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              <p className="text-lg font-medium mb-1">Welcome to GPT4All Log Analysis</p>
              <p>Paste your log file content or upload a log file to begin analysis</p>
            </div>
          ) : (
            conversations.map((message, index) => (
              <div 
                key={index} 
                className={`max-w-3xl mb-4 ${message.role === 'user' ? 'ml-auto' : 'mr-auto'}`}
              >
                <div className={`rounded-lg p-3 ${
                  message.role === 'user' 
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100' 
                    : message.error 
                      ? 'bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                }`}>
                  {message.content}
                  
                  {message.metadata && (
                    <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                      {message.metadata.processingTime && (
                        <span className="mr-3">
                          Processing time: {message.metadata.processingTime.toFixed(2)}s
                        </span>
                      )}
                      {message.metadata.model && (
                        <span>Model: {message.metadata.model}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {isAnalyzing && (
            <div className="flex items-center justify-center gap-2 text-gray-500 dark:text-gray-400">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse delay-150"></div>
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse delay-300"></div>
              <span className="ml-2">Analyzing with GPT4All...</span>
            </div>
          )}
        </div>
        
        {/* Input Area */}
        <div className="border-t border-gray-300 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800">
          <div 
            className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg mb-4 p-6 text-center cursor-pointer"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => document.getElementById('file-upload').click()}
          >
            <input 
              id="file-upload" 
              type="file"
              accept=".log,.txt,.json"
              className="hidden"
              onChange={handleFileChange}
            />
            <svg className="w-8 h-8 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
            </svg>
            <p className="text-gray-600 dark:text-gray-300">
              {selectedFile ? `Selected: ${selectedFile.name}` : 'Drag & drop log file here or click to browse'}
            </p>
          </div>
          
          <div className="flex flex-col gap-3">
            <textarea 
              className="w-full p-3 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Paste log content here..."
              rows="5"
              value={inputText}
              onChange={handleInputChange}
            ></textarea>
            
            <div className="flex justify-between">
              <div>
                {logs.length > 0 && (
                  <select className="p-2 border border-gray-300 dark:border-gray-700 rounded-lg dark:bg-gray-700 dark:text-white">
                    <option value="">Load recent log...</option>
                    {logs.map((log, index) => (
                      <option key={index} value={index}>Log {index + 1}</option>
                    ))}
                  </select>
                )}
              </div>
              
              <button 
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                onClick={analyzeLog}
                disabled={isAnalyzing || !inputText.trim()}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze with GPT4All'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GPT4AllInterface;
