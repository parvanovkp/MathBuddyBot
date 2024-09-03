import React, { useState, useEffect, useRef } from 'react';
import { PlusCircle, Send } from 'lucide-react';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

const ChatInterface = ({ messages, onSendMessage, onNewChat, isTyping }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const renderMessage = (content) => {
    const parts = content.split(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/);
    return parts.map((part, index) => {
      if (part.startsWith('$$') && part.endsWith('$$')) {
        return <BlockMath key={index} math={part.slice(2, -2)} />;
      } else if (part.startsWith('$') && part.endsWith('$')) {
        return <InlineMath key={index} math={part.slice(1, -1)} />;
      } else {
        return <span key={index}>{part}</span>;
      }
    });
  };

  return (
    <div className="mt-6">
      <div 
        className="bg-white rounded-lg p-4 h-64 overflow-y-auto mb-4 border border-gray-200"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`mb-2 ${msg.type === 'user' ? 'text-right' : 'text-left'}`}
          >
            <div className={`inline-block max-w-[95%] ${msg.type === 'user' ? 'text-blue-600' : 'text-gray-800'}`}>
              <div className="font-bold mb-1">{msg.type === 'user' ? 'You' : 'MathBuddy'}</div>
              <div className="text-sm">{renderMessage(msg.content)}</div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="text-left text-gray-500">
            MathBuddy is typing...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSubmit} className="flex items-center">
        <button 
          type="button" 
          className="p-2 text-gray-500 hover:text-gray-700"
          aria-label="New chat"
          title="New chat"
          onClick={onNewChat}
        >
          <PlusCircle size={24} />
        </button>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-grow p-2 border border-gray-300 rounded-l resize-none"
          placeholder="Send a message. Press Shift+Enter for new line."
          aria-label="Message input"
          rows="1"
          disabled={isTyping}
        />
        <button 
          type="submit" 
          className="p-2 bg-blue-500 text-white rounded-r hover:bg-blue-600"
          aria-label="Send message"
          title="Send message"
          disabled={isTyping}
        >
          <Send size={24} />
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;