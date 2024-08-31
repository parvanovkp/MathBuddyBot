# backend/nlp.py

import os
import dspy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get OpenAI API key from environment
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Explicitly create the language model and configure it
turbo = dspy.OpenAI(model="gpt-3.5-turbo-0125", api_key=openai_api_key)
dspy.settings.configure(lm=turbo)

class MathTutor(dspy.Module):
    def __init__(self):
        super().__init__()
        
        # Explicitly create the language model and configure it
        turbo = dspy.OpenAI(model="gpt-3.5-turbo-0125", api_key=os.getenv("OPENAI_API_KEY"))
        dspy.settings.configure(lm=turbo)

        # Initialize ChainOfThought components
        self.understand_query = dspy.ChainOfThought("query -> problem_type, steps")
        self.explain_step = dspy.ChainOfThought("step, previous_result -> explanation, wolfram_query")
        self.summarize = dspy.ChainOfThought("all_steps, final_result -> summary")

    def forward(self, query):
        # Understand the query and break it into steps using DSPY
        understanding = self.understand_query(query=query)
        
        all_steps = []
        for step in understanding.steps:
            # Convert the previous_result to a string
            previous_result_str = "\n".join(
                [f"Step {i+1}: {step_info['explanation']}" for i, step_info in enumerate(all_steps)]
            ) if all_steps else "No previous steps."

            # Generate explanation and WolframAlpha query for each step
            step_info = self.explain_step(step=step, previous_result=previous_result_str)
            
            all_steps.append({
                "explanation": step_info.explanation,
                "wolfram_query": step_info.wolfram_query
            })

        # Convert all_steps list into a string to pass to summarize
        all_steps_str = "\n".join(
            [f"Step {i+1}: {step_info['explanation']}" for i, step_info in enumerate(all_steps)]
        )

        # Summarize the solution
        summary = self.summarize(all_steps=all_steps_str, final_result="To be computed by WolframAlpha")

        return dspy.Prediction(
            problem_type=understanding.problem_type,
            steps=all_steps,
            summary=summary.summary
        )