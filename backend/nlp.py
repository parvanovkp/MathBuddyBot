import os
import dspy
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

# Get OpenAI API key from environment
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Configure DSPY
dspy.configure(api_key=openai_api_key)

class MathTutor(dspy.Module):
    def __init__(self):
        super().__init__()
        
        # Explicitly create the language model and configure it
        turbo = dspy.OpenAI(model="gpt-3.5-turbo-0125", api_key=os.environ["OPENAI_API_KEY"])
        dspy.settings.configure(lm=turbo)

        # Initialize ChainOfThought components
        self.understand_query = dspy.ChainOfThought("query -> problem_type, steps")
        self.explain_step = dspy.ChainOfThought("step, previous_result -> explanation, wolfram_query")
        self.summarize = dspy.ChainOfThought("all_steps, final_result -> summary")

    def forward(self, query):
        print(f"Received query: {query}")
        
        # Understand the query and break it into steps using DSPY
        try:
            understanding = self.understand_query(query=query)
            print(f"Understanding: {understanding}")
        except Exception as e:
            print(f"Error in understanding query: {e}")
            return {"error": "Failed to process the query."}
        
        all_steps = []
        for step in understanding.steps:
            try:
                previous_result_str = "\n".join(
                    [f"Step {i+1}: {step_info['explanation']}" for i, step_info in enumerate(all_steps)]
                ) if all_steps else "No previous steps."

                print(f"Processing step: {step}")
                step_info = self.explain_step(step=step, previous_result=previous_result_str)
                print(f"Step Info: {step_info}")

                all_steps.append({
                    "explanation": step_info.explanation,
                    "wolfram_query": step_info.wolfram_query
                })
            except Exception as e:
                print(f"Error processing step: {e}")
                return {"error": "Failed to process a step."}
        
        try:
            summary = self.summarize(all_steps=all_steps, final_result="To be computed by WolframAlpha")
            print(f"Summary: {summary}")
        except Exception as e:
            print(f"Error in summarizing: {e}")
            return {"error": "Failed to summarize the results."}
        
        return dspy.Prediction(
            problem_type=understanding.problem_type,
            steps=all_steps,
            summary=summary.summary
        )
