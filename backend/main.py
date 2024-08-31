# backend/main.py

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .nlp import MathTutor
from .math_processing import process_math_query

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize MathTutor
tutor = MathTutor()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, update with specific frontend URLs in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

@app.post("/solve")
async def solve_problem(query: Query):
    try:
        logger.info(f"Received query: {query.question}")
        # Process the query using MathTutor
        result = tutor(query.question)

        # For each step, get the WolframAlpha result
        for step in result.steps:
            wolfram_result, _ = process_math_query(step['wolfram_query'])
            step['wolfram_result'] = wolfram_result

        response = {
            "problem_type": result.problem_type,
            "steps": result.steps,
            "summary": result.summary
        }
        logger.info(f"Processed query successfully: {response}")
        return response
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)