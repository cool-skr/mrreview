import os
from typing import List, Dict
from rich.progress import track
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_PATH = os.path.join(os.getcwd(), 'vector_db_store')

def create_vector_store(file_paths: List[str], issues_summary: str):
    """
    Creates a FAISS vector store from a list of code files and an issues summary.
    
    Args:
        file_paths: A list of paths to the code files to be indexed.
        issues_summary: A string containing the formatted report of all found issues.
    """
    print("Creating vector store for Q&A...")
    
    documents = []
    for file_path in track(file_path, description="[cyan]Ingesting files...[/cyan]"):
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents.extend(loader.load())
        except Exception as e:
            print(f"Warning: Could not load file {file_path}. Skipping. Error: {e}")
            
    if issues_summary:
        from langchain_core.documents import Document
        summary_doc = Document(page_content=issues_summary, metadata={"source": "analysis_summary.md"})
        documents.append(summary_doc)
        
    if not documents:
        print("No documents were loaded to create the vector store.")
        return

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    
    print("Loading embedding model (may download on first run)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print(f"Creating and saving vector store at: {DB_PATH}")
    db = FAISS.from_documents(docs, embeddings)
    db.save_local(DB_PATH)
    print("Vector store created successfully.")