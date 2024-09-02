import os
from dotenv import load_dotenv
import logging
import time
import uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ["OPENAI_API_KEY", "WOLFRAM_ALPHA_APP_ID"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"{var} not found in environment variables")

from .nlp import tutor

# Setup logging
logging.basicConfig(level=logging.DEBUG)
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
    question: str

class SessionResponse(BaseModel):
    session_id: str

class StepResponse(BaseModel):
    step: str
    is_final: bool

class AnswerValidation(BaseModel):
    answer: str

class HintRequest(BaseModel):
    session_id: str

# In-memory session storage (replace with a database in production)
sessions: Dict[str, Dict[str, Any]] = {}

def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.post("/start_session", response_model=SessionResponse)
async def start_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {"problem": None, "steps": [], "current_step": 0}
    logger.info(f"Started new session: {session_id}")
    return {"session_id": session_id}

@app.post("/solve")
async def solve_problem(query: Query, session_id: str):
    start_time = time.time()
    try:
        logger.info(f"Received query for session {session_id}: {query.question}")
        session = get_session(session_id)
        
        result = await tutor.solve(query.question, session_id)
        logger.debug(f"MathTutor result: {result}")

        # Update session with problem and steps
        session["problem"] = query.question
        session["steps"] = result.get("steps", [])
        session["current_step"] = 0

        logger.info(f"Processed query successfully: {result}")
        end_time = time.time()
        logger.info(f"Total processing time: {end_time - start_time:.2f} seconds")
        return result
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        end_time = time.time()
        logger.info(f"Total processing time (with error): {end_time - start_time:.2f} seconds")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/next_step", response_model=StepResponse)
async def get_next_step(session_id: str):
    session = get_session(session_id)
    if session["current_step"] >= len(session["steps"]):
        return {"step": "Problem solving complete", "is_final": True}
    
    step = session["steps"][session["current_step"]]
    session["current_step"] += 1
    return {"step": step, "is_final": session["current_step"] >= len(session["steps"])}

@app.post("/validate_answer")
async def validate_answer(validation: AnswerValidation, session_id: str):
    session = get_session(session_id)
    result = await tutor.validate_answer(session["problem"], validation.answer, session_id)
    return {"is_correct": result["is_correct"], "feedback": result["feedback"]}

@app.post("/get_hint", response_model=Dict[str, str])
async def get_hint(hint_request: HintRequest):
    session = get_session(hint_request.session_id)
    hint = await tutor.get_hint(session["problem"], session["current_step"], hint_request.session_id)
    return {"hint": hint}

@app.get("/get_progress")
async def get_progress(session_id: str):
    progress = tutor.student_progress.get(session_id, {"topic": "3rd Grade", "difficulty": 1})
    return progress

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)