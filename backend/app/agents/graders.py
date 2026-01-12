from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from app.core.config import settings

llm = ChatOpenAI(model=settings.TOOL_MODEL, base_url=settings.TOOL_API_BASE, api_key=settings.OPENAI_API_KEY, temperature=0)


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")

structured_llm_grader = llm.with_structured_output(GradeDocuments)

system_prompt = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader

class GradeHallucinations(BaseModel):
    """Binary score for hallucination check in generation documents."""
    binary_score: str = Field(description="Answer is grounded in the facts, 'yes' or 'no'")

structured_llm_hallucination_grader = llm.with_structured_output(GradeHallucinations)

hallucination_system_prompt = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. 

Your goal is to detect factual contradictions or invented information.
- Grade 'yes' if the answer is a summary, rephrasing, or direct extraction of the facts.
- Grade 'no' ONLY if the LLM makes a specific claim (like a number, date, or name) that is explicitly absent or contradicted by the facts.

Give a binary score 'yes' or 'no'."""

hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", hallucination_system_prompt),
        ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
    ]
)

hallucination_grader = hallucination_prompt | structured_llm_hallucination_grader

class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""
    binary_score: str = Field(description="Answer addresses the question, 'yes' or 'no'")

structured_llm_answer_grader = llm.with_structured_output(GradeAnswer)

answer_system_prompt = """
You are a grader assessing whether an answer addresses the user's question.

- Grade 'yes' if the answer provides the requested information OR if it clearly explains that the information is not available in the provided documents.
- Grade 'yes' if the answer lists relevant resources, papers, or links requested by the user.
- Grade 'no' only if the answer is completely irrelevant or ignores the question.

Give a binary score 'yes' or 'no'.
"""

answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", answer_system_prompt),
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
    ]
)

answer_grader = answer_prompt | structured_llm_answer_grader
