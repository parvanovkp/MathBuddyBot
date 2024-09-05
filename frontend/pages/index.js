import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import ChatInterface from '../components/ChatInterface';
import SuggestedQuestions from '../components/SuggestedQuestions';
import 'katex/dist/katex.min.css';

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    startNewSession();
  }, []);

  const startNewSession = async () => {
    try {
      const response = await fetch('/api/start_session', { method: 'POST' });
      const data = await response.json();
      setSessionId(data.session_id);
      setMessages([]);
    } catch (error) {
      console.error('Error starting new session:', error);
    }
  };

  const handleSendMessage = async (message) => {
    const userMessage = { type: 'user', content: message };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setIsTyping(true);
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      });
      
      const data = await response.json();
      
      // Simulate typing effect
      let typedMessage = '';
      const fullMessage = data.response;
      
      setMessages(prevMessages => [...prevMessages, { type: 'bot', content: '' }]);

      for (let i = 0; i < fullMessage.length; i++) {
        typedMessage += fullMessage[i];
        setMessages(prevMessages => [
          ...prevMessages.slice(0, -1),
          { type: 'bot', content: typedMessage }
        ]);
        await new Promise(resolve => setTimeout(resolve, 20)); // Adjust typing speed here
      }
      
      setIsTyping(false);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prevMessages => [...prevMessages, { type: 'bot', content: 'Sorry, there was an error processing your request.' }]);
      setIsTyping(false);
    }
  };

  return (
    <Layout>
      <Head>
        <title>MathBuddyBot</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="p-4 max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-2">Welcome to MathBuddyBot!</h1>
        <p className="mb-4">
          Hi there! I'm MathBuddyBot, your friendly AI math tutor. I'm here to help you with everything from basic arithmetic to Calculus 1. What would you like to learn today?
        </p>

        <SuggestedQuestions onQuestionClick={handleSendMessage} />
        <ChatInterface 
          messages={messages} 
          onSendMessage={handleSendMessage} 
          onNewChat={startNewSession}
          isTyping={isTyping}
        />
      </main>
    </Layout>
  );
}