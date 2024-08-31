import React from 'react';
import LatexRenderer from './LatexRenderer';

const SuggestedQuestions = ({ onQuestionClick }) => {
  const questions = [
    { text: "What is the derivative of $x^2$?", latex: null },
    { text: "Solve for x: $2x + 5 = 13$", latex: null },
    { text: "What is the integral of $\\sin(x)$?", latex: null },
    { 
      text: "Explain the quadratic formula:", 
      latex: "ax^2 + bx + c = 0" 
    }
  ];

  return (
    <div className="grid grid-cols-2 gap-4 mb-6" aria-label="Suggested questions">
      {questions.map((question, index) => (
        <button
          key={index}
          onClick={() => onQuestionClick(question.text + (question.latex ? ` $$${question.latex}$$.` : ''))}
          className="bg-white p-4 rounded-lg shadow-md text-left hover:bg-gray-50 transition-colors"
          aria-label={`Ask question: ${question.text}`}
        >
          <div>{question.text.split('$').map((part, i) => 
            i % 2 === 0 ? part : <LatexRenderer key={i}>{part}</LatexRenderer>
          )}</div>
          {question.latex && (
            <div className="mt-2 text-center">
              <LatexRenderer>{question.latex}</LatexRenderer>.
            </div>
          )}
        </button>
      ))}
    </div>
  );
};

export default SuggestedQuestions;