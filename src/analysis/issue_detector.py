import re
from tree_sitter import Tree, Node, Language
from typing import Iterator, Dict

from .models import Issue

COMPLEXITY_THRESHOLD = 10
FUNCTION_QUERIES: Dict[str, str] = {
    "python": "(function_definition) @function",
    "javascript": "[(function_declaration) (arrow_function) (method_definition)] @function"
}
COMPLEXITY_QUERIES: Dict[str, str] = {
    "python": "[(if_statement) (for_statement) (while_statement) (except_clause) (boolean_operator)] @complexity",
    "javascript": "[(if_statement) (for_statement) (while_statement) (switch_case) (catch_clause) (ternary_expression) (binary_expression operator: ['&&', '||'])] @complexity"
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
