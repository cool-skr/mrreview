from typing import List, TypedDict, Annotated
import operator

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    question: str
    
    documents: List[str]
    
    generation: str

def create_agent_graph(retriever):
    """
    Creates the LangGraph agent for our Q&A system.
    """
    

    def retrieve_docs(state):
        """
        Node 1: Retrieves documents from the vector store based on the question.
        """
        print("---AGENT STEP: RETRIEVING DOCUMENTS---")
        question = state["question"]
        documents = retriever.invoke(question)
        return {"documents": documents, "question": question}

    def generate_answer(state):
        """
        Node 2: Generates an answer using the retrieved documents.
        This is where we'll eventually put a more complex "synthesis" prompt.
        """
        print("---AGENT STEP: GENERATING ANSWER---")
        question = state["question"]
        documents = state["documents"]
        
        from src.qa.retriever import RAG_PROMPT_TEMPLATE
        from src.ai.caller import get_llm
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        llm = get_llm()
        
        rag_chain = prompt | llm | StrOutputParser()
        generation = rag_chain.invoke({"context": documents, "question": question})
        
        return {"documents": documents, "question": question, "generation": generation}

    
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", retrieve_docs)
    workflow.add_node("generate", generate_answer)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    agent = workflow.compile()
    
    print("Agent graph compiled successfully.")
    return agent