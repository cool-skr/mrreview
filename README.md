# Code Quality Intelligence Agent (CQIA)

[](https://python.org)
[](https://opensource.org/licenses/MIT)
[](https://www.langchain.com/)

An advanced CLI tool that performs a multi-faceted analysis of codebases, identifies quality issues using both deterministic and AI-powered detectors, generates rich reports with visualizations, and provides an interactive, conversational Q\&A agent to explore the code.

-----

*Replace this with a screenshot or animated GIF of the agent's rich terminal output.*
*(A GIF showing the progress bar, the final rich report, and a short `ask` session would be highly effective.)*

## 🎯 The Problem

Modern software teams struggle to maintain code quality at scale. Between code reviews, testing, security, and managing technical debt, developers spend significant time on quality assurance tasks. This agent automates and augments these tasks, going beyond simple linting to provide deep, actionable insights.

## ✨ Features

  * **🧠 Multi-Faceted Analysis:** Combines multiple analysis techniques:
      * **AST Parsing:** Deep structural analysis for complexity and documentation gaps.
      * **Static Tool Orchestration:** Integrates with industry-standard tools like **Bandit** (Python security) and **ESLint** (JavaScript quality).
      * **AI-Powered Detection:** Uses LLMs to find nuanced issues like performance anti-patterns.
  * **🤖 AI-Enriched Reporting:** Goes beyond simple error codes, using an LLM to provide human-readable explanations and actionable suggestions for fixing issues.
  * **📊 Rich, Developer-Friendly Reports:**
      * Beautiful, color-coded reports directly in your terminal.
      * Optional severity distribution charts (`--chart`).
      * Optional self-contained, shareable HTML reports (`--html`).
  * **💬 Interactive Q\&A Agent:**
      * Features a powerful RAG (Retrieval-Augmented Generation) pipeline.
      * Uses a multi-step **LangGraph** agent to reason about complex, multi-context questions.
  * **🚀 GitHub Integration:**
      * Analyzes pull request diffs and posts findings as review comments directly on GitHub.
  * **📦 Professional Tooling:**
      * Packaged as a proper installable CLI tool (`cqia`).
      * Robust, asynchronous web server for remote analysis (planned).
      * Clean, modular, and extensible architecture.

## 🛠️ Installation

### Prerequisites

  * Git
  * Python 3.9, 3.10, or 3.11
  * Node.js and npm (for ESLint integration)

### Setup Instructions

1.  **Clone the Repository:**

    ```bash
    git clone <your-repository-url>
    cd cqia-agent
    ```

2.  **Set Up Python Environment:**

    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Python Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Node.js Dependencies:**

    ```bash
    npm install
    ```

5.  **Install the CLI Tool:**
    This command installs your project in "editable" mode, creating the `cqia` command.

    ```bash
    pip install -e .
    ```

## ⚙️ Configuration

The agent requires API keys for AI features and GitHub integration.

1.  Create a file named `.env` in the root of the project.
2.  Add your keys to this file. It is already in `.gitignore`, so it will not be committed.

<!-- end list -->

```env
# .env file

# Required for all AI features (enrichment, AI detectors, Q&A)
GROQ_API_KEY="gsk_YourGroqAPIKey"

# Required for the 'gh-review' command
GITHUB_TOKEN="ghp_YourGitHubPersonalAccessToken"
```

## 📖 Usage

### Analyzing a Repository

The `analyze` command is the main entry point for running a code quality scan.

**Basic Analysis with AI Enrichment:**

```bash
cqia analyze /path/to/your/project
```

**Analysis with Chart and HTML Report:**

```bash
cqia analyze . --chart --html report.html
```

**Fast Analysis (No AI Features):**

```bash
cqia analyze . --no-enrich
```

### Interactive Q\&A

First, run `analyze` on a repository to build the knowledge base. Then, start the interactive session with the `ask` command.

```bash
# Step 1: Analyze and build the index
cqia analyze /path/to/your/project

# Step 2: Start the Q&A session
cqia ask /path/to/your/project
```

**Sample Questions:**

  * `What are the most critical issues in this codebase?`
  * `Explain the complexity issue in test/test.py.`
  * `Give me a better, refactored version of the inefficientStringBuilder function.`
  * `Compare the security issues found by Bandit and the hardcoded secret detector.`

### GitHub PR Review

To analyze a pull request and post comments:

```bash
cqia gh-review <owner/repo> <pr_number> --path . --base <base_sha> --head <head_sha>
```

  * `<owner/repo>`: e.g., `my-username/my-cool-project`
  * `<pr_number>`: The number of the pull request on GitHub.
  * `<base_sha>`: The commit SHA of the target branch (e.g., `main`).
  * `<head_sha>`: The commit SHA of the feature branch.

## 📁 Project Structure

```
cqia/
├── .env                  # Environment variables (API keys)
├── .gitignore
├── package.json          # Node.js dependencies (ESLint)
├── pyproject.toml        # Python package definition and dependencies
├── README.md             # This file
├── test/                 # Test files (test.py, test.js)
├── venv/                 # Python virtual environment
└── src/
    └── cqia_agent/       # The core Python package
        ├── __init__.py
        ├── main.py       # CLI command definitions (using Click)
        ├── core_analyzer.py # The central analysis orchestration logic
        ├── ai/             # Modules for AI interaction (caller, enricher)
        ├── analysis/     # Deterministic detectors (AST, models, etc.)
        ├── integrations/ # GitHub integration logic
        ├── qa/           # RAG and Agentic Q&A logic (indexer, agent)
        └── reporting/    # Report generators (display, visualizer, HTML)
```

## 📄 License

This project is licensed under the MIT License.