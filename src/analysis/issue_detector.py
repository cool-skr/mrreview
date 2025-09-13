from tree_sitter import Tree, Node, Language
from typing import Iterator, Dict

from .models import Issue

COMPLEXITY_THRESHOLD = 10

FUNCTION_QUERIES: Dict[str, str] = {
    "python": """
    (function_definition) @function
    """,
    "javascript": """
    [
      (function_declaration)
      (arrow_function)
      (method_definition)
    ] @function
    """
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


def detect_complexity_issues(
    tree: Tree, language: Language, file_path: str, file_content: bytes, lang_name: str
) -> Iterator[Issue]:
    """
    Analyzes an AST to find functions with high cyclomatic complexity.
    """
    func_query_str = FUNCTION_QUERIES.get(lang_name)
    complexity_query_str = COMPLEXITY_QUERIES.get(lang_name)
    if not func_query_str or not complexity_query_str:
        return

    func_query = language.query(func_query_str)
    complexity_query = language.query(complexity_query_str)

    function_captures = func_query.captures(tree.root_node)

    for node, _ in function_captures:
        name_node = node.child_by_field_name("name")
        if name_node:
            func_name = name_node.text.decode('utf8')
        else:
            func_name = "anonymous"

        decision_points = complexity_query.captures(node)
        complexity_score = 1 + len(decision_points)

        if complexity_score > COMPLEXITY_THRESHOLD:
            line_number = node.start_point[0] + 1
            column_number = node.start_point[1] + 1
            
            yield Issue(
                file_path=file_path,
                line_number=line_number,
                column_number=column_number,
                code="complexity",
                message=f"Function '{func_name}' has a high cyclomatic complexity of {complexity_score} (threshold is {COMPLEXITY_THRESHOLD}). Consider refactoring.",
                severity="HIGH"
            )