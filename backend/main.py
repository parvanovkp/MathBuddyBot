# main.py (in the backend folder)

import os
from dotenv import load_dotenv
import logging
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from openai import OpenAI
import wolframalpha

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ["OPENAI_API_KEY", "WOLFRAM_ALPHA_APP_ID"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"{var} not found in environment variables")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    message: str

class SessionResponse(BaseModel):
    session_id: str

# In-memory session storage (replace with a database in production)
sessions: Dict[str, Dict[str, Any]] = {}

# Initialize OpenAI and Wolfram Alpha
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
wolfram_client = wolframalpha.Client(os.getenv("WOLFRAM_ALPHA_APP_ID"))

SYSTEM_PROMPT = """
You are MathBuddyBot, an AI math tutor for topics from 3rd grade to Calculus 1. Your goal is to guide students through problem-solving steps and help them understand mathematical concepts.

Key guidelines:
1. Be extremely concise in every response. Avoid unnecessary explanations unless the student asks for more details.
2. Adjust your level based on the complexity of the student's question. If unsure, ask for clarification about their math level.
3. Use Wolfram Alpha for calculations and verifications. Always double-check your mathematical statements with Wolfram Alpha before presenting them to the student.
4. Guide students through problem-solving rather than giving immediate answers.
5. Encourage critical thinking by asking probing questions.
6. Provide step-by-step explanations only when necessary.
7. Use analogies and real-world examples sparingly and only when they significantly aid understanding.
8. If a student is struggling, break down the problem into smaller, manageable parts.
9. Regularly check the student's understanding by asking them to explain concepts back to you.

Remember, your role is to facilitate learning, not just to provide answers. Use Wolfram Alpha to ensure accuracy in your explanations and calculations.

To use Wolfram Alpha, include the phrase "Wolfram Alpha query: [your query]" in your response. The system will replace this with the Wolfram Alpha result.

Current topic: {topic}
Current difficulty level: {difficulty}
"""

@app.post("/start_session", response_model=SessionResponse)
async def start_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "messages": [],
        "topic": "3rd Grade Math",
        "difficulty": 1
    }
    logger.info(f"Started new session: {session_id}")
    return {"session_id": session_id}

@app.post("/chat")
async def chat(query: Query, session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session["messages"].append({"role": "user", "content": query.message})
    
    # Prepare the messages for the API call
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(topic=session["topic"], difficulty=session["difficulty"])},
        *session["messages"]
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        bot_message = response.choices[0].message.content
        
        # Check if Wolfram Alpha calculation is needed
        while "Wolfram Alpha query:" in bot_message:
            wolfram_query = bot_message.split("Wolfram Alpha query:")[-1].split("\n")[0].strip()
            wolfram_result = wolfram_client.query(wolfram_query)
            wolfram_pods = list(wolfram_result.pods)
            if len(wolfram_pods) > 1:
                wolfram_answer = next((pod.text for pod in wolfram_pods if pod.title == 'Result' or pod.title == 'Solution'), "No clear result found.")
                bot_message = bot_message.replace(f"Wolfram Alpha query: {wolfram_query}", f"Wolfram Alpha result: {wolfram_answer}")
            else:
                bot_message = bot_message.replace(f"Wolfram Alpha query: {wolfram_query}", "Wolfram Alpha couldn't provide a clear answer for this query.")
        
        session["messages"].append({"role": "assistant", "content": bot_message})
        
        # Adjust difficulty based on the complexity of the question and response
        if any(word in query.message.lower() for word in ['calculus', 'derivative', 'integral', 'limit']):
            session["difficulty"] = max(session["difficulty"], 8)
            session["topic"] = "Calculus 1"
        elif any(word in query.message.lower() for word in ['algebra', 'equation', 'polynomial']):
            session["difficulty"] = max(session["difficulty"], 5)
            session["topic"] = "Algebra"
        
        return {"response": bot_message}
    
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)