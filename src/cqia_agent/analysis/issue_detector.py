import re
import subprocess
import json
from tree_sitter import Tree, Node, Language
from typing import Iterator, Dict

from .models import Issue
from cqia_agent.ai.caller import call_ai 

def run_eslint_detector(file_path: str) -> Iterator[Issue]:
    """
    Runs the ESLint scanner on a JavaScript file and yields issues.
    """
    if not file_path.endswith('.js'):
        return

    command = ["npx", "eslint", "-f", "json", file_path]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, shell=True)
        
        if result.stdout:
            data = json.loads(result.stdout)
            if not data:
                return

            file_results = data[0]
            for issue in file_results.get("messages", []):
                severity_map = {1: "MEDIUM", 2: "HIGH"}
                
                yield Issue(
                    file_path=file_results.get("filePath"),
                    line_number=issue.get("line"),
                    column_number=issue.get("column"),
                    code=f"eslint:{issue.get('ruleId')}",
                    message=issue.get("message"),
                    severity=severity_map.get(issue.get("severity"), "LOW")
                )
    except FileNotFoundError:
        print("Warning: 'npx' command not found. Is Node.js/npm installed correctly?")
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Failed to parse ESLint output for {file_path}. Error: {e}")

def run_bandit_detector(file_path: str) -> Iterator[Issue]:
    """
    Runs the Bandit security scanner on a Python file and yields issues.
    """
    if not file_path.endswith('.py'):
        return

    command = ["bandit", "-f", "json", file_path]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode > 1:
            print(f"Warning: Bandit encountered a fatal error on {file_path}. Error: {result.stderr}")
            return

        if not result.stdout:
            return

        data = json.loads(result.stdout)
        
        for issue in data.get("results", []):
            severity_map = {
                "LOW": "LOW",
                "MEDIUM": "MEDIUM",
                "HIGH": "HIGH"
            }
            
            yield Issue(
                file_path=issue.get("filename"),
                line_number=issue.get("line_number"),
                column_number=issue.get("col_offset"),
                code=f"bandit:{issue.get('test_id')}",
                message=issue.get("issue_text"),
                severity=severity_map.get(issue.get("issue_severity"), "LOW")
            )

    except FileNotFoundError:
        print("Warning: 'bandit' command not found. Is it installed in the environment?")
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Failed to parse Bandit output for {file_path}. Error: {e}")

COMPLEXITY_THRESHOLD = 10
FUNCTION_QUERIES: Dict[str, str] = {
    "python": "(function_definition) @function",
    "javascript": "[(function_declaration) (arrow_function) (method_definition)] @function"
}
COMPLEXITY_QUERIES: Dict[str, str] = {
    "python": """
    [
      (if_statement)
      (for_statement)
      (while_statement)
      (except_clause)
      (boolean_operator)
    ] @complexity
    """,
    "javascript": """
    [
      (if_statement)
      (for_statement)
      (while_statement)
      (switch_case)
      (catch_clause)
      (ternary_expression)
      (binary_expression operator: "&&")
      (binary_expression operator: "||")
    ] @complexity
    """
}

def detect_complexity_issues(tree: Tree, language: Language, file_path: str, file_content: bytes, lang_name: str) -> Iterator[Issue]:
    func_query_str = FUNCTION_QUERIES.get(lang_name)
    complexity_query_str = COMPLEXITY_QUERIES.get(lang_name)
    if not func_query_str or not complexity_query_str:
        return
    func_query = language.query(func_query_str)
    complexity_query = language.query(complexity_query_str)
    function_captures = func_query.captures(tree.root_node)
    for node, _ in function_captures:
        name_node = node.child_by_field_name("name")
        func_name = name_node.text.decode('utf8') if name_node else "anonymous"
        decision_points = complexity_query.captures(node)
        complexity_score = 1 + len(decision_points)
        if complexity_score > COMPLEXITY_THRESHOLD:
            yield Issue(
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1] + 1,
                code="complexity",
                message=f"Function '{func_name}' has a high cyclomatic complexity of {complexity_score} (threshold is {COMPLEXITY_THRESHOLD}). Consider refactoring.",
                severity="HIGH"
            )

