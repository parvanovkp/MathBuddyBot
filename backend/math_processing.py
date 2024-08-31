import os
import aiohttp
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get WolframAlpha App ID
WOLFRAM_ALPHA_APP_ID = os.getenv("WOLFRAM_ALPHA_APP_ID")

if not WOLFRAM_ALPHA_APP_ID:
    raise ValueError("WOLFRAM_ALPHA_APP_ID not found in environment variables")

async def process_math_query(query: str):
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                'input': query,
                'format': 'plaintext',
                'output': 'JSON',
                'appid': WOLFRAM_ALPHA_APP_ID
            }
            async with session.get('http://api.wolframalpha.com/v2/query', params=params) as response:
                if response.status != 200:
                    raise ValueError(f"WolframAlpha API returned status code {response.status}")
                data = await response.json()

            # Process the JSON response to extract the result
            result = "Result not found"
            for pod in data.get('queryresult', {}).get('pods', []):
                if pod.get('title') in ['Result', 'Solution', 'Derivative', 'Indefinite integral', 'Numeric result', 'Rate']:
                    result = pod.get('subpods', [{}])[0].get('plaintext', 'Result not found')
                    break
            
            if result == "Result not found":
                # If no specific result found, look for other relevant information
                relevant_titles = ['Decimal approximation', 'Exact result', 'Simplified result', 'Input interpretation']
                for pod in data.get('queryresult', {}).get('pods', []):
                    if pod.get('title') in relevant_titles:
                        result = pod.get('subpods', [{}])[0].get('plaintext', 'Result not found')
                        break

            logger.debug(f"WolframAlpha result for query '{query}': {result}")
            return result
    except Exception as e:
        logger.error(f"Error processing with WolframAlpha: {str(e)}")
        raise