import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('Home');
  const [expandedHelpTopic, setExpandedHelpTopic] = useState(null);
  const [viewingHistory, setViewingHistory] = useState(false);
  const [currentHistoryId, setCurrentHistoryId] = useState(null);
  const messagesEndRef = useRef(null);

  // Sample conversation history data
  const historyData = [
    { 
      id: 1,
      date: 'May 19, 2025', 
      topic: 'Kubernetes Basics', 
      messages: [
        { sender: 'You', text: 'What is Kubernetes?' },
        { sender: 'Assistant', text: 'Kubernetes is an open-source container orchestration platform that automates the deployment, scaling, and management of containerized applications. It was originally developed by Google and is now maintained by the Cloud Native Computing Foundation (CNCF).' },
        { sender: 'You', text: 'What are pods in Kubernetes?' },
        { sender: 'Assistant', text: 'In Kubernetes, pods are the smallest deployable units that can be created, scheduled, and managed. A pod is a logical group of one or more containers that share storage and network resources. Containers within a pod are always co-located and co-scheduled, and run in a shared context on the same node.' }
      ]
    },
    { 
      id: 2,
      date: 'May 18, 2025', 
      topic: 'Docker Containers', 
      messages: [
        { sender: 'You', text: 'What is Docker?' },
        { sender: 'Assistant', text: 'Docker is a platform that enables developers to build, package, and distribute applications within standardized units called containers. Containers bundle an application with all its dependencies, libraries, and configuration files, ensuring it runs the same way across different environments.' }
      ]
    },
    { 
      id: 3,
      date: 'May 17, 2025', 
      topic: 'CI/CD Pipeline Setup', 
      messages: [
        { sender: 'You', text: 'How do I create a CI/CD pipeline?' },
        { sender: 'Assistant', text: 'Creating a CI/CD (Continuous Integration/Continuous Delivery) pipeline involves several steps: 1) Choose a CI/CD tool like Jenkins, GitLab CI, or GitHub Actions, 2) Define your pipeline stages in code, typically including build, test, security scan, and deploy stages, 3) Connect your code repository to trigger builds automatically, 4) Configure deployment targets for your applications.' }
      ]
    },
    { 
      id: 4,
      date: 'May 15, 2025', 
      topic: 'AWS Architecture', 
      messages: [
        { sender: 'You', text: 'What is AWS Lambda?' },
        { sender: 'Assistant', text: 'AWS Lambda is a serverless computing service provided by Amazon Web Services. It allows you to run code without provisioning or managing servers. You simply upload your code, and Lambda takes care of everything required to run and scale your code with high availability. You only pay for the compute time you consume.' }
      ]
    }
  ];

  // Help topics with content
  const helpTopics = [
    {
      title: 'Getting Started with the AI Assistant',
      content: 'The AI Assistant is designed to help you with technical concepts and questions. Simply type your question in the input box and press "Send" to get a response. The assistant is particularly knowledgeable about DevOps, cloud computing, and software development topics.'
    },
    {
      title: 'Available Commands and Functions',
      content: 'You can ask the AI Assistant about technical concepts, request explanations of technologies, get code samples, or ask for help with troubleshooting. The assistant can provide detailed explanations, analogies, and real-world examples to help you understand complex topics.'
    },
    {
      title: 'Understanding AI Responses',
      content: 'The AI Assistant provides responses based on its training data. Responses typically include a formal definition, layman\'s terms explanation, and practical examples. If a response isn\'t clear, you can ask for clarification or request a simpler explanation.'
    },
    {
      title: 'Privacy and Data Usage',
      content: 'Your conversations with the AI Assistant are stored according to your settings preferences. By default, conversations are saved for 30 days to improve the service quality. You can adjust these settings in the Settings tab or delete your conversation history at any time.'
    },
    {
      title: 'Troubleshooting Connection Issues',
      content: 'If you experience connection issues, ensure your internet connection is stable. Check that the API endpoint is correctly configured. If problems persist, try refreshing the page or clearing your browser cache.'
    },
    {
      title: 'API Integration Documentation',
      content: 'The AI Assistant can be integrated with your applications using our API. Detailed API documentation, including endpoints, request formats, and example code, is available on our developer portal.'
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // If we're viewing history, start a new conversation from this point
    if (viewingHistory) {
      setViewingHistory(false);
      setCurrentHistoryId(null);
    }

    const userMessage = { sender: 'You', text: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();
      const botMessage = { sender: 'Assistant', text: data.response };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        sender: 'Assistant', 
        text: 'I apologize, but I encountered an error while processing your request. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // View a conversation from history
  const viewConversation = (historyId) => {
    const conversation = historyData.find(item => item.id === historyId);
    if (conversation) {
      setMessages(conversation.messages);
      setViewingHistory(true);
      setCurrentHistoryId(historyId);
      setActiveTab('Home');
    }
  };

  // Start a new conversation
  const startNewConversation = () => {
    setMessages([]);
    setViewingHistory(false);
    setCurrentHistoryId(null);
    setActiveTab('Home');
  };

  // Toggle help topic expansion
  const toggleHelpTopic = (index) => {
    setExpandedHelpTopic(expandedHelpTopic === index ? null : index);
  };

  // Get current conversation title
  const getCurrentTitle = () => {
    if (viewingHistory && currentHistoryId) {
      const conversation = historyData.find(item => item.id === currentHistoryId);
      return conversation ? `${conversation.topic} (${conversation.date})` : 'AI Assistant';
    }
    return 'AI Assistant';
  };

  // Render appropriate content based on active tab
  const renderContent = () => {
    switch (activeTab) {
      case 'Home':
        return (
          <div className="chat-box">
            {viewingHistory && currentHistoryId && (
              <div className="history-banner">
                <div className="history-title">
                  Viewing: {historyData.find(h => h.id === currentHistoryId)?.topic}
                </div>
                <button 
                  className="history-new-btn"
                  onClick={startNewConversation}
                >
                  Start New Conversation
                </button>
              </div>
            )}
            
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h2>Welcome to AI Assistant</h2>
                <p>Ask me anything and I'll do my best to assist you.</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`message-container ${msg.sender.toLowerCase()}`}>
                  <div className="sender">{msg.sender}:</div>
                  <div className="message-text">{msg.text}</div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="message-container assistant">
                <div className="sender">Assistant:</div>
                <div className="message-text">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        );
      
      case 'History':
        return (
          <div className="tab-content history-tab">
            <h2>Conversation History</h2>
            {historyData.length === 0 ? (
              <div className="history-empty">
                <p>No conversation history found.</p>
                <p>Start a new conversation to see it here.</p>
              </div>
            ) : (
              <div className="history-list">
                {historyData.map((item) => (
                  <div key={item.id} className="history-item">
                    <div className="history-date">{item.date}</div>
                    <div className="history-topic">{item.topic}</div>
                    <div className="history-messages">{item.messages.length} messages</div>
                    <button 
                      className="history-view-btn"
                      onClick={() => viewConversation(item.id)}
                    >
                      View
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      
      case 'Help':
        return (
          <div className="tab-content help-tab">
            <h2>Help & Documentation</h2>
            <div className="help-topics">
              {helpTopics.map((topic, index) => (
                <div key={index} className="help-topic-container">
                  <div 
                    className={`help-topic ${expandedHelpTopic === index ? 'expanded' : ''}`}
                    onClick={() => toggleHelpTopic(index)}
                  >
                    <div className="help-topic-title">{topic.title}</div>
                    <div className="help-topic-icon">
                      {expandedHelpTopic === index ? '▼' : '→'}
                    </div>
                  </div>
                  {expandedHelpTopic === index && (
                    <div className="help-topic-content">
                      {topic.content}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="help-contact">
              <h3>Need more help?</h3>
              <p>Contact our support team at support@aiassistant.com</p>
              <button className="help-support-btn">Contact Support</button>
            </div>
          </div>
        );
      
      default:
        return (
          <div className="chat-box">
            <div className="welcome-message">
              <h2>Welcome to AI Assistant</h2>
              <p>Ask me anything and I'll do my best to assist you.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="app">
      <div className="menu-bar">
        <div className="menu-left">
          <button 
            className={`menu-button ${activeTab === 'Home' ? 'active' : ''}`}
            onClick={() => setActiveTab('Home')}
          >
            Home
          </button>
          <button 
            className={`menu-button ${activeTab === 'History' ? 'active' : ''}`}
            onClick={() => setActiveTab('History')}
          >
            History
          </button>
        </div>
        <div className="menu-title">{getCurrentTitle()}</div>
        <div className="menu-right">
          <button 
            className={`menu-button ${activeTab === 'Help' ? 'active' : ''}`}
            onClick={() => setActiveTab('Help')}
          >
            Help
          </button>
        </div>
      </div>

      <div className="chat-container">
        {renderContent()}
      </div>
      
      <div className="input-container">
        <input
          type="text"
          placeholder={viewingHistory ? "Continue this conversation..." : "Ask something..."}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              sendMessage();
            }
          }}
        />
        <button 
          onClick={sendMessage}
          className="send-button"
          disabled={!input.trim() || isLoading}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default App;