import os
from github import Github, GithubException
from dotenv import load_dotenv
from datetime import datetime

# --- ACTION REQUIRED: PLEASE EDIT THESE THREE VALUES ---

# 1. Put your repository name here in the format "owner/repo"
REPO_NAME = "cool-skr/mrreview" 

# 2. Put the number of an open Pull Request from that repository here
PR_NUMBER = 1

# 3. This is the comment that will be posted
COMMENT_BODY = f"Hello from the CQIA Agent! This is a test comment to verify API access. It was posted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."

# ----------------------------------------------------

def post_test_comment():
    """
    A simple script to test posting a comment to a GitHub PR.
    """
    print("--- Running GitHub PR Comment Test ---")

    # 1. Load environment variables from .env file
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")

    if not token :
        print("\n❌ ERROR: GITHUB_TOKEN not found or invalid in your .env file.")
        return
    
    if REPO_NAME == "YOUR_USERNAME/YOUR_REPO_NAME" or PR_NUMBER == 0:
        print("\n❌ ERROR: Please edit the REPO_NAME and PR_NUMBER variables in this script before running.")
        return

    print(f"Attempting to post a comment to PR #{PR_NUMBER} in repository '{REPO_NAME}'...")

    try:
        # 2. Authenticate and get the PR object
        g = Github(token)
        repo = g.get_repo(REPO_NAME)
        pr = repo.get_pull(PR_NUMBER)

        # 3. Create the comment using create_issue_comment
        pr.create_issue_comment(COMMENT_BODY)

        print("\n✅ SUCCESS! The test comment was posted to your pull request.")
        print("Please go to the GitHub website to verify.")

    except GithubException as e:
        print(f"\n❌ FAILED: A GitHub API error occurred.")
        print(f"  - Status Code: {e.status}")
        print(f"  - Error Message: {e.data.get('message')}")
        print("\n  Common Fixes:")
        print("  - For 404 errors: Double-check your REPO_NAME.")
        print("  - For 403/401 errors: Verify your GITHUB_TOKEN permissions (it needs 'repo' scope, 'pull_requests: write' permission, and access to this specific repository).")
    except Exception as e:
        print(f"\n❌ FAILED: An unexpected error occurred: {e}")

if __name__ == "__main__":
    post_test_comment()