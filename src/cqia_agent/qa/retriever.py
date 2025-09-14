from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from cqia_agent.ai.caller import get_llm

RAG_PROMPT_TEMPLATE = """
You are an expert code analysis assistant. A user is asking a question about a codebase.
Answer the user's question based *only* on the provided context.

**IMPORTANT FORMATTING RULES:**
- Structure your response with the following sections, using these exact markers:
  [TITLE]: A short, descriptive title for your answer.
  [SUMMARY]: A one or two-sentence summary of the answer.
  [RESPONSE]: The full answer, formatted in standard GitHub-flavored Markdown. You can include code blocks, bullet points, and bold text.

Context:
{context}

Question:
{question}
"""

def create_rag_chain(vector_store: FAISS):
    """
    Creates the full RAG (Retrieval-Augmented Generation) chain.
    """
    retriever = vector_store.as_retriever()
    prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    llm = get_llm()

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain