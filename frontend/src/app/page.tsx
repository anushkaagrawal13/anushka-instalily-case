'use client';

// [PASTE THE ENTIRE CHAT COMPONENT CODE HERE FROM THE FIRST ARTIFACT]
// It starts with: import React, { useState, useRef, useEffect } from 'react';
// And ends with: export default PartSelectChatAgent;

import React, { useState, useRef, useEffect } from 'react';
import { Send, Package, Wrench, ShoppingCart, CheckCircle, AlertCircle, Loader2, MessageSquare, Search } from 'lucide-react';

const PartSelectChatAgent = () => {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      content: 'Hello! I\'m your PartSelect assistant for Refrigerator and Dishwasher parts. I can help you with:\n\n• Installation instructions\n• Part compatibility checks\n• Troubleshooting issues\n• Product recommendations\n\nHow can I help you today?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Simulated backend response logic
  const processQuery = async (query) => {
    const lowerQuery = query.toLowerCase();
    
    // Installation query
    if (lowerQuery.includes('install') && lowerQuery.includes('ps11752778')) {
      return {
        type: 'installation',
        content: '**Installation Guide for Part PS11752778 - Dishwasher Upper Rack Adjuster**\n\n**Tools Needed:**\n• Phillips screwdriver\n• Needle-nose pliers (optional)\n\n**Step-by-Step Instructions:**\n\n1. **Safety First**: Disconnect power to the dishwasher\n2. **Remove Upper Rack**: Pull the rack completely out of the dishwasher\n3. **Locate Adjuster**: Find the worn adjuster on the side of the rack\n4. **Remove Old Part**: Press the release tab and slide out the old adjuster\n5. **Install New Adjuster**: Align the new PS11752778 adjuster and snap it into place\n6. **Test Movement**: Ensure the adjuster moves smoothly up and down\n7. **Reinstall Rack**: Slide the rack back into the dishwasher\n8. **Test**: Run a test cycle to verify proper operation\n\n**Estimated Time:** 15-20 minutes\n**Difficulty:** Easy\n\n[View Video Tutorial](https://www.partselect.com/PS11752778)',
        partInfo: {
          partNumber: 'PS11752778',
          name: 'Upper Rack Adjuster',
          price: '$12.99',
          inStock: true
        }
      };
    }
    
    // Compatibility query
    if (lowerQuery.includes('compatible') && lowerQuery.includes('wdt780saem1')) {
      return {
        type: 'compatibility',
        content: '**Compatibility Check for Model WDT780SAEM1**\n\nGreat news! I found several compatible parts for your Whirlpool dishwasher model **WDT780SAEM1**.\n\n**Based on your question, here are the most relevant parts:**',
        products: [
          {
            partNumber: 'W10350375',
            name: 'Dishwasher Upper Rack Assembly',
            price: '$89.95',
            compatibility: 'Direct Fit',
            fixPercentage: 95
          },
          {
            partNumber: 'W10195416',
            name: 'Dishwasher Spray Arm',
            price: '$32.50',
            compatibility: 'Direct Fit',
            fixPercentage: 88
          },
          {
            partNumber: 'W10712395',
            name: 'Door Latch Assembly',
            price: '$67.80',
            compatibility: 'Direct Fit',
            fixPercentage: 92
          }
        ]
      };
    }
    
    // Troubleshooting query
    if (lowerQuery.includes('ice maker') && lowerQuery.includes('not working')) {
      return {
        type: 'troubleshooting',
        content: '**Troubleshooting: Ice Maker Not Working - Whirlpool Refrigerator**\n\n**Common Causes & Solutions:**',
        troubleshooting: [
          {
            issue: 'Water Supply Issue',
            solution: 'Check if water supply valve is fully open. Inspect water line for kinks or freezing.',
            likelihood: 'High - 35%'
          },
          {
            issue: 'Faulty Ice Maker Assembly',
            solution: 'Test the ice maker module. If it doesn\'t cycle, replacement may be needed.',
            likelihood: 'High - 30%'
          },
          {
            issue: 'Water Inlet Valve Problem',
            solution: 'Check for proper water pressure (20-120 PSI). Test valve with multimeter.',
            likelihood: 'Medium - 20%'
          }
        ],
        recommendedParts: [
          {
            partNumber: 'W10190965',
            name: 'Ice Maker Assembly',
            price: '$124.99',
            fixPercentage: 87,
            reviews: 4.5
          },
          {
            partNumber: 'W10408179',
            name: 'Water Inlet Valve',
            price: '$45.50',
            fixPercentage: 78,
            reviews: 4.3
          }
        ]
      };
    }
    
    // Default general query
    return {
      type: 'general',
      content: 'I can help you with that! To provide the most accurate information, please specify:\n\n• Part number (e.g., PS11752778)\n• Model number (e.g., WDT780SAEM1)\n• Specific issue or question\n\nOr try asking:\n• "How do I install part PS11752778?"\n• "Is part X compatible with model Y?"\n• "My ice maker isn\'t working"'
    };
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Simulate API delay
    setTimeout(async () => {
      const response = await processQuery(input);
      
      const botMessage = {
        type: 'bot',
        content: response.content,
        data: response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const renderMessage = (message) => {
    if (message.type === 'user') {
      return (
        <div className="flex justify-end mb-4">
          <div className="bg-blue-600 text-white rounded-lg px-4 py-2 max-w-md">
            {message.content}
          </div>
        </div>
      );
    }

    return (
      <div className="flex justify-start mb-4">
        <div className="bg-white rounded-lg px-4 py-3 max-w-2xl shadow-sm border border-gray-200">
          <div className="prose prose-sm max-w-none">
            {message.content.split('\n').map((line, i) => {
              if (line.startsWith('**') && line.endsWith('**')) {
                return <div key={i} className="font-bold text-gray-900 mt-3 mb-2">{line.replace(/\*\*/g, '')}</div>;
              }
              if (line.startsWith('•')) {
                return <div key={i} className="ml-4 mb-1 text-gray-700">{line}</div>;
              }
              if (line.trim().match(/^\d+\./)) {
                return <div key={i} className="ml-4 mb-2 text-gray-700">{line}</div>;
              }
              if (line.includes('[View Video Tutorial]')) {
                return <div key={i} className="mt-3"><a href="#" className="text-blue-600 hover:underline">{line.match(/\[(.*?)\]/)[1]}</a></div>;
              }
              return line ? <div key={i} className="mb-1 text-gray-700">{line}</div> : <div key={i} className="h-2" />;
            })}
          </div>

          {/* Render part info card */}
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

          {/* Render compatible products */}
          {message.data?.products && (
            <div className="mt-4 space-y-3">
              {message.data.products.map((product, idx) => (
                <div key={idx} className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">{product.name}</div>
                      <div className="text-sm text-gray-600">Part #{product.partNumber}</div>
                      <div className="mt-1 flex items-center space-x-3 text-xs">
                        <span className="text-green-600 font-medium">{product.compatibility}</span>
                        <span className="text-gray-500">{product.fixPercentage}% fix rate</span>
                      </div>
                    </div>
                    <div className="text-right ml-4">
                      <div className="font-bold text-gray-900">{product.price}</div>
                      <button className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                        View
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Render troubleshooting */}
          {message.data?.troubleshooting && (
            <div className="mt-4 space-y-3">
              {message.data.troubleshooting.map((item, idx) => (
                <div key={idx} className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-start">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">{item.issue}</div>
                      <div className="text-sm text-gray-600 mt-1">{item.solution}</div>
                      <div className="text-xs text-yellow-700 mt-2 font-medium">{item.likelihood}</div>
                    </div>
                  </div>
                </div>
              ))}
              
              {message.data.recommendedParts && (
                <div className="mt-4">
                  <div className="font-semibold text-gray-900 mb-2">Recommended Replacement Parts:</div>
                  {message.data.recommendedParts.map((part, idx) => (
                    <div key={idx} className="p-3 bg-green-50 border border-green-200 rounded-lg mb-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold text-gray-900">{part.name}</div>
                          <div className="text-sm text-gray-600">Part #{part.partNumber}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            ⭐ {part.reviews}/5 • {part.fixPercentage}% fix rate
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold text-gray-900">{part.price}</div>
                          <button className="mt-2 bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm">
                            Add to Cart
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  const quickActions = [
    { icon: Wrench, text: 'Installation Help', query: 'How do I install part PS11752778?' },
    { icon: Search, text: 'Check Compatibility', query: 'Is this part compatible with my WDT780SAEM1 model?' },
    { icon: AlertCircle, text: 'Troubleshoot Issue', query: 'My Whirlpool ice maker is not working' },
  ];

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

      {/* Quick Actions */}
      {messages.length === 1 && (
        <div className="max-w-4xl mx-auto px-4 py-6 w-full">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {quickActions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(action.query)}
                  className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
                >
                  <action.icon className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">{action.text}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto">
          {messages.map((message, idx) => (
            <div key={idx}>{renderMessage(message)}</div>
          ))}
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
            Specialized in Refrigerator and Dishwasher parts • Powered by AI
          </p>
        </div>
      </div>
    </div>
  );
};

export default PartSelectChatAgent;