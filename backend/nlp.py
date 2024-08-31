import os
import asyncio
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get OpenAI API key from environment
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Initialize AsyncOpenAI client
client = AsyncOpenAI(api_key=api_key)

class MathTutor:
    async def solve(self, query: str):
        logger.info(f"MathTutor processing query: {query}")
        
        prompt = f"""
        Solve this calculus problem step by step: {query}

        Provide the following:
        1. Problem type: [Type]
        2. Steps:
           Step 1: [Explanation]
           Step 2: [Explanation]
           Step 3: [Explanation]
           Step 4: [Explanation]
           Step 5: [Explanation]
        3. Final answer: [Answer]
        4. Summary: [Brief summary]

        Ensure all steps are complete, show all algebraic manipulations, and provide the final answer in its simplest form.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful math tutor specializing in calculus."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = response.choices[0].message.content
            logger.debug(f"Raw API response: {result}")
            
            return {
                "solution": result
            }
        except Exception as e:
            logger.error(f"Error in MathTutor: {str(e)}")
            raise

# Initialize MathTutor
tutor = MathTutor()