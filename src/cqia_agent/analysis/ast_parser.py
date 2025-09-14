import os
from typing import Optional, Tuple

from tree_sitter import Tree, Language, Parser
from tree_sitter_languages import get_language

LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
}

def parse_file_to_ast(file_path: str) -> Optional[Tuple[Tree, Language]]:
    """
    Reads a file and parses it into a tree-sitter AST Tree.

    Args:
        file_path: The absolute path to the code file.

    Returns:
        A tuple of (Tree, Language) if parsing is successful, otherwise None.
    """
    file_ext = os.path.splitext(file_path)[1]
    lang_name = LANG_MAP.get(file_ext)

    if not lang_name:
        return None

    try:
        with open(file_path, "rb") as f:
            content_bytes = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

    language = get_language(lang_name)
    
    parser = Parser()
    
    parser.set_language(language)

    tree = parser.parse(content_bytes)
    
    return tree, language