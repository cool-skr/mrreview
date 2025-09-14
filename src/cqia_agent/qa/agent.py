from typing import List, TypedDict, Annotated
import operator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langgraph.graph import StateGraph, END
from cqia_agent.ai.caller import get_llm

DECOMPOSE_PROMPT_TEMPLATE = """
You are a query decomposition expert. Your task is to break down a user's complex question about a codebase into a list of simpler, self-contained sub-questions. These sub-questions will be used to retrieve relevant documents from a vector database.
- Generate 2-3 sub-questions at most.
- Each sub-question should be a simple string.
- Return ONLY a JSON object with a single key "sub_questions" containing a list of these strings.
User Question: "{question}"
JSON Output:
"""
SYNTHESIZE_PROMPT_TEMPLATE = """
You are an expert code analysis assistant. You have been provided with context retrieved for several sub-questions derived from the user's original, complex question.
Your task is to synthesize this information into a single, coherent, and well-formatted answer to the user's original question.
Use the context to provide detailed explanations, code snippets, and actionable advice. Keep it concise if felt necessary but keep it human.Format your response using GitHub-flavored Markdown.
Original Question: {question}
Retrieved Context:
---
{context}
---
Final Answer:
"""

class AgentState(TypedDict):
    question: str
    sub_questions: List[str]
    documents: Annotated[list, operator.add]
    generation: str


def decompose_question_node(state):
    print("---AGENT STEP: DECOMPOSING QUESTION---")
    question = state["question"]
    prompt = ChatPromptTemplate.from_template(DECOMPOSE_PROMPT_TEMPLATE)
    llm = get_llm()
    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke({"question": question})
    return {"sub_questions": result['sub_questions'], "documents": []}

def retrieve_docs_node(state, retriever):
    print("---AGENT STEP: RETRIEVING DOCUMENTS---")
    sub_question = state["sub_questions"][0]
    remaining_questions = state["sub_questions"][1:]
    documents = retriever.invoke(sub_question)
    return {"documents": documents, "sub_questions": remaining_questions}

def synthesize_answer_node(state):
    print("---AGENT STEP: SYNTHESIZING FINAL ANSWER---")
    question = state["question"]
    documents = state["documents"]
    context_str = "\n\n".join([doc.page_content for doc in documents])
    prompt = ChatPromptTemplate.from_template(SYNTHESIZE_PROMPT_TEMPLATE)
    llm = get_llm()
    chain = prompt | llm | StrOutputParser()
    generation = chain.invoke({"context": context_str, "question": question})
    return {"generation": generation}

def router_node(state):
    print("---AGENT STEP: ROUTING---")
    if len(state["sub_questions"]) > 0:
        return "retrieve"
    else:
        return "synthesize"

def create_agent_graph(retriever):
    workflow = StateGraph(AgentState)
    workflow.add_node("decompose", decompose_question_node)
    workflow.add_node("retrieve", lambda state: retrieve_docs_node(state, retriever))
    workflow.add_node("synthesize", synthesize_answer_node)
    workflow.set_entry_point("decompose")
    workflow.add_conditional_edges(
        "decompose",
        router_node,
        {
            "retrieve": "retrieve",
            "synthesize": "synthesize"
        }
    )
    workflow.add_conditional_edges(
        "retrieve",
        router_node,
        {
            "retrieve": "retrieve",
            "synthesize": "synthesize"
        }
    )
    workflow.add_edge("synthesize", END)
    agent = workflow.compile()
    print("Multi-context agent graph compiled successfully.")
    return agent