import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { marked } from "marked";

function ProductCard({ card }) {
  if (!card) return null;
  return (
    <div className="product-card p-4 border rounded shadow-sm flex mt-2">
      <img src={card.image} alt={card.name} width={120} />
      <div className="ml-4">
        <div className="font-bold">{card.name}</div>
        <div className="text-sm">Part #: {card.part_number}</div>
        <div className="text-sm">Brand: {card.brand}</div>
        <a href={card.link} target="_blank" rel="noreferrer" className="text-blue-600">
          View on PartSelect
        </a>
      </div>
    </div>
  );
}

function ChatWindow() {
  const defaultMessage = [{
    role: "assistant",
    content: "Hi, how can I help you today?"
  }];

  const [messages, setMessages] = useState(defaultMessage);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (inputText) => {
    if (!inputText.trim()) return;

    // Add user message
    setMessages(prev => [...prev, { role: "user", content: inputText }]);
    setInput("");

    try {
      // Call backend
      const res = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: inputText })
      });
      const data = await res.json();

      // Add assistant message with optional product card
      setMessages(prev => [
        ...prev,
        { 
          role: "assistant", 
          content: data.answer, 
          product_card: data.product_card 
        }
      ]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong." }
      ]);
    }
  };

  return (
    <div className="messages-container">
      {messages.map((message, index) => (
        <div key={index} className={`${message.role}-message-container`}>
          {message.content && (
            <div className={`message ${message.role}-message`}>
              <div dangerouslySetInnerHTML={{
                __html: marked(message.content || "").replace(/<p>|<\/p>/g, "")
              }} />
            </div>
          )}
          {message.role === "assistant" && message.product_card && (
            <ProductCard card={message.product_card} />
          )}
        </div>
      ))}
      <div ref={messagesEndRef} />
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          onKeyPress={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              handleSend(input);
              e.preventDefault();
            }
          }}
        />
        <button className="send-button" onClick={() => handleSend(input)}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;