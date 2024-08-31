import logging
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

@app.post("/solve")
async def solve_problem(query: Query):
    start_time = time.time()
    try:
        logger.info(f"Received query: {query.question}")
        
        result = await tutor.solve(query.question)
        logger.debug(f"MathTutor result: {result}")

        logger.info(f"Processed query successfully: {result}")
        end_time = time.time()
        logger.info(f"Total processing time: {end_time - start_time:.2f} seconds")
        return result
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        end_time = time.time()
        logger.info(f"Total processing time (with error): {end_time - start_time:.2f} seconds")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)