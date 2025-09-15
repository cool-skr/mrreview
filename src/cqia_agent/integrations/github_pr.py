# src/cqia_agent/integrations/github_pr.py
import os
from typing import List
from github import Github, GithubException
from git import Repo, GitCommandError
from ..analysis.models import Issue

def get_changed_files_from_diff(repo_path: str, base_sha: str, head_sha: str) -> List[str]:
    """Uses GitPython to get a list of changed files between two commits."""
    try:
        repo = Repo(repo_path)
        # Use git diff to find files that were added (A) or modified (M)
        diff_output = repo.git.diff(f"{base_sha}...{head_sha}", name_status=True)
        
        changed_files = []
        for line in diff_output.splitlines():
            status, file_path = line.split('\t')
            # We are interested in added or modified files
            if status in ['A', 'M']:
                # We need the full path for our analyzer
                full_path = os.path.join(repo.working_dir, file_path)
                changed_files.append(full_path)
        return changed_files
    except GitCommandError as e:
        print(f"Error running git diff: {e}")
        return []
    except Exception as e:
        print(f"An error occurred with GitPython: {e}")
        return []

def post_pr_review(repo_name: str, pr_number: int, head_sha: str, issues: List[Issue]):
    """Posts a list of issues as comments on a GitHub Pull Request."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found in environment. Cannot post review.")
        return

    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        if pr.head.sha != head_sha:
            print("Warning: The local head SHA does not match the PR's head SHA. Comments may be on outdated code.")

        comments = []
        for issue in issues:
            relative_path = os.path.relpath(issue.file_path, start=os.getcwd())
            
            pr_files = [f.filename for f in pr.get_files()]
            if relative_path.replace('\\', '/') not in pr_files:
                continue

            comment_body = (f"**CQIA Found an Issue: [{issue.severity}]**\n\n"
                          f"**Code:** `{issue.code}`\n"
                          f"**Message:** {issue.message}\n\n")
            if issue.ai_suggestion:
                comment_body += f"**AI Suggestion:**\n{issue.ai_suggestion}"
            
            comments.append({"body": comment_body, "path": relative_path, "line": issue.line_number})
        
        if not comments:
            print("No new issues found on the changed lines of this PR.")
            pr.create_issue_comment("✅ CQIA analysis complete. No new issues found!")
            return

        commit_obj = repo.get_commit(sha=pr.head.sha)

        pr.create_review(
            commit=commit_obj,
            body="CQIA found some issues in this PR. Please review the comments below.",
            event="COMMENT",
            comments=comments
        )
        print(f"Successfully posted {len(comments)} comments to PR #{pr_number} in {repo_name}.")

    except GithubException as e:
        print(f"GitHub API Error for repository '{repo_name}': {e.status} - {e.data.get('message')}")
        print("Please check that the repository name is correct and your GITHUB_TOKEN has the 'repo' scope.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")