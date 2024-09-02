import os
import aiohttp
import logging
from dotenv import load_dotenv
from langchain_community.utilities import WolframAlphaAPIWrapper
from langchain.agents import Tool
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get WolframAlpha App ID
WOLFRAM_ALPHA_APP_ID = os.getenv("WOLFRAM_ALPHA_APP_ID")

if not WOLFRAM_ALPHA_APP_ID:
    raise ValueError("WOLFRAM_ALPHA_APP_ID not found in environment variables")

# Initialize Wolfram Alpha wrapper
wolfram = WolframAlphaAPIWrapper(wolfram_alpha_appid=WOLFRAM_ALPHA_APP_ID)

# Create a LangChain Tool for Wolfram Alpha
wolfram_tool = Tool(
    name="Wolfram Alpha",
    func=wolfram.run,
    description="Useful for getting precise mathematical computations and solutions."
)

async def process_math_query(query: str) -> Dict[str, Any]:
    try:
        result = await wolfram.arun(query)
        logger.debug(f"WolframAlpha result for query '{query}': {result}")
        return parse_wolfram_result(result)
    except Exception as e:
        logger.error(f"Error processing with WolframAlpha: {str(e)}")
        raise

def parse_wolfram_result(result: str) -> Dict[str, Any]:
    # Parse the result string into a structured format
    lines = result.split('\n')
    parsed_result = {
        "input_interpretation": "",
        "result": "",
        "steps": [],
        "additional_info": {}
    }

    current_section = ""
    for line in lines:
        if line.startswith("Input interpretation:"):
            current_section = "input_interpretation"
            parsed_result["input_interpretation"] = line.split(":", 1)[1].strip()
        elif line.startswith("Result:"):
            current_section = "result"
            parsed_result["result"] = line.split(":", 1)[1].strip()
        elif line.startswith("Step"):
            current_section = "steps"
            parsed_result["steps"].append(line.strip())
        else:
            if ":" in line:
                key, value = line.split(":", 1)
                parsed_result["additional_info"][key.strip()] = value.strip()
            elif current_section == "steps":
                parsed_result["steps"].append(line.strip())

    return parsed_result

async def validate_answer(problem: str, answer: str) -> Dict[str, Any]:
    query = f"Is {answer} the correct answer to {problem}?"
    result = await process_math_query(query)
    is_correct = "yes" in result["result"].lower() or "correct" in result["result"].lower()
    return {
        "is_correct": is_correct,
        "feedback": result["result"]
    }

def get_wolfram_tool() -> Tool:
    return wolfram_tool