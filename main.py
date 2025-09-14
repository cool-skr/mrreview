import click
import os
from dotenv import load_dotenv

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
    """A Code Quality Intelligence Agent
    
    Set your GROQ_API_KEY in a .env file.
    """
    load_dotenv()

@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True))
@click.option('--no-enrich', is_flag=True, help="Disable AI enrichment for a faster, offline analysis.")
def analyze(path, no_enrich):
    """Analyzes the code repository at the given path."""
    click.echo(f"🚀 Starting analysis of '{path}'...")
    
    code_files = list(find_code_files(path))
    
    if not code_files:
        click.secho("No supported code files (.py, .js) found in the specified path.", fg="yellow")
        return
        
    click.echo(f"Found {len(code_files)} code file(s) to analyze.")
    click.echo("1. Running deterministic detectors...")

    all_issues = []
    file_contents = {} 
    for file_path in code_files:
        try:
            with open(file_path, "rb") as f:
                file_contents[file_path] = f.read()
        except Exception:
            continue
        
        all_issues.extend(detect_hardcoded_secrets(file_path, file_contents[file_path]))
        
        parse_result = parse_file_to_ast(file_path)
        if parse_result:
            tree, language = parse_result
            lang_name = "python" if file_path.endswith('.py') else "javascript"
            
            all_issues.extend(detect_complexity_issues(tree, language, file_path, file_contents[file_path], lang_name))
            all_issues.extend(detect_missing_documentation(tree, language, file_path, file_contents[file_path], lang_name))

    if not no_enrich and all_issues:
        click.echo(f"\n2. Enriching {len(all_issues)} issue(s) with AI... (this may take a moment)")
        enriched_issues = []
        for issue in all_issues:
            file_content_str = file_contents[issue.file_path].decode('utf-8', errors='ignore')
            enriched_issues.append(enrich_issue(issue, file_content_str))
        all_issues = enriched_issues

    click.echo("\n3. Analysis Report:")
    if not all_issues:
        click.secho("✅ No issues found. Great job!", fg="green")
    else:
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_issues = sorted(all_issues, key=lambda i: (severity_order.get(i.severity, 99), i.file_path))
        
        click.secho(f"Found {len(all_issues)} issue(s):", fg="yellow")
        for issue in sorted_issues:
            color = {"CRITICAL": "red", "HIGH": "yellow", "MEDIUM": "blue"}.get(issue.severity, "white")
            click.secho(f"\n- [{issue.severity}]", fg=color, nl=False)
            click.echo(f" {issue.file_path}:{issue.line_number}")
            click.echo(f"  └─ {issue.message}")
            
            if issue.ai_explanation:
                click.secho("    AI Explanation:", bold=True)
                click.echo(f"      {issue.ai_explanation}")
            if issue.ai_suggestion:
                click.secho("    AI Suggestion:", bold=True)
                click.echo(f"      {issue.ai_suggestion}")

    click.secho("\n✅ Analysis complete!", fg="green")


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
