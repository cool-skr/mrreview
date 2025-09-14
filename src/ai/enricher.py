import re
from typing import Optional, Dict
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

1.  **[EXPLANATION]**: In a friendly and educational tone, explain *why* this is an issue.
2.  **[SUGGESTION]**: Provide a clear, actionable suggestion for how to fix the issue.
Other than that remove any extra special asteriks (*)
Do not have duplicates in content
"""

def _extract_code_context(file_content: str, line_number: int, context_lines: int = 5) -> str:
    lines = file_content.splitlines()
    start = max(0, line_number - context_lines - 1)
    end = min(len(lines), line_number + context_lines)
    snippet_lines = lines[start:end]
    return "\n".join(f"{i+1:4d}| {line}" for i, line in enumerate(snippet_lines, start=start))

def _parse_ai_response(response: str) -> tuple[Optional[str], Optional[str]]:
    """A more robust parser for the AI's response."""
    exp_marker = "[explanation]"
    sug_marker = "[suggestion]"
    response_lower = response.lower()
    
    exp_start = response_lower.find(exp_marker)
    sug_start = response_lower.find(sug_marker)

    explanation = None
    suggestion = None

    if exp_start != -1:
        exp_content_start = exp_start + len(exp_marker)
        exp_content_end = sug_start if sug_start > exp_start else len(response)
        explanation = response[exp_content_start:exp_content_end].strip()

    if sug_start != -1:
        sug_content_start = sug_start + len(sug_marker)
        sug_content_end = exp_start if exp_start > sug_start else len(response)
        suggestion = response[sug_content_start:sug_content_end].strip()

    if suggestion and not explanation:
        explanation = response[:sug_start].strip()
    if explanation and not suggestion:
        suggestion = response[exp_start + len(exp_marker):].strip()

    return explanation, suggestion

def enrich_issue(issue: Issue, file_content_str: str) -> Issue:
    code_snippet = _extract_code_context(file_content_str, issue.line_number)
    context = { "issue_code": issue.code, "file_path": issue.file_path, "line_number": issue.line_number, "issue_message": issue.message, "code_snippet": code_snippet }
    ai_response = call_ai(ENRICHMENT_PROMPT_TEMPLATE, context)
    if ai_response:
        explanation, suggestion = _parse_ai_response(ai_response)
        issue.ai_explanation = explanation
        issue.ai_suggestion = suggestion
    return issue