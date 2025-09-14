import re
from typing import Optional
from src.analysis.models import Issue
from src.ai.caller import call_ai

ENRICHMENT_PROMPT_TEMPLATE = """
You are an expert code reviewer. A static analysis tool has found the following issue:
- Issue Type: {issue_code}
- File: {file_path}
- Line: {line_number}
- Original Message: {issue_message}

Here is the relevant code snippet from the file:

{code_snippet}


Your task is to enrich this finding. Please provide a response in two parts, using the exact markers "[EXPLANATION]" and "[SUGGESTION]".

1.  **[EXPLANATION]**: In a friendly and educational tone, explain *why* this is an issue. Go beyond the original message. Explain the potential impact on maintainability, security, or performance.
2.  **[SUGGESTION]**: Provide a clear, actionable suggestion for how to fix the issue. If possible, include a small, corrected code snippet.
"""

def _extract_code_context(file_content: str, line_number: int, context_lines: int = 5) -> str:
    """Extracts a snippet of code centered around a specific line number."""
    lines = file_content.splitlines()
    start = max(0, line_number - context_lines - 1)
    end = min(len(lines), line_number + context_lines)
    
    snippet_lines = lines[start:end]
    return "\n".join(f"{i+1:4d}| {line}" for i, line in enumerate(snippet_lines, start=start))

def _parse_ai_response(response: str) -> tuple[Optional[str], Optional[str]]:
    """Parses the AI's response to extract the explanation and suggestion."""
    explanation_match = re.search(r"[EXPLANATION]\s*(.*?)\s*[SUGGESTION]", response, re.DOTALL)
    suggestion_match = re.search(r"[SUGGESTION]\s*(.*)", response, re.DOTALL)

    explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided."
    suggestion = suggestion_match.group(1).strip() if suggestion_match else "No suggestion provided."
    
    return explanation, suggestion

def enrich_issue(issue: Issue, file_content_str: str) -> Issue:
    """
    Uses an LLM to enrich a given issue with a detailed explanation and suggestion.
    """
    code_snippet = _extract_code_context(file_content_str, issue.line_number)
    
    context = {
        "issue_code": issue.code,
        "file_path": issue.file_path,
        "line_number": issue.line_number,
        "issue_message": issue.message,
        "code_snippet": code_snippet,
    }
    
    ai_response = call_ai(ENRICHMENT_PROMPT_TEMPLATE, context)
    
    if ai_response:
        explanation, suggestion = _parse_ai_response(ai_response)
        issue.ai_explanation = explanation
        issue.ai_suggestion = suggestion
        
    return issue