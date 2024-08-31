# backend/math_processing.py

import os
import wolframalpha
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize WolframAlpha client
wolfram_client = wolframalpha.Client(os.getenv("WOLFRAM_ALPHA_APP_ID"))

def process_math_query(query: str):
    """
    Process a mathematical query using WolframAlpha and return the result and steps.
    
    :param query: A string representing the mathematical query
    :return: A tuple containing the result and a list of steps
    """
    try:
        res = wolfram_client.query(query)
        result = next(res.results).text
        steps = [f"Query processed by WolframAlpha: {query}", f"Result: {result}"]
        return result, steps
    except Exception as e:
        raise ValueError(f"Error processing with WolframAlpha: {str(e)}")