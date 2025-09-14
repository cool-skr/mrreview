import os
from typing import Iterator, Set

SUPPORTED_EXTENSIONS: Set[str] = {'.py', '.js'}

IGNORE_DIRECTORIES: Set[str] = {'__pycache__', '.git', 'node_modules', 'venv'}

def find_code_files(start_path: str) -> Iterator[str]:
    """
    Recursively finds all code files with supported extensions in a given directory,
    skipping specified ignored directories.

    Args:
        start_path: The absolute path to the directory to start searching from.

    Yields:
        An iterator of absolute paths to the found code files.
    """

    if os.path.isfile(start_path):
        file_ext = os.path.splitext(start_path)[1]
        if file_ext in SUPPORTED_EXTENSIONS:
            yield start_path
        return 
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRECTORIES]
            
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                file_path = os.path.join(root, file)
                yield file_path