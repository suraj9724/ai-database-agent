import React, { useState, useRef, useEffect } from 'react'
import {
  Bot,
  User,
  Send,
  PlusCircle,
  Copy,
  Check,
  Sparkles,
  AlertCircle,
  Database,
  RefreshCw,
  Terminal
} from 'lucide-react'

// Suggested sample queries matching the backend's invoice & sales database
const SAMPLE_QUERIES = [
  'Which customer has the highest invoice?',
  'What is the total value of unpaid invoices?',
  'How many invoices does TechNova Solutions have?',
  'Which invoices are partially paid?',
  'How much did we receive from BlueSky Enterprises?',
  'Show me all invoices for TechNova Solutions.'
]

function generateConversationId() {
  return 'conv-' + Math.random().toString(36).substring(2, 10)
}

export default function App() {
  const [conversationId, setConversationId] = useState(() => {
    return localStorage.getItem('ai_agent_conv_id') || generateConversationId()
  })
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('ai_agent_messages')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const [copiedIndex, setCopiedIndex] = useState(null)
  const [backendStatus, setBackendStatus] = useState('ready') // 'ready' | 'error' | 'checking'

  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Save conversationId & messages to localStorage
  useEffect(() => {
    localStorage.setItem('ai_agent_conv_id', conversationId)
  }, [conversationId])

  useEffect(() => {
    localStorage.setItem('ai_agent_messages', JSON.stringify(messages))
  }, [messages])

  // Auto-scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Handle textarea auto-resize
  const handleInputChange = (e) => {
    setInputMessage(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`
    }
  }

  // Start new conversation
  const handleNewChat = () => {
    const newId = generateConversationId()
    setConversationId(newId)
    setMessages([])
    setErrorMessage(null)
    setInputMessage('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.focus()
    }
  }

  // Copy message content
  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(idx)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  // Send message to FastAPI backend
  const handleSendMessage = async (textToSend) => {
    const message = (textToSend || inputMessage).trim()
    if (!message || isLoading) return

    setErrorMessage(null)
    setInputMessage('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    const userMessageItem = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setMessages((prev) => [...prev, userMessageItem])
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json'
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: message
        })
      })

      if (!response.ok) {
        throw new Error(
          `Backend returned ${response.status}: ${response.statusText || 'Unable to connect to FastAPI'}`
        )
      }

      const data = await response.json()
      const assistantMessageItem = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer || 'No response returned from the agent.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }

      setMessages((prev) => [...prev, assistantMessageItem])
      setBackendStatus('ready')
    } catch (err) {
      console.error('Chat error:', err)
      setBackendStatus('error')
      setErrorMessage(
        err.message.includes('Failed to fetch')
          ? 'Cannot connect to FastAPI backend. Ensure uvicorn is running: python -m uvicorn ai.api.main:app --reload --port 8000'
          : err.message
      )
    } finally {
      setIsLoading(false)
    }
  }

  // Enter to send (Shift+Enter for new line)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="app-container" id="chatbot-app">
      <div className="bg-glow-orb" />

      {/* Header */}
      <header className="chat-header" id="chat-header">
        <div className="header-brand">
          <div className="brand-icon">
            <Database size={22} />
          </div>
          <div>
            <h1 className="brand-title">
              Database AI Assistant
              <Sparkles size={16} color="#818cf8" />
            </h1>
            <p className="brand-subtitle">Natural language SQL & business intelligence</p>
          </div>
        </div>

        <div className="header-actions">
          <div
            id="status-indicator"
            className={`status-pill ${backendStatus === 'error' ? 'offline' : ''}`}
            title={
              backendStatus === 'error'
                ? 'Backend disconnected (Check port 8000)'
                : 'Connected via proxy to FastAPI backend'
            }
          >
            <span className="status-dot" />
            {backendStatus === 'error' ? 'Backend Offline' : 'Ready'}
          </div>

          <button
            id="btn-new-chat"
            className="btn-secondary"
            onClick={handleNewChat}
            title="Start a new conversation"
          >
            <PlusCircle size={16} />
            <span>New Chat</span>
          </button>
        </div>
      </header>

      {/* Error Banner */}
      {errorMessage && (
        <div className="chat-error-banner" id="error-banner">
          <div className="chat-error-text">
            <AlertCircle size={18} />
            <span>{errorMessage}</span>
          </div>
          <button
            className="copy-btn"
            onClick={() => setErrorMessage(null)}
            style={{ color: '#fca5a5' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Chat Messages Area */}
      <main className="chat-messages" id="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state" id="empty-state">
            <div className="empty-state-icon">
              <Bot size={34} color="#ffffff" />
            </div>
            <h2>How can I help with your database today?</h2>
            <p>
              Ask questions in plain English. I'll translate them to queries, inspect the invoices,
              customers, and payment records, and explain the answers clearly.
            </p>

            <span className="quick-prompts-title">Sample Inquiries</span>
            <div className="quick-prompts-grid">
              {SAMPLE_QUERIES.map((query, index) => (
                <button
                  key={index}
                  id={`prompt-card-${index}`}
                  className="prompt-card"
                  onClick={() => handleSendMessage(query)}
                >
                  <span>{query}</span>
                  <Sparkles size={14} color="#818cf8" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={msg.id || index}
              id={`message-${index}`}
              className={`message-row ${msg.role}`}
            >
              <div className={`message-avatar ${msg.role}`}>
                {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
              </div>

              <div className="message-content-wrapper">
                <div className="message-bubble">{msg.content}</div>

                <div className="message-meta">
                  <span>{msg.timestamp}</span>
                  {msg.role === 'assistant' && (
                    <button
                      id={`copy-btn-${index}`}
                      className="copy-btn"
                      onClick={() => handleCopy(msg.content, index)}
                      title="Copy response"
                    >
                      {copiedIndex === index ? (
                        <>
                          <Check size={12} color="#10b981" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Loading / Typing indicator */}
        {isLoading && (
          <div className="message-row assistant" id="typing-indicator-row">
            <div className="message-avatar assistant">
              <Bot size={20} />
            </div>
            <div className="typing-bubble">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <footer className="chat-input-area" id="chat-input-area">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSendMessage()
          }}
          className="chat-input-wrapper"
        >
          <textarea
            id="chat-input-textarea"
            ref={textareaRef}
            className="chat-textarea"
            placeholder="Ask about invoices, customers, revenue, or outstanding balance..."
            value={inputMessage}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isLoading}
          />

          <button
            id="btn-send-message"
            type="submit"
            className="btn-send"
            disabled={!inputMessage.trim() || isLoading}
            title="Send message (Enter)"
          >
            {isLoading ? <RefreshCw size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </form>

        <div className="input-footer-hint">
          <span>Press Enter to send, Shift + Enter for new line</span>
          <span className="conversation-tag" title="Active Conversation ID">
            ID: {conversationId}
          </span>
        </div>
      </footer>
    </div>
  )
}
