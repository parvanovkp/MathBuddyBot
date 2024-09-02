import os
import logging
from typing import List, Dict, Any, Union
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from .math_processing import get_wolfram_tool, validate_answer as wolfram_validate_answer

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Math topics hierarchy
MATH_TOPICS = {
    "3rd Grade": [
        "Basic Arithmetic", "Number Sense", "Fractions", "Measurement and Data", "Geometry"
    ],
    "4th Grade": [
        "Multi-digit Arithmetic", "Fractions and Decimals", "Measurement and Data", "Geometry"
    ],
    "5th Grade": [
        "Operations with Fractions", "Decimals", "Volume", "Coordinate Plane"
    ],
    "6th Grade": [
        "Ratios and Proportions", "Expressions and Equations", "Geometry", "Statistics"
    ],
    "7th Grade": [
        "Rational Numbers", "Algebraic Expressions", "Geometry", "Probability"
    ],
    "8th Grade": [
        "Linear Equations", "Functions", "Geometry", "Statistics"
    ],
    "Algebra I": [
        "Solving Equations", "Graphing Functions", "Polynomials", "Quadratic Equations"
    ],
    "Geometry": [
        "Congruence", "Similarity", "Right Triangles", "Circles", "Coordinate Geometry"
    ],
    "Algebra II": [
        "Complex Numbers", "Polynomial Functions", "Rational Functions", "Exponential and Logarithmic Functions"
    ],
    "Pre-Calculus": [
        "Trigonometry", "Vectors", "Matrices", "Conic Sections", "Limits"
    ],
    "Calculus 1": [
        "Limits and Continuity", "Derivatives", "Applications of Derivatives", "Integrals", "Applications of Integrals"
    ]
}

class MathTutor:
    def __init__(self):
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)
        self.memory = ConversationBufferMemory(input_key="input", memory_key="chat_history")
        self.tools = [get_wolfram_tool()]
        self.tool_names = [tool.name for tool in self.tools]
        self.prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad", "chat_history", "difficulty", "topic", "tools", "tool_names"],
            template="""
You are MathBuddyBot, an advanced AI math tutor specializing in topics from 3rd grade to Calculus 1. 
Your goal is to guide students through problem-solving steps, provide hints, and validate their answers.

Current difficulty level: {difficulty}
Current topic: {topic}

Chat History:
{chat_history}

Current task: {input}

Think step-by-step about how to approach this task:
1) Determine if the task requires mathematical computation or explanation.
2) If computation is needed, consider using the Wolfram Alpha tool.
3) If explanation is needed, formulate a clear and concise response.
4) Always provide step-by-step guidance and explanations.
5) Break down the solution into clear, numbered steps.
6) Adjust your explanation based on the current difficulty level and topic.

Available tools: {tool_names}
Tool details: {tools}

{agent_scratchpad}

Your response should be in the following format:
Thought: Your step-by-step reasoning
Action: The action to take (either "Wolfram Alpha" or "Final Answer")
Action Input: The input for the action
Observation: The result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: The final answer to the original input question, including numbered steps for the solution
"""
        )
        
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            memory=self.memory
        )
        self.student_progress = {}

    async def solve(self, query: str, session_id: str) -> Dict[str, Any]:
        logger.info(f"MathTutor processing query for session {session_id}: {query}")
        try:
            progress = self.student_progress.get(session_id, {"topic": "3rd Grade", "difficulty": 1})
            
            response = await self.agent_executor.ainvoke(
                {
                    "input": query,
                    "difficulty": progress["difficulty"],
                    "topic": progress["topic"],
                    "tools": self.tools,
                    "tool_names": self.tool_names
                }
            )
            logger.debug(f"MathTutor response: {response}")
            
            steps = self.extract_steps(response['output'])
            
            self.update_progress(session_id, steps)
            
            return {"solution": response['output'], "steps": steps}
        except Exception as e:
            logger.error(f"Error in MathTutor: {str(e)}")
            raise

    def extract_steps(self, response: str) -> List[str]:
        steps = []
        lines = response.split('\n')
        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                steps.append(line.strip())
        return steps

    async def validate_answer(self, problem: str, answer: str, session_id: str) -> Dict[str, Any]:
        progress = self.student_progress.get(session_id, {"topic": "3rd Grade", "difficulty": 1})
        
        wolfram_result = await wolfram_validate_answer(problem, answer)
        
        gpt_feedback = await self.get_gpt_feedback(problem, answer, wolfram_result["is_correct"], progress)
        
        result = {
            "is_correct": wolfram_result["is_correct"],
            "feedback": gpt_feedback
        }
        
        self.update_progress(session_id, [], result["is_correct"])
        
        return result

    async def get_gpt_feedback(self, problem: str, answer: str, is_correct: bool, progress: Dict[str, Any]) -> str:
        prompt = f"""
        Problem: {problem}
        Student's answer: {answer}
        Is the answer correct: {"Yes" if is_correct else "No"}
        Current topic: {progress['topic']}
        Current difficulty: {progress['difficulty']}
        
        Provide detailed feedback on the student's answer. If the answer is incorrect, explain why and provide guidance on how to approach the problem correctly. If the answer is correct, provide positive reinforcement and possibly suggest a more advanced aspect of the topic to explore.
        
        Your feedback should be encouraging and tailored to the student's current topic and difficulty level.
        """
        
        response = await self.llm.agenerate([prompt])
        feedback = response.generations[0][0].text.strip()
        return feedback

    async def get_hint(self, problem: str, step: int, session_id: str) -> str:
        progress = self.student_progress.get(session_id, {"topic": "3rd Grade", "difficulty": 1})
        prompt = f"""
        For the problem: {problem}
        Provide a hint for step {step + 1} of the solution. 
        The hint should guide the student towards the next step without giving away the full answer.
        
        Current topic: {progress['topic']}
        Current difficulty: {progress['difficulty']}
        
        Adjust your hint based on the current topic and difficulty level.
        """
        
        response = await self.llm.agenerate([prompt])
        hint = response.generations[0][0].text.strip()
        
        return hint

    def update_progress(self, session_id: str, steps: List[str], is_correct: bool = True):
        progress = self.student_progress.get(session_id, {"topic": "3rd Grade", "difficulty": 1})
        
        if is_correct:
            progress["difficulty"] = min(10, progress["difficulty"] + 1)
        else:
            progress["difficulty"] = max(1, progress["difficulty"] - 1)
        
        if progress["difficulty"] >= 8:
            current_grade = progress["topic"].split()[0]
            next_grade = self.get_next_grade(current_grade)
            if next_grade:
                progress["topic"] = next_grade
                progress["difficulty"] = 1
        
        self.student_progress[session_id] = progress

    def get_next_grade(self, current_grade: str) -> str:
        grades = list(MATH_TOPICS.keys())
        try:
            current_index = grades.index(current_grade)
            if current_index < len(grades) - 1:
                return grades[current_index + 1]
        except ValueError:
            pass
        return ""

    def get_prerequisites(self, topic: str) -> List[str]:
        for grade, topics in MATH_TOPICS.items():
            if topic in topics:
                index = list(MATH_TOPICS.keys()).index(grade)
                if index > 0:
                    return MATH_TOPICS[list(MATH_TOPICS.keys())[index - 1]]
        return []

# Initialize MathTutor
tutor = MathTutor()