import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useChat } from '../hooks/useChat'
import { Button } from '../components/ui/Button'
import { Avatar } from '../components/ui/Avatar'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { useChatStore } from '../context/ChatContext'

export const Chat = () => {
  const { isAuthenticated } = useAuth()
  const { loading, error, sendMessage, streamMessage, reset } = useChat()
  const { messages, currentConversationId, addConversation } = useChatStore()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isStreaming, setIsStreaming] = useState(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isStreaming])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !isAuthenticated()) return

    if (isStreaming) return

    const userId = localStorage.getItem('user_id') || 'user_' + Date.now()
    localStorage.setItem('user_id', userId)

    setIsStreaming(true)
    let fullResponse = ''

    await streamMessage(input, userId, (chunk) => {
      fullResponse += chunk
    })

    setIsStreaming(false)
    setInput('')
  }

  const handleNewChat = () => {
    reset()
    addConversation(Date.now().toString(), 'New Conversation', '')
  }

  if (!isAuthenticated()) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Please login to chat</h2>
          <Button onClick={() => window.location.href = '/login'}>Login</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-600 text-white">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">AI Assistant</h2>
            <p className="text-sm text-gray-500">Powered by Gemini 2.5 Flash</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={handleNewChat}>
          New Chat
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-2">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary-100 text-primary-600">
              <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">How can I help you today?</h3>
              <p className="text-gray-500 mt-2">Ask me anything about products, get recommendations, or search by image.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl">
              {[
                'Find trending products',
                'Get personalized recommendations',
                'Search by image',
                'Compare products',
              ].map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setInput(prompt)
                    document.getElementById('chat-input')?.focus()
                  }}
                  className="p-4 text-left rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`flex-shrink-0 rounded-full overflow-hidden ${msg.role === 'user' ? 'bg-gray-200' : 'bg-primary-600'}`}>
                <Avatar
                  name={msg.role === 'user' ? 'You' : 'AI Assistant'}
                  size="md"
                  className={msg.role === 'user' ? 'bg-gray-200 text-gray-600' : 'bg-primary-600 text-white'}
                />
              </div>
              <div
                className={`max-w-[80%] rounded-2xl px-6 py-4 ${
                  msg.role === 'user'
                    ? 'bg-primary-600 text-white rounded-tr-none'
                    : 'bg-gray-100 text-gray-900 rounded-tl-none'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p className={`text-xs mt-2 ${msg.role === 'user' ? 'text-primary-200' : 'text-gray-500'}`}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex gap-4">
            <div className="flex-shrink-0 rounded-full overflow-hidden bg-primary-600">
              <Avatar name="AI Assistant" size="md" className="bg-primary-600 text-white" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-tl-none px-6 py-4">
              <LoadingSpinner size="sm" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 pt-4">
        {error && (
          <div className="mb-4 bg-red-50 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}
        <form onSubmit={handleSendMessage} className="flex gap-4">
          <div className="flex-1 relative">
            <input
              id="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything..."
              className="w-full rounded-full border-gray-300 bg-gray-50 py-4 px-6 pr-12 focus:border-primary-500 focus:ring-primary-500"
              disabled={loading || isStreaming}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading || isStreaming}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-primary-600 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary-700 transition-colors"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </form>
        <p className="text-center text-xs text-gray-500 mt-2">
          AI responses may vary. Verify important information.
        </p>
      </div>
    </div>
  )
}
