import os
from dotenv import load_dotenv
import logging
import uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from openai import OpenAI
import requests
import re
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ["OPENAI_API_KEY", "WOLFRAM_ALPHA_APP_ID", "API_KEY", "FRONTEND_URL"]
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
    allow_origins=[os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    message: str
    session_id: str

class SessionResponse(BaseModel):
    session_id: str

# In-memory session storage (replace with a database in production)
sessions: Dict[str, Dict[str, Any]] = {}

# Rate limiting
RATE_LIMIT = 50  # requests per day
rate_limit_data: Dict[str, Dict[str, Any]] = {}

# API key security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Depends(api_key_header)):
    expected_api_key = os.getenv("API_KEY")
    logger.info(f"Received API Key: {api_key_header}, Expected: {expected_api_key}")  # Debug print
    if api_key_header == expected_api_key:
        return api_key_header
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate API KEY"
    )

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are MathBuddy, an AI math tutor specializing in topics from 3rd grade to Calculus 1. Your role is to guide and support students in their learning process, not to solve problems for them. Adapt your language and explanations to the student's level, which can range from elementary school math to high school calculus. Focus on the following:

1. Use KaTeX syntax for all mathematical expressions. Inline formulas should be enclosed in single dollar signs ($...$) and display formulas in double dollar signs ($$...$$).
2. Be concise and encouraging in your responses.
3. Instead of solving problems, ask guiding questions to help students reach the solution themselves.
4. Break down complex problems into smaller, manageable steps.
5. Provide hints and explanations about concepts, but avoid giving direct answers.
6. When you need to verify a mathematical statement or calculation, use the format: "Wolfram Alpha query: [query]". Format the query exactly as it should be input into Wolfram Alpha, without any additional text or explanation.
7. After receiving a Wolfram Alpha result, interpret it for the student. Confirm if the student's answer is correct and provide the verified result in LaTeX format, enclosed in double dollar signs ($$...$$).
8. If a student is stuck, suggest reviewing specific concepts or offer a small hint to move forward.
9. Regularly check the student's understanding by asking them to explain concepts back to you.
10. Adjust your language and explanation complexity based on the current topic and difficulty level.

Remember, your goal is to facilitate learning and critical thinking in mathematics from 3rd grade to Calculus 1.

Current topic: {topic}
Current difficulty level: {difficulty}
"""

def query_wolfram_alpha(query: str) -> str:
    base_url = "https://www.wolframalpha.com/api/v1/llm-api"
    
    # Remove square brackets and strip whitespace
    clean_query = query.strip("[]").strip()
    
    params = {
        "input": clean_query,
        "appid": os.getenv("WOLFRAM_ALPHA_APP_ID"),
    }
    try:
        response = requests.get(base_url, params=params)
        
        if response.status_code != 200:
            return f"Error querying Wolfram Alpha: Status code {response.status_code}. Response: {response.text[:200]}"
        
        result = response.text.strip()
        return result
    except Exception as e:
        return f"Error processing Wolfram Alpha response: {str(e)}"

def extract_wolfram_result(wolfram_response: str) -> str:
    extraction_prompt = f"""
    Extract only the essential mathematical result from the following Wolfram Alpha response. 
    Provide the result in LaTeX format, enclosed in double dollar signs ($$...$$), without any additional explanation or context.
    If there are multiple forms of the result, choose the simplest or most relevant one.
    Preface the result with "Correct answer:" (outside the LaTeX delimiters).

    Wolfram Alpha response:
    {wolfram_response}

    Extracted result (in LaTeX):
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts and formats mathematical results."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Error extracting result from Wolfram Alpha response."

def format_katex(text: str) -> str:
    # Replace inline math delimiters
    text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', r'$\1$', text)
    # Replace display math delimiters
    text = re.sub(r'\$\$(.+?)\$\$', r'$$\1$$', text)
    return text

def check_rate_limit(session_id: str):
    now = datetime.now()
    if session_id not in rate_limit_data:
        rate_limit_data[session_id] = {"count": 1, "reset_time": now + timedelta(days=1)}
    elif rate_limit_data[session_id]["reset_time"] < now:
        rate_limit_data[session_id] = {"count": 1, "reset_time": now + timedelta(days=1)}
    elif rate_limit_data[session_id]["count"] >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    else:
        rate_limit_data[session_id]["count"] += 1

@app.post("/start_session", response_model=SessionResponse)
async def start_session(api_key: str = Depends(get_api_key)):
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "messages": [],
        "topic": "General Math",
        "difficulty": 5  # Start at a middle difficulty
    }
    return {"session_id": session_id}

@app.post("/chat")
async def chat(query: Query, api_key: str = Depends(get_api_key)):
    if query.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    check_rate_limit(query.session_id)
    
    session = sessions[query.session_id]
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
        
        # Check if Wolfram Alpha query is needed
        if "Wolfram Alpha query:" in bot_message:
            wolfram_queries = re.findall(r"Wolfram Alpha query: (.+?)(?=\n|$)", bot_message)
            for wolfram_query in wolfram_queries:
                wolfram_result = query_wolfram_alpha(wolfram_query.strip())
                extracted_result = extract_wolfram_result(wolfram_result)
                bot_message = bot_message.replace(f"Wolfram Alpha query: {wolfram_query}", extracted_result)
        
        # Format the message with KaTeX syntax
        bot_message = format_katex(bot_message)
        
        session["messages"].append({"role": "assistant", "content": bot_message})
        
        # Adjust difficulty and topic based on the complexity of the question
        if any(word in query.message.lower() for word in ['calculus', 'derivative', 'integral', 'limit']):
            session["difficulty"] = 10
            session["topic"] = "Calculus 1"
        elif any(word in query.message.lower() for word in ['algebra', 'equation', 'polynomial', 'function']):
            session["difficulty"] = max(session["difficulty"], 7)
            session["topic"] = "Algebra"
        elif any(word in query.message.lower() for word in ['geometry', 'triangle', 'circle', 'area']):
            session["difficulty"] = max(session["difficulty"], 6)
            session["topic"] = "Geometry"
        elif any(word in query.message.lower() for word in ['fraction', 'decimal', 'percentage']):
            session["difficulty"] = max(session["difficulty"], 4)
            session["topic"] = "Fractions and Decimals"
        else:
            session["difficulty"] = max(3, session["difficulty"])  # Ensure we don't go below 3rd grade level
        
        return {"response": bot_message}
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))