def detect_missing_documentation(tree: Tree, language: Language, file_path: str, file_content: bytes, lang_name: str) -> Iterator[Issue]:
    """Analyzes an AST to find functions that are missing docstrings."""
    func_query_str = FUNCTION_QUERIES.get(lang_name)
    if not func_query_str:
        return

    func_query = language.query(func_query_str)
    function_captures = func_query.captures(tree.root_node)

    for node, _ in function_captures:
        if lang_name == 'python':
            body_node = node.child_by_field_name('body')
            if not body_node or not body_node.children or body_node.children[0].type != 'expression_statement' or body_node.children[0].children[0].type != 'string':
                name_node = node.child_by_field_name("name")
                func_name = name_node.text.decode('utf8') if name_node else "anonymous"
                yield Issue(
                    file_path=file_path,
                    line_number=node.start_point[0] + 1,
                    column_number=node.start_point[1] + 1,
                    code="documentation",
                    message=f"Function '{func_name}' is missing a docstring.",
                    severity="MEDIUM"
                )
        elif lang_name == 'javascript':
            if node.prev_named_sibling is None or node.prev_named_sibling.type != 'comment':
                name_node = node.child_by_field_name("name")
                func_name = name_node.text.decode('utf8') if name_node else "anonymous"
                yield Issue(
                    file_path=file_path,
                    line_number=node.start_point[0] + 1,
                    column_number=node.start_point[1] + 1,
                    code="documentation",
                    message=f"Function '{func_name}' is missing a JSDoc comment.",
                    severity="MEDIUM"
                )

SECRET_PATTERNS = [
    re.compile(b'(api_key|secret_key|password|token)[\s]*[=:]\s*[\'\"][a-zA-Z0-9_.-]{16,}[\'\"]', re.IGNORECASE),
    re.compile(b'-----BEGIN RSA PRIVATE KEY-----', re.IGNORECASE)
]

def detect_hardcoded_secrets(file_path: str, file_content: bytes) -> Iterator[Issue]:
    """Scans raw file content for patterns that look like hardcoded secrets."""
    for line_num, line in enumerate(file_content.splitlines(), 1):
        for pattern in SECRET_PATTERNS:
            if pattern.search(line):
                yield Issue(
                    file_path=file_path,
                    line_number=line_num,
                    column_number=0,
                    code="security",
                    message="Potential hardcoded secret found. Do not commit credentials to source control.",
                    severity="CRITICAL"
                )

PERFORMANCE_PROMPT_TEMPLATE = """
You are a senior Python performance optimization expert. Analyze the following code snippet which contains a loop.
Identify common performance anti-patterns such as:
- Inefficient string concatenation inside the loop.
- Redundant calculations or API calls inside the loop that could be moved outside.
- Using inefficient data structures for lookups (e.g., list instead of set).

If you find a clear and definite anti-pattern, respond with the single word "Yes:", followed by your explanation and suggestion.
If the code seems acceptable or the optimization is trivial, respond with the single word "No."

Code Snippet:
```python
{code_snippet}

"""

LOOP_QUERIES: Dict[str, str] = {
"python": "[(for_statement) (while_statement)] @loop",
"javascript": "[(for_statement) (while_statement)] @loop"
}

def detect_performance_issues_with_ai(tree: Tree, language: Language, file_path: str, file_content: bytes, lang_name: str) -> Iterator[Issue]:
    """
    Uses an LLM to analyze loops for common performance anti-patterns.
    """
    loop_query_str = LOOP_QUERIES.get(lang_name)
    if not loop_query_str:
        return

    loop_query = language.query(loop_query_str)
    loop_captures = loop_query.captures(tree.root_node)

    for node, _ in loop_captures:
        code_snippet = file_content[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
        
        context = {"code_snippet": code_snippet}
        ai_response = call_ai(PERFORMANCE_PROMPT_TEMPLATE, context)

        if ai_response and ai_response.strip().lower().startswith("yes:"):
            explanation = ai_response.strip()[4:].strip()
            
            yield Issue(
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1] + 1,
                code="performance",
                message=f"Potential performance anti-pattern detected in a loop.",
                severity="LOW",
                ai_explanation=explanation, 
                ai_suggestion="Review the AI explanation for optimization suggestions."
            )