import os
import re
from typing import List, Dict, Set
from github import Github, GithubException
from git import Repo, GitCommandError
from ..analysis.models import Issue

def get_changed_files_from_diff(repo_path: str, base_sha: str, head_sha: str) -> List[str]:
    """Uses GitPython to get a list of changed files between two commits."""
    try:
        repo = Repo(repo_path)
        diff_output = repo.git.diff(f"{base_sha}...{head_sha}", name_status=True)
        changed_files = []
        for line in diff_output.splitlines():
            if '\t' in line:
                status, file_path = line.split('\t')
                if status in ['A', 'M']:
                    full_path = os.path.join(repo.working_dir, file_path)
                    changed_files.append(full_path)
        return changed_files
    except GitCommandError as e:
        print(f"Error running git diff: {e}")
        return []
    except Exception as e:
        print(f"An error occurred with GitPython: {e}")
        return []

def get_changed_lines_from_pr(pr) -> Dict[str, Set[int]]:
    """
    Parses the diff of a pull request to find all added or modified line numbers.
    """
    changed_lines = {}
    diff_files = pr.get_files()
    for file in diff_files:
        changed_lines[file.filename] = set()
        if not file.patch:
            continue
        current_line_in_file = 0
        for line in file.patch.split('\n'):
            if line.startswith('@@'):
                match = re.search(r'\+([0-9]+)', line)
                if match:
                    current_line_in_file = int(match.group(1))
            elif line.startswith('+') and not line.startswith('+++'):
                changed_lines[file.filename].add(current_line_in_file)
                current_line_in_file += 1
            elif not line.startswith('-'):
                current_line_in_file += 1
    return changed_lines


def format_issues_for_pr_comment(issues: List[Issue]) -> str:
    """
    Formats a list of issues into a single Markdown string for a PR summary comment.
    """
    if not issues:
        return "✅ **CQIA Analysis Complete**\n\nNo new issues found on the changed lines. Great job!"

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    sorted_issues = sorted(issues, key=lambda i: (severity_order.get(i.severity, 99), i.file_path, i.line_number))

    summary = f"### 🤖 CQIA Analysis Report: Found {len(sorted_issues)} issue(s)\n\n"
    summary += "| Severity | File | Line | Message |\n"
    summary += "|:---|:---|:---|:---|\n"
    
    for issue in sorted_issues:
        file_path = os.path.basename(issue.file_path) 
        message = issue.message.split('\n')[0]
        summary += f"| `{issue.severity}` | `{file_path}` | {issue.line_number} | {message} |\n"
        
    summary += "\n---\n*This comment was generated automatically by the Code Quality Intelligence Agent.*"
    return summary

def post_pr_comment(repo_name: str, pr_number: int, issues: List[Issue]):
    """
    Posts a single, consolidated summary comment to a GitHub Pull Request.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found in environment.")
        return

    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        comment_body = format_issues_for_pr_comment(issues)
        
        pr.create_issue_comment(comment_body)
        
        if issues:
            print(f"Successfully posted a summary comment with {len(issues)} issues to PR #{pr_number}.")
        else:
            print(f"Successfully posted a 'no issues found' comment to PR #{pr_number}.")

    except GithubException as e:
        print(f"GitHub API Error for repository '{repo_name}': {e.status} - {e.data.get('message')}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")