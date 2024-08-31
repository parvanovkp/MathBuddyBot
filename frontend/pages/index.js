import React, { useState } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import ChatInterface from '../components/ChatInterface';
import SuggestedQuestions from '../components/SuggestedQuestions';
import 'katex/dist/katex.min.css';


export default function Home() {
  const [messages, setMessages] = useState([]);

  const handleSendMessage = async (message) => {
    setMessages([...messages, { type: 'user', content: message }]);
    // Here you would call your API to get the response
    // For now, we'll just echo the message
    setMessages(prevMessages => [...prevMessages, { type: 'bot', content: `You asked: ${message}` }]);
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  return (
    <Layout>
      <Head>
        <title>Math AI Chatbot</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="p-6 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Welcome to MathBuddyBot!</h1>
        <p className="mb-6">
          This is an open source AI chatbot built with Next.js, 
          specialized in answering math questions up to the calculus 2 level.
        </p>

        <SuggestedQuestions onQuestionClick={handleSendMessage} />
        <ChatInterface 
          messages={messages} 
          onSendMessage={handleSendMessage} 
          onNewChat={handleNewChat}
        />
      </main>
    </Layout>
  );
}