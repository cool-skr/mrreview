import click
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from src.utils.file_handler import find_code_files
from src.analysis.ast_parser import parse_file_to_ast
from src.analysis.issue_detector import (
    detect_complexity_issues,
    detect_missing_documentation,
    detect_hardcoded_secrets,
)
from src.ai.enricher import enrich_issue

@click.group()
def cli():
    load_dotenv()

@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True))
@click.option('--no-enrich', is_flag=True, help="Disable AI enrichment for a faster, offline analysis.")
def analyze(path, no_enrich):
    """Analyzes the code repository at the given path."""
    # Create a console object for rich printing
    console = Console()

    console.print(f"🚀 Starting analysis of '{path}'...", style="bold green")
    
    code_files = list(find_code_files(path))
    if not code_files:
        console.print("No supported code files (.py, .js) found.", style="yellow")
        return
        
    console.print(f"Found {len(code_files)} code file(s) to analyze.")
    console.print("1. Running deterministic detectors...")

    all_issues = []
    file_contents = {}
    for file_path in code_files:
        try:
            with open(file_path, "rb") as f:
                file_contents[file_path] = f.read()
        except Exception: continue
        
        all_issues.extend(detect_hardcoded_secrets(file_path, file_contents[file_path]))
        
        parse_result = parse_file_to_ast(file_path)
        if parse_result:
            tree, language = parse_result
            lang_name = "python" if file_path.endswith('.py') else "javascript"
            all_issues.extend(detect_complexity_issues(tree, language, file_path, file_contents[file_path], lang_name))
            all_issues.extend(detect_missing_documentation(tree, language, file_path, file_contents[file_path], lang_name))

    if not no_enrich and all_issues:
        console.print(f"\n2. Enriching {len(all_issues)} issue(s) with AI... (this may take a moment)", style="bold cyan")
        enriched_issues = [
            enrich_issue(issue, file_contents[issue.file_path].decode('utf-8', errors='ignore'))
            for issue in all_issues
        ]
        all_issues = enriched_issues

    console.print("\n[bold magenta]3. Analysis Report:[/bold magenta]")
    if not all_issues:
        console.print("✅ No issues found. Great job!", style="bold green")
    else:
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_issues = sorted(all_issues, key=lambda i: (severity_order.get(i.severity, 99), i.file_path))
        
        console.print(f"Found {len(all_issues)} issue(s):", style="bold yellow")
        for issue in sorted_issues:
            # Construct a Markdown string for each issue
            color = {"CRITICAL": "red", "HIGH": "yellow", "MEDIUM": "cyan"}.get(issue.severity, "white")
            
            report_md = f"\n---\n"
            report_md += f"### [{issue.severity}] - `{issue.file_path}:{issue.line_number}`\n"
            report_md += f"> {issue.message}\n\n"
            
            if issue.ai_explanation:
                report_md += f"**AI Explanation:**\n{issue.ai_explanation}\n\n"
            if issue.ai_suggestion:
                report_md += f"**AI Suggestion:**\n{issue.ai_suggestion}\n"

            console.print(Markdown(report_md, style=color))

    console.print("\n✅ Analysis complete!", style="bold green")


@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True))
def ask(path):
    """Starts an interactive Q&A session about the codebase."""
    click.echo(f"🤖 Starting interactive Q&A for '{path}'. Type 'exit' to end.")
    
    
    while True:
        question = click.prompt("Ask a question about the code")
        if question.lower() == 'exit':
            break
        
        answer = f"Thinking about '{question}'... (Q&A logic not implemented yet)"
        click.echo(answer)

if __name__ == "__main__":
    cli()
