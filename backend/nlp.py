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
    # ... (keep all other grade levels)
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
            input_variables=["input", "agent_scratchpad", "chat_history", "difficulty", "topic", "tools", "tool_names", "solution", "current_step"],
            template="""
You are MathBuddyBot, an advanced AI math tutor specializing in topics from 3rd grade to Calculus 1. 
Your goal is to guide students through problem-solving steps, provide hints, and validate their answers.
Do not solve the problem outright. Instead, break it down into steps and ask guiding questions.

Current difficulty level: {difficulty}
Current topic: {topic}
Current step in solution: {current_step}
Full solution: {solution}

Chat History:
{chat_history}

Current task: {input}

Follow these guidelines:
1) Break down the problem into smaller, manageable steps.
2) Ask guiding questions to lead the student towards the solution.
3) Provide hints about relevant concepts rather than giving away the answer.
4) Adjust your explanation based on the current difficulty level and topic.
5) Always encourage the student and provide positive reinforcement.
6) If the student provides a correct step or partial solution, acknowledge it and guide them to the next step.
7) If the student is stuck or provides an incorrect answer, provide a hint or ask a leading question.
8) Use the solution and current step to track the student's progress and provide appropriate guidance.

Available tools: {tool_names}
Tool details: {tools}

{agent_scratchpad}

Your response should be conversational and natural, as if you were a human tutor speaking to the student.
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
            progress = self.student_progress.get(session_id, {"topic": "Calculus 1", "difficulty": 8, "current_step": 0, "solution": None})
            
            if progress["solution"] is None:
                # Precompute the solution using Wolfram Alpha
                wolfram_tool = get_wolfram_tool()
                solution = await wolfram_tool.arun(query)
                progress["solution"] = solution
                self.student_progress[session_id] = progress
            
            response = await self.agent_executor.ainvoke(
                {
                    "input": query,
                    "difficulty": progress["difficulty"],
                    "topic": progress["topic"],
                    "tools": self.tools,
                    "tool_names": self.tool_names,
                    "solution": progress["solution"],
                    "current_step": progress["current_step"]
                }
            )
            logger.debug(f"MathTutor response: {response}")
            
            return {"solution": response['output'], "steps": []}
        except Exception as e:
            logger.error(f"Error in MathTutor: {str(e)}")
            raise

    async def process_response(self, response: str, session_id: str) -> Dict[str, Any]:
        progress = self.student_progress.get(session_id, {"topic": "Calculus 1", "difficulty": 8, "current_step": 0, "solution": None})
        
        # Use GPT to analyze the response and determine if the student has made progress
        analysis_prompt = f"""
        Student's response: {response}
        Current step: {progress['current_step']}
        Full solution: {progress['solution']}

        Analyze the student's response and determine:
        1. If the student has made progress towards the solution.
        2. If any part of their response is correct.
        3. What the next step or hint should be.

        Provide your analysis in the following format:
        Progress made: [Yes/No]
        Correct parts: [List any correct parts of the student's response]
        Next step: [Describe the next step or hint to provide]
        """

        analysis = await self.llm.agenerate([analysis_prompt])
        analysis_text = analysis.generations[0][0].text.strip()

        # Parse the analysis
        analysis_lines = analysis_text.split('\n')
        progress_made = analysis_lines[0].split(': ')[1].lower() == 'yes'
        correct_parts = analysis_lines[1].split(': ')[1]
        next_step = analysis_lines[2].split(': ')[1]

        if progress_made:
            progress["current_step"] += 1
            self.student_progress[session_id] = progress

        return {
            "progress_made": progress_made,
            "correct_parts": correct_parts,
            "next_step": next_step
        }

    async def validate_answer(self, problem: str, answer: str, session_id: str) -> Dict[str, Any]:
        progress = self.student_progress.get(session_id, {"topic": "Calculus 1", "difficulty": 8})
        
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
        
        Provide encouraging feedback on the student's answer. If the answer is incorrect, give a hint or ask a guiding question to help them find the correct answer. If the answer is correct, provide positive reinforcement and possibly suggest a more advanced aspect of the topic to explore.
        
        Your feedback should be tailored to the student's current topic and difficulty level.
        """
        
        response = await self.llm.agenerate([prompt])
        feedback = response.generations[0][0].text.strip()
        return feedback

    async def get_hint(self, problem: str, step: int, session_id: str) -> str:
        progress = self.student_progress.get(session_id, {"topic": "Calculus 1", "difficulty": 8})
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
        progress = self.student_progress.get(session_id, {"topic": "Calculus 1", "difficulty": 8})
        
        if is_correct:
            progress["difficulty"] = min(10, progress["difficulty"] + 1)
        else:
            progress["difficulty"] = max(1, progress["difficulty"] - 1)
        
        if progress["difficulty"] >= 10:
            current_grade = progress["topic"].split()[0]
            next_grade = self.get_next_grade(current_grade)
            if next_grade:
                progress["topic"] = next_grade
                progress["difficulty"] = 8
        
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