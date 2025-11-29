'use client';

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Package, CheckCircle, ShoppingCart, Loader2 } from 'lucide-react';

export default function Home() {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      content: `Hello! I'm your PartSelect assistant for Refrigerator and Dishwasher parts. I can help you with:\n

-- Installation instructions \n
-- Part compatibility checks\n
-- Troubleshooting issues\n
-- Product recommendations\n

How can I help you today?`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      type: 'user' as const,
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentQuery = input;
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5001/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: currentQuery }),
      });

      const data = await response.json();
      
      const botMessage = {
        type: 'bot' as const,
        content: data.response || "Sorry, I couldn't process that request.",
        data: data,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        type: 'bot' as const,
        content: 'Sorry, I encountered an error. Please make sure the backend server is running on port 5001.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = (message: any, index: number) => {
    if (message.type === 'user') {
      return (
        <div key={index} className="flex justify-end mb-4">
          <div className="bg-blue-600 text-white rounded-lg px-4 py-2 max-w-md">
            {message.content}
          </div>
        </div>
      );
    }

    return (
      <div key={index} className="flex justify-start mb-4">
        <div className="bg-white rounded-lg px-4 py-3 max-w-2xl shadow-sm border border-gray-200">
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>

          {message.data?.partInfo && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-gray-900">{message.data.partInfo.name}</div>
                  <div className="text-sm text-gray-600">Part #{message.data.partInfo.partNumber}</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-green-600">{message.data.partInfo.price}</div>
                  <div className="text-xs text-green-600 flex items-center">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    In Stock
                  </div>
                </div>
              </div>
              <button className="mt-3 w-full bg-orange-500 hover:bg-orange-600 text-white py-2 rounded-lg font-medium flex items-center justify-center">
                <ShoppingCart className="w-4 h-4 mr-2" />
                Add to Cart
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-orange-500 p-2 rounded-lg">
                <Package className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">PartSelect Assistant</h1>
                <p className="text-sm text-gray-600">Refrigerator & Dishwasher Parts Expert</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto">
          {messages.map((message, idx) => renderMessage(message, idx))}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="bg-white rounded-lg px-4 py-3 shadow-sm border border-gray-200">
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex space-x-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about installation, compatibility, or troubleshooting..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white px-6 py-3 rounded-lg font-medium flex items-center space-x-2 transition-colors"
            >
              <Send className="w-5 h-5" />
              <span>Send</span>
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Specialized in Refrigerator and Dishwasher parts • Powered by OpenAI
          </p>
        </div>
      </div>
    </div>
  );
}
