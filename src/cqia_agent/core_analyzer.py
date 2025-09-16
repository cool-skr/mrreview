import os
from typing import List, Dict, Tuple
from rich.progress import track
from .utils.file_handler import find_code_files
from .analysis.ast_parser import parse_file_to_ast
from .analysis.issue_detector import (
    run_eslint_detector,
    run_bandit_detector,
    detect_complexity_issues,
    detect_missing_documentation,
    detect_hardcoded_secrets,
    detect_performance_issues_with_ai
)
from .ai.enricher import enrich_issue
from .analysis.models import Issue

def perform_analysis(path: str = None, files: List[str] = None, no_enrich: bool = False) -> Tuple[List[Issue], Dict[str, bytes]]:
    """
    Performs a full analysis on a given path or list of files and returns issues and file contents.
    This is the core logic engine of the agent.
    """
    if files:
        code_files = files
    elif path:
        code_files = list(find_code_files(path))
    else:
        # Neither path nor files provided, return empty
        return [], {}

    if not code_files:
        return [], {}

    all_issues = []
    file_contents: Dict[str, bytes] = {}
    for file_path in track(code_files, description="[cyan]Analyzing files...[/cyan]"):
        try:
            with open(file_path, "rb") as f:
                file_contents[file_path] = f.read()
        except Exception:
            continue
        
        all_issues.extend(run_eslint_detector(file_path))
        all_issues.extend(run_bandit_detector(file_path))
        all_issues.extend(detect_hardcoded_secrets(file_path, file_contents[file_path]))
        
        parse_result = parse_file_to_ast(file_path)
        if parse_result:
            tree, language = parse_result
            lang_name = "python" if file_path.endswith('.py') else "javascript"
            
            all_issues.extend(detect_complexity_issues(tree, language, file_path, file_contents[file_path], lang_name))
            all_issues.extend(detect_missing_documentation(tree, language, file_path, file_contents[file_path], lang_name))
            if not no_enrich:
                all_issues.extend(detect_performance_issues_with_ai(tree, language, file_path, file_contents[file_path], lang_name))

    if not no_enrich and all_issues:
        print(f"\nEnriching {len(all_issues)} issue(s) with AI... (this may take a moment)")
        enriched_issues = [
            enrich_issue(issue, file_contents[issue.file_path].decode('utf-8', errors='ignore'))
            for issue in all_issues
        ]
        all_issues = enriched_issues
        
    return all_issues, file_contents