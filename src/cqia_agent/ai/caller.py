import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from typing import Optional, Dict


def get_llm():
    """Initializes and returns the ChatGroq LLM instance."""
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file.")
    model_name=os.getenv("GROQ_MODEL_NAME","openai/gpt-oss-20b")
    
    return ChatGroq(
        temperature=0, 
        model_name=model_name, 
        api_key=api_key
    )

def call_ai(prompt_template: str, context: Dict) -> Optional[str]:
    """
    Calls the configured LLM with a given prompt template and context.

    Args:
        prompt_template: A string template for the prompt.
        context: A dictionary containing values to format the prompt.
                 For example, {"code_snippet": "def hello()..."}

    Returns:
        The string response from the AI, or None if an error occurs.
    """
    try:
        llm = get_llm()
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        chain = prompt | llm
        
        response = chain.invoke(context)
        
        return response.content
    except Exception as e:
        print(f"An error occurred while calling the AI: {e}")
        return None

if __name__ == '__main__':
    print("Testing AI Caller...")
    from dotenv import load_dotenv
    load_dotenv()

    test_prompt = "Explain why the following Python code is simple: {code_snippet}"
    test_context = {"code_snippet": "x = 1\ny = x + 1\nprint(y)"}
    
    ai_response = call_ai(test_prompt, test_context)
    
    if ai_response:
        print("Successfully received response from AI:")
        print(ai_response)
    else:
        print("Failed to get response from AI.")